"""
Unit tests for amortization calculations.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from calc.amortization import amortize, total_payments, remaining_balance_at_month


def test_amortize_basic():
    """Test basic amortization calculation."""
    # Known test case: $100,000 loan at 6% for 30 years
    loan_amount = 100000
    rate = 0.06
    term = 30
    
    schedule = amortize(loan_amount, rate, term)
    
    # Should have 360 months
    assert len(schedule) == 360
    
    # First payment should be around $599.55
    first_payment = schedule.iloc[0]["interest"] + schedule.iloc[0]["principal"]
    assert abs(first_payment - 599.55) < 1.0
    
    # First month interest should be $500 (100k * 0.06 / 12)
    assert abs(schedule.iloc[0]["interest"] - 500.0) < 0.01
    
    # Final balance should be near zero
    assert schedule.iloc[-1]["balance"] < 1.0


def test_amortize_zero_loan():
    """Test amortization with zero loan amount (100% down payment)."""
    schedule = amortize(0, 0.06, 30)
    
    # Should return empty DataFrame
    assert schedule.empty


def test_total_payments():
    """Test total payments calculation."""
    schedule = amortize(100000, 0.06, 30)
    totals = total_payments(schedule)
    
    # Total payments should be around $215,838
    assert abs(totals["total_payments"] - 215838) < 100
    
    # Total principal should equal original loan
    assert abs(totals["total_principal"] - 100000) < 1.0
    
    # Total interest should be around $115,838
    assert abs(totals["total_interest"] - 115838) < 100


def test_remaining_balance():
    """Test remaining balance calculation."""
    # After 120 months (10 years) of a 30-year loan
    remaining = remaining_balance_at_month(100000, 0.06, 30, 120)
    
    # Should be around $79,000-$81,000
    assert 79000 < remaining < 81000
    
    # After full term should be zero
    remaining_end = remaining_balance_at_month(100000, 0.06, 30, 360)
    assert remaining_end < 1.0


def test_edge_cases():
    """Test edge cases."""
    # Zero loan amount
    assert remaining_balance_at_month(0, 0.06, 30, 120) == 0
    
    # Month beyond term
    assert remaining_balance_at_month(100000, 0.06, 30, 400) == 0
    
    # Zero or negative month
    assert remaining_balance_at_month(100000, 0.06, 30, 0) == 0
    assert remaining_balance_at_month(100000, 0.06, 30, -5) == 0


if __name__ == "__main__":
    pytest.main([__file__]) 