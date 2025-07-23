"""
Tax parameter lookup and calculation service.
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from calc.models import TaxParams


def get_data_path() -> Path:
    """Get path to data directory."""
    return Path(__file__).parent.parent / "data"


def load_tax_data() -> dict:
    """Load tax data from JSON file."""
    data_path = get_data_path() / "tax_defaults.json"
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return basic defaults if file not found - using legacy format for compatibility
        return {
            "2024": {
                "federal": {
                    "single": {"marginal_rate": 0.24, "standard_deduction": 14600, "salt_cap": 10000},
                    "married": {"marginal_rate": 0.24, "standard_deduction": 29200, "salt_cap": 10000}
                },
                "states": {
                    "NY": {
                        "single": {"marginal_rate": 0.065, "standard_deduction": 8000},
                        "married": {"marginal_rate": 0.065, "standard_deduction": 16050}
                    },
                    "NJ": {
                        "single": {"marginal_rate": 0.0897, "standard_deduction": 1000},
                        "married": {"marginal_rate": 0.0897, "standard_deduction": 2000}
                    }
                }
            }
        }


def calculate_marginal_rate_from_brackets(income: float, tax_brackets: List[Dict]) -> float:
    """
    Calculate marginal tax rate based on income and tax brackets.
    
    Args:
        income: Taxable income amount
        tax_brackets: List of tax bracket dictionaries with min_income, max_income, rate
        
    Returns:
        Marginal tax rate as decimal (e.g., 0.24 for 24%)
    """
    if not tax_brackets:
        return 0.0
    
    # Sort brackets by min_income to ensure proper ordering
    sorted_brackets = sorted(tax_brackets, key=lambda x: x['min_income'])
    
    for bracket in sorted_brackets:
        min_income = bracket['min_income']
        max_income = bracket['max_income']
        
        # Check if income falls in this bracket
        if income >= min_income:
            # If max_income is None (top bracket) or income is below max
            if max_income is None or income < max_income:
                return bracket['rate']
    
    # If no bracket found, return the highest bracket rate
    return sorted_brackets[-1]['rate']


def get_effective_tax_rate_from_brackets(income: float, tax_brackets: List[Dict]) -> float:
    """
    Calculate effective tax rate based on progressive tax brackets.
    
    Args:
        income: Taxable income amount
        tax_brackets: List of tax bracket dictionaries
        
    Returns:
        Effective tax rate as decimal
    """
    if not tax_brackets or income <= 0:
        return 0.0
    
    total_tax = 0.0
    sorted_brackets = sorted(tax_brackets, key=lambda x: x['min_income'])
    
    for bracket in sorted_brackets:
        min_income = bracket['min_income']
        max_income = bracket['max_income']
        rate = bracket['rate']
        
        if income <= min_income:
            break
            
        # Calculate taxable amount in this bracket
        bracket_max = max_income if max_income is not None else income
        taxable_in_bracket = min(income, bracket_max) - min_income
        
        if taxable_in_bracket > 0:
            total_tax += taxable_in_bracket * rate
    
    return total_tax / income if income > 0 else 0.0


def parse_location(location: str) -> tuple[str, str]:
    """Parse location string into city and state."""
    if "," in location:
        parts = location.split(",")
        city = parts[0].strip()
        state = parts[1].strip().upper()
        return city, state
    else:
        # Assume it's just a state
        return "", location.strip().upper()


def get_tax_params(
    location: str, 
    filing_status: str = "single", 
    year: int = 2024,
    income: Optional[float] = None,
    manual_federal_rate: Optional[float] = None,
    manual_state_rate: Optional[float] = None
) -> TaxParams:
    """
    Get tax parameters for a given location and filing status.
    
    Args:
        location: Location string (e.g., "NYC, NY", "Hoboken, NJ")
        filing_status: "single" or "married"
        year: Tax year (defaults to 2024)
        income: Annual income for bracket-based calculation (optional)
        manual_federal_rate: Manual override for federal rate (optional)
        manual_state_rate: Manual override for state rate (optional)
        
    Returns:
        TaxParams object with federal and state tax information
    """
    tax_data = load_tax_data()
    year_str = str(year)
    
    # Get year data or default to 2024
    year_data = tax_data.get(year_str, tax_data.get("2024", {}))
    
    # Parse location to get state
    city, state = parse_location(location)
    
    # Get federal parameters
    federal_data = year_data.get("federal", {}).get(filing_status, {})
    standard_deduction = federal_data.get("standard_deduction", 14600 if filing_status == "single" else 29200)
    salt_cap = federal_data.get("salt_cap", 10000)
    
    # Calculate federal marginal rate
    if manual_federal_rate is not None:
        federal_marginal_rate = manual_federal_rate
    elif income is not None and "tax_brackets" in federal_data:
        # Use income-based calculation
        taxable_income = max(0, income - standard_deduction)
        federal_marginal_rate = calculate_marginal_rate_from_brackets(taxable_income, federal_data["tax_brackets"])
    else:
        # Fallback to legacy fixed rate or default
        federal_marginal_rate = federal_data.get("marginal_rate", 0.24)
    
    # Get state parameters
    state_data = year_data.get("states", {}).get(state, {}).get(filing_status, {})
    
    # Calculate state marginal rate
    if manual_state_rate is not None:
        state_marginal_rate = manual_state_rate
    elif income is not None and "tax_brackets" in state_data:
        # Use income-based calculation
        state_standard_deduction = state_data.get("standard_deduction", 0)
        taxable_income = max(0, income - state_standard_deduction)
        state_marginal_rate = calculate_marginal_rate_from_brackets(taxable_income, state_data["tax_brackets"])
    else:
        # Fallback to legacy fixed rate or default
        state_marginal_rate = state_data.get("marginal_rate", 0.0)
    
    # Add local taxes if available (e.g., NYC local income tax)
    local_marginal_rate = 0.0
    local_taxes = year_data.get("local_taxes", {})
    if city in local_taxes and filing_status in local_taxes[city]:
        local_data = local_taxes[city][filing_status]
        if income is not None and "tax_brackets" in local_data:
            # Use local standard deduction if available, otherwise use state deduction
            local_standard_deduction = local_data.get("standard_deduction", state_standard_deduction)
            local_taxable_income = max(0, income - local_standard_deduction)
            local_marginal_rate = calculate_marginal_rate_from_brackets(local_taxable_income, local_data["tax_brackets"])
        else:
            # Fallback to legacy fixed rate
            local_marginal_rate = local_data.get("marginal_rate", 0.0)
    
    # Combine state and local rates
    combined_state_local_rate = state_marginal_rate + local_marginal_rate
    
    # Combine federal and state standard deductions (take the higher one)
    state_standard_deduction = state_data.get("standard_deduction", 0)
    final_standard_deduction = max(standard_deduction, state_standard_deduction)
    
    return TaxParams(
        federal_marginal_rate=federal_marginal_rate,
        state_marginal_rate=combined_state_local_rate,
        salt_cap=salt_cap,
        standard_deduction=final_standard_deduction,
        location=location,
        filing_status=filing_status
    )


def get_marginal_tax_rate(
    location: str, 
    filing_status: str = "single", 
    income: Optional[float] = None,
    manual_federal_rate: Optional[float] = None,
    manual_state_rate: Optional[float] = None
) -> float:
    """
    Get combined federal + state marginal tax rate for location.
    
    Args:
        location: Location string
        filing_status: Filing status
        income: Annual income for bracket-based calculation (optional)
        manual_federal_rate: Manual override for federal rate (optional)
        manual_state_rate: Manual override for state rate (optional)
        
    Returns:
        Combined marginal tax rate
    """
    tax_params = get_tax_params(location, filing_status, income=income, 
                               manual_federal_rate=manual_federal_rate,
                               manual_state_rate=manual_state_rate)
    return tax_params.federal_marginal_rate + tax_params.state_marginal_rate


def get_tax_breakdown(
    location: str,
    filing_status: str = "single",
    income: float = 100000
) -> Dict[str, Any]:
    """
    Get detailed tax breakdown showing effective vs marginal rates.
    
    Args:
        location: Location string
        filing_status: Filing status
        income: Annual income
        
    Returns:
        Dictionary with detailed tax information
    """
    tax_data = load_tax_data()
    year_data = tax_data.get("2024", {})
    city, state = parse_location(location)
    
    # Federal calculation
    federal_data = year_data.get("federal", {}).get(filing_status, {})
    federal_std_ded = federal_data.get("standard_deduction", 14600 if filing_status == "single" else 29200)
    federal_taxable = max(0, income - federal_std_ded)
    
    federal_marginal = 0.0
    federal_effective = 0.0
    
    if "tax_brackets" in federal_data:
        federal_marginal = calculate_marginal_rate_from_brackets(federal_taxable, federal_data["tax_brackets"])
        federal_effective = get_effective_tax_rate_from_brackets(federal_taxable, federal_data["tax_brackets"])
    
    # State calculation
    state_data = year_data.get("states", {}).get(state, {}).get(filing_status, {})
    state_std_ded = state_data.get("standard_deduction", 0)
    state_taxable = max(0, income - state_std_ded)
    
    state_marginal = 0.0
    state_effective = 0.0
    
    if "tax_brackets" in state_data:
        state_marginal = calculate_marginal_rate_from_brackets(state_taxable, state_data["tax_brackets"])
        state_effective = get_effective_tax_rate_from_brackets(state_taxable, state_data["tax_brackets"])
    
    # Add local taxes if available (e.g., NYC local income tax)
    local_marginal = 0.0
    local_effective = 0.0
    local_taxes = year_data.get("local_taxes", {})
    if city in local_taxes and filing_status in local_taxes[city]:
        local_data = local_taxes[city][filing_status]
        if "tax_brackets" in local_data:
            local_std_ded = local_data.get("standard_deduction", state_std_ded)
            local_taxable = max(0, income - local_std_ded)
            local_marginal = calculate_marginal_rate_from_brackets(local_taxable, local_data["tax_brackets"])
            local_effective = get_effective_tax_rate_from_brackets(local_taxable, local_data["tax_brackets"])
    
    # Combine state and local rates
    combined_state_marginal = state_marginal + local_marginal
    combined_state_effective = state_effective + local_effective
    
    return {
        "income": income,
        "location": location,
        "filing_status": filing_status,
        "federal": {
            "taxable_income": federal_taxable,
            "marginal_rate": federal_marginal,
            "effective_rate": federal_effective,
            "standard_deduction": federal_std_ded
        },
        "state": {
            "taxable_income": state_taxable,
            "marginal_rate": combined_state_marginal,
            "effective_rate": combined_state_effective,
            "standard_deduction": state_std_ded,
            "state_code": state
        },
        "combined": {
            "marginal_rate": federal_marginal + combined_state_marginal,
            "effective_rate": federal_effective + combined_state_effective
        }
    }


def get_available_locations() -> list[str]:
    """
    Get list of available locations with tax data.
    
    Returns:
        List of location strings
    """
    tax_data = load_tax_data()
    year_data = tax_data.get("2024", {})
    states = year_data.get("states", {}).keys()
    
    # Return common locations for each state
    locations = []
    for state in states:
        if state == "NY":
            locations.extend(["NYC, NY", "Brooklyn, NY", "Queens, NY", "Bronx, NY", "Staten Island, NY", "Westchester County, NY", "Long Island, NY"])
        elif state == "NJ":
            locations.extend(["Hoboken, NJ", "Jersey City, NJ", "Fort Lee, NJ", "Princeton, NJ", "Summit, NJ", "Montclair, NJ"])
        elif state == "CT":
            locations.extend(["Stamford, CT", "Greenwich, CT", "New Canaan, CT"])
        elif state == "CA":
            locations.extend(["Los Angeles, CA", "San Francisco, CA", "San Diego, CA", "San Jose, CA", "Oakland, CA", "Palo Alto, CA", "Beverly Hills, CA"])
        elif state == "TX":
            locations.extend(["Dallas, TX", "Houston, TX", "Austin, TX", "San Antonio, TX", "Fort Worth, TX", "Plano, TX"])
        elif state == "FL":
            locations.extend(["Miami, FL", "Orlando, FL", "Tampa, FL", "Jacksonville, FL", "Fort Lauderdale, FL", "Naples, FL"])
        elif state == "IL":
            locations.extend(["Chicago, IL", "Naperville, IL", "Evanston, IL", "Lake Forest, IL"])
        elif state == "WA":
            locations.extend(["Seattle, WA", "Bellevue, WA", "Redmond, WA", "Tacoma, WA"])
        elif state == "MA":
            locations.extend(["Boston, MA", "Cambridge, MA", "Newton, MA", "Brookline, MA"])
        elif state == "VA":
            locations.extend(["Arlington, VA", "Alexandria, VA", "Fairfax, VA", "Richmond, VA"])
        elif state == "GA":
            locations.extend(["Atlanta, GA", "Sandy Springs, GA", "Alpharetta, GA"])
        elif state == "NC":
            locations.extend(["Charlotte, NC", "Raleigh, NC", "Durham, NC"])
        elif state == "OH":
            locations.extend(["Columbus, OH", "Cleveland, OH", "Cincinnati, OH"])
        elif state == "PA":
            locations.extend(["Philadelphia, PA", "Pittsburgh, PA"])
        elif state == "MI":
            locations.extend(["Detroit, MI", "Grand Rapids, MI"])
        elif state == "AZ":
            locations.extend(["Phoenix, AZ", "Scottsdale, AZ", "Tucson, AZ"])
        elif state == "NV":
            locations.extend(["Las Vegas, NV", "Reno, NV"])
        elif state == "CO":
            locations.extend(["Denver, CO", "Boulder, CO", "Colorado Springs, CO"])
        elif state == "OR":
            locations.extend(["Portland, OR", "Eugene, OR"])
    
    return sorted(locations) 