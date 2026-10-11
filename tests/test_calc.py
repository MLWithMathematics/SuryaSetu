import pytest
from calc import (
    get_state_data,
    monthly_units,
    size_system,
    compute_bill,
    subsidy_for,
    payback_for,
    estimate_units_from_amount,
    compute_emi,
    full_recommendation,
)


def test_zero_units():
    # Sizing for 0 units should clamp to minimum 1.0 kW
    system = size_system(0, 4.2)
    assert system == 1.0


def test_very_high_units():
    # Sizing for 2000 units with 4.0 yield -> 2000 / (30 * 4) = 16.67 kW -> clamp to 10.0 kW
    system = size_system(2000, 4.0)
    assert system == 10.0


def test_units_below_first_slab():
    # In MH, first slab is 0-100 at 4.75, fixed charge is 128.0
    # 50 units -> 50 * 4.75 + 128 = 237.5 + 128 = 365.5
    bill = compute_bill(50, "MH")
    assert bill == 365.5


def test_unknown_state():
    state_data, assumptions = get_state_data("UNKNOWN_STATE_XYZ")
    assert state_data["code"] == "_other"
    assert len(assumptions) > 0
    assert "not found in database" in assumptions[0]


def test_subsidy_cap_at_3kw():
    # 1 kW: 30,000
    sub1, _ = subsidy_for(1.0)
    assert sub1 == 30000.0

    # 2 kW: 60,000
    sub2, _ = subsidy_for(2.0)
    assert sub2 == 60000.0

    # 3 kW: 60,000 + 18,000 = 78,000
    sub3, _ = subsidy_for(3.0)
    assert sub3 == 78000.0

    # 5 kW: capped at 78,000
    sub5, exp5 = subsidy_for(5.0)
    assert sub5 == 78000.0
    assert "₹78,000" in exp5


def test_near_zero_savings_payback():
    payback = payback_for(cost=100000, subsidy=30000, annual_savings=0.0)
    assert payback == 99.0

    payback_negative = payback_for(cost=100000, subsidy=30000, annual_savings=-500.0)
    assert payback_negative == 99.0


def test_amount_only_mode():
    # Given an amount, estimate units, then compute bill back — verify close round-trip
    state = "MH"
    original_units = 250.0
    bill = compute_bill(original_units, state)

    estimated_units = estimate_units_from_amount(bill, state)
    assert pytest.approx(estimated_units, abs=1.0) == original_units

    # Also test through full_recommendation with units_kwh=0 and amount_payable provided
    rec = full_recommendation(state=state, units_kwh=0, amount_payable=bill)
    assert rec["system_kw"] > 0
    assert any("estimated as" in a for a in rec["assumptions"])


def test_monthly_units_scaling():
    # 100 units in 20 days -> (100 / 20) * 30 = 150 units
    scaled = monthly_units(100, billing_days=20)
    assert scaled == 150.0

    # 300 units in 60 days -> (300 / 60) * 30 = 150 units
    scaled60 = monthly_units(300, billing_days=60)
    assert scaled60 == 150.0


def test_monthly_units_with_history():
    history = [200.0, 250.0, 300.0]
    avg = monthly_units(0, billing_days=30, history_units=history)
    assert avg == 250.0


def test_emi_calculation():
    # Principal 100,000 at 5.75% for 10 years (120 months)
    # Monthly rate = 0.0575 / 12 = 0.004791666...
    # EMI should be approx 1098.24
    emi = compute_emi(100000, annual_rate=5.75, tenure_years=10)
    assert 1090 <= emi <= 1110


def test_rooftop_recommendation_always_active():
    # Since personal rooftop is always assumed, recommendations size solar systems directly
    rec = full_recommendation(state="MH", units_kwh=300)
    assert rec["system_kw"] > 0.0
    assert rec["subsidy"] > 0.0
    assert rec["cost"] > 0.0
    assert rec["bill_before"] > rec["bill_after"]
    assert rec["has_roof"] == "yes"
    assert len(rec["checklist"]) > 0
    assert any("Portal" in item or "vendor" in item.lower() for item in rec["checklist"])


def test_full_recommendation_structure():
    rec = full_recommendation(state="MH", units_kwh=300, has_roof="yes")
    required_keys = [
        "system_kw",
        "subsidy",
        "cost",
        "bill_before",
        "bill_after",
        "payback_years",
        "emi",
        "explanation",
        "checklist",
        "assumptions",
        "has_roof",
        "savings_monthly",
        "savings_annual",
        "generated_units",
    ]
    for key in required_keys:
        assert key in rec, f"Missing key '{key}' in full_recommendation response"

    assert rec["system_kw"] >= 1.0
    assert rec["cost"] > 0
    assert rec["bill_before"] > rec["bill_after"]
    assert rec["savings_monthly"] > 0
    assert rec["savings_annual"] > 0
    assert isinstance(rec["checklist"], list)
    assert isinstance(rec["assumptions"], list)


def test_rajasthan_tariff_and_high_yield():
    rec = full_recommendation("RJ", 450.0, billing_days=30, has_roof="yes")
    # Rajasthan has high solar yield (4.8 kWh/kW/day)
    assert rec["system_kw"] > 0
    assert rec["cost"] > 0
    assert rec["subsidy"] == 78000.0  # PM Surya Ghar cap
    assert rec["bill_before"] > 2500.0
    assert rec["bill_after"] < rec["bill_before"]
    assert rec["payback_years"] > 0
    # No fallback assumption should be present since RJ is officially configured
    assert not any("not found" in a.lower() for a in rec["assumptions"])

