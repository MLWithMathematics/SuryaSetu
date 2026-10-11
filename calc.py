import json
import math
from pathlib import Path

# Load states data once at module level
STATES_PATH = Path(__file__).parent / 'data' / 'states.json'
STATES = json.loads(STATES_PATH.read_text(encoding='utf-8'))


def get_state_data(state_code: str) -> tuple[dict, list[str]]:
    """Return (state_data, assumptions). Falls back to _other with an assumption note."""
    code = (state_code or "").strip().upper()
    assumptions: list[str] = []

    if code in STATES:
        return STATES[code], assumptions

    # Try matching state name
    for k, v in STATES.items():
        if k != "_other" and v.get("name", "").strip().lower() == code.lower():
            return v, assumptions

    assumptions.append(
        f"State '{state_code}' not found in database; using national average tariff and solar yield assumptions."
    )
    return STATES["_other"], assumptions


def monthly_units(units_kwh: float, billing_days: int = 30, history_units: list[float] | None = None) -> float:
    """Scale units to 30 days, or average history_units if provided."""
    if history_units and len(history_units) > 0:
        avg = sum(history_units) / float(len(history_units))
        return round(max(0.0, avg), 2)

    units = max(0.0, float(units_kwh))
    days = max(1, int(billing_days))
    scaled = (units / days) * 30.0
    return round(scaled, 2)


def size_system(monthly_units_val: float, yield_per_kw_day: float) -> float:
    """kW = monthly_units / (30 * yield). Rounded to nearest 0.5, clamped 1-10."""
    effective_yield = max(1.0, float(yield_per_kw_day))
    raw_kw = monthly_units_val / (30.0 * effective_yield)
    rounded = round(raw_kw * 2.0) / 2.0
    clamped = max(1.0, min(10.0, rounded))
    return round(clamped, 1)


def compute_bill(units: float, state_code: str) -> float:
    """Apply slab tariff + fixed charges. Floor at 0."""
    state_data, _ = get_state_data(state_code)
    fixed_charge = float(state_data.get("fixed_charge_per_month", 0.0))
    slabs = state_data.get("domestic_slabs", [])

    if units <= 0:
        return round(max(0.0, fixed_charge), 2)

    remaining_units = float(units)
    energy_charge = 0.0

    for slab in slabs:
        from_kwh = float(slab.get("from_kwh", 0))
        to_kwh = slab.get("to_kwh")
        rate = float(slab.get("rate_per_kwh", 0.0))

        slab_start = max(0.0, from_kwh - 1.0) if from_kwh > 0 else 0.0

        if to_kwh is not None:
            slab_cap = float(to_kwh) - slab_start
            units_in_slab = min(remaining_units, slab_cap)
            energy_charge += units_in_slab * rate
            remaining_units -= units_in_slab
            if remaining_units <= 0:
                break
        else:
            # Unbounded top slab
            energy_charge += remaining_units * rate
            remaining_units = 0.0
            break

    total_bill = max(0.0, energy_charge + fixed_charge)
    return round(total_bill, 2)


def subsidy_for(system_kw: float) -> tuple[float, str]:
    """PM Surya Ghar subsidy: Rs 30,000/kW for first 2 kW, Rs 18,000/kW for next 1 kW. Cap at 3 kW (max Rs 78,000). Returns (subsidy_amount, explanation)."""
    kw = max(0.0, float(system_kw))
    if kw <= 0:
        return 0.0, "No subsidy for 0 kW system."

    # Tier 1: up to 2 kW @ 30,000/kW
    tier1_kw = min(kw, 2.0)
    subsidy_tier1 = tier1_kw * 30000.0

    # Tier 2: next 1 kW (from 2 to 3 kW) @ 18,000/kW
    tier2_kw = max(0.0, min(kw - 2.0, 1.0))
    subsidy_tier2 = tier2_kw * 18000.0

    # Cap at 3 kW total (Rs 78,000 max)
    total_subsidy = round(min(78000.0, subsidy_tier1 + subsidy_tier2), 2)

    explanation = (
        f"PM Surya Ghar Muft Bijli Yojana: ₹{int(total_subsidy):,} subsidy "
        f"(₹30,000/kW for up to 2 kW + ₹18,000 for 3rd kW, max ₹78,000)."
    )
    return total_subsidy, explanation


def payback_for(cost: float, subsidy: float, annual_savings: float) -> float:
    """(cost - subsidy) / annual_savings. Handle zero savings -> return 99."""
    if annual_savings <= 0:
        return 99.0

    net_cost = max(0.0, float(cost) - float(subsidy))
    if net_cost <= 0:
        return 0.0

    payback = net_cost / float(annual_savings)
    return round(min(99.0, payback), 1)


def estimate_units_from_amount(amount: float, state_code: str) -> float:
    """Invert the slab function to estimate kWh from bill amount."""
    state_data, _ = get_state_data(state_code)
    fixed_charge = float(state_data.get("fixed_charge_per_month", 0.0))
    slabs = state_data.get("domestic_slabs", [])

    net_amount = float(amount) - fixed_charge
    if net_amount <= 0:
        return 0.0

    total_units = 0.0
    for slab in slabs:
        from_kwh = float(slab.get("from_kwh", 0))
        to_kwh = slab.get("to_kwh")
        rate = float(slab.get("rate_per_kwh", 0.0))

        if rate <= 0:
            continue

        slab_start = max(0.0, from_kwh - 1.0) if from_kwh > 0 else 0.0

        if to_kwh is not None:
            slab_cap = float(to_kwh) - slab_start
            cost_of_slab = slab_cap * rate

            if net_amount <= cost_of_slab:
                units = net_amount / rate
                total_units += units
                net_amount = 0.0
                break
            else:
                total_units += slab_cap
                net_amount -= cost_of_slab
        else:
            # Unbounded slab
            units = net_amount / rate
            total_units += units
            net_amount = 0.0
            break

    return round(total_units, 1)


def compute_emi(principal: float, annual_rate: float = 5.75, tenure_years: int = 10) -> float:
    """Standard EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)."""
    p = max(0.0, float(principal))
    if p <= 0:
        return 0.0

    n = max(1, int(tenure_years) * 12)
    monthly_rate = (annual_rate / 100.0) / 12.0

    if monthly_rate <= 0:
        return round(p / n, 2)

    factor = math.pow(1.0 + monthly_rate, n)
    emi = (p * monthly_rate * factor) / (factor - 1.0)
    return round(emi, 2)


def full_recommendation(
    state: str,
    units_kwh: float,
    billing_days: int = 30,
    amount_payable: float | None = None,
    sanctioned_load_kw: float | None = None,
    fixed_charges: float | None = None,
    history_units: list[float] | None = None,
    has_roof: str = "yes",
    lang: str = "en",
) -> dict:
    """Orchestrate all calculations and return the full verdict dict."""
    state_data, assumptions = get_state_data(state)
    has_roof_norm = (has_roof or "yes").strip().lower()

    # Determine monthly units
    if (units_kwh is None or units_kwh <= 0) and amount_payable and amount_payable > 0:
        effective_units = estimate_units_from_amount(amount_payable, state)
        assumptions.append(
            f"Units consumed estimated as {effective_units:.1f} kWh based on bill amount ₹{amount_payable:.2f}."
        )
    else:
        effective_units = monthly_units(units_kwh or 0.0, billing_days, history_units)

    if billing_days != 30 and (not history_units or len(history_units) == 0):
        assumptions.append(
            f"Billed units normalized from {billing_days} days to standard 30-day billing cycle."
        )

    # Compute bill before solar
    bill_before = compute_bill(effective_units, state)
    if fixed_charges is not None and fixed_charges > 0:
        # If user explicitly provided fixed charges, note it
        assumptions.append(f"Using state tariff fixed charge baseline of ₹{state_data['fixed_charge_per_month']}/mo.")

    # Check sanctioned load assumption
    if sanctioned_load_kw is not None and sanctioned_load_kw > 0:
        assumptions.append(f"Sanctioned load recorded as {sanctioned_load_kw:.1f} kW.")

    # Solar system sizing (rooftop solar assumed)
    yield_rate = float(state_data.get("yield_kwh_per_kw_day", 4.2))
    system_kw = size_system(effective_units, yield_rate)

    if sanctioned_load_kw is not None and sanctioned_load_kw > 0 and system_kw > sanctioned_load_kw:
        assumptions.append(
            f"Recommended solar size ({system_kw} kW) exceeds your sanctioned load ({sanctioned_load_kw} kW). DISCOM load enhancement will be required."
        )

    generated_units = round(system_kw * yield_rate * 30.0, 1)
    net_units = max(0.0, effective_units - generated_units)
    bill_after = compute_bill(net_units, state)

    savings_monthly = round(max(0.0, bill_before - bill_after), 2)
    savings_annual = round(savings_monthly * 12.0, 2)

    cost_per_kw = float(state_data.get("cost_per_kw", 55000.0))
    total_cost = round(system_kw * cost_per_kw, 2)

    subsidy_amount, subsidy_exp = subsidy_for(system_kw)
    payback_years = payback_for(total_cost, subsidy_amount, savings_annual)

    net_capital = max(0.0, total_cost - subsidy_amount)
    emi = compute_emi(net_capital, annual_rate=5.75, tenure_years=10)

    checklist = [
        "Inspect terrace for shadow-free South-facing orientation and structural weight support.",
        "Ensure electricity connection and bill are registered in property owner's name.",
        "Register on the PM Surya Ghar National Portal (https://pmsuryaghar.gov.in).",
        "Select an empanelled vendor from your DISCOM list for turnkey installation.",
        "Apply for bi-directional net-meter inspection and grid synchronization with your DISCOM."
    ]

    return {
        "system_kw": system_kw,
        "subsidy": subsidy_amount,
        "cost": total_cost,
        "bill_before": bill_before,
        "bill_after": bill_after,
        "payback_years": payback_years,
        "emi": emi,
        "explanation": subsidy_exp,
        "checklist": checklist,
        "assumptions": assumptions,
        "has_roof": has_roof_norm,
        "savings_monthly": savings_monthly,
        "savings_annual": savings_annual,
        "generated_units": generated_units,
    }
