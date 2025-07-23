"""
Rent scenario cash flow calculations.
"""
import numpy as np
import pandas as pd
from typing import Optional

from .models import UserInputs, DerivedInputs


def calculate_rent_cash_flows(
    user_inputs: UserInputs,
    derived_inputs: DerivedInputs,
    buy_monthly_outflows: pd.Series
) -> pd.DataFrame:
    """
    Calculate month-by-month cash flows for renting scenario.
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        buy_monthly_outflows: Monthly net outflows from buying scenario (for surplus calculation)
        
    Returns:
        DataFrame with monthly cash flows for renting
    """
    cash_flows = []
    portfolio_balance = 0
    
    # Initial investment from down payment that would have been used for buying
    initial_investment = derived_inputs.down_payment_amount + user_inputs.closing_costs_buy
    portfolio_balance = initial_investment
    
    for month in range(1, derived_inputs.horizon_months + 1):
        # Current rent with growth
        months_elapsed = month - 1
        current_rent = user_inputs.rent_today_monthly * ((1 + derived_inputs.monthly_rent_growth_rate) ** months_elapsed)
        
        # Other renter costs
        other_costs = user_inputs.other_renter_costs_monthly
        
        # Total monthly rental outflow
        total_rent_outflow = current_rent + other_costs
        
        # Calculate surplus to invest
        # Surplus = what you would have spent on buying - what you spend on renting
        buy_outflow = buy_monthly_outflows.iloc[month - 1] if month <= len(buy_monthly_outflows) else 0
        monthly_surplus = max(0, buy_outflow - total_rent_outflow)
        
        # Add surplus to portfolio and apply returns
        portfolio_balance = portfolio_balance * (1 + derived_inputs.monthly_alt_return_rate) + monthly_surplus
        
        cash_flows.append({
            "month": month,
            "rent_payment": current_rent,
            "other_renter_costs": other_costs,
            "total_rent_outflow": total_rent_outflow,
            "monthly_surplus": monthly_surplus,
            "portfolio_balance": portfolio_balance,
            "cumulative_rent_outflow": 0  # Will be calculated below
        })
    
    df = pd.DataFrame(cash_flows)
    
    # Calculate cumulative outflows
    df["cumulative_rent_outflow"] = df["total_rent_outflow"].cumsum()
    
    return df


def calculate_investment_portfolio_value(
    initial_investment: float,
    monthly_contributions: pd.Series,
    monthly_return_rate: float
) -> pd.Series:
    """
    Calculate investment portfolio value over time with monthly contributions.
    
    Args:
        initial_investment: Initial lump sum investment
        monthly_contributions: Series of monthly contribution amounts
        monthly_return_rate: Monthly return rate
        
    Returns:
        Series of portfolio values by month
    """
    portfolio_values = []
    balance = initial_investment
    
    for contribution in monthly_contributions:
        # Apply return to existing balance
        balance *= (1 + monthly_return_rate)
        # Add monthly contribution
        balance += contribution
        portfolio_values.append(balance)
    
    return pd.Series(portfolio_values)


def calculate_rent_opportunity_cost(
    user_inputs: UserInputs,
    derived_inputs: DerivedInputs
) -> dict:
    """
    Calculate opportunity cost metrics for renting scenario.
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        
    Returns:
        Dictionary with opportunity cost analysis
    """
    # Total rent paid over horizon
    total_rent_paid = 0
    current_rent = user_inputs.rent_today_monthly
    
    for month in range(derived_inputs.horizon_months):
        total_rent_paid += current_rent
        current_rent *= (1 + derived_inputs.monthly_rent_growth_rate)
    
    # Total other costs
    total_other_costs = user_inputs.other_renter_costs_monthly * derived_inputs.horizon_months
    
    # Total renting costs
    total_renting_costs = total_rent_paid + total_other_costs
    
    # Opportunity cost of not building equity
    # This is the difference between rent payments and mortgage principal payments
    
    return {
        "total_rent_paid": total_rent_paid,
        "total_other_costs": total_other_costs,
        "total_renting_costs": total_renting_costs,
        "average_monthly_rent": total_rent_paid / derived_inputs.horizon_months
    }


def project_rent_growth(
    initial_rent: float,
    growth_rate_annual: float,
    horizon_months: int
) -> pd.Series:
    """
    Project rent payments over time with growth.
    
    Args:
        initial_rent: Starting monthly rent
        growth_rate_annual: Annual rent growth rate
        horizon_months: Number of months to project
        
    Returns:
        Series of monthly rent payments
    """
    monthly_growth_rate = growth_rate_annual / 12
    months = range(horizon_months)
    
    rent_payments = [initial_rent * ((1 + monthly_growth_rate) ** month) for month in months]
    
    return pd.Series(rent_payments) 