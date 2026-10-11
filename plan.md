# Bijli Bill Solar Advisor: Build Plan (Local-First, Manual Form First)

**What it does:** the user enters a few details from their electricity bill (or uploads a photo to prefill them) and gets a rooftop-solar verdict: system size, subsidy, bill after solar, payback, next steps.
**Run mode:** one FastAPI server on your laptop serving both the API and the web page. Open it on your phone over the same Wi-Fi.
**Build time:** about 13 hours.
**AWS pieces:** the Strands Agents SDK on Bedrock writes the explanation and calls the calculator tools. This stays mandatory; it is what keeps the project AWS-eligible without a deployment.

## Key decision: the manual form is the product, the photo is an optional helper

- The **manual form is the main input** and is built first. It always works.
- **Photo extraction is only a prefill helper.** It fills the same form fields, and the user checks them before calculating. If it fails, nothing else breaks.
- **Hard time-box: 90 minutes** on photo extraction. If it is not giving correct units on at least 4 of 5 bills by then, set `PHOTO_ENABLED=false`, which hides the upload tab, and move on. Do not return to it.

---

## 1. Scope

**P0: must work**
1. Manual bill form (section 5).
2. Deterministic calculator: system size, subsidy, bill after solar, payback.
3. Strands agent calls the calculator tools and writes the explanation in English.
4. Verdict screen with a "what to do next" checklist.
5. Tariff data for 3 states.

**P1: in this order**
1. Photo upload that prefills the form (time-boxed, see above).
2. "No roof / flat / rented" branch with bill-cutting tips from the user's own usage.
3. "Fill sample bill" button (prefills the form with realistic values).
4. Hindi/English toggle.
5. "I only know my bill amount" mode: estimate units from the amount using the state slabs.
6. Loan EMI estimate.

**Cut:** accounts, roof detection from satellite images, vendor marketplace, more than 3 states, image storage, voice.

---

## 2. Architecture

```
Phone browser --(LAN, http://<laptop-ip>:8000)--> FastAPI (single process)
   |-- GET  /            static frontend (manual form + optional photo tab)
   |-- GET  /config      { photo_enabled: bool }
   |-- POST /recommend   form fields -> verdict            (core)
   |-- POST /analyze     bill image  -> prefill fields     (optional, P1)
                              |
 agent.py   -> Strands agent -> calc.py tools -> Bedrock text (explanation)
 calc.py    -> pure Python math + data/states.json
 extract.py -> Bedrock vision (boto3 Converse), only if PHOTO_ENABLED
```

**Rules**
- **Numbers come from code, never from the LLM.**
- **The form is the single source of truth.** `/recommend` only ever receives form fields, whether typed or prefilled.
- Nothing is stored. Photos are processed in memory and discarded.
- Phone camera capture works over plain HTTP with `<input type="file" accept="image/*" capture="environment">`.

---

## 3. Setup (hour 0 to 1)

- [ ] Python 3.11+ venv. `pip install fastapi uvicorn python-multipart pydantic boto3 strands-agents pytest`
- [ ] AWS credentials on the laptop (`aws configure`), one region where your model is available.
- [ ] Enable Bedrock model access in the console. Set `MODEL_ID=...` as an env var (check the Bedrock model catalog).
- [ ] Smoke test: a minimal Strands agent that answers "hello" through Bedrock. Do this first.
- [ ] Run `uvicorn app:app --host 0.0.0.0 --port 8000` and open it from your phone (allow the port in your firewall).

---



## 4. Manual form (frontend and request body)

Put the form first on screen. Add a small "Upload bill photo (beta)" tab only if `photo_enabled` is true.

| Field | Required | Notes |
|---|---|---|
| State | Yes | Dropdown: your 3 states plus "Other". |
| Units consumed this bill (kWh) | Yes* | Help text: "Look for 'Units consumed' or 'Total consumption' on your bill." |
| Billing days | No | Default 30. |
| Amount payable (Rs) | No* | *Needed instead of units in "amount-only" mode. |
| Sanctioned load (kW) | No | Used only for sanity checks. |
| Fixed charges (Rs) | No | Defaults from `states.json`. |
| Last months' units | No | Up to 6 numbers; used to average. |
| Roof available? | Yes | Yes / No / Not sure. |
| Language | Yes | English / Hindi (P1). |

**Validation:** units 1 to 5000, billing days 20 to 62, amounts positive. Show friendly inline errors. Category is assumed domestic; add a note that commercial bills are not supported.

**Request body for `/recommend`:**
```json
{
  "state": "string",
  "units_kwh": 0,
  "billing_days": 30,
  "amount_payable": null,
  "sanctioned_load_kw": null,
  "fixed_charges": null,
  "history_units": [],
  "has_roof": "yes|no|unsure",
  "lang": "en|hi"
}
```

**Response:**
```json
{
  "system_kw": 3.0,
  "subsidy": 0,
  "cost": 0,
  "bill_before": 0,
  "bill_after": 0,
  "payback_years": 0,
  "emi": null,
  "explanation": "...",
  "checklist": ["...", "..."],
  "assumptions": ["..."]
}
```

---

## 5. Calculator (calc.py), pure functions with tests

1. **Monthly units** = units_kwh scaled to 30 days (or average of `history_units` if present).
2. **System size (kW)** = monthly_units / (30 x yield_kwh_per_kw_day), rounded to the nearest 0.5, clamped 1 to 10.
3. **Subsidy:** the scheme caps support at 3 kW, up to Rs 78,000. Use the official per-kW split. **VERIFY on the national portal before coding.**
4. **Cost:** assumed cost per kW. **Placeholder, VERIFY.**
5. **Bill after solar:** apply the state's slab tariff to (units minus generated units), floored at 0, plus fixed charges.
6. **Annual savings** = (bill before minus bill after) x 12.
7. **Payback (years)** = (cost minus subsidy) / annual savings.
8. **Amount-only mode (P1):** invert the slab function to estimate units from amount payable.
9. **EMI (P1):** standard EMI formula. Reported scheme loan rate was 5.75% over 10 years as of March 2026. **VERIFY, may have changed.**

**Tests to write:** zero units, very high units (clamp to 10 kW), units below the first slab, unknown state (national-average fallback, flagged in `assumptions`), subsidy cap at 3 kW, near-zero savings payback, amount-only inversion round trip.

**`data/states.json`:** 3 states only. For each: domestic slabs, fixed charge, `yield_kwh_per_kw_day`. Take slabs from the DISCOM's current tariff order or your own bills; do not invent values. Yields are estimates; cross-check with a solar resource source.

---

## 6. Strands agent (agent.py)

- **Tools:** `size_system`, `compute_bill`, `subsidy_for`, `payback_for`, each a thin wrapper over calc.py.
- **System prompt:** "Call the tools for every number. Never compute or invent figures. Write a short explanation in {lang}. Say these are estimates."
- **Guardrail:** after the agent runs, check that the numbers in its response match the tool outputs. If the agent skips a tool, call the functions directly and attach the explanation anyway.
- Time-box agent debugging to 1.5 hours.

---

## 7. Photo extraction (optional, extract.py)

Only works as a prefill. Send the image to Bedrock vision and return values for the form fields: `state`, `units_kwh`, `billing_days`, `amount_payable`, `sanctioned_load_kw`, `fixed_charges`, `history_units`, plus `confidence`.

**Prompt rules:** JSON only; `null` for anything not clearly visible; never guess. Validate with pydantic; on any failure return an empty prefill and a message "Couldn't read this photo, please type the values."

**Image handling:** resize on the client to about 1280 px, JPEG quality about 0.8.

**Kill switch:** `PHOTO_ENABLED=false` hides the tab and the `/analyze` route returns 404. Use it at the 90-minute mark if needed.

---

## 8. Verdict screen

- Headline: "A 3 kW system can cut your bill from Rs X to about Rs Y."
- Cards: system size, subsidy, payback, bill after.
- 4-step checklist: apply on the national portal, DISCOM approval, installation, net metering and subsidy.
- "Estimates, not a quote" and the `assumptions` list.
- **No-roof variant:** usage-based tips instead of the solar verdict.

---

## 9. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Photo extraction misreads or takes too long | Hard stop at 90 minutes; `PHOTO_ENABLED=false`. |
| Bedrock access or quota problems | Test in hour 0 to 1; swap `MODEL_ID`. |
| Strands agent misbehaves | Guardrail plus direct function calls; keep the agent in the flow. |
| Wrong tariff or subsidy numbers | Label as estimates; verify the 3 states you use. |
| Running behind | Cut P1 from the bottom up. |

---

## 10. Repo layout

```
/app.py            # FastAPI: routes + static files
/calc.py           # sizing, tariff, subsidy, payback (pure functions)
/agent.py          # Strands agent + guardrail
/extract.py        # optional Bedrock vision prefill
/data/states.json
/static/           # index.html, app.js, styles.css
/tests/test_calc.py
/requirements.txt
/plan.md
```

