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
        # Test NYC single
        tax_params = get_tax_params("NYC, NY", "single")
        assert isinstance(tax_params, TaxParams)
        assert tax_params.federal_marginal_rate > 0
        assert tax_params.state_marginal_rate > 0
        assert tax_params.salt_cap == 10000  # 2024 SALT cap
        assert tax_params.location == "NYC, NY"
        assert tax_params.filing_status == "single"
        
        # Test NJ married
        tax_params_nj = get_tax_params("Hoboken, NJ", "married")
        assert tax_params_nj.federal_marginal_rate > 0
        assert tax_params_nj.state_marginal_rate > 0
        assert tax_params_nj.location == "Hoboken, NJ"
        assert tax_params_nj.filing_status == "married"
        
        # Married should have higher standard deduction
        assert tax_params_nj.standard_deduction > tax_params.standard_deduction
    
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
        
        for location in test_locations:
            # Tax service should handle location
            tax_params = get_tax_params(location, "single")
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
        assert len(tax_locs) > 0
        assert "NYC, NY" in tax_locs
        
        # Property locations
        prop_locs = get_property_locations()
        assert isinstance(prop_locs, list)
        assert len(prop_locs) > 0
        assert "NYC, NY" in prop_locs
        
        # Should have some overlap
        common_locs = set(tax_locs) & set(prop_locs)
        assert len(common_locs) > 0
    
    def test_data_loading_resilience(self):
        """Test that services handle missing data files gracefully."""
        # Services should not crash even if data files are missing
        # (They should return reasonable defaults)
        
        # This is more of a resilience test - in a real deployment
        # we'd temporarily move data files to test fallback behavior
        
        # For now, just test that services return valid data
        tax_params = get_tax_params("NonExistent, XX", "single")
        assert tax_params.federal_marginal_rate > 0  # Should get some default
        
        prop_info = get_property_info("NonExistent, XX")
        assert prop_info["property_tax_rate"] > 0  # Should get default
    
    def test_service_data_consistency(self):
        """Test that data is internally consistent across services."""
        # Test multiple locations for consistency
        locations = ["NYC, NY", "Hoboken, NJ", "Princeton, NJ"]
        
        for location in locations:
            # Get data from both services
            tax_params = get_tax_params(location, "single")
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