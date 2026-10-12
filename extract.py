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


DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

STATE_MAP = {
    # Uttar Pradesh (UPPCL discoms)
    "uttar pradesh": "UP",
    "उत्तर प्रदेश": "UP",
    "uppcl": "UP",
    "pvvnl": "UP",
    "mvvnl": "UP",
    "dvvnl": "UP",
    "puvvnl": "UP",
    "kesco": "UP",
    "पश्चिमांचल": "UP",
    "मध्यांचल": "UP",
    "दक्षिणांचल": "UP",
    "पूर्वांचल": "UP",
    # Rajasthan (JVVNL/AVVNL/JdVVNL)
    "rajasthan": "RJ",
    "राजस्थान": "RJ",
    "jvvnl": "RJ",
    "avvnl": "RJ",
    "jdvvnl": "RJ",
    "जयपुर": "RJ",
    "अजमेर": "RJ",
    "जोधपुर": "RJ",
    # Maharashtra (MSEDCL)
    "maharashtra": "MH",
    "महाराष्ट्र": "MH",
    "msedcl": "MH",
    "mahavitaran": "MH",
    "महावितरण": "MH",
    "महाडिस्कॉम": "MH",
    "best": "MH",
    # Delhi (BSES/TPDDL)
    "delhi": "DL",
    "दिल्ली": "DL",
    "bses": "DL",
    "brpl": "DL",
    "bypl": "DL",
    "tpddl": "DL",
    "tata power": "DL",
}


PROMPT_TEXT = (
    "You are an expert bilingual OCR and electricity bill parser specialized in Indian DISCOM bills "
    "(such as UPPCL, JVVNL, MSEDCL, BSES, TPDDL, BESCOM, etc.).\n"
    "Indian electricity bills are frequently printed in HINDI (हिंदी / देवनागरी लिपि), ENGLISH, or BILINGUALLY.\n"
    "Carefully extract the bill details and return ONLY a single valid JSON object:\n"
    "{\n"
    '  "state": "UP" | "RJ" | "MH" | "DL" | other 2-letter state code or null,\n'
    '  "units_kwh": float or null,\n'
    '  "billing_days": integer or null,\n'
    '  "amount_payable": float or null,\n'
    '  "sanctioned_load_kw": float or null,\n'
    '  "fixed_charges": float or null,\n'
    '  "confidence": float between 0.0 and 1.0\n'
    "}\n\n"
    "BILINGUAL FIELD MAPPING (Search for both Hindi and English terms):\n"
    "1. STATE (state):\n"
    "   - UP (Uttar Pradesh): UPPCL, पश्चिमांचल (PVVNL), मध्यांचल (MVVNL), दक्षिणांचल (DVVNL), पूर्वांचल (PUVVNL), केस्को (KESCO), उत्तर प्रदेश\n"
    "   - RJ (Rajasthan): JVVNL, AVVNL, JdVVNL, जयपुर विद्युत, अजमेर विद्युत, जोधपुर विद्युत, राजस्थान\n"
    "   - MH (Maharashtra): MSEDCL, Mahavitaran, महावितरण, महाडिस्कॉम, BEST, Tata Power, Adani, महाराष्ट्र\n"
    "   - DL (Delhi): BSES (BRPL/BYPL), TPDDL (Tata Power-DDL), NDMC, दिल्ली\n\n"
    "2. UNITS CONSUMED / BILLED (units_kwh):\n"
    "   - In HINDI: 'उपभोग यूनिट', 'खपत यूनिट', 'कुल यूनिट', 'बिल यूनिट', 'खपत', 'प्रयुक्त यूनिट', 'वास्तविक खपत', 'यूनिट (kWh)'\n"
    "   - In ENGLISH: 'Billed Units', 'Units Consumed', 'Total Consumption', 'Active Energy Consumption', 'Units (kWh)', 'kWh'\n"
    "   - If not labeled directly, calculate: Current Reading (वर्तमान पठन) - Previous Reading (पिछला पठन).\n\n"
    "3. TOTAL AMOUNT PAYABLE (amount_payable):\n"
    "   - In HINDI: 'कुल देय राशि', 'देय राशि', 'कुल धनराशि', 'भुगतान राशि', 'अंतिम देय राशि', 'शुद्ध देय राशि', 'वर्तमान बिल राशि'\n"
    "   - In ENGLISH: 'Total Amount Payable', 'Net Payable', 'Total Bill Amount', 'Amount Due', 'Net Amount', 'Total (₹)'\n\n"
    "4. SANCTIONED LOAD (sanctioned_load_kw):\n"
    "   - In HINDI: 'स्वीकृत भार', 'स्वीकृत लोड', 'अनुबंधित भार', 'संवितरित भार', 'भार (kW / किलोवाट / HP)'\n"
    "   - In ENGLISH: 'Sanctioned Load', 'Connected Load', 'Contract Demand', 'Load (kW)'\n"
    "   - If load is in HP (हॉर्सपावर), multiply by 0.746 to convert to kW.\n\n"
    "5. FIXED CHARGES (fixed_charges):\n"
    "   - In HINDI: 'स्थायी शुल्क', 'नियत शुल्क', 'नियत प्रभार', 'मांग प्रभार'\n"
    "   - In ENGLISH: 'Fixed Charges', 'Demand Charges', 'Meter Rent'\n\n"
    "6. BILLING DAYS (billing_days):\n"
    "   - In HINDI: 'बिल अवधि', 'बिलिंग दिन', 'दिन'\n"
    "   - In ENGLISH: 'Billing Days', 'Bill Period Days', 'Days' (defaults to 30 if not specified)\n\n"
    "NUMERIC & DEVANAGARI RULES:\n"
    "- If numbers appear in Devanagari numerals (०,१,२,३,४,५,६,७,८,९), convert them to Arabic numerals (0-9).\n"
    "- Output ONLY the raw JSON object without markdown code blocks, backticks, or conversational preamble."
)


def _normalize_extracted_dict(data: dict) -> dict:
    """Normalize state codes, Devanagari numerals, currency symbols, and units."""
    if not isinstance(data, dict):
        return {}

    clean = {}

    # State normalization
    raw_state = str(data.get("state") or "").strip().lower()
    clean_state = None
    for pattern, code in STATE_MAP.items():
        if pattern in raw_state:
            clean_state = code
            break
    if not clean_state:
        # Check standard 2-letter uppercase codes
        candidate = raw_state.strip().upper()
        if candidate in ["MH", "RJ", "UP", "DL", "GJ", "MP", "HR", "PB", "KA", "TN", "KL", "WB"]:
            clean_state = candidate
    clean["state"] = clean_state

    # Number cleaning helper
    def parse_num(val) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).translate(DEVANAGARI_DIGITS)
        s = re.sub(r"[₹$,\sA-Za-z\/\-\u0900-\u097F]", "", s)
        m = re.search(r"\d+(\.\d+)?", s)
        if m:
            try:
                return float(m.group(0))
            except ValueError:
                return None
        return None

    clean["units_kwh"] = parse_num(data.get("units_kwh") or data.get("units"))
    clean["amount_payable"] = parse_num(data.get("amount_payable") or data.get("amount"))
    clean["sanctioned_load_kw"] = parse_num(data.get("sanctioned_load_kw") or data.get("sanctioned_load") or data.get("load"))
    clean["fixed_charges"] = parse_num(data.get("fixed_charges"))

    raw_days = parse_num(data.get("billing_days") or data.get("days"))
    clean["billing_days"] = int(round(raw_days)) if raw_days is not None else None

    raw_conf = parse_num(data.get("confidence"))
    clean["confidence"] = min(1.0, max(0.0, raw_conf)) if raw_conf is not None else 0.85

    return clean


def _clean_json_response(raw_text: str) -> dict:
    """Clean markdown code fences, commentary preambles, and parse JSON."""
    raw = raw_text.strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return _normalize_extracted_dict(parsed)
        except Exception:
            pass
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        parsed = json.loads(raw)
        return _normalize_extracted_dict(parsed)
    except Exception:
        return {}


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


async def _extract_with_nvidia(image_bytes: bytes, content_type: str) -> dict:
    """Extract bill data using free NVIDIA NIM Image-to-Text vision models."""
    from openai import OpenAI

    api_key = os.environ.get("NVIDIA_API_KEY")
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = content_type or "image/jpeg"
    data_url = f"data:{mime};base64,{b64}"

    # Default to NVIDIA NIM's active Image-to-Text VLM endpoint
    model_name = os.environ.get("NVIDIA_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")

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
    Send image to available free vision model (Gemini or NVIDIA NIM) or AWS Bedrock.
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

    # 2. Try NVIDIA NIM Vision
    if os.environ.get("NVIDIA_API_KEY"):
        try:
            return await _extract_with_nvidia(image_bytes, content_type)
        except Exception as exc:
            logger.warning("NVIDIA vision extraction failed (%s), trying fallbacks", exc)

    # 3. Try AWS Bedrock
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        try:
            return await _extract_with_bedrock(image_bytes, content_type)
        except Exception as exc:
            logger.warning("Bedrock vision extraction failed (%s)", exc)

    # If no provider is configured, return helpful guidance
    return {
        "error": "No vision API key found. Add GEMINI_API_KEY (free at aistudio.google.com) or NVIDIA_API_KEY (free at build.nvidia.com) to your .env file to enable photo OCR.",
        "confidence": 0.0,
    }
