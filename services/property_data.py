"""
Property data lookup service.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict


def get_data_path() -> Path:
    """Get the path to the data directory."""
    current_dir = Path(__file__).parent
    return current_dir.parent / "data"


def load_property_tax_data() -> pd.DataFrame:
    """Load property tax data from CSV file."""
    data_path = get_data_path() / "property_tax_defaults.csv"
    
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        # Return basic defaults if file not found
        return pd.DataFrame({
            "location": ["DEFAULT"],
            "state": ["DEFAULT"],
            "county": ["DEFAULT"],
            "property_tax_rate": [0.012],
            "effective_rate": [0.012],
            "data_source": ["National Average"],
            "last_updated": ["2024"]
        })


def get_property_tax_rate(location: str) -> float:
    """
    Get property tax rate for a location.
    
    Args:
        location: Location string (e.g., "NYC, NY", "Hoboken, NJ")
        
    Returns:
        Annual property tax rate as decimal (e.g., 0.012 for 1.2%)
    """
    df = load_property_tax_data()
    
    # Try exact match first
    exact_match = df[df["location"].str.lower() == location.lower()]
    if not exact_match.empty:
        return exact_match.iloc[0]["property_tax_rate"]
    
    # Try partial match (city name)
    if "," in location:
        city_name = location.split(",")[0].strip().lower()
        partial_match = df[df["location"].str.lower().str.contains(city_name, na=False)]
        if not partial_match.empty:
            return partial_match.iloc[0]["property_tax_rate"]
    
    # Fallback to state average
    if "," in location:
        state = location.split(",")[1].strip().upper()
        state_match = df[df["state"] == state]
        if not state_match.empty:
            # Return average for the state
            return state_match["property_tax_rate"].mean()
    
    # Final fallback to default
    default_match = df[df["location"] == "DEFAULT"]
    if not default_match.empty:
        return default_match.iloc[0]["property_tax_rate"]
    
    # Hard-coded fallback
    return 0.012  # 1.2% national average


def get_property_info(location: str) -> Dict[str, any]:
    """
    Get comprehensive property tax information for a location.
    
    Args:
        location: Location string
        
    Returns:
        Dictionary with property tax info including rate, source, etc.
    """
    df = load_property_tax_data()
    
    # Try exact match first
    exact_match = df[df["location"].str.lower() == location.lower()]
    if not exact_match.empty:
        row = exact_match.iloc[0]
        return {
            "property_tax_rate": row["property_tax_rate"],
            "effective_rate": row["effective_rate"],
            "county": row["county"],
            "state": row["state"],
            "data_source": row["data_source"],
            "last_updated": row["last_updated"],
            "match_type": "exact"
        }
    
    # Try partial match
    if "," in location:
        city_name = location.split(",")[0].strip().lower()
        partial_match = df[df["location"].str.lower().str.contains(city_name, na=False)]
        if not partial_match.empty:
            row = partial_match.iloc[0]
            return {
                "property_tax_rate": row["property_tax_rate"],
                "effective_rate": row["effective_rate"],
                "county": row["county"],
                "state": row["state"],
                "data_source": row["data_source"],
                "last_updated": row["last_updated"],
                "match_type": "partial"
            }
    
    # Fallback to default
    default_match = df[df["location"] == "DEFAULT"]
    if not default_match.empty:
        row = default_match.iloc[0]
        return {
            "property_tax_rate": row["property_tax_rate"],
            "effective_rate": row["effective_rate"],
            "county": "Unknown",
            "state": "Unknown",
            "data_source": row["data_source"],
            "last_updated": row["last_updated"],
            "match_type": "default"
        }
    
    return {
        "property_tax_rate": 0.012,
        "effective_rate": 0.012,
        "county": "Unknown",
        "state": "Unknown",
        "data_source": "Hard-coded fallback",
        "last_updated": "2024",
        "match_type": "fallback"
    }


def get_available_locations() -> list[str]:
    """
    Get list of available locations with property tax data.
    
    Returns:
        List of location strings
    """
    df = load_property_tax_data()
    locations = df[df["location"] != "DEFAULT"]["location"].tolist()
    return sorted(locations)


def search_locations(query: str) -> list[str]:
    """
    Search for locations matching a query string.
    
    Args:
        query: Search query
        
    Returns:
        List of matching location strings
    """
    df = load_property_tax_data()
    query_lower = query.lower()
    
    matches = df[
        df["location"].str.lower().str.contains(query_lower, na=False) |
        df["county"].str.lower().str.contains(query_lower, na=False) |
        df["state"].str.lower().str.contains(query_lower, na=False)
    ]
    
    return matches["location"].tolist() 