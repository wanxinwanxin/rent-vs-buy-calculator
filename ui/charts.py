"""
Chart components for displaying rent vs buy results.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any

from calc.models import CalculationResults
from calc.metrics import format_currency, format_percentage


def display_key_metrics(results: CalculationResults) -> None:
    """Display key metrics as Streamlit metric cards."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        net_worth_color = "normal" if results.net_worth_difference >= 0 else "inverse"
        st.metric(
            "Net Worth Difference",
            format_currency(results.net_worth_difference),
            help="Buy minus Rent net worth at end of horizon"
        )
    
    with col2:
        npv_color = "inverse" if results.npv_difference >= 0 else "normal"  # Lower NPV cost is better
        st.metric(
            "NPV Cost Difference", 
            format_currency(results.npv_difference),
            help="Present value of buy costs minus rent costs (lower is better)"
        )
    
    with col3:
        if results.breakeven_month:
            breakeven_years = results.breakeven_month / 12
            st.metric(
                "Break-even Time",
                f"{breakeven_years:.1f} years",
                help="Time until buying becomes cheaper than renting"
            )
        else:
            st.metric(
                "Break-even Time",
                "Never",
                help="Buying never becomes cheaper in the analysis period"
            )
    
    with col4:
        if results.irr_buy_investment:
            st.metric(
                "Buy Investment IRR",
                format_percentage(results.irr_buy_investment),
                help="Internal rate of return for the buy investment"
            )
        else:
            st.metric(
                "Buy Investment IRR",
                "N/A",
                help="Could not calculate IRR"
            )


def create_monthly_cashflow_chart(cash_flows: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create monthly cash flow comparison chart."""
    
    buy_df = cash_flows["buy"]
    rent_df = cash_flows["rent"]
    
    fig = go.Figure()
    
    # Add buy monthly outflow
    fig.add_trace(go.Scatter(
        x=buy_df["month"],
        y=buy_df["net_monthly_outflow"],
        mode='lines',
        name='Buy Monthly Cost',
        line=dict(color='red', width=2),
        hovertemplate='Month %{x}<br>Buy Cost: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add rent monthly outflow
    fig.add_trace(go.Scatter(
        x=rent_df["month"],
        y=rent_df["total_rent_outflow"],
        mode='lines',
        name='Rent Monthly Cost',
        line=dict(color='blue', width=2),
        hovertemplate='Month %{x}<br>Rent Cost: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Monthly Cash Flow Comparison",
        xaxis_title="Month",
        yaxis_title="Monthly Outflow ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_cumulative_cost_chart(cash_flows: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create cumulative cost comparison chart."""
    
    buy_df = cash_flows["buy"]
    rent_df = cash_flows["rent"]
    
    fig = go.Figure()
    
    # Add cumulative buy costs
    fig.add_trace(go.Scatter(
        x=buy_df["month"],
        y=buy_df["cumulative_net_outflow"],
        mode='lines',
        name='Cumulative Buy Costs',
        line=dict(color='red', width=2),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.1)',
        hovertemplate='Month %{x}<br>Cumulative Buy: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add cumulative rent costs  
    fig.add_trace(go.Scatter(
        x=rent_df["month"],
        y=rent_df["cumulative_rent_outflow"],
        mode='lines',
        name='Cumulative Rent Costs',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,0,255,0.1)',
        hovertemplate='Month %{x}<br>Cumulative Rent: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Cumulative Cost Comparison",
        xaxis_title="Month",
        yaxis_title="Cumulative Outflow ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_net_worth_progression_chart(cash_flows: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create net worth progression chart."""
    
    buy_df = cash_flows["buy"]
    rent_df = cash_flows["rent"]
    
    # Calculate home equity progression (simplified)
    if not buy_df.empty and "home_value" in buy_df.columns:
        home_equity = buy_df["home_value"] - (buy_df["home_value"] * 0.8)  # Simplified equity calc
    else:
        home_equity = pd.Series([0] * len(buy_df))
    
    # Get portfolio progression
    portfolio_values = rent_df["portfolio_balance"] if not rent_df.empty else pd.Series([0] * len(buy_df))
    
    fig = go.Figure()
    
    # Add home equity
    fig.add_trace(go.Scatter(
        x=buy_df["month"] if not buy_df.empty else [],
        y=home_equity,
        mode='lines',
        name='Home Equity (Buy)',
        line=dict(color='green', width=2),
        hovertemplate='Month %{x}<br>Home Equity: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add investment portfolio
    fig.add_trace(go.Scatter(
        x=rent_df["month"] if not rent_df.empty else [],
        y=portfolio_values,
        mode='lines',
        name='Investment Portfolio (Rent)',
        line=dict(color='orange', width=2),
        hovertemplate='Month %{x}<br>Portfolio: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Net Worth Progression",
        xaxis_title="Month", 
        yaxis_title="Net Worth ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_cost_breakdown_chart(results: CalculationResults) -> go.Figure:
    """Create cost breakdown pie charts for buy vs rent."""
    
    # Create subplots for side-by-side pie charts
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles=("Buy Scenario Costs", "Rent Scenario Costs")
    )
    
    # Buy scenario breakdown
    buy_labels = ["Interest Paid", "Tax Shield (Saved)", "Other Costs"]
    buy_values = [
        results.total_interest_paid,
        -results.total_tax_shield,  # Negative because it's a saving
        results.npv_buy_costs - results.total_interest_paid + results.total_tax_shield
    ]
    
    # Rent scenario breakdown  
    rent_labels = ["Rent Payments", "Opportunity Cost"]
    rent_values = [
        results.npv_rent_costs * 0.8,  # Approximate
        results.npv_rent_costs * 0.2   # Approximate
    ]
    
    # Add buy pie chart
    fig.add_trace(go.Pie(
        labels=buy_labels,
        values=buy_values,
        name="Buy Costs",
        marker_colors=['red', 'green', 'orange']
    ), row=1, col=1)
    
    # Add rent pie chart  
    fig.add_trace(go.Pie(
        labels=rent_labels,
        values=rent_values,
        name="Rent Costs",
        marker_colors=['blue', 'lightblue']
    ), row=1, col=2)
    
    fig.update_traces(hoverinfo="label+percent+value", textinfo="label+percent")
    fig.update_layout(title_text="Cost Breakdown Analysis")
    
    return fig


def display_detailed_tables(cash_flows: Dict[str, pd.DataFrame]) -> None:
    """Display detailed cash flow tables in expanders."""
    
    buy_df = cash_flows["buy"]
    rent_df = cash_flows["rent"]
    
    with st.expander("📊 Detailed Buy Cash Flows"):
        if not buy_df.empty:
            # Select key columns for display
            display_cols = [
                "month", "home_value", "mortgage_payment", "property_tax", 
                "maintenance", "tax_shield", "net_monthly_outflow"
            ]
            available_cols = [col for col in display_cols if col in buy_df.columns]
            
            st.dataframe(
                buy_df[available_cols].round(0),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No buy cash flow data available")
    
    with st.expander("📊 Detailed Rent Cash Flows"):
        if not rent_df.empty:
            # Select key columns for display
            display_cols = [
                "month", "rent_payment", "other_renter_costs", "monthly_surplus", 
                "portfolio_balance", "total_rent_outflow"
            ]
            available_cols = [col for col in display_cols if col in rent_df.columns]
            
            st.dataframe(
                rent_df[available_cols].round(0),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No rent cash flow data available")


def display_assumptions_info(user_inputs, tax_params, property_info) -> None:
    """Display assumptions and data sources in an expander."""
    
    with st.expander("ℹ️ Assumptions & Data Sources"):
        st.subheader("Tax Assumptions")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Federal Marginal Rate:** {format_percentage(tax_params.federal_marginal_rate)}")
            st.write(f"**State Marginal Rate:** {format_percentage(tax_params.state_marginal_rate)}")
            st.write(f"**SALT Cap:** {format_currency(tax_params.salt_cap)}")
        
        with col2:
            st.write(f"**Standard Deduction:** {format_currency(tax_params.standard_deduction)}")
            st.write(f"**Filing Status:** {tax_params.filing_status.title()}")
            st.write(f"**Location:** {tax_params.location}")
        
        st.subheader("Property Tax Information")
        if property_info:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Property Tax Rate:** {format_percentage(property_info['property_tax_rate'])}")
                st.write(f"**County:** {property_info.get('county', 'Unknown')}")
            with col2:
                st.write(f"**Data Source:** {property_info.get('data_source', 'Unknown')}")
                st.write(f"**Match Type:** {property_info.get('match_type', 'Unknown')}")
        
        st.subheader("Key Assumptions")
        st.write(f"**Home Appreciation:** {format_percentage(user_inputs.annual_appreciation)}")
        st.write(f"**Rent Growth:** {format_percentage(user_inputs.rent_growth_pct)}")
        st.write(f"**Alternative Return:** {format_percentage(user_inputs.alt_return_annual)}")
        st.write(f"**Maintenance:** {format_percentage(user_inputs.maintenance_pct)} of home value")
        st.write(f"**Selling Costs:** {format_percentage(user_inputs.selling_cost_pct)} of sale price") 