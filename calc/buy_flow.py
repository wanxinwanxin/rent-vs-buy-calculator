"""
Buy scenario cash flow calculations.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional

from .models import UserInputs, DerivedInputs, TaxParams
from .amortization import amortize, remaining_balance_at_month


def calculate_monthly_owner_costs(
    user_inputs: UserInputs,
    derived_inputs: DerivedInputs,
    home_value: float,
    month: int
) -> dict:
    """
    Calculate monthly costs for homeownership at a given month.
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        home_value: Current home value
        month: Current month (1-indexed)
        
    Returns:
        Dictionary with monthly cost components
    """
    # Property tax (monthly)
    monthly_property_tax = (home_value * user_inputs.property_tax_rate) / 12
    
    # Insurance and HOA (monthly)
    monthly_insurance_hoa = user_inputs.insurance_hoa_annual / 12
    
    # Maintenance (monthly, as percentage of current home value)
    monthly_maintenance = (home_value * user_inputs.maintenance_pct) / 12
    
    # Other costs (monthly)
    monthly_other = user_inputs.other_owner_costs_annual / 12
    
    # PMI calculation (simplified - assumes PMI until 20% equity)
    pmi_payment = 0
    if user_inputs.pmi_annual_pct and user_inputs.pmi_threshold_pct:
        current_loan_balance = remaining_balance_at_month(
            derived_inputs.loan_amount,
            user_inputs.mortgage_rate,
            user_inputs.mortgage_term_years,
            month
        )
        current_ltv = current_loan_balance / home_value if home_value > 0 else 0
        
        if current_ltv > user_inputs.pmi_threshold_pct:
            pmi_payment = (current_loan_balance * user_inputs.pmi_annual_pct) / 12
    
    return {
        "property_tax": monthly_property_tax,
        "insurance_hoa": monthly_insurance_hoa,
        "maintenance": monthly_maintenance,
        "other_costs": monthly_other,
        "pmi": pmi_payment,
        "total_monthly_costs": monthly_property_tax + monthly_insurance_hoa + monthly_maintenance + monthly_other + pmi_payment
    }


def calculate_tax_shield(
    mortgage_interest: float,
    property_tax: float,
    tax_params: TaxParams,
    points_deduction: float = 0
) -> float:
    """
    Calculate tax shield from mortgage interest and property tax deductions.
    Simplified implementation - uses itemized vs standard deduction logic.
    
    Args:
        mortgage_interest: Monthly mortgage interest payment
        property_tax: Monthly property tax payment
        tax_params: Tax parameters for location/filing status
        points_deduction: One-time points deduction (amortized)
        
    Returns:
        Monthly tax shield amount
    """
    # Annual itemizable deductions
    annual_mortgage_interest = mortgage_interest * 12
    annual_property_tax = property_tax * 12
    annual_points = points_deduction
    
    # Apply SALT cap to property taxes
    salt_limited_property_tax = min(annual_property_tax, tax_params.salt_cap)
    
    total_itemizable = annual_mortgage_interest + salt_limited_property_tax + annual_points
    
    # Compare to standard deduction
    if total_itemizable > tax_params.standard_deduction:
        excess_deduction = total_itemizable - tax_params.standard_deduction
        combined_marginal_rate = tax_params.federal_marginal_rate + tax_params.state_marginal_rate
        annual_tax_shield = excess_deduction * combined_marginal_rate
        return annual_tax_shield / 12
    
    return 0  # No benefit if standard deduction is better


def calculate_buy_cash_flows(
    user_inputs: UserInputs,
    derived_inputs: DerivedInputs,
    tax_params: TaxParams
) -> pd.DataFrame:
    """
    Calculate month-by-month cash flows for buying scenario.
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        tax_params: Tax parameters
        
    Returns:
        DataFrame with monthly cash flows for buying
    """
    # Get amortization schedule
    amort_schedule = amortize(
        derived_inputs.loan_amount,
        user_inputs.mortgage_rate,
        user_inputs.mortgage_term_years
    )
    
    # Handle case where there's no loan (100% down payment)
    if amort_schedule.empty:
        months = range(1, derived_inputs.horizon_months + 1)
        amort_schedule = pd.DataFrame({
            "month": months,
            "interest": [0] * len(months),
            "principal": [0] * len(months),
            "balance": [0] * len(months)
        })
    
    # Calculate home value appreciation over time
    initial_home_value = user_inputs.purchase_price
    
    # Points deduction (one-time, amortized over loan term or 5 years, whichever is shorter)
    points_annual_deduction = 0
    if user_inputs.points_pct:
        total_points = derived_inputs.loan_amount * user_inputs.points_pct
        amortization_years = min(user_inputs.mortgage_term_years, 5)
        points_annual_deduction = total_points / amortization_years
    
    cash_flows = []
    
    for month in range(1, derived_inputs.horizon_months + 1):
        # Current home value with appreciation
        home_value = initial_home_value * ((1 + derived_inputs.monthly_appreciation_rate) ** (month - 1))
        
        # Get mortgage payment components for this month
        if month <= len(amort_schedule):
            interest_payment = amort_schedule.iloc[month - 1]["interest"]
            principal_payment = amort_schedule.iloc[month - 1]["principal"]
        else:
            # Loan is paid off
            interest_payment = 0
            principal_payment = 0
        
        mortgage_payment = interest_payment + principal_payment
        
        # Calculate other monthly costs
        monthly_costs = calculate_monthly_owner_costs(user_inputs, derived_inputs, home_value, month)
        
        # Calculate tax shield
        tax_shield = calculate_tax_shield(
            interest_payment,
            monthly_costs["property_tax"],
            tax_params,
            points_annual_deduction / 12
        )
        
        # Total monthly outflow (before tax shield)
        gross_outflow = mortgage_payment + monthly_costs["total_monthly_costs"]
        
        # After-tax monthly outflow
        net_outflow = gross_outflow - tax_shield
        
        # True out-of-pocket cost (excluding principal which builds equity)
        true_monthly_cost = interest_payment + monthly_costs["total_monthly_costs"] - tax_shield
        
        cash_flows.append({
            "month": month,
            "home_value": home_value,
            "mortgage_interest": interest_payment,
            "mortgage_principal": principal_payment,
            "mortgage_payment": mortgage_payment,
            "property_tax": monthly_costs["property_tax"],
            "insurance_hoa": monthly_costs["insurance_hoa"],
            "maintenance": monthly_costs["maintenance"],
            "other_costs": monthly_costs["other_costs"],
            "pmi": monthly_costs["pmi"],
            "total_other_costs": monthly_costs["total_monthly_costs"],
            "tax_shield": tax_shield,
            "gross_monthly_outflow": gross_outflow,
            "net_monthly_outflow": net_outflow,
            "true_monthly_cost": true_monthly_cost,
            "cumulative_net_outflow": 0,  # Will be calculated below
            "cumulative_true_cost": 0     # Will be calculated below
        })
    
    df = pd.DataFrame(cash_flows)
    
    # Calculate cumulative outflows
    df["cumulative_net_outflow"] = df["net_monthly_outflow"].cumsum()
    
    # Calculate cumulative true costs (excluding principal, including down payment)
    down_payment_plus_closing = derived_inputs.down_payment_amount + user_inputs.closing_costs_buy
    df["cumulative_true_cost"] = down_payment_plus_closing + df["true_monthly_cost"].cumsum()
    
    return df


def calculate_home_equity_at_exit(
    user_inputs: UserInputs,
    derived_inputs: DerivedInputs,
    exit_month: int
) -> float:
    """
    Calculate net home equity at exit (after selling costs).
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        exit_month: Month when selling (1-indexed)
        
    Returns:
        Net equity after selling costs
    """
    # Home value at exit with appreciation
    exit_home_value = user_inputs.purchase_price * ((1 + derived_inputs.monthly_appreciation_rate) ** (exit_month - 1))
    
    # Remaining loan balance
    remaining_balance = remaining_balance_at_month(
        derived_inputs.loan_amount,
        user_inputs.mortgage_rate,
        user_inputs.mortgage_term_years,
        exit_month
    )
    
    # Selling costs
    selling_costs = exit_home_value * user_inputs.selling_cost_pct
    
    # Net equity
    net_equity = exit_home_value - remaining_balance - selling_costs
    
    return max(net_equity, 0)  # Equity can't be negative (would walk away) 