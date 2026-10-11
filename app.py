import os
import logging
from typing import Optional, List
from pathlib import Path

# Compatibility patch for Starlette 1.x with FastAPI
import starlette.routing
_orig_router_init = starlette.routing.Router.__init__
def _compat_router_init(self, *args, on_startup=None, on_shutdown=None, **kwargs):
    return _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _compat_router_init

from fastapi import FastAPI, File, UploadFile, HTTPException
FastAPI.max_body_size = None
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

from calc import full_recommendation
from agent import get_solar_explanation, detect_provider
from extract import PHOTO_ENABLED, extract_bill_data

logger = logging.getLogger(__name__)

# Ensure static directory exists
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = STATIC_DIR / "index.html"
if not INDEX_FILE.exists():
    INDEX_FILE.write_text(
        "<!DOCTYPE html><html><head><title>SuryaSetu — Solar Advisor</title></head>"
        "<body><h1>SuryaSetu</h1><p>Backend API is active.</p></body></html>",
        encoding="utf-8",
    )

app = FastAPI(title="SuryaSetu — Solar Advisor")

# CORS middleware for local dev and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    state: str = Field(..., description="Indian state code (e.g. MH, UP, DL) or state name")
    units_kwh: float = Field(0.0, ge=0.0, le=5000.0, description="Monthly electricity consumption in kWh")
    billing_days: int = Field(30, ge=20, le=62, description="Billing cycle duration in days (20-62)")
    amount_payable: Optional[float] = Field(None, gt=0.0, description="Total electricity bill amount in INR")
    sanctioned_load_kw: Optional[float] = Field(None, gt=0.0, description="Sanctioned load in kW")
    fixed_charges: Optional[float] = Field(None, ge=0.0, description="Monthly fixed charges in INR")
    history_units: List[float] = Field(default_factory=list, description="Historical monthly consumption values")
    has_roof: str = Field("yes", description="'yes', 'no', or 'unsure'")
    lang: str = Field("en", description="Preferred explanation language: 'en' or 'hi'")

    @field_validator("has_roof")
    @classmethod
    def validate_has_roof(cls, v: str) -> str:
        norm = (v or "").strip().lower()
        if norm not in ["yes", "no", "unsure"]:
            raise ValueError("has_roof must be 'yes', 'no', or 'unsure'")
        return norm

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        norm = (v or "").strip().lower()
        if norm not in ["en", "hi"]:
            return "en"
        return norm

    @model_validator(mode="after")
    def validate_units_or_amount(self):
        has_units = self.units_kwh > 0 or (self.history_units and len(self.history_units) > 0)
        has_amount = self.amount_payable is not None and self.amount_payable > 0
        if not has_units and not has_amount:
            raise ValueError(
                "Please provide either monthly units (units_kwh), historical consumption (history_units), "
                "or bill amount payable (amount_payable)."
            )
        return self


@app.get("/")
async def index():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({"message": "SuryaSetu Solar Advisor API is running"})


@app.get("/styles.css")
async def styles():
    return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def script():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.get("/config")
async def config():
    return {
        "photo_enabled": PHOTO_ENABLED,
        "provider": detect_provider(),
    }


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    try:
        rec = full_recommendation(
            state=req.state,
            units_kwh=req.units_kwh,
            billing_days=req.billing_days,
            amount_payable=req.amount_payable,
            sanctioned_load_kw=req.sanctioned_load_kw,
            fixed_charges=req.fixed_charges,
            history_units=req.history_units,
            has_roof=req.has_roof,
            lang=req.lang,
        )

        try:
            explanation = get_solar_explanation(rec, lang=req.lang)
            if explanation:
                rec["explanation"] = explanation
        except Exception as exc:
            logger.warning("Agent explanation failed: %s", exc)

        return rec

    except Exception as exc:
        logger.error("Error in /recommend endpoint: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not PHOTO_ENABLED:
        raise HTTPException(status_code=404, detail="Photo extraction is disabled")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        content_type = file.content_type or "image/jpeg"
        extraction = await extract_bill_data(content, content_type=content_type)
        return extraction
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in /analyze endpoint: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
