import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project directory
load_dotenv(Path(__file__).parent / ".env")

from calc import full_recommendation, size_system, compute_bill, subsidy_for, payback_for

try:
    from strands import Agent
    from strands.models.bedrock import BedrockModel
except ImportError:
    Agent = None
    BedrockModel = None

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def detect_provider() -> str:
    """Detect which AI provider is configured."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("NVIDIA_API_KEY"):
        return "nvidia"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        return "bedrock"
    return "offline"


def _template_explanation(rec: dict, lang: str = "en") -> str:
    """Detailed template-based explanation matching official DISCOM & PM Surya Ghar metrics."""
    system_kw = rec.get("system_kw", 0.0)
    cost = rec.get("cost", 0.0)
    subsidy = rec.get("subsidy", 0.0)
    savings_monthly = rec.get("savings_monthly", 0.0)
    payback_years = rec.get("payback_years", 0.0)
    bill_before = rec.get("bill_before", 0.0)
    bill_after = rec.get("bill_after", 0.0)
    emi = rec.get("emi", 0.0)

    if lang == "hi":
        bill_after_text = "लगभग नगण्य" if bill_after <= 150 else f"लगभग ₹{int(bill_after):,}"
        return (
            f"आपके उपभोग के आधार पर {system_kw:.1f} kW का सोलर सिस्टम उपयुक्त है जिसकी अनुमानित लागत ₹{int(cost):,} है। "
            f"पीएम सूर्य घर योजना के तहत आपको ₹{int(subsidy):,} की सब्सिडी मिलेगी, जिससे आपका मासिक बिल ₹{int(bill_before):,} "
            f"से घटकर {bill_after_text} हो जाएगा। अनुमानित पेबैक अवधि {payback_years:.1f} वर्ष है तथा ईएमआई लगभग ₹{int(emi):,}/माह होगी "
            f"(कृपया ध्यान दें कि ये सभी आंकड़े अनुमानित हैं)।"
        )

    # English fallback
    bill_after_text = "almost negligible" if bill_after <= 150 else f"about ₹{int(bill_after):,}"
    return (
        f"Based on your electricity usage, we recommend a {system_kw:.1f} kW rooftop solar system with an estimated "
        f"cost of ₹{int(cost):,}. Under PM Surya Ghar Muft Bijli Yojana, you are eligible for ₹{int(subsidy):,} in direct subsidy, "
        f"cutting your monthly bill from ₹{int(bill_before):,} down to {bill_after_text}. The estimated payback period is "
        f"{payback_years:.1f} years with a loan EMI of approximately ₹{int(emi):,}/month (please note all figures are estimates)."
    )


def _call_gemini(user_prompt: str, system_prompt: str) -> str:
    """Free Google Gemini API via official google-genai SDK."""
    try:
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return ""

        client = genai.Client(api_key=api_key)
        candidates = [
            os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
            "gemini-flash-latest",
            "gemini-3.8-flash",
        ]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=1000,
        )
        for model_name in candidates:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config,
                )
                return (resp.text or "").strip()
            except Exception as exc:
                logger.info("Gemini explanation attempt with %s failed (%s), trying next", model_name, exc)
        return ""
    except Exception as exc:
        logger.warning("Gemini explanation failed (%s)", exc)
        return ""


def _call_groq(user_prompt: str, system_prompt: str) -> str:
    """Free Groq API (Llama 3.3 70B / 3.1 8B)."""
    try:
        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return ""

        client = Groq(api_key=api_key)
        model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("Groq explanation failed (%s)", exc)
        return ""


def _call_nvidia(user_prompt: str, system_prompt: str) -> str:
    """Free NVIDIA NIM Open Models via OpenAI client."""
    try:
        from openai import OpenAI

        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            return ""

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        model_name = os.environ.get("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")

        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("NVIDIA explanation failed (%s)", exc)
        return ""


def _call_openai(user_prompt: str, system_prompt: str) -> str:
    """Standard OpenAI-compatible API."""
    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return ""

        client = OpenAI(api_key=api_key)
        model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("OpenAI explanation failed (%s)", exc)
        return ""


def _call_strands_bedrock(user_prompt: str, system_prompt: str) -> str:
    """AWS Bedrock via Strands Agents."""
    if Agent is None or BedrockModel is None:
        return ""

    try:
        model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=[full_recommendation, size_system, compute_bill, subsidy_for, payback_for],
        )
        resp = agent(user_prompt)
        return str(resp).strip()
    except Exception as exc:
        logger.warning("Strands Bedrock agent call failed (%s)", exc)
        return ""


def _clean_explanation_text(text: str) -> str:
    """Strip annoying preambles and meta-commentary from LLM output."""
    import re
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    t = re.sub(
        r"^(here is (a|the) (detailed )?advisor verdict[^:\n]*[:\n]*|here is (a|the) [^:\n]*summary[^:\n]*[:\n]*)",
        "",
        t,
        flags=re.IGNORECASE,
    ).strip()
    return t


def get_solar_explanation(recommendation: dict, lang: str = "en") -> str:
    """
    Generate a detailed, human-readable explanation using free LLM providers
    (Google Gemini, Groq, NVIDIA NIM) or AWS Bedrock, with template fallback.
    Guarantees full numeric details (capacity, cost, subsidy, bill before/after, EMI).
    """
    # Always guarantee complete, detailed templates for both languages
    template_hi = _template_explanation(recommendation, lang="hi")
    template_en = _template_explanation(recommendation, lang="en")
    recommendation["explanation_hi"] = template_hi
    recommendation["explanation_en"] = template_en

    system_prompt = (
        "You are an expert solar energy advisor for Indian households under the PM Surya Ghar Muft Bijli Yojana. "
        "All numbers are pre-computed. Do NOT compute any numbers yourself. "
        "Explicitly state that all figures are estimates. "
        "Provide a comprehensive, reassuring 3-4 sentence breakdown including: "
        "system size (kW), total cost (₹), direct PM Surya Ghar subsidy (₹), monthly bill reduction (before vs after), "
        "payback period (years), and monthly loan EMI (₹). "
        "Do NOT include conversational preambles like 'Here is the verdict' or 'Here is a detailed advisor verdict'."
    )
    if lang == "hi":
        system_prompt += (
            "\nCRITICAL: Respond COMPLETELY in fluent, grammatical Hindi (Devanagari script). "
            "Start directly with 'आपके उपभोग के आधार पर...'. Do NOT write any English text."
        )
    else:
        system_prompt += (
            "\nCRITICAL: Respond in clear, friendly English. "
            "Start directly with 'Based on your electricity usage...'."
        )

    user_prompt = (
        f"Generate the detailed explanation for this solar recommendation:\n"
        f"{json.dumps(recommendation, indent=2)}\n"
        f"Language: {'Hindi' if lang == 'hi' else 'English'}."
    )

    provider = detect_provider()
    raw_text = ""

    if provider == "gemini":
        raw_text = _call_gemini(user_prompt, system_prompt)
    elif provider == "groq":
        raw_text = _call_groq(user_prompt, system_prompt)
    elif provider == "nvidia":
        raw_text = _call_nvidia(user_prompt, system_prompt)
    elif provider == "openai":
        raw_text = _call_openai(user_prompt, system_prompt)
    elif provider == "bedrock":
        raw_text = _call_strands_bedrock(user_prompt, system_prompt)

    # Fallbacks across configured providers if primary returned empty
    if not raw_text and (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        raw_text = _call_gemini(user_prompt, system_prompt)
    if not raw_text and os.environ.get("GROQ_API_KEY"):
        raw_text = _call_groq(user_prompt, system_prompt)
    if not raw_text and os.environ.get("NVIDIA_API_KEY"):
        raw_text = _call_nvidia(user_prompt, system_prompt)

    if raw_text:
        cleaned = _clean_explanation_text(raw_text)
        # Verify it's a complete, healthy explanation and didn't truncate
        if len(cleaned) >= 80 and not cleaned.endswith(("...", "to your", "tailored to", "your")):
            if lang == "hi":
                recommendation["explanation_hi"] = cleaned
            else:
                recommendation["explanation_en"] = cleaned
            return cleaned

    # Return the rich, complete template (matching Image 2)
    return template_hi if lang == "hi" else template_en
