import os
import re
import json
import logging
import base64
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)

PHOTO_ENABLED = os.environ.get("PHOTO_ENABLED", "true").lower() == "true"
MODEL_ID = os.environ.get("VISION_MODEL_ID", os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"))
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


class BillExtraction(BaseModel):
    state: Optional[str] = None
    units_kwh: Optional[float] = None
    billing_days: Optional[int] = None
    amount_payable: Optional[float] = None
    sanctioned_load_kw: Optional[float] = None
    fixed_charges: Optional[float] = None
    confidence: float = 0.0
    error: Optional[str] = None


PROMPT_TEXT = (
    "You are an expert OCR and electricity bill parser for Indian DISCOM bills (e.g. MSEDCL, UPPCL, BSES, JVVNL, TNEB, BESCOM, etc.). "
    "Extract the following fields from this electricity bill and return ONLY a single valid JSON object:\n"
    "{\n"
    '  "state": "MH" | "RJ" | "UP" | "DL" | other 2-letter state code or null,\n'
    '  "units_kwh": float or null,\n'
    '  "billing_days": integer or null,\n'
    '  "amount_payable": float or null,\n'
    '  "sanctioned_load_kw": float or null,\n'
    '  "fixed_charges": float or null,\n'
    '  "confidence": float between 0.0 and 1.0\n'
    "}\n"
    "Rules:\n"
    "1. Look for 'Units consumed', 'Billed Units', 'Total consumption' for units_kwh.\n"
    "2. If a value is missing or unclear, output null. Never guess or hallucinate.\n"
    "3. Confidence should reflect overall legibility and extraction completeness.\n"
    "4. Output strictly valid JSON without any markdown formatting or commentary."
)


def _clean_json_response(raw_text: str) -> dict:
    """Clean markdown code fences, commentary preambles, and parse JSON."""
    raw = raw_text.strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return json.loads(raw)


async def _extract_with_gemini(image_bytes: bytes, content_type: str) -> dict:
    """Extract bill data using free Google Gemini Flash vision models."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    candidates = [
        os.environ.get("GEMINI_VISION_MODEL", "gemini-3.5-flash"),
        "gemini-flash-latest",
        "gemini-3.8-flash",
    ]

    mime = content_type or "image/jpeg"
    part = types.Part.from_bytes(data=image_bytes, mime_type=mime)
    config = types.GenerateContentConfig(temperature=0.0)

    last_exc = None
    for model_name in candidates:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=[part, PROMPT_TEXT],
                config=config,
            )
            parsed = _clean_json_response(resp.text or "{}")
            validated = BillExtraction(**parsed)
            return validated.model_dump()
        except Exception as exc:
            last_exc = exc
            logger.info("Gemini %s attempt failed (%s), trying next candidate", model_name, exc)

    raise last_exc or RuntimeError("All Gemini vision model candidates failed")


async def _extract_with_groq(image_bytes: bytes, content_type: str) -> dict:
    """Extract bill data using Groq vision (if supported by active key)."""
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = content_type or "image/jpeg"
    data_url = f"data:{mime};base64,{b64}"

    model_name = os.environ.get("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")

    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_TEXT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    content = resp.choices[0].message.content or "{}"
    parsed = _clean_json_response(content)
    validated = BillExtraction(**parsed)
    return validated.model_dump()


async def _extract_with_nvidia(image_bytes: bytes, content_type: str) -> dict:
    """Extract bill data using free NVIDIA NIM Image-to-Text vision models."""
    from openai import OpenAI

    api_key = os.environ.get("NVIDIA_API_KEY")
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = content_type or "image/jpeg"
    data_url = f"data:{mime};base64,{b64}"

    # Default to NVIDIA NIM's active Image-to-Text VLM endpoint
    model_name = os.environ.get("NVIDIA_VISION_MODEL", "Qwen/Qwen-Image-2512")

    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_TEXT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        temperature=0.0,
    )

    content = resp.choices[0].message.content or "{}"
    parsed = _clean_json_response(content)
    validated = BillExtraction(**parsed)
    return validated.model_dump()


async def _extract_with_bedrock(image_bytes: bytes, content_type: str) -> dict:
    """Extract bill data using AWS Bedrock Claude vision."""
    if boto3 is None:
        raise ValueError("boto3 is not available")

    img_fmt = "jpeg"
    lower_type = (content_type or "").lower()
    if "png" in lower_type:
        img_fmt = "png"
    elif "webp" in lower_type:
        img_fmt = "webp"
    elif "gif" in lower_type:
        img_fmt = "gif"

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": img_fmt,
                            "source": {"bytes": image_bytes},
                        }
                    },
                    {"text": PROMPT_TEXT},
                ],
            }
        ],
        inferenceConfig={"maxTokens": 1024, "temperature": 0.0},
    )

    message_content = response.get("output", {}).get("message", {}).get("content", [])
    raw_text = ""
    for block in message_content:
        if "text" in block:
            raw_text += block["text"]

    parsed = _clean_json_response(raw_text)
    validated = BillExtraction(**parsed)
    return validated.model_dump()


async def extract_bill_data(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Send image to available free vision model (Gemini, Groq, NVIDIA) or Bedrock.
    Return dict with extracted fields + confidence.
    """
    if not PHOTO_ENABLED:
        return {"error": "Photo extraction is disabled", "confidence": 0.0}

    # 1. Try Google Gemini (best free vision accuracy)
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        try:
            return await _extract_with_gemini(image_bytes, content_type)
        except Exception as exc:
            logger.warning("Gemini vision extraction failed (%s), trying fallbacks", exc)

    # 2. Try Groq Vision
    if os.environ.get("GROQ_API_KEY"):
        try:
            return await _extract_with_groq(image_bytes, content_type)
        except Exception as exc:
            logger.warning("Groq vision extraction failed (%s), trying fallbacks", exc)

    # 3. Try NVIDIA Vision
    if os.environ.get("NVIDIA_API_KEY"):
        try:
            return await _extract_with_nvidia(image_bytes, content_type)
        except Exception as exc:
            logger.warning("NVIDIA vision extraction failed (%s), trying fallbacks", exc)

    # 4. Try AWS Bedrock
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        try:
            return await _extract_with_bedrock(image_bytes, content_type)
        except Exception as exc:
            logger.warning("Bedrock vision extraction failed (%s)", exc)

    # If no provider is configured, return helpful guidance
    return {
        "error": "No vision API key found. Add GEMINI_API_KEY (free at aistudio.google.com) or GROQ_API_KEY (free at console.groq.com) to your .env file to enable photo OCR.",
        "confidence": 0.0,
    }
