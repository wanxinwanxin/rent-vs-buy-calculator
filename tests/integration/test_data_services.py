"""
Integration tests for data services (tax lookup, property data, etc.).
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.tax_lookup import get_tax_params, get_available_locations as get_tax_locations
from services.property_data import get_property_info, get_property_tax_rate, get_available_locations as get_property_locations
from services.mortgage_rates import get_current_mortgage_rates, get_rate_trends
from calc.models import TaxParams


class TestDataServicesIntegration:
    """Test integration between different data services."""
    
    def test_tax_lookup_service(self):
        """Test tax lookup service with various inputs."""
        test_income = 100000  # Use test income for marginal rate calculation
        # Test NYC single
        tax_params = get_tax_params("NYC, NY", "single", income=test_income)
        assert isinstance(tax_params, TaxParams)
        assert tax_params.federal_marginal_rate > 0
        assert tax_params.state_marginal_rate > 0
        assert tax_params.salt_cap == 10000  # 2024 SALT cap
        assert tax_params.location == "NYC, NY"
        assert tax_params.filing_status == "single"
        
        # Test NJ married
        tax_params_nj = get_tax_params("Hoboken, NJ", "married", income=test_income)
        assert tax_params_nj.federal_marginal_rate > 0
        assert tax_params_nj.state_marginal_rate > 0
        assert tax_params_nj.location == "Hoboken, NJ"
        assert tax_params_nj.filing_status == "married"
        
        # Married should have higher standard deduction
        assert tax_params_nj.standard_deduction > tax_params.standard_deduction
    
    def test_nyc_local_tax(self):
        """Test NYC local income tax is properly included."""
        # Test NYC vs other NY locations to ensure local tax is included
        test_income = 100000  # Use test income for marginal rate calculation
        nyc_params = get_tax_params("NYC, NY", "single", income=test_income)
        westchester_params = get_tax_params("Westchester County, NY", "single", income=test_income)
        
        # NYC should have higher effective state+local rate due to local tax
        # NYC local tax brackets should be included in the calculation
        assert nyc_params.state_marginal_rate > westchester_params.state_marginal_rate
        
        # Both should have same federal rate
        assert nyc_params.federal_marginal_rate == westchester_params.federal_marginal_rate
        
        # Verify NYC includes local tax (should be roughly 3.8% higher)
        local_tax_difference = nyc_params.state_marginal_rate - westchester_params.state_marginal_rate
        assert 0.035 <= local_tax_difference <= 0.045  # Expect roughly 3.8% local tax
    
    def test_new_states_tax_lookup(self):
        """Test tax lookup for all newly added states."""
        test_locations = [
            ("Los Angeles, CA", "California should have state tax"),
            ("Dallas, TX", "Texas should have no state tax"),
            ("Miami, FL", "Florida should have no state tax"),
            ("Chicago, IL", "Illinois should have state tax"),
            ("Seattle, WA", "Washington should have no state tax"),
            ("Boston, MA", "Massachusetts should have state tax"),
            ("Arlington, VA", "Virginia should have state tax"),
            ("Atlanta, GA", "Georgia should have state tax"),
            ("Charlotte, NC", "North Carolina should have state tax"),
            ("Columbus, OH", "Ohio should have state tax"),
            ("Philadelphia, PA", "Pennsylvania should have state tax"),
            ("Detroit, MI", "Michigan should have state tax"),
            ("Phoenix, AZ", "Arizona should have state tax"),
            ("Las Vegas, NV", "Nevada should have no state tax"),
            ("Denver, CO", "Colorado should have state tax"),
            ("Portland, OR", "Oregon should have state tax")
        ]
        
        test_income = 100000  # Use test income for marginal rate calculation
        for location, description in test_locations:
            tax_params = get_tax_params(location, "single", income=test_income)
            assert isinstance(tax_params, TaxParams), f"Failed for {location}: {description}"
            assert tax_params.federal_marginal_rate > 0, f"No federal tax for {location}"
            assert tax_params.location == location, f"Location mismatch for {location}"
            
            # Check state tax expectations
            if location.endswith(", TX") or location.endswith(", FL") or location.endswith(", WA") or location.endswith(", NV"):
                # No state income tax states
                assert tax_params.state_marginal_rate == 0, f"{location} should have no state tax"
            else:
                # States with income tax
                assert tax_params.state_marginal_rate > 0, f"{location} should have state tax"
    
    def test_property_data_service(self):
        """Test property data service with various locations."""
        # Test exact match
        nyc_info = get_property_info("NYC, NY")
        assert "property_tax_rate" in nyc_info
        assert nyc_info["property_tax_rate"] > 0
        assert nyc_info["match_type"] == "exact"
        
        # Test property tax rate lookup
        nyc_rate = get_property_tax_rate("NYC, NY")
        assert nyc_rate == nyc_info["property_tax_rate"]
        
        # Test partial match
        hoboken_info = get_property_info("Hoboken, NJ")
        assert hoboken_info["property_tax_rate"] > 0
        
        # Test unknown location (should fallback)
        unknown_info = get_property_info("Unknown City, ZZ")
        assert unknown_info["property_tax_rate"] == 0.012  # Default
        assert unknown_info["match_type"] in ["default", "fallback"]
    
    def test_new_cities_property_data(self):
        """Test property data for all newly added cities."""
        new_cities = [
            "Los Angeles, CA", "San Francisco, CA", "San Diego, CA", "San Jose, CA",
            "Dallas, TX", "Houston, TX", "Austin, TX", "San Antonio, TX",
            "Miami, FL", "Orlando, FL", "Tampa, FL", "Jacksonville, FL",
            "Chicago, IL", "Naperville, IL", "Evanston, IL",
            "Seattle, WA", "Bellevue, WA", "Redmond, WA",
            "Boston, MA", "Cambridge, MA", "Newton, MA",
            "Arlington, VA", "Alexandria, VA", "Fairfax, VA",
            "Atlanta, GA", "Sandy Springs, GA", "Alpharetta, GA",
            "Charlotte, NC", "Raleigh, NC", "Durham, NC",
            "Columbus, OH", "Cleveland, OH", "Cincinnati, OH",
            "Philadelphia, PA", "Pittsburgh, PA",
            "Detroit, MI", "Grand Rapids, MI",
            "Phoenix, AZ", "Scottsdale, AZ", "Tucson, AZ",
            "Las Vegas, NV", "Reno, NV",
            "Denver, CO", "Boulder, CO", "Colorado Springs, CO",
            "Portland, OR", "Eugene, OR"
        ]
        
        for city in new_cities:
            prop_info = get_property_info(city)
            assert "property_tax_rate" in prop_info, f"Missing property tax rate for {city}"
            assert prop_info["property_tax_rate"] > 0, f"Invalid property tax rate for {city}"
            assert prop_info["property_tax_rate"] < 0.1, f"Property tax rate too high for {city}"
            assert prop_info["match_type"] == "exact", f"Should be exact match for {city}"
            
            # Test property tax rate lookup directly
            rate = get_property_tax_rate(city)
            assert rate == prop_info["property_tax_rate"], f"Rate mismatch for {city}"
    
    def test_property_tax_rate_sanity(self):
        """Test that property tax rates are reasonable across all cities."""
        all_locations = get_property_locations()
        
        for location in all_locations:
            if location == "DEFAULT":
                continue
                
            rate = get_property_tax_rate(location)
            # Property tax rates should be between 0.5% and 8% (very broad range)
            assert 0.005 <= rate <= 0.08, f"Unreasonable property tax rate {rate} for {location}"
    
    def test_mortgage_rates_service(self):
        """Test mortgage rates service (placeholder implementation)."""
        # Test current rates
        rates = get_current_mortgage_rates()
        assert "rate" in rates
        assert rates["rate"] > 0
        assert rates["rate"] < 1  # Should be reasonable
        
        # Test with location
        ny_rates = get_current_mortgage_rates(location="NYC, NY")
        assert ny_rates["rate"] > 0
        
        # Test different loan types
        fha_rates = get_current_mortgage_rates(loan_type="fha")
        conventional_rates = get_current_mortgage_rates(loan_type="conventional")
        assert fha_rates["rate"] != conventional_rates["rate"]  # Should be different
        
        # Test rate trends
        trends = get_rate_trends()
        assert "current_rate" in trends
        assert "trend_direction" in trends
    
    def test_location_consistency(self):
        """Test that location handling is consistent across services."""
        test_locations = ["NYC, NY", "Hoboken, NJ", "Jersey City, NJ"]
        test_income = 100000  # Use test income for marginal rate calculation
        
        for location in test_locations:
            # Tax service should handle location
            tax_params = get_tax_params(location, "single", income=test_income)
            assert tax_params.location == location
            
            # Property service should handle location
            prop_info = get_property_info(location)
            assert prop_info["property_tax_rate"] > 0
            
            # Should be consistent rate
            prop_rate = get_property_tax_rate(location)
            assert prop_rate == prop_info["property_tax_rate"]
    
    def test_expanded_location_consistency(self):
        """Test location consistency for newly added cities."""
        # Test a sample of new locations across different states
        test_locations = [
            "Los Angeles, CA", "Dallas, TX", "Miami, FL", "Chicago, IL",
            "Seattle, WA", "Boston, MA", "Atlanta, GA", "Denver, CO"
        ]
        test_income = 100000  # Use test income for marginal rate calculation
        
        for location in test_locations:
            # Tax service should handle location
            tax_params = get_tax_params(location, "single", income=test_income)
            assert tax_params.location == location
            
            # Property service should handle location
            prop_info = get_property_info(location)
            assert prop_info["property_tax_rate"] > 0
            
            # Should be consistent rate
            prop_rate = get_property_tax_rate(location)
            assert prop_rate == prop_info["property_tax_rate"]
    
    def test_available_locations(self):
        """Test available locations from different services."""
        # Tax locations
        tax_locs = get_tax_locations()
        assert isinstance(tax_locs, list)
        assert len(tax_locs) > 50  # Should have many more locations now
        assert "NYC, NY" in tax_locs
        
        # Should include new major cities
        assert "Los Angeles, CA" in tax_locs
        assert "Dallas, TX" in tax_locs
        assert "Miami, FL" in tax_locs
        assert "Chicago, IL" in tax_locs
        assert "Seattle, WA" in tax_locs
        
        # Property locations
        prop_locs = get_property_locations()
        assert isinstance(prop_locs, list)
        assert len(prop_locs) > 50  # Should have many more locations now
        assert "NYC, NY" in prop_locs
        
        # Should include new major cities
        assert "Los Angeles, CA" in prop_locs
        assert "Dallas, TX" in prop_locs
        assert "Miami, FL" in prop_locs
        assert "Chicago, IL" in prop_locs
        assert "Seattle, WA" in prop_locs
        
        # Should have significant overlap now
        common_locs = set(tax_locs) & set(prop_locs)
        assert len(common_locs) > 40  # Should have many common locations
    
    def test_state_coverage(self):
        """Test that all major states are covered in both services."""
        expected_states = ["NY", "NJ", "CT", "CA", "TX", "FL", "IL", "WA", "MA", "VA", "GA", "NC", "OH", "PA", "MI", "AZ", "NV", "CO", "OR"]
        
        tax_locs = get_tax_locations()
        prop_locs = get_property_locations()
        
        for state in expected_states:
            # Check tax locations have cities from this state
            tax_has_state = any(loc.endswith(f", {state}") for loc in tax_locs)
            assert tax_has_state, f"Tax service missing locations for state {state}"
            
            # Check property locations have cities from this state
            prop_has_state = any(loc.endswith(f", {state}") for loc in prop_locs)
            assert prop_has_state, f"Property service missing locations for state {state}"
    
    def test_data_loading_resilience(self):
        """Test that services handle missing data files gracefully."""
        # Services should not crash even if data files are missing
        # (They should return reasonable defaults)
        
        # This is more of a resilience test - in a real deployment
        # we'd temporarily move data files to test fallback behavior
        
        # For now, just test that services return valid data
        test_income = 100000  # Use test income for marginal rate calculation
        tax_params = get_tax_params("NonExistent, XX", "single", income=test_income)
        assert tax_params.federal_marginal_rate > 0  # Should get some default
        
        prop_info = get_property_info("NonExistent, XX")
        assert prop_info["property_tax_rate"] > 0  # Should get default
    
    def test_service_data_consistency(self):
        """Test that data is internally consistent across services."""
        # Test multiple locations for consistency
        locations = ["NYC, NY", "Hoboken, NJ", "Princeton, NJ", "Los Angeles, CA", "Dallas, TX", "Miami, FL"]
        test_income = 100000  # Use test income for marginal rate calculation
        
        for location in locations:
            # Get data from both services
            tax_params = get_tax_params(location, "single", income=test_income)
            prop_info = get_property_info(location)
            
            # Basic sanity checks
            assert 0 < tax_params.federal_marginal_rate < 1
            assert 0 <= tax_params.state_marginal_rate < 1
            assert 0 < prop_info["property_tax_rate"] < 0.1
            
            # Combined tax rate should be reasonable
            combined_rate = tax_params.federal_marginal_rate + tax_params.state_marginal_rate
            assert combined_rate < 0.8  # Total tax rate shouldn't exceed 80%


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 