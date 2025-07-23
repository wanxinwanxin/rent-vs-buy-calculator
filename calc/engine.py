"""
Main calculation engine that orchestrates rent vs buy analysis.
"""
import pandas as pd
from typing import Dict, Any

from .models import UserInputs, DerivedInputs, TaxParams, CalculationResults
from .buy_flow import calculate_buy_cash_flows, calculate_home_equity_at_exit
from .rent_flow import calculate_rent_cash_flows
from .metrics import calculate_npv, calculate_breakeven_month, calculate_buy_vs_rent_irr


def run_full_analysis(
    user_inputs: UserInputs,
    tax_params: TaxParams
) -> CalculationResults:
    """
    Run complete rent vs buy analysis.
    
    Args:
        user_inputs: User input parameters
        tax_params: Tax parameters for the location
        
    Returns:
        CalculationResults with all metrics and analysis
    """
    # Calculate derived inputs
    derived_inputs = DerivedInputs.from_user_inputs(user_inputs)
    
    # Calculate buy scenario cash flows
    buy_cash_flows = calculate_buy_cash_flows(user_inputs, derived_inputs, tax_params)
    
    # Calculate rent scenario cash flows
    rent_cash_flows = calculate_rent_cash_flows(
        user_inputs, 
        derived_inputs, 
        buy_cash_flows["net_monthly_outflow"]
    )
    
    # Calculate final positions
    final_home_equity = calculate_home_equity_at_exit(
        user_inputs, 
        derived_inputs, 
        derived_inputs.horizon_months
    )
    
    final_portfolio_value = rent_cash_flows.iloc[-1]["portfolio_balance"] if not rent_cash_flows.empty else 0
    
    # Calculate NPVs
    npv_buy_costs = calculate_npv(
        buy_cash_flows["net_monthly_outflow"], 
        derived_inputs.monthly_inflation_rate
    )
    
    npv_rent_costs = calculate_npv(
        rent_cash_flows["total_rent_outflow"], 
        derived_inputs.monthly_inflation_rate
    )
    
    # Calculate break-even month
    breakeven_month = calculate_breakeven_month(
        buy_cash_flows["cumulative_net_outflow"],
        rent_cash_flows["cumulative_rent_outflow"]
    )
    
    # Calculate IRR for buy investment
    irr_buy = calculate_buy_vs_rent_irr(
        user_inputs, 
        derived_inputs, 
        buy_cash_flows, 
        final_home_equity
    )
    
    # Calculate average monthly payments
    avg_buy_payment = buy_cash_flows["net_monthly_outflow"].mean() if not buy_cash_flows.empty else 0
    avg_rent_payment = rent_cash_flows["total_rent_outflow"].mean() if not rent_cash_flows.empty else 0
    
    # Monthly invested surplus (average)
    avg_invested_surplus = rent_cash_flows["monthly_surplus"].mean() if not rent_cash_flows.empty else 0
    
    # Calculate summary metrics
    net_worth_difference = final_home_equity - final_portfolio_value
    npv_difference = npv_buy_costs - npv_rent_costs
    
    # Calculate total amounts for reporting
    total_interest_paid = buy_cash_flows["mortgage_interest"].sum() if not buy_cash_flows.empty else 0
    total_tax_shield = buy_cash_flows["tax_shield"].sum() if not buy_cash_flows.empty else 0
    total_appreciation = final_home_equity - derived_inputs.down_payment_amount if final_home_equity > 0 else 0
    
    return CalculationResults(
        # Monthly flows
        monthly_buy_payment=avg_buy_payment,
        monthly_buy_after_tax=avg_buy_payment,  # Already after-tax in calculation
        monthly_rent_payment=avg_rent_payment,
        monthly_invested_surplus=avg_invested_surplus,
        
        # End state
        home_equity_at_exit=final_home_equity,
        investment_portfolio_value=final_portfolio_value,
        net_worth_difference=net_worth_difference,
        
        # Metrics
        npv_buy_costs=npv_buy_costs,
        npv_rent_costs=npv_rent_costs,
        npv_difference=npv_difference,
        irr_buy_investment=irr_buy,
        breakeven_month=breakeven_month,
        
        # Sensitivity data
        total_interest_paid=total_interest_paid,
        total_tax_shield=total_tax_shield,
        total_appreciation=total_appreciation
    )


def get_detailed_cash_flows(
    user_inputs: UserInputs,
    tax_params: TaxParams
) -> Dict[str, pd.DataFrame]:
    """
    Get detailed month-by-month cash flows for both scenarios.
    
    Args:
        user_inputs: User input parameters
        tax_params: Tax parameters for the location
        
    Returns:
        Dictionary with 'buy' and 'rent' DataFrames containing detailed cash flows
    """
    # Calculate derived inputs
    derived_inputs = DerivedInputs.from_user_inputs(user_inputs)
    
    # Calculate cash flows
    buy_cash_flows = calculate_buy_cash_flows(user_inputs, derived_inputs, tax_params)
    rent_cash_flows = calculate_rent_cash_flows(
        user_inputs, 
        derived_inputs, 
        buy_cash_flows["net_monthly_outflow"]
    )
    
    return {
        "buy": buy_cash_flows,
        "rent": rent_cash_flows,
        "derived_inputs": derived_inputs
    } 