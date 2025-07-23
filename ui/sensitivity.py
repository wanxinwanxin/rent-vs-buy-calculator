"""
Sensitivity analysis components for rent vs buy calculator.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List

from calc.engine import run_full_analysis
from calc.models import UserInputs
from calc.metrics import format_currency, format_percentage


def create_sensitivity_panel(base_user_inputs: UserInputs, tax_params) -> None:
    """Create sensitivity analysis panel with sliders."""
    
    st.subheader("🎯 Sensitivity Analysis")
    st.markdown("See how changing key variables affects the buy vs rent decision:")
    
    # Create three key sensitivity variables
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏠 Home Appreciation**")
        appreciation_range = st.slider(
            "Annual Appreciation Rate",
            min_value=-0.02,
            max_value=0.08,
            value=base_user_inputs.annual_appreciation,
            step=0.005,
            format="%.1%",
            key="sensitivity_appreciation",
            help="How much the home value increases each year"
        )
        
    with col2:
        st.markdown("**📈 Investment Return**")
        return_range = st.slider(
            "Alternative Return Rate", 
            min_value=0.02,
            max_value=0.12,
            value=base_user_inputs.alt_return_annual,
            step=0.005,
            format="%.1%",
            key="sensitivity_return",
            help="Expected annual return from investing rent surplus"
        )
        
    with col3:
        st.markdown("**🏠 Mortgage Rate**")
        rate_range = st.slider(
            "Mortgage Interest Rate",
            min_value=0.03,
            max_value=0.10,
            value=base_user_inputs.mortgage_rate,
            step=0.0025,
            format="%.2%",
            key="sensitivity_rate",
            help="Annual mortgage interest rate"
        )
    
    # Calculate sensitivity results
    if st.button("🔄 Run Sensitivity Analysis", key="run_sensitivity"):
        with st.spinner("Calculating scenarios..."):
            sensitivity_results = calculate_sensitivity_scenarios(
                base_user_inputs, tax_params, appreciation_range, return_range, rate_range
            )
            
            display_sensitivity_results(sensitivity_results, base_user_inputs)


def calculate_sensitivity_scenarios(
    base_inputs: UserInputs, 
    tax_params, 
    appreciation: float,
    alt_return: float, 
    mortgage_rate: float
) -> Dict:
    """Calculate results for different sensitivity scenarios."""
    
    scenarios = {
        "Base Case": base_inputs,
        "High Appreciation": base_inputs.model_copy(update={"annual_appreciation": appreciation}),
        "High Alt Return": base_inputs.model_copy(update={"alt_return_annual": alt_return}),
        "High Mortgage Rate": base_inputs.model_copy(update={"mortgage_rate": mortgage_rate}),
        "Combined Optimistic": base_inputs.model_copy(update={
            "annual_appreciation": appreciation,
            "alt_return_annual": max(0.02, alt_return - 0.02)  # Lower alt return in optimistic scenario
        }),
        "Combined Pessimistic": base_inputs.model_copy(update={
            "annual_appreciation": max(-0.02, appreciation - 0.02),
            "mortgage_rate": mortgage_rate,
            "alt_return_annual": alt_return
        })
    }
    
    results = {}
    for name, inputs in scenarios.items():
        try:
            result = run_full_analysis(inputs, tax_params)
            results[name] = {
                "net_worth_diff": result.net_worth_difference,
                "npv_diff": result.npv_difference,
                "breakeven_month": result.breakeven_month,
                "inputs": inputs
            }
        except Exception as e:
            st.warning(f"Could not calculate scenario '{name}': {e}")
            results[name] = {
                "net_worth_diff": 0,
                "npv_diff": 0,
                "breakeven_month": None,
                "inputs": inputs
            }
    
    return results


def display_sensitivity_results(results: Dict, base_inputs: UserInputs) -> None:
    """Display sensitivity analysis results."""
    
    # Create DataFrame for easier plotting
    data = []
    for scenario, result in results.items():
        data.append({
            "Scenario": scenario,
            "Net Worth Difference": result["net_worth_diff"],
            "NPV Difference": result["npv_diff"],
            "Break-even (Years)": result["breakeven_month"] / 12 if result["breakeven_month"] else None
        })
    
    df = pd.DataFrame(data)
    
    # Display results table
    st.subheader("Scenario Comparison")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_df["Net Worth Difference"] = display_df["Net Worth Difference"].apply(lambda x: format_currency(x))
    display_df["NPV Difference"] = display_df["NPV Difference"].apply(lambda x: format_currency(x))
    display_df["Break-even (Years)"] = display_df["Break-even (Years)"].apply(
        lambda x: f"{x:.1f}" if x is not None else "Never"
    )
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Create sensitivity chart
    fig = go.Figure()
    
    # Add net worth difference bars
    colors = ['blue' if x >= 0 else 'red' for x in df["Net Worth Difference"]]
    
    fig.add_trace(go.Bar(
        x=df["Scenario"],
        y=df["Net Worth Difference"],
        name="Net Worth Difference (Buy - Rent)",
        marker_color=colors,
        text=[format_currency(x) for x in df["Net Worth Difference"]],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Sensitivity Analysis: Net Worth Difference Across Scenarios",
        xaxis_title="Scenario",
        yaxis_title="Net Worth Difference ($)",
        showlegend=False,
        height=500
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary insights
    st.subheader("📊 Key Insights")
    
    base_result = results.get("Base Case", {})
    best_scenario = max(results.items(), key=lambda x: x[1]["net_worth_diff"])
    worst_scenario = min(results.items(), key=lambda x: x[1]["net_worth_diff"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Best Case Scenario",
            best_scenario[0],
            format_currency(best_scenario[1]["net_worth_diff"]),
        )
    
    with col2:
        st.metric(
            "Worst Case Scenario", 
            worst_scenario[0],
            format_currency(worst_scenario[1]["net_worth_diff"])
        )
    
    with col3:
        range_diff = best_scenario[1]["net_worth_diff"] - worst_scenario[1]["net_worth_diff"]
        st.metric(
            "Range of Outcomes",
            format_currency(range_diff),
            help="Difference between best and worst case scenarios"
        )


def create_tornado_chart(base_inputs: UserInputs, tax_params) -> None:
    """Create a tornado chart showing variable impact."""
    st.subheader("🌪️ Variable Impact Analysis")
    
    variables = {
        "Home Appreciation": {"base": base_inputs.annual_appreciation, "range": 0.02},
        "Mortgage Rate": {"base": base_inputs.mortgage_rate, "range": 0.01},
        "Alt Investment Return": {"base": base_inputs.alt_return_annual, "range": 0.02},
        "Rent Growth": {"base": base_inputs.rent_growth_pct, "range": 0.01}
    }
    
    impacts = []
    base_result = run_full_analysis(base_inputs, tax_params)
    
    for var_name, var_info in variables.items():
        # Test high and low values
        high_inputs = base_inputs.model_copy()
        low_inputs = base_inputs.model_copy()
        
        if var_name == "Home Appreciation":
            high_inputs.annual_appreciation = var_info["base"] + var_info["range"]
            low_inputs.annual_appreciation = var_info["base"] - var_info["range"]
        elif var_name == "Mortgage Rate":
            high_inputs.mortgage_rate = var_info["base"] + var_info["range"]
            low_inputs.mortgage_rate = var_info["base"] - var_info["range"]
        elif var_name == "Alt Investment Return":
            high_inputs.alt_return_annual = var_info["base"] + var_info["range"]
            low_inputs.alt_return_annual = var_info["base"] - var_info["range"]
        elif var_name == "Rent Growth":
            high_inputs.rent_growth_pct = var_info["base"] + var_info["range"]
            low_inputs.rent_growth_pct = var_info["base"] - var_info["range"]
        
        try:
            high_result = run_full_analysis(high_inputs, tax_params)
            low_result = run_full_analysis(low_inputs, tax_params)
            
            high_impact = high_result.net_worth_difference - base_result.net_worth_difference
            low_impact = low_result.net_worth_difference - base_result.net_worth_difference
            
            impacts.append({
                "Variable": var_name,
                "High Impact": high_impact,
                "Low Impact": low_impact,
                "Range": abs(high_impact - low_impact)
            })
        except Exception:
            continue
    
    if impacts:
        # Sort by range (sensitivity)
        impacts.sort(key=lambda x: x["Range"], reverse=True)
        
        # Create tornado chart
        fig = go.Figure()
        
        variables = [item["Variable"] for item in impacts]
        high_values = [item["High Impact"] for item in impacts]
        low_values = [item["Low Impact"] for item in impacts]
        
        fig.add_trace(go.Bar(
            y=variables,
            x=high_values,
            name="High Value Impact",
            orientation='h',
            marker_color='green',
            opacity=0.7
        ))
        
        fig.add_trace(go.Bar(
            y=variables,
            x=low_values,
            name="Low Value Impact", 
            orientation='h',
            marker_color='red',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Variable Sensitivity (Impact on Net Worth Difference)",
            xaxis_title="Impact on Net Worth ($)",
            barmode='overlay',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True) 