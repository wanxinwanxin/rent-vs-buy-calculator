"""
Tax parameter lookup service.
"""
import json
import os
from typing import Optional
from pathlib import Path

from calc.models import TaxParams


def get_data_path() -> Path:
    """Get the path to the data directory."""
    current_dir = Path(__file__).parent
    return current_dir.parent / "data"


def load_tax_data() -> dict:
    """Load tax data from JSON file."""
    data_path = get_data_path() / "tax_defaults.json"
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return basic defaults if file not found
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


def parse_location(location: str) -> tuple[str, str]:
    """
    Parse location string to extract city and state.
    
    Args:
        location: Location string like "NYC, NY" or "Hoboken, NJ"
        
    Returns:
        Tuple of (city, state)
    """
    if "," in location:
        parts = [part.strip() for part in location.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[1]
    
    # Default fallback
    return location, "NY"


def get_tax_params(location: str, filing_status: str = "single", year: int = 2024) -> TaxParams:
    """
    Get tax parameters for a given location and filing status.
    
    Args:
        location: Location string (e.g., "NYC, NY", "Hoboken, NJ")
        filing_status: "single" or "married"
        year: Tax year (defaults to 2024)
        
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
    federal_marginal_rate = federal_data.get("marginal_rate", 0.24)
    standard_deduction = federal_data.get("standard_deduction", 14600 if filing_status == "single" else 29200)
    salt_cap = federal_data.get("salt_cap", 10000)
    
    # Get state parameters
    state_data = year_data.get("states", {}).get(state, {}).get(filing_status, {})
    state_marginal_rate = state_data.get("marginal_rate", 0.0)  # Default to 0 if state not found
    
    # Combine federal and state standard deductions (take the higher one)
    state_standard_deduction = state_data.get("standard_deduction", 0)
    final_standard_deduction = max(standard_deduction, state_standard_deduction)
    
    return TaxParams(
        federal_marginal_rate=federal_marginal_rate,
        state_marginal_rate=state_marginal_rate,
        salt_cap=salt_cap,
        standard_deduction=final_standard_deduction,
        location=location,
        filing_status=filing_status
    )


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
            locations.extend(["NYC, NY", "Brooklyn, NY", "Queens, NY", "Westchester County, NY"])
        elif state == "NJ":
            locations.extend(["Hoboken, NJ", "Jersey City, NJ", "Princeton, NJ"])
        elif state == "CT":
            locations.extend(["Stamford, CT", "Greenwich, CT"])
    
    return locations


def get_marginal_tax_rate(location: str, filing_status: str = "single") -> float:
    """
    Get combined federal + state marginal tax rate for location.
    
    Args:
        location: Location string
        filing_status: Filing status
        
    Returns:
        Combined marginal tax rate
    """
    tax_params = get_tax_params(location, filing_status)
    return tax_params.federal_marginal_rate + tax_params.state_marginal_rate 