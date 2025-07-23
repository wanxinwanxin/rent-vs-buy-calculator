"""
Streamlit UI widgets for rent vs buy calculator.
"""
import streamlit as st
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

from calc.models import UserInputs
from services.tax_lookup import get_available_locations as get_tax_locations
from services.property_data import get_available_locations as get_property_locations, get_property_tax_rate
from services.mortgage_rates import load_assumptions


def load_default_assumptions() -> dict:
    """Load default assumptions from YAML file."""
    try:
        current_dir = Path(__file__).parent
        data_path = current_dir.parent / "data" / "assumptions.yaml"
        with open(data_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


def create_household_inputs() -> Dict[str, Any]:
    """Create household information input widgets."""
    st.subheader("💰 Household Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        income_you = st.number_input(
            "Your Annual Income",
            min_value=0,
            value=100000,
            step=5000,
            format="%,d",
            help="Your gross annual income before taxes"
        )
        
        filing_status = st.selectbox(
            "Filing Status",
            ["single", "married"],
            help="Tax filing status"
        )
    
    with col2:
        income_spouse = st.number_input(
            "Spouse Annual Income",
            min_value=0,
            value=0 if filing_status == "single" else 80000,
            step=5000,
            format="%,d",
            help="Spouse's gross annual income (if married)"
        )
        
        income_growth = st.slider(
            "Annual Income Growth",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            format="%.1f%%",
            help="Expected annual income growth rate"
        )
    
    # Location with smart defaults
    available_locations = get_property_locations()
    default_location = "NYC, NY" if "NYC, NY" in available_locations else available_locations[0] if available_locations else "NYC, NY"
    
    location = st.selectbox(
        "Location",
        available_locations,
        index=available_locations.index(default_location) if default_location in available_locations else 0,
        help="Location for tax and property data lookup"
    )
    
    return {
        "income_you": income_you,
        "income_spouse": income_spouse,
        "income_growth": income_growth / 100.0,  # Convert percentage back to decimal
        "filing_status": filing_status,
        "location": location
    }


def create_buy_inputs(location: str) -> Dict[str, Any]:
    """Create buy scenario input widgets."""
    st.subheader("🏠 Buy Scenario")
    
    assumptions = load_default_assumptions()
    mortgage_defaults = assumptions.get("mortgage", {})
    homeowner_defaults = assumptions.get("homeownership", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        purchase_price = st.number_input(
            "Purchase Price",
            min_value=0,
            value=800000,
            step=25000,
            format="%,d",
            help="Total home purchase price"
        )
        
        down_payment_pct = st.slider(
            "Down Payment %",
            min_value=0.0,
            max_value=100.0,
            value=mortgage_defaults.get("typical_down_payment", 0.20) * 100,
            step=5.0,
            format="%.0f%%",
            help="Down payment as percentage of purchase price"
        )
        
        closing_costs_buy = st.number_input(
            "Closing Costs",
            min_value=0,
            value=int(purchase_price * 0.02),  # 2% default
            step=1000,
            format="%,d",
            help="One-time closing costs for buying"
        )
        
        mortgage_rate = st.slider(
            "Mortgage Rate",
            min_value=1.0,
            max_value=12.0,
            value=mortgage_defaults.get("typical_rate", 0.07) * 100,
            step=0.25,
            format="%.2f%%",
            help="Annual mortgage interest rate"
        )
        
        mortgage_term_years = st.selectbox(
            "Mortgage Term",
            [15, 20, 25, 30],
            index=3,  # Default to 30 years
            help="Mortgage term in years"
        )
    
    with col2:
        # Auto-populate property tax rate based on location
        default_prop_tax_rate = get_property_tax_rate(location)
        property_tax_rate = st.slider(
            "Property Tax Rate",
            min_value=0.0,
            max_value=5.0,
            value=default_prop_tax_rate * 100,
            step=0.1,
            format="%.1f%%",
            help=f"Annual property tax rate (auto-filled: {default_prop_tax_rate*100:.1f}% for {location})"
        )
        
        insurance_hoa_annual = st.number_input(
            "Insurance + HOA (Annual)",
            min_value=0,
            value=int(purchase_price * homeowner_defaults.get("insurance_annual_pct", 0.003)),
            step=500,
            format="%,d",
            help="Annual insurance and HOA fees"
        )
        
        maintenance_pct = st.slider(
            "Maintenance %",
            min_value=0.0,
            max_value=5.0,
            value=homeowner_defaults.get("maintenance_pct", 0.015) * 100,
            step=0.25,
            format="%.2f%%",
            help="Annual maintenance as % of home value"
        )
        
        annual_appreciation = st.slider(
            "Annual Appreciation",
            min_value=-5.0,
            max_value=10.0,
            value=assumptions.get("market", {}).get("home_appreciation", 0.03) * 100,
            step=0.5,
            format="%.1f%%",
            help="Expected annual home appreciation rate"
        )
        
        selling_cost_pct = st.slider(
            "Selling Costs %",
            min_value=0.0,
            max_value=10.0,
            value=homeowner_defaults.get("selling_cost_pct", 0.06) * 100,
            step=0.5,
            format="%.1f%%",
            help="Selling costs as % of sale price (realtor, transfer tax, etc.)"
        )
    
    # Advanced buy options in expander
    with st.expander("Advanced Buy Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            points_pct = st.slider(
                "Mortgage Points",
                min_value=0.0,
                max_value=3.0,
                value=0.0,
                step=0.5,
                format="%.1f%%",
                help="Points paid upfront to reduce rate"
            )
            
            other_owner_costs_annual = st.number_input(
                "Other Annual Costs",
                min_value=0,
                value=0,
                step=500,
                format="%,d",
                help="Other annual homeowner costs"
            )
        
        with col2:
            pmi_threshold_pct = st.slider(
                "PMI Threshold LTV",
                min_value=70.0,
                max_value=95.0,
                value=80.0,
                step=5.0,
                format="%.0f%%",
                help="LTV below which PMI is removed"
            )
            
            pmi_annual_pct = st.slider(
                "PMI Rate",
                min_value=0.0,
                max_value=2.0,
                value=assumptions.get("pmi", {}).get("annual_rate", 0.005) * 100,
                step=0.1,
                format="%.1f%%",
                help="Annual PMI rate on loan balance"
            )
    
    return {
        "purchase_price": purchase_price,
        "down_payment_pct": down_payment_pct / 100.0,  # Convert percentage back to decimal
        "closing_costs_buy": closing_costs_buy,
        "mortgage_rate": mortgage_rate / 100.0,  # Convert percentage back to decimal
        "mortgage_term_years": mortgage_term_years,
        "points_pct": points_pct / 100.0 if points_pct > 0 else None,  # Convert percentage back to decimal
        "property_tax_rate": property_tax_rate / 100.0,  # Convert percentage back to decimal
        "insurance_hoa_annual": insurance_hoa_annual,
        "maintenance_pct": maintenance_pct / 100.0,  # Convert percentage back to decimal
        "other_owner_costs_annual": other_owner_costs_annual,
        "annual_appreciation": annual_appreciation / 100.0,  # Convert percentage back to decimal
        "selling_cost_pct": selling_cost_pct / 100.0,  # Convert percentage back to decimal
        "pmi_threshold_pct": pmi_threshold_pct / 100.0,  # Convert percentage back to decimal
        "pmi_annual_pct": pmi_annual_pct / 100.0,  # Convert percentage back to decimal
        "refinance_enabled": False,  # Not implemented in UI yet
        "expected_refi_rate": None
    }


def create_rent_inputs() -> Dict[str, Any]:
    """Create rent scenario input widgets."""
    st.subheader("🏠 Rent Scenario")
    
    assumptions = load_default_assumptions()
    
    col1, col2 = st.columns(2)
    
    with col1:
        rent_today_monthly = st.number_input(
            "Current Monthly Rent",
            min_value=0,
            value=4000,
            step=100,
            format="%,d",
            help="Current monthly rent payment"
        )
        
        rent_growth_pct = st.slider(
            "Annual Rent Growth",
            min_value=0.0,
            max_value=8.0,
            value=assumptions.get("market", {}).get("rent_growth_rate", 0.03) * 100,
            step=0.5,
            format="%.1f%%",
            help="Expected annual rent growth rate"
        )
    
    with col2:
        other_renter_costs_monthly = st.number_input(
            "Other Monthly Costs",
            min_value=0,
            value=200,
            step=50,
            format="%,d",
            help="Other monthly renter costs (parking, storage, etc.)"
        )
    
    return {
        "rent_today_monthly": rent_today_monthly,
        "rent_growth_pct": rent_growth_pct / 100.0,  # Convert percentage back to decimal
        "other_renter_costs_monthly": other_renter_costs_monthly
    }


def create_finance_inputs() -> Dict[str, Any]:
    """Create financial assumptions input widgets."""
    st.subheader("📈 Financial Assumptions")
    
    assumptions = load_default_assumptions()
    financial_defaults = assumptions.get("financial", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        alt_return_annual = st.slider(
            "Alternative Investment Return",
            min_value=1.0,
            max_value=15.0,
            value=financial_defaults.get("alt_return_annual", 0.07) * 100,
            step=0.5,
            format="%.1f%%",
            help="Expected annual return from alternative investments (e.g., stock market)"
        )
        
        inflation_discount_annual = st.slider(
            "Inflation/Discount Rate",
            min_value=1.0,
            max_value=8.0,
            value=financial_defaults.get("inflation_rate", 0.03) * 100,
            step=0.5,
            format="%.1f%%",
            help="Inflation rate for discounting future cash flows"
        )
    
    with col2:
        horizon_years = st.slider(
            "Analysis Horizon",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
            help="Number of years to analyze"
        )
    
    return {
        "alt_return_annual": alt_return_annual / 100.0,  # Convert percentage back to decimal
        "inflation_discount_annual": inflation_discount_annual / 100.0,  # Convert percentage back to decimal
        "horizon_years": horizon_years
    }


def create_user_inputs() -> UserInputs:
    """Create and validate complete UserInputs from all widgets."""
    
    # Create input sections
    household_data = create_household_inputs()
    
    st.divider()
    buy_data = create_buy_inputs(household_data["location"])
    
    st.divider()
    rent_data = create_rent_inputs()
    
    st.divider()
    finance_data = create_finance_inputs()
    
    # Combine all inputs
    combined_data = {**household_data, **buy_data, **rent_data, **finance_data}
    
    # Create and validate UserInputs object
    try:
        user_inputs = UserInputs(**combined_data)
        return user_inputs
    except Exception as e:
        st.error(f"Input validation error: {e}")
        # Return a default UserInputs object to prevent crashes
        return UserInputs(
            income_you=100000,
            purchase_price=800000,
            rent_today_monthly=4000
        ) 