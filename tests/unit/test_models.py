"""
Unit tests for Pydantic models.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from calc.models import UserInputs, DerivedInputs, TaxParams, CalculationResults
from pydantic import ValidationError


def test_user_inputs_valid():
    """Test valid UserInputs creation."""
    inputs = UserInputs(
        income_you=100000,
        purchase_price=500000,
        rent_today_monthly=3000
    )
    
    assert inputs.income_you == 100000
    assert inputs.purchase_price == 500000
    assert inputs.rent_today_monthly == 3000
    
    # Check defaults
    assert inputs.income_spouse == 0
    assert inputs.down_payment_pct == 0.20
    assert inputs.mortgage_rate == 0.07
    assert inputs.filing_status == "single"


def test_user_inputs_validation():
    """Test UserInputs validation."""
    # Negative income should fail
    with pytest.raises(ValidationError):
        UserInputs(
            income_you=-1000,
            purchase_price=500000,
            rent_today_monthly=3000
        )
    
    # Zero purchase price should fail
    with pytest.raises(ValidationError):
        UserInputs(
            income_you=100000,
            purchase_price=0,
            rent_today_monthly=3000
        )
    
    # Down payment > 100% should fail
    with pytest.raises(ValidationError):
        UserInputs(
            income_you=100000,
            purchase_price=500000,
            rent_today_monthly=3000,
            down_payment_pct=1.5
        )


def test_derived_inputs():
    """Test DerivedInputs calculation."""
    user_inputs = UserInputs(
        income_you=100000,
        purchase_price=500000,
        rent_today_monthly=3000,
        down_payment_pct=0.20,
        mortgage_rate=0.06,
        horizon_years=10
    )
    
    derived = DerivedInputs.from_user_inputs(user_inputs)
    
    # Check calculated values
    assert derived.loan_amount == 400000  # 500k * (1 - 0.2)
    assert derived.down_payment_amount == 100000  # 500k * 0.2
    assert derived.horizon_months == 120  # 10 * 12
    assert abs(derived.monthly_mortgage_rate - 0.005) < 0.0001  # 0.06 / 12


def test_tax_params():
    """Test TaxParams creation."""
    tax_params = TaxParams(
        federal_marginal_rate=0.24,
        state_marginal_rate=0.065,
        salt_cap=10000,
        standard_deduction=14600,
        location="NYC, NY",
        filing_status="single"
    )
    
    assert tax_params.federal_marginal_rate == 0.24
    assert tax_params.state_marginal_rate == 0.065
    assert tax_params.location == "NYC, NY"


def test_calculation_results():
    """Test CalculationResults creation."""
    results = CalculationResults(
        monthly_buy_payment=3500,
        monthly_buy_after_tax=3200,
        monthly_rent_payment=3000,
        monthly_invested_surplus=200,
        home_equity_at_exit=200000,
        investment_portfolio_value=150000,
        net_worth_difference=50000,
        npv_buy_costs=800000,
        npv_rent_costs=750000,
        npv_difference=50000,
        irr_buy_investment=0.05,
        breakeven_month=72,
        total_interest_paid=150000,
        total_tax_shield=25000,
        total_appreciation=100000
    )
    
    assert results.net_worth_difference == 50000
    assert results.breakeven_month == 72
    assert results.irr_buy_investment == 0.05


if __name__ == "__main__":
    pytest.main([__file__]) 