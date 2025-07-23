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
    """Parse location string into city and state/country."""
    if "," in location:
        parts = location.split(",")
        city = parts[0].strip()
        region = parts[1].strip().upper()
        return city, region
    else:
        # Assume it's just a state/country
        return "", location.strip().upper()


def is_international_location(location: str) -> tuple[bool, str]:
    """
    Check if location is international and return country code.
    
    Returns:
        Tuple of (is_international, country_code)
    """
    city, region = parse_location(location)
    
    # International location patterns
    international_regions = {
        # Canada
        'ON': 'canada', 'BC': 'canada', 'QC': 'canada', 'AB': 'canada',
        # UK
        'UK': 'united_kingdom', 'ENGLAND': 'united_kingdom', 'SCOTLAND': 'united_kingdom',
        'GREATER LONDON': 'united_kingdom', 'GREATER MANCHESTER': 'united_kingdom',
        'WEST MIDLANDS': 'united_kingdom', 'MERSEYSIDE': 'united_kingdom',
        # Australia  
        'NSW': 'australia', 'VIC': 'australia', 'QLD': 'australia', 'WA': 'australia', 'SA': 'australia',
        # Singapore
        'SG': 'singapore', 'SINGAPORE': 'singapore',
        # Japan
        'JP': 'japan', 'JAPAN': 'japan',
        # Hong Kong
        'HK': 'hong_kong', 'HONG KONG': 'hong_kong',
        # European Countries
        'GERMANY': 'germany', 'DE': 'germany',
        'FRANCE': 'france', 'FR': 'france',
        'ITALY': 'italy', 'IT': 'italy',
        'SPAIN': 'spain', 'ES': 'spain',
        'NETHERLANDS': 'netherlands', 'NL': 'netherlands',
        'SWITZERLAND': 'switzerland', 'CH': 'switzerland',
        'BELGIUM': 'belgium', 'BE': 'belgium',
        'AUSTRIA': 'austria', 'AT': 'austria',
        'SWEDEN': 'sweden', 'SE': 'sweden',
        'NORWAY': 'norway', 'NO': 'norway',
        'DENMARK': 'denmark', 'DK': 'denmark',
        'FINLAND': 'finland', 'FI': 'finland'
    }
    
    # Check for international patterns in city names
    international_cities = {
        'TORONTO': 'canada', 'VANCOUVER': 'canada', 'MONTREAL': 'canada', 'CALGARY': 'canada', 'OTTAWA': 'canada', 'EDMONTON': 'canada',
        'LONDON': 'united_kingdom', 'MANCHESTER': 'united_kingdom', 'EDINBURGH': 'united_kingdom', 
        'BIRMINGHAM': 'united_kingdom', 'GLASGOW': 'united_kingdom', 'LIVERPOOL': 'united_kingdom',
        'SYDNEY': 'australia', 'MELBOURNE': 'australia', 'BRISBANE': 'australia', 'PERTH': 'australia', 'ADELAIDE': 'australia',
        'SINGAPORE': 'singapore',
        'TOKYO': 'japan', 'OSAKA': 'japan', 'YOKOHAMA': 'japan',
        'HONG KONG': 'hong_kong',
        # European Cities
        'BERLIN': 'germany', 'MUNICH': 'germany', 'HAMBURG': 'germany', 'FRANKFURT': 'germany', 'COLOGNE': 'germany', 'STUTTGART': 'germany',
        'PARIS': 'france', 'LYON': 'france', 'MARSEILLE': 'france', 'TOULOUSE': 'france', 'NICE': 'france', 'BORDEAUX': 'france',
        'ROME': 'italy', 'MILAN': 'italy', 'NAPLES': 'italy', 'TURIN': 'italy', 'FLORENCE': 'italy', 'BOLOGNA': 'italy',
        'MADRID': 'spain', 'BARCELONA': 'spain', 'VALENCIA': 'spain', 'SEVILLE': 'spain', 'BILBAO': 'spain', 'MALAGA': 'spain',
        'AMSTERDAM': 'netherlands', 'ROTTERDAM': 'netherlands', 'THE HAGUE': 'netherlands', 'UTRECHT': 'netherlands', 'EINDHOVEN': 'netherlands', 'TILBURG': 'netherlands',
        'ZURICH': 'switzerland', 'GENEVA': 'switzerland', 'BASEL': 'switzerland', 'BERN': 'switzerland', 'LAUSANNE': 'switzerland', 'WINTERTHUR': 'switzerland',
        'BRUSSELS': 'belgium', 'ANTWERP': 'belgium', 'GHENT': 'belgium', 'BRUGES': 'belgium', 'LEUVEN': 'belgium', 'LIEGE': 'belgium',
        'VIENNA': 'austria', 'SALZBURG': 'austria', 'INNSBRUCK': 'austria', 'GRAZ': 'austria', 'LINZ': 'austria', 'KLAGENFURT': 'austria',
        'STOCKHOLM': 'sweden', 'GOTHENBURG': 'sweden', 'MALMÖ': 'sweden', 'UPPSALA': 'sweden', 'VÄSTERÅS': 'sweden', 'ÖREBRO': 'sweden',
        'OSLO': 'norway', 'BERGEN': 'norway', 'TRONDHEIM': 'norway', 'STAVANGER': 'norway', 'KRISTIANSAND': 'norway', 'FREDRIKSTAD': 'norway',
        'COPENHAGEN': 'denmark', 'AARHUS': 'denmark', 'ODENSE': 'denmark', 'AALBORG': 'denmark', 'ESBJERG': 'denmark', 'RANDERS': 'denmark',
        'HELSINKI': 'finland', 'TAMPERE': 'finland', 'TURKU': 'finland', 'OULU': 'finland', 'JYVÄSKYLÄ': 'finland', 'LAHTI': 'finland'
    }
    
    if region in international_regions:
        return True, international_regions[region]
    elif city.upper() in international_cities:
        return True, international_cities[city.upper()]
    
    return False, ""


def get_international_tax_params(
    location: str,
    country: str,
    filing_status: str = "single",
    year: int = 2024,
    income: Optional[float] = None,
    manual_federal_rate: Optional[float] = None,
    manual_state_rate: Optional[float] = None
) -> TaxParams:
    """
    Get tax parameters for international locations.
    """
    tax_data = load_tax_data()
    year_str = str(year)
    
    # Get year data or default to 2024
    year_data = tax_data.get(year_str, tax_data.get("2024", {}))
    international_data = year_data.get("international", {})
    
    city, region = parse_location(location)
    
    if country == "canada":
        # Canada has federal + provincial taxes
        federal_data = international_data.get("canada", {}).get("federal", {}).get(filing_status, {})
        provincial_data = international_data.get("canada", {}).get("provinces", {}).get(region, {}).get(filing_status, {})
        
        federal_std_ded = federal_data.get("standard_deduction", 15000)
        provincial_std_ded = provincial_data.get("standard_deduction", 0)
        
        # Calculate federal rate
        if manual_federal_rate is not None:
            federal_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in federal_data:
            taxable_income = max(0, income - federal_std_ded)
            federal_rate = calculate_marginal_rate_from_brackets(taxable_income, federal_data["tax_brackets"])
        else:
            federal_rate = 0.25  # Default
        
        # Calculate provincial rate
        if manual_state_rate is not None:
            provincial_rate = manual_state_rate
        elif income is not None and "tax_brackets" in provincial_data:
            taxable_income = max(0, income - provincial_std_ded)
            provincial_rate = calculate_marginal_rate_from_brackets(taxable_income, provincial_data["tax_brackets"])
        else:
            provincial_rate = 0.10  # Default
        
        return TaxParams(
            federal_marginal_rate=federal_rate,
            state_marginal_rate=provincial_rate,
            salt_cap=0,  # No SALT cap in Canada
            standard_deduction=max(federal_std_ded, provincial_std_ded),
            location=location,
            filing_status=filing_status
        )
    
    elif country == "united_kingdom":
        # UK has income tax (varies by region)
        region_key = "scotland" if "SCOTLAND" in region.upper() or "EDINBURGH" in city.upper() or "GLASGOW" in city.upper() else "england"
        
        uk_data = international_data.get("united_kingdom", {}).get("income_tax", {}).get(region_key, {}).get(filing_status, {})
        
        std_ded = uk_data.get("standard_deduction", 12570)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in uk_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, uk_data["tax_brackets"])
        else:
            tax_rate = 0.20  # Default basic rate
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,  # No separate state tax
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    elif country == "australia":
        # Australia has federal tax only
        aus_data = international_data.get("australia", {}).get("federal", {}).get(filing_status, {})
        
        std_ded = aus_data.get("standard_deduction", 18200)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in aus_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, aus_data["tax_brackets"])
        else:
            tax_rate = 0.325  # Default middle rate
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    elif country == "singapore":
        # Singapore income tax
        residency = "resident" if manual_state_rate is None else "non_resident"
        sg_data = international_data.get("singapore", {}).get("income_tax", {}).get(residency, {}).get(filing_status, {})
        
        std_ded = sg_data.get("standard_deduction", 1000 if residency == "resident" else 0)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in sg_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, sg_data["tax_brackets"])
        else:
            tax_rate = 0.24 if residency == "non_resident" else 0.07  # Default rates
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    elif country == "japan":
        # Japan income tax
        jp_data = international_data.get("japan", {}).get("income_tax", {}).get("resident", {}).get(filing_status, {})
        
        std_ded = jp_data.get("standard_deduction", 380000 if filing_status == "single" else 760000)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in jp_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, jp_data["tax_brackets"])
        else:
            tax_rate = 0.20  # Default rate
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    elif country == "hong_kong":
        # Hong Kong salaries tax
        hk_data = international_data.get("hong_kong", {}).get("salaries_tax", {}).get("resident", {}).get(filing_status, {})
        
        std_ded = hk_data.get("standard_deduction", 132000 if filing_status == "single" else 264000)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in hk_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, hk_data["tax_brackets"])
        else:
            tax_rate = 0.17  # Default max rate
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    # European countries - handle federal tax systems
    elif country in ["germany", "france", "italy", "spain", "netherlands", "switzerland", "belgium", "austria", "sweden", "norway", "denmark", "finland"]:
        country_data = international_data.get(country, {}).get("federal", {}).get(filing_status, {})
        
        std_ded = country_data.get("standard_deduction", 0)
        
        if manual_federal_rate is not None:
            tax_rate = manual_federal_rate
        elif income is not None and "tax_brackets" in country_data:
            taxable_income = max(0, income - std_ded)
            tax_rate = calculate_marginal_rate_from_brackets(taxable_income, country_data["tax_brackets"])
        else:
            # Default rates by country based on research
            default_rates = {
                "germany": 0.42, "france": 0.30, "italy": 0.38, "spain": 0.37,
                "netherlands": 0.495, "switzerland": 0.11, "belgium": 0.45, "austria": 0.48,
                "sweden": 0.32, "norway": 0.316, "denmark": 0.379, "finland": 0.175
            }
            tax_rate = default_rates.get(country, 0.25)
        
        return TaxParams(
            federal_marginal_rate=tax_rate,
            state_marginal_rate=0,  # European countries typically have single tax system
            salt_cap=0,
            standard_deduction=std_ded,
            location=location,
            filing_status=filing_status
        )
    
    # Fallback for unknown international locations
    return TaxParams(
        federal_marginal_rate=0.25,
        state_marginal_rate=0,
        salt_cap=0,
        standard_deduction=10000,
        location=location,
        filing_status=filing_status
    )


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
    Supports both US and international locations.
    
    Args:
        location: Location string (e.g., "NYC, NY", "Toronto, ON", "London, England")
        filing_status: "single" or "married"
        year: Tax year (defaults to 2024)
        income: Annual income for bracket-based calculation (optional)
        manual_federal_rate: Manual override for federal rate (optional)
        manual_state_rate: Manual override for state rate (optional)
        
    Returns:
        TaxParams object with federal and state tax information
    """
    # Check if this is an international location
    is_international, country = is_international_location(location)
    
    if is_international:
        return get_international_tax_params(
            location, country, filing_status, year, income, 
            manual_federal_rate, manual_state_rate
        )
    
    # Original US logic
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
    Includes both US and international locations.
    
    Returns:
        List of location strings
    """
    tax_data = load_tax_data()
    year_data = tax_data.get("2024", {})
    
    locations = []
    
    # US locations
    states = year_data.get("states", {}).keys()
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
    
    # International locations
    international_locations = [
        # Canada
        "Toronto, ON", "Vancouver, BC", "Montreal, QC", "Calgary, AB", "Ottawa, ON", "Edmonton, AB",
        # United Kingdom  
        "London, England", "Manchester, England", "Edinburgh, Scotland", "Birmingham, England", "Glasgow, Scotland", "Liverpool, England",
        # Australia
        "Sydney, NSW", "Melbourne, VIC", "Brisbane, QLD", "Perth, WA", "Adelaide, SA",
        # Singapore
        "Singapore",
        # Japan
        "Tokyo, Japan", "Osaka, Japan", "Yokohama, Japan",
        # Hong Kong
        "Hong Kong",
        # European Countries
        # Germany
        "Berlin, Germany", "Munich, Germany", "Hamburg, Germany", "Frankfurt, Germany", "Cologne, Germany", "Stuttgart, Germany",
        # France
        "Paris, France", "Lyon, France", "Marseille, France", "Toulouse, France", "Nice, France", "Bordeaux, France",
        # Italy
        "Rome, Italy", "Milan, Italy", "Naples, Italy", "Turin, Italy", "Florence, Italy", "Bologna, Italy",
        # Spain
        "Madrid, Spain", "Barcelona, Spain", "Valencia, Spain", "Seville, Spain", "Bilbao, Spain", "Malaga, Spain",
        # Netherlands
        "Amsterdam, Netherlands", "Rotterdam, Netherlands", "The Hague, Netherlands", "Utrecht, Netherlands", "Eindhoven, Netherlands", "Tilburg, Netherlands",
        # Switzerland
        "Zurich, Switzerland", "Geneva, Switzerland", "Basel, Switzerland", "Bern, Switzerland", "Lausanne, Switzerland", "Winterthur, Switzerland",
        # Belgium
        "Brussels, Belgium", "Antwerp, Belgium", "Ghent, Belgium", "Bruges, Belgium", "Leuven, Belgium", "Liege, Belgium",
        # Austria
        "Vienna, Austria", "Salzburg, Austria", "Innsbruck, Austria", "Graz, Austria", "Linz, Austria", "Klagenfurt, Austria",
        # Sweden
        "Stockholm, Sweden", "Gothenburg, Sweden", "Malmö, Sweden", "Uppsala, Sweden", "Västerås, Sweden", "Örebro, Sweden",
        # Norway
        "Oslo, Norway", "Bergen, Norway", "Trondheim, Norway", "Stavanger, Norway", "Kristiansand, Norway", "Fredrikstad, Norway",
        # Denmark
        "Copenhagen, Denmark", "Aarhus, Denmark", "Odense, Denmark", "Aalborg, Denmark", "Esbjerg, Denmark", "Randers, Denmark",
        # Finland
        "Helsinki, Finland", "Tampere, Finland", "Turku, Finland", "Oulu, Finland", "Jyväskylä, Finland", "Lahti, Finland"
    ]
    
    locations.extend(international_locations)
    
    return sorted(locations) 