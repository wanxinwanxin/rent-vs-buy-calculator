"""
Input validation and error handling for rent vs buy calculator.
"""
from typing import List, Tuple, Optional
from calc.models import UserInputs, DerivedInputs, TaxParams


class ValidationError(Exception):
    """Custom validation error for calculator inputs."""
    pass


def validate_user_inputs(inputs: UserInputs) -> List[str]:
    """
    Validate user inputs and return list of error messages.
    
    Args:
        inputs: UserInputs object to validate
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    
    # Income validation
    if inputs.income_you <= 0:
        errors.append("Your income must be greater than $0")
    
    if inputs.income_you + inputs.income_spouse > 10_000_000:
        errors.append("Combined income exceeds reasonable limits ($10M)")
    
    # Purchase price validation
    if inputs.purchase_price <= 0:
        errors.append("Purchase price must be greater than $0")
    
    if inputs.purchase_price > 50_000_000:
        errors.append("Purchase price exceeds reasonable limits ($50M)")
    
    # Down payment validation
    down_payment_amount = inputs.purchase_price * inputs.down_payment_pct
    if down_payment_amount < 1000 and inputs.down_payment_pct > 0:
        errors.append("Down payment amount is too small (minimum $1,000)")
    
    if inputs.down_payment_pct > 0.95:
        errors.append("Down payment cannot exceed 95% of purchase price")
    
    # Mortgage validation
    if inputs.mortgage_rate <= 0 or inputs.mortgage_rate > 0.30:
        errors.append("Mortgage rate must be between 0.1% and 30%")
    
    if inputs.mortgage_term_years < 1 or inputs.mortgage_term_years > 50:
        errors.append("Mortgage term must be between 1 and 50 years")
    
    # Rent validation
    if inputs.rent_today_monthly <= 0:
        errors.append("Monthly rent must be greater than $0")
    
    if inputs.rent_today_monthly > 100_000:
        errors.append("Monthly rent exceeds reasonable limits ($100K)")
    
    # Rate validation
    if inputs.alt_return_annual < -0.50 or inputs.alt_return_annual > 0.50:
        errors.append("Alternative return rate must be between -50% and 50%")
    
    if inputs.annual_appreciation < -0.20 or inputs.annual_appreciation > 0.30:
        errors.append("Home appreciation rate must be between -20% and 30%")
    
    if inputs.rent_growth_pct < -0.10 or inputs.rent_growth_pct > 0.20:
        errors.append("Rent growth rate must be between -10% and 20%")
    
    # Horizon validation
    if inputs.horizon_years < 1:
        errors.append("Analysis horizon must be at least 1 year")
    
    if inputs.horizon_years > 50:
        errors.append("Analysis horizon cannot exceed 50 years")
    
    # Property tax validation
    if inputs.property_tax_rate < 0 or inputs.property_tax_rate > 0.10:
        errors.append("Property tax rate must be between 0% and 10%")
    
    # Logical validations
    loan_amount = inputs.purchase_price * (1 - inputs.down_payment_pct)
    if loan_amount > 0:
        monthly_payment_estimate = loan_amount * (inputs.mortgage_rate / 12)
        monthly_income = (inputs.income_you + inputs.income_spouse) / 12
        
        if monthly_payment_estimate > monthly_income * 0.80:
            errors.append("Mortgage payment exceeds 80% of monthly income - unrealistic scenario")
    
    # Rent vs income check
    monthly_income = (inputs.income_you + inputs.income_spouse) / 12
    if inputs.rent_today_monthly > monthly_income * 0.90:
        errors.append("Rent exceeds 90% of monthly income - unrealistic scenario")
    
    return errors


def validate_calculation_inputs(
    user_inputs: UserInputs, 
    derived_inputs: DerivedInputs, 
    tax_params: TaxParams
) -> List[str]:
    """
    Validate inputs before running calculations.
    
    Args:
        user_inputs: User inputs
        derived_inputs: Derived calculations
        tax_params: Tax parameters
        
    Returns:
        List of error messages
    """
    errors = []
    
    # Derived input validation
    if derived_inputs.loan_amount < 0:
        errors.append("Loan amount cannot be negative")
    
    if derived_inputs.horizon_months <= 0:
        errors.append("Analysis horizon must be positive")
    
    # Tax parameter validation
    if tax_params.federal_marginal_rate < 0 or tax_params.federal_marginal_rate > 1:
        errors.append("Federal tax rate must be between 0% and 100%")
    
    if tax_params.state_marginal_rate < 0 or tax_params.state_marginal_rate > 1:
        errors.append("State tax rate must be between 0% and 100%")
    
    if tax_params.salt_cap < 0:
        errors.append("SALT cap cannot be negative")
    
    # Check for extreme scenarios that might cause calculation issues
    if derived_inputs.monthly_mortgage_rate > 0.05:  # 60% annual rate
        errors.append("Mortgage rate too high for reliable calculations")
    
    if derived_inputs.monthly_alt_return_rate < -0.10:  # -120% annual loss
        errors.append("Investment return rate too negative for reliable calculations")
    
    return errors


def sanitize_inputs(inputs: UserInputs) -> UserInputs:
    """
    Sanitize and clean user inputs to prevent calculation errors.
    
    Args:
        inputs: Raw user inputs
        
    Returns:
        Sanitized user inputs
    """
    # Create a copy to avoid modifying the original
    sanitized_data = inputs.model_dump()
    
    # Round monetary values to avoid floating point precision issues
    sanitized_data["purchase_price"] = round(sanitized_data["purchase_price"], 2)
    sanitized_data["rent_today_monthly"] = round(sanitized_data["rent_today_monthly"], 2)
    sanitized_data["closing_costs_buy"] = round(sanitized_data["closing_costs_buy"], 2)
    sanitized_data["insurance_hoa_annual"] = round(sanitized_data["insurance_hoa_annual"], 2)
    sanitized_data["other_owner_costs_annual"] = round(sanitized_data["other_owner_costs_annual"], 2)
    sanitized_data["other_renter_costs_monthly"] = round(sanitized_data["other_renter_costs_monthly"], 2)
    
    # Round rates to reasonable precision
    sanitized_data["mortgage_rate"] = round(sanitized_data["mortgage_rate"], 6)
    sanitized_data["property_tax_rate"] = round(sanitized_data["property_tax_rate"], 6)
    sanitized_data["annual_appreciation"] = round(sanitized_data["annual_appreciation"], 6)
    sanitized_data["alt_return_annual"] = round(sanitized_data["alt_return_annual"], 6)
    sanitized_data["rent_growth_pct"] = round(sanitized_data["rent_growth_pct"], 6)
    
    # Ensure percentages are within valid ranges
    sanitized_data["down_payment_pct"] = max(0, min(1, sanitized_data["down_payment_pct"]))
    sanitized_data["maintenance_pct"] = max(0, min(0.10, sanitized_data["maintenance_pct"]))
    sanitized_data["selling_cost_pct"] = max(0, min(0.20, sanitized_data["selling_cost_pct"]))
    
    # Handle edge cases for PMI
    if sanitized_data.get("pmi_threshold_pct"):
        sanitized_data["pmi_threshold_pct"] = max(0.05, min(0.95, sanitized_data["pmi_threshold_pct"]))
    
    if sanitized_data.get("pmi_annual_pct"):
        sanitized_data["pmi_annual_pct"] = max(0, min(0.05, sanitized_data["pmi_annual_pct"]))
    
    return UserInputs(**sanitized_data)


def check_calculation_feasibility(user_inputs: UserInputs) -> Tuple[bool, List[str]]:
    """
    Check if the calculation is feasible and likely to produce meaningful results.
    
    Args:
        user_inputs: User inputs to check
        
    Returns:
        Tuple of (is_feasible, warning_messages)
    """
    warnings = []
    is_feasible = True
    
    # Check for extreme scenarios
    loan_amount = user_inputs.purchase_price * (1 - user_inputs.down_payment_pct)
    
    # Mortgage payment feasibility
    if loan_amount > 0:
        estimated_payment = loan_amount * (user_inputs.mortgage_rate / 12) * 1.5  # P&I + taxes/insurance estimate
        monthly_income = (user_inputs.income_you + user_inputs.income_spouse) / 12
        
        if estimated_payment > monthly_income * 0.50:
            warnings.append("Mortgage payment exceeds 50% of income - high debt-to-income ratio")
        
        if estimated_payment > monthly_income:
            warnings.append("Mortgage payment exceeds total income - scenario not feasible")
            is_feasible = False
    
    # Rent affordability
    monthly_income = (user_inputs.income_you + user_inputs.income_spouse) / 12
    if user_inputs.rent_today_monthly > monthly_income * 0.70:
        warnings.append("Rent exceeds 70% of income - high rent burden")
    
    # Market assumptions check
    if user_inputs.annual_appreciation > user_inputs.alt_return_annual + 0.05:
        warnings.append("Home appreciation significantly exceeds investment returns - may favor buying unrealistically")
    
    if user_inputs.alt_return_annual > user_inputs.annual_appreciation + 0.05:
        warnings.append("Investment returns significantly exceed home appreciation - may favor renting unrealistically")
    
    # Time horizon warnings
    if user_inputs.horizon_years < 3:
        warnings.append("Short analysis horizon - transaction costs may dominate")
    
    if user_inputs.horizon_years > 30:
        warnings.append("Very long analysis horizon - projections become less reliable")
    
    # Rate environment warnings
    if user_inputs.mortgage_rate > 0.12:
        warnings.append("Very high mortgage rate - consider if this scenario is realistic")
    
    if user_inputs.mortgage_rate < 0.02:
        warnings.append("Very low mortgage rate - consider if this scenario is realistic")
    
    return is_feasible, warnings 