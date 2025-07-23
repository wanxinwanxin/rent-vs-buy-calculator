"""
Mortgage amortization calculations.
"""
import numpy as np
import numpy_financial as npf
import pandas as pd
from typing import Optional


def amortize(loan_amount: float, rate_annual: float, term_years: int) -> pd.DataFrame:
    """
    Calculate mortgage amortization schedule.
    
    Args:
        loan_amount: Principal loan amount
        rate_annual: Annual interest rate (e.g., 0.07 for 7%)
        term_years: Loan term in years
        
    Returns:
        DataFrame with columns: month, interest, principal, balance, cumulative_interest, cumulative_principal
    """
    if loan_amount <= 0:
        # No loan case (100% down payment)
        return pd.DataFrame(columns=["month", "interest", "principal", "balance", "cumulative_interest", "cumulative_principal"])
    
    n = term_years * 12
    r = rate_annual / 12
    
    # Calculate monthly payment using numpy-financial PMT function
    pmt = npf.pmt(r, n, -loan_amount)
    
    bal = loan_amount
    rows = []
    cumulative_interest = 0
    cumulative_principal = 0
    
    for m in range(1, n + 1):
        interest = bal * r
        principal = pmt - interest
        bal = max(bal - principal, 0)  # Ensure balance doesn't go negative
        
        cumulative_interest += interest
        cumulative_principal += principal
        
        rows.append({
            "month": m,
            "interest": interest,
            "principal": principal,
            "balance": bal,
            "cumulative_interest": cumulative_interest,
            "cumulative_principal": cumulative_principal
        })
    
    return pd.DataFrame(rows)


def calculate_pmi(
    loan_amount: float,
    home_value: float,
    pmi_annual_rate: float,
    pmi_threshold_ltv: float = 0.80
) -> pd.DataFrame:
    """
    Calculate PMI payments based on current loan-to-value ratio.
    
    Args:
        loan_amount: Current loan balance
        home_value: Current home value
        pmi_annual_rate: Annual PMI rate (e.g., 0.005 for 0.5%)
        pmi_threshold_ltv: LTV threshold below which PMI is removed
        
    Returns:
        DataFrame with PMI payment by month
    """
    if loan_amount <= 0 or home_value <= 0:
        return pd.DataFrame(columns=["month", "pmi_payment"])
    
    current_ltv = loan_amount / home_value
    
    if current_ltv <= pmi_threshold_ltv:
        # No PMI required
        return pd.DataFrame(columns=["month", "pmi_payment"])
    
    monthly_pmi = (loan_amount * pmi_annual_rate) / 12
    
    return pd.DataFrame({
        "month": [1],
        "pmi_payment": [monthly_pmi]
    })


def total_payments(amortization_df: pd.DataFrame) -> dict:
    """
    Calculate total payments over the life of the loan.
    
    Args:
        amortization_df: Output from amortize() function
        
    Returns:
        Dictionary with total_interest, total_principal, total_payments
    """
    if amortization_df.empty:
        return {
            "total_interest": 0,
            "total_principal": 0,
            "total_payments": 0
        }
    
    total_interest = amortization_df["interest"].sum()
    total_principal = amortization_df["principal"].sum()
    total_payments = total_interest + total_principal
    
    return {
        "total_interest": total_interest,
        "total_principal": total_principal,
        "total_payments": total_payments
    }


def remaining_balance_at_month(
    loan_amount: float, 
    rate_annual: float, 
    term_years: int, 
    month: int
) -> float:
    """
    Calculate remaining loan balance at a specific month.
    
    Args:
        loan_amount: Original loan amount
        rate_annual: Annual interest rate
        term_years: Loan term in years
        month: Month number (1-indexed)
        
    Returns:
        Remaining balance at the specified month
    """
    if loan_amount <= 0 or month <= 0:
        return 0
    
    total_months = term_years * 12
    if month > total_months:
        return 0
    
    r = rate_annual / 12
    pmt = npf.pmt(r, total_months, -loan_amount)
    
    # Calculate remaining balance using present value formula
    remaining_payments = total_months - month
    if remaining_payments <= 0:
        return 0
    
    remaining_balance = npf.pv(r, remaining_payments, -pmt, 0)
    return max(remaining_balance, 0) 