"""
Data models for rent vs buy calculator inputs and outputs.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class UserInputs(BaseModel):
    """Core input schema for rent vs buy calculation."""
    
    # Household
    income_you: float = Field(gt=0, description="Your annual income")
    income_spouse: float = Field(ge=0, default=0, description="Spouse annual income")
    income_growth: float = Field(ge=0, default=0.03, description="Annual income growth rate")
    filing_status: Literal["single", "married"] = Field(default="single")
    location: str = Field(default="NYC, NY", description="Location for tax/property data")

    # Buy side
    purchase_price: float = Field(gt=0, description="Home purchase price")
    down_payment_pct: float = Field(ge=0, le=1, default=0.20, description="Down payment percentage")
    closing_costs_buy: float = Field(ge=0, default=0, description="Closing costs for buying")
    mortgage_rate: float = Field(gt=0, le=1, default=0.07, description="Annual mortgage rate")
    mortgage_term_years: int = Field(gt=0, default=30, description="Mortgage term in years")
    points_pct: Optional[float] = Field(ge=0, le=1, default=None, description="Points paid upfront")
    property_tax_rate: float = Field(ge=0, le=1, default=0.012, description="Annual property tax rate")
    insurance_hoa_annual: float = Field(ge=0, default=0, description="Annual insurance + HOA")
    maintenance_pct: float = Field(ge=0, le=1, default=0.015, description="Annual maintenance as % of home value")
    other_owner_costs_annual: float = Field(ge=0, default=0, description="Other annual owner costs")
    annual_appreciation: float = Field(ge=0, default=0.03, description="Annual home appreciation rate")
    selling_cost_pct: float = Field(ge=0, le=1, default=0.06, description="Selling costs as % of sale price")

    # Rent side
    rent_today_monthly: float = Field(gt=0, description="Current monthly rent")
    rent_growth_pct: float = Field(ge=0, default=0.03, description="Annual rent growth rate")
    other_renter_costs_monthly: float = Field(ge=0, default=0, description="Other monthly renter costs")

    # Finance
    alt_return_annual: float = Field(gt=0, default=0.07, description="Alternative investment return rate")
    inflation_discount_annual: float = Field(gt=0, default=0.03, description="Inflation/discount rate")
    horizon_years: int = Field(gt=0, default=10, description="Analysis horizon in years")

    # PMI, Refi toggles
    pmi_threshold_pct: Optional[float] = Field(ge=0, le=1, default=0.20, description="PMI threshold LTV")
    pmi_annual_pct: Optional[float] = Field(ge=0, le=1, default=0.005, description="Annual PMI rate")
    refinance_enabled: bool = Field(default=False, description="Enable refinancing consideration")
    expected_refi_rate: Optional[float] = Field(ge=0, le=1, default=None, description="Expected refi rate")


class DerivedInputs(BaseModel):
    """Derived calculations from user inputs."""
    
    loan_amount: float
    monthly_mortgage_rate: float
    monthly_rent_growth_rate: float
    monthly_alt_return_rate: float
    monthly_inflation_rate: float
    monthly_appreciation_rate: float
    horizon_months: int
    down_payment_amount: float
    
    @classmethod
    def from_user_inputs(cls, user_inputs: UserInputs) -> "DerivedInputs":
        """Calculate derived inputs from user inputs."""
        loan_amount = user_inputs.purchase_price * (1 - user_inputs.down_payment_pct)
        
        return cls(
            loan_amount=loan_amount,
            monthly_mortgage_rate=user_inputs.mortgage_rate / 12,
            monthly_rent_growth_rate=user_inputs.rent_growth_pct / 12,
            monthly_alt_return_rate=user_inputs.alt_return_annual / 12,
            monthly_inflation_rate=user_inputs.inflation_discount_annual / 12,
            monthly_appreciation_rate=user_inputs.annual_appreciation / 12,
            horizon_months=user_inputs.horizon_years * 12,
            down_payment_amount=user_inputs.purchase_price * user_inputs.down_payment_pct
        )


class TaxParams(BaseModel):
    """Tax parameters for a given location and filing status."""
    
    federal_marginal_rate: float
    state_marginal_rate: float
    salt_cap: float
    standard_deduction: float
    location: str
    filing_status: str


class CalculationResults(BaseModel):
    """Results of rent vs buy calculation."""
    
    # Monthly flows
    monthly_buy_payment: float
    monthly_buy_after_tax: float
    monthly_rent_payment: float
    monthly_invested_surplus: float
    
    # End state
    home_equity_at_exit: float
    investment_portfolio_value: float
    net_worth_difference: float  # buy - rent
    
    # Metrics
    npv_buy_costs: float
    npv_rent_costs: float
    npv_difference: float
    irr_buy_investment: Optional[float]
    breakeven_month: Optional[int]
    
    # Sensitivity data (for future use)
    total_interest_paid: float
    total_tax_shield: float
    total_appreciation: float 