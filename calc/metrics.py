"""
Financial metrics calculations for rent vs buy analysis.
"""
import numpy as np
import pandas as pd
from typing import Optional, Dict, List
import numpy_financial as npf


def calculate_npv(
    cash_flows: pd.Series,
    discount_rate_monthly: float
) -> float:
    """
    Calculate Net Present Value of cash flows.
    
    Args:
        cash_flows: Series of monthly cash flows (negative for outflows)
        discount_rate_monthly: Monthly discount rate
        
    Returns:
        NPV of the cash flows
    """
    if cash_flows.empty:
        return 0
    
    # Create periods array (0, 1, 2, ...)
    periods = np.arange(len(cash_flows))
    
    # Calculate present value of each cash flow
    pv_factors = (1 + discount_rate_monthly) ** (-periods)
    present_values = cash_flows * pv_factors
    
    return present_values.sum()


def calculate_irr(cash_flows: List[float], guess: float = 0.1) -> Optional[float]:
    """
    Calculate Internal Rate of Return for cash flows.
    
    Args:
        cash_flows: List of cash flows (initial negative, then positives/negatives)
        guess: Initial guess for IRR calculation
        
    Returns:
        Annual IRR or None if calculation fails
    """
    try:
        # Use numpy-financial for IRR calculation
        monthly_irr = npf.irr(cash_flows)
        
        if monthly_irr is None or np.isnan(monthly_irr) or np.isinf(monthly_irr):
            return None
        
        # Convert monthly IRR to annual
        annual_irr = (1 + monthly_irr) ** 12 - 1
        
        # Sanity check - IRR should be reasonable
        if annual_irr < -0.99 or annual_irr > 10:  # -99% to 1000%
            return None
            
        return annual_irr
        
    except (ValueError, OverflowError, RuntimeError):
        return None


def calculate_breakeven_month(
    buy_cumulative_costs: pd.Series,
    rent_cumulative_costs: pd.Series
) -> Optional[int]:
    """
    Calculate the month when buying becomes cheaper than renting (break-even).
    
    Args:
        buy_cumulative_costs: Cumulative costs for buying scenario
        rent_cumulative_costs: Cumulative costs for renting scenario
        
    Returns:
        Month number (1-indexed) when buying breaks even, or None if never
    """
    if len(buy_cumulative_costs) != len(rent_cumulative_costs):
        return None
    
    # Find where cumulative buy costs <= cumulative rent costs
    cost_difference = buy_cumulative_costs - rent_cumulative_costs
    breakeven_indices = np.where(cost_difference <= 0)[0]
    
    if len(breakeven_indices) > 0:
        return int(breakeven_indices[0] + 1)  # Convert to 1-indexed
    
    return None


def calculate_buy_vs_rent_irr(
    user_inputs,
    derived_inputs,
    buy_cash_flows: pd.DataFrame,
    final_home_equity: float
) -> Optional[float]:
    """
    Calculate IRR for the "buy investment" decision.
    
    Args:
        user_inputs: User input parameters
        derived_inputs: Derived calculations  
        buy_cash_flows: Monthly cash flows from buying
        final_home_equity: Net equity at the end
        
    Returns:
        Annual IRR for the buy vs rent decision
    """
    # Build cash flow stream for IRR calculation
    cash_flows = []
    
    # Initial investment (down payment + closing costs)
    initial_investment = -(derived_inputs.down_payment_amount + user_inputs.closing_costs_buy)
    cash_flows.append(initial_investment)
    
    # Monthly net outflows (negative cash flows)
    for _, row in buy_cash_flows.iterrows():
        cash_flows.append(-row["net_monthly_outflow"])
    
    # Final positive cash flow from selling
    cash_flows[-1] += final_home_equity
    
    return calculate_irr(cash_flows)


def calculate_sensitivity_analysis(
    base_inputs,
    variable_name: str,
    variable_range: List[float],
    calc_function
) -> pd.DataFrame:
    """
    Perform sensitivity analysis on a variable.
    
    Args:
        base_inputs: Base case input parameters
        variable_name: Name of variable to vary
        variable_range: List of values to test
        calc_function: Function that calculates results given inputs
        
    Returns:
        DataFrame with sensitivity results
    """
    results = []
    
    for value in variable_range:
        # Create modified inputs
        modified_inputs = base_inputs.copy()
        setattr(modified_inputs, variable_name, value)
        
        # Calculate results
        try:
            result = calc_function(modified_inputs)
            results.append({
                variable_name: value,
                "npv_difference": result.get("npv_difference", 0),
                "net_worth_difference": result.get("net_worth_difference", 0),
                "breakeven_month": result.get("breakeven_month", None)
            })
        except Exception:
            # Handle calculation errors gracefully
            results.append({
                variable_name: value,
                "npv_difference": np.nan,
                "net_worth_difference": np.nan,
                "breakeven_month": None
            })
    
    return pd.DataFrame(results)


def calculate_scenario_comparison(
    buy_results: Dict,
    rent_results: Dict,
    user_inputs,
    derived_inputs
) -> Dict:
    """
    Compare buy vs rent scenarios and calculate key metrics.
    
    Args:
        buy_results: Results from buy scenario calculation
        rent_results: Results from rent scenario calculation
        user_inputs: User input parameters
        derived_inputs: Derived calculations
        
    Returns:
        Dictionary with comparison metrics
    """
    # Net worth difference (buy - rent)
    buy_net_worth = buy_results.get("final_home_equity", 0)
    rent_net_worth = rent_results.get("final_portfolio_value", 0)
    net_worth_difference = buy_net_worth - rent_net_worth
    
    # NPV of costs (lower is better)
    buy_npv_costs = buy_results.get("npv_costs", 0)
    rent_npv_costs = rent_results.get("npv_costs", 0)
    npv_difference = buy_npv_costs - rent_npv_costs
    
    # Cash flow comparison
    buy_monthly_avg = buy_results.get("avg_monthly_outflow", 0)
    rent_monthly_avg = rent_results.get("avg_monthly_outflow", 0)
    monthly_difference = buy_monthly_avg - rent_monthly_avg
    
    # Break-even analysis
    breakeven_month = calculate_breakeven_month(
        buy_results.get("cumulative_costs", pd.Series()),
        rent_results.get("cumulative_costs", pd.Series())
    )
    
    # Recommendation logic
    recommendation = "Buy" if net_worth_difference > 0 else "Rent"
    
    if abs(net_worth_difference) < (user_inputs.purchase_price * 0.05):  # Within 5% of home price
        recommendation = "Neutral - Consider lifestyle factors"
    
    return {
        "net_worth_difference": net_worth_difference,
        "npv_difference": npv_difference,
        "monthly_difference": monthly_difference,
        "breakeven_month": breakeven_month,
        "buy_net_worth": buy_net_worth,
        "rent_net_worth": rent_net_worth,
        "buy_npv_costs": buy_npv_costs,
        "rent_npv_costs": rent_npv_costs,
        "recommendation": recommendation
    }


def format_currency(amount: float) -> str:
    """Format a number as currency."""
    return f"${amount:,.0f}"


def format_percentage(rate: float) -> str:
    """Format a rate as percentage."""
    return f"{rate*100:.1f}%" 