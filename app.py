"""
Rent vs. Buy Calculator - Streamlit Application

A comprehensive tool to analyze the financial implications of renting versus buying a home.
"""

import streamlit as st
import traceback
from pathlib import Path

# Add the current directory to Python path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from calc.engine import run_full_analysis, get_detailed_cash_flows
from calc.models import UserInputs, DerivedInputs
from calc.validation import validate_user_inputs, sanitize_inputs, check_calculation_feasibility
from services.tax_lookup import get_tax_params
from services.property_data import get_property_info
from ui.widgets import create_user_inputs
from ui.charts import (
    display_key_metrics, 
    create_monthly_cashflow_chart,
    create_cumulative_cost_chart,
    create_net_worth_progression_chart,
    create_cost_breakdown_chart,
    display_detailed_tables,
    display_assumptions_info
)
from ui.sensitivity import create_sensitivity_panel, create_tornado_chart
from calc.metrics import format_currency


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Rent vs. Buy Calculator",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def display_header():
    """Display the application header and introduction."""
    st.title("🏠 Rent vs. Buy Calculator")
    st.markdown("""
    **Compare the financial impact of renting versus buying a home over time.**
    
    This calculator analyzes monthly cash flows, tax implications, investment returns, and long-term net worth 
    to help you make an informed decision about whether to rent or buy.
    """)
    
    # Add info about the calculator
    with st.expander("ℹ️ How this calculator works"):
        st.markdown("""
        **This calculator compares two scenarios:**
        
        1. **Buy Scenario**: Purchase a home with mortgage, pay monthly costs (P&I, taxes, maintenance), 
           build equity through principal payments and appreciation
           
        2. **Rent Scenario**: Pay monthly rent, invest the difference (down payment + monthly surplus) 
           in alternative investments
        
        **Key Metrics:**
        - **Net Worth Difference**: Buy equity minus investment portfolio at end of horizon
        - **NPV Cost Difference**: Present value of buy costs minus rent costs 
        - **Break-even Time**: When cumulative buy costs equal cumulative rent costs
        - **IRR**: Internal rate of return for the buy investment decision
        
        **Features:**
        - Tax shield calculations (mortgage interest + property tax deductions)
        - Regional tax and property data for NYC/NJ area
        - Detailed monthly cash flow projections
        - Multiple visualization options
        """)


def main():
    """Main application logic."""
    configure_page()
    display_header()
    
    # Create sidebar for inputs
    with st.sidebar:
        st.header("📊 Input Parameters")
        st.markdown("Configure your scenario below:")
        
        # Create user inputs using widgets
        try:
            user_inputs = create_user_inputs()
        except Exception as e:
            st.error(f"Error creating inputs: {e}")
            st.stop()
    
    # Main content area
    if st.sidebar.button("🔄 Calculate", type="primary", use_container_width=True):
        
        # Validate inputs before calculation
        validation_errors = validate_user_inputs(user_inputs)
        if validation_errors:
            st.sidebar.error("❌ Input Validation Errors:")
            for error in validation_errors:
                st.sidebar.error(f"• {error}")
            st.stop()
        
        # Check feasibility and show warnings
        is_feasible, warnings = check_calculation_feasibility(user_inputs)
        if warnings:
            st.sidebar.warning("⚠️ Scenario Warnings:")
            for warning in warnings:
                st.sidebar.warning(f"• {warning}")
        
        if not is_feasible:
            st.sidebar.error("❌ Scenario not feasible - please adjust inputs")
            st.stop()
        
        with st.spinner("Running analysis..."):
            try:
                # Sanitize inputs
                clean_inputs = sanitize_inputs(user_inputs)
                
                # Get tax parameters for location
                total_income = clean_inputs.income_you + clean_inputs.income_spouse
                manual_federal = clean_inputs.manual_federal_rate if clean_inputs.use_manual_tax_rates else None
                manual_state = clean_inputs.manual_state_rate if clean_inputs.use_manual_tax_rates else None
                
                tax_params = get_tax_params(
                    clean_inputs.location, 
                    clean_inputs.filing_status,
                    income=total_income,
                    manual_federal_rate=manual_federal,
                    manual_state_rate=manual_state
                )
                
                # Get property info
                property_info = get_property_info(clean_inputs.location)
                
                # Run the full analysis
                results = run_full_analysis(clean_inputs, tax_params)
                
                # Get detailed cash flows for charts
                cash_flows = get_detailed_cash_flows(clean_inputs, tax_params)
                
                # Store results in session state
                st.session_state.results = results
                st.session_state.cash_flows = cash_flows
                st.session_state.user_inputs = clean_inputs
                st.session_state.tax_params = tax_params
                st.session_state.property_info = property_info
                
                st.success("✅ Analysis complete!")
                
            except Exception as e:
                st.error(f"❌ Error during calculation: {str(e)}")
                st.error("Please check your inputs and try again.")
                if st.checkbox("Show detailed error"):
                    st.code(traceback.format_exc())
                st.stop()
    
    # Display results if available
    if hasattr(st.session_state, 'results') and st.session_state.results:
        display_results()
    else:
        # Show sample/default view
        st.info("👆 Configure your parameters in the sidebar and click 'Calculate' to see results.")
        display_sample_info()


def display_results():
    """Display calculation results and visualizations."""
    results = st.session_state.results
    cash_flows = st.session_state.cash_flows
    user_inputs = st.session_state.user_inputs
    tax_params = st.session_state.tax_params
    property_info = st.session_state.property_info
    
    # Key metrics
    st.subheader("📊 Key Results")
    display_key_metrics(results)
    
    # Recommendation
    st.subheader("💡 Recommendation")
    if results.net_worth_difference > 0:
        if results.net_worth_difference > user_inputs.purchase_price * 0.1:  # >10% of home price
            st.success(f"**Strong Buy Signal** - Buying is projected to result in {format_currency(results.net_worth_difference)} higher net worth after {user_inputs.horizon_years} years.")
        else:
            st.info(f"**Slight Buy Advantage** - Buying is projected to result in {format_currency(results.net_worth_difference)} higher net worth, but the difference is modest.")
    else:
        if abs(results.net_worth_difference) > user_inputs.purchase_price * 0.1:
            st.warning(f"**Strong Rent Signal** - Renting is projected to result in {format_currency(abs(results.net_worth_difference))} higher net worth after {user_inputs.horizon_years} years.")
        else:
            st.info(f"**Slight Rent Advantage** - Renting is projected to result in {format_currency(abs(results.net_worth_difference))} higher net worth, but the difference is modest.")
    
    # Additional context
    if results.breakeven_month and results.breakeven_month <= user_inputs.horizon_years * 12:
        st.info(f"💡 Buying breaks even after {results.breakeven_month/12:.1f} years")
    else:
        st.warning("⚠️ Buying does not break even within the analysis period")
    
    # Charts
    st.subheader("📈 Analysis Charts")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Monthly Cash Flow", "Cumulative Costs", "Net Worth Growth", "Cost Breakdown", "Sensitivity"])
    
    with tab1:
        st.plotly_chart(
            create_monthly_cashflow_chart(cash_flows), 
            use_container_width=True
        )
        
    with tab2:
        st.plotly_chart(
            create_cumulative_cost_chart(cash_flows), 
            use_container_width=True
        )
        
    with tab3:
        st.plotly_chart(
            create_net_worth_progression_chart(cash_flows), 
            use_container_width=True
        )
        
    with tab4:
        st.plotly_chart(
            create_cost_breakdown_chart(results), 
            use_container_width=True
        )
        
    with tab5:
        create_sensitivity_panel(user_inputs, tax_params)
        st.divider()
        create_tornado_chart(user_inputs, tax_params)
    
    # Detailed tables and assumptions
    display_detailed_tables(cash_flows)
    display_assumptions_info(user_inputs, tax_params, property_info)


def display_sample_info():
    """Display sample information when no calculation has been run."""
    st.subheader("📋 Sample Analysis")
    st.markdown("""
    **Example Scenario: NYC Professional**
    - Income: $150,000/year
    - Home Price: $800,000 (20% down)
    - Rent: $4,000/month
    - Location: NYC, NY
    - Analysis Period: 10 years
    
    **Typical Considerations:**
    - **Break-even**: Usually 5-7 years in high-cost areas
    - **Tax Benefits**: Mortgage interest + property tax deductions
    - **Opportunity Cost**: Rent surplus invested in stock market
    - **Transaction Costs**: ~6% to sell, ~2% closing costs to buy
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Factors Favoring Buying:**
        - Long-term stability (>7 years)
        - Home appreciation >3%/year
        - Low mortgage rates (<6%)
        - High rent vs. buy ratio
        - Tax benefits (itemize deductions)
        """)
    
    with col2:
        st.markdown("""
        **Factors Favoring Renting:**
        - Short-term flexibility (<5 years)
        - High home prices vs. rent
        - High mortgage rates (>8%)
        - Strong stock market returns (>8%)
        - No maintenance/repair costs
        """)


if __name__ == "__main__":
    main() 