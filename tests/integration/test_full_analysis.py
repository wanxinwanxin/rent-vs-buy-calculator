"""
Integration tests for full rent vs buy analysis.
Tests the complete calculation flow with known scenarios.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from calc.engine import run_full_analysis, get_detailed_cash_flows
from calc.models import UserInputs
from services.tax_lookup import get_tax_params
from services.property_data import get_property_info


class TestFullAnalysis:
    """Test complete analysis flow with known scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Golden scenario 1: NYC professional, buy favorable
        self.scenario_nyc_buy = UserInputs(
            income_you=150000,
            income_spouse=100000,
            filing_status="married",
            location="NYC, NY",
            purchase_price=800000,
            down_payment_pct=0.20,
            mortgage_rate=0.06,
            mortgage_term_years=30,
            rent_today_monthly=4000,
            alt_return_annual=0.07,
            annual_appreciation=0.04,  # Higher appreciation favors buying
            horizon_years=10
        )
        
        # Golden scenario 2: NYC professional, rent favorable  
        self.scenario_nyc_rent = UserInputs(
            income_you=150000,
            income_spouse=100000,
            filing_status="married",
            location="NYC, NY",
            purchase_price=800000,
            down_payment_pct=0.20,
            mortgage_rate=0.08,  # Higher rate favors renting
            mortgage_term_years=30,
            rent_today_monthly=3500,  # Lower rent favors renting
            alt_return_annual=0.09,  # Higher returns favor renting
            annual_appreciation=0.02,
            horizon_years=10
        )
        
        # Edge case: 100% down payment
        self.scenario_cash_buy = UserInputs(
            income_you=200000,
            purchase_price=500000,
            down_payment_pct=1.0,  # Cash purchase
            rent_today_monthly=3000,
            horizon_years=5
        )
    
    def test_nyc_buy_scenario_calculation(self):
        """Test NYC scenario that should favor buying."""
        tax_params = get_tax_params(self.scenario_nyc_buy.location, self.scenario_nyc_buy.filing_status)
        results = run_full_analysis(self.scenario_nyc_buy, tax_params)
        
        # Verify results structure
        assert results is not None
        assert hasattr(results, 'net_worth_difference')
        assert hasattr(results, 'npv_difference')
        assert hasattr(results, 'breakeven_month')
        
        # Should favor buying (positive net worth difference)
        assert results.net_worth_difference > 0, "Expected buying to be favorable in this scenario"
        
        # Should have reasonable break-even time (within horizon)
        assert results.breakeven_month is not None
        assert results.breakeven_month <= self.scenario_nyc_buy.horizon_years * 12
        
        # Verify magnitude is reasonable
        assert abs(results.net_worth_difference) < 1_000_000, "Net worth difference seems unreasonably large"
    
    def test_nyc_rent_scenario_calculation(self):
        """Test NYC scenario that should favor renting."""
        tax_params = get_tax_params(self.scenario_nyc_rent.location, self.scenario_nyc_rent.filing_status)
        results = run_full_analysis(self.scenario_nyc_rent, tax_params)
        
        # Verify results structure
        assert results is not None
        
        # Should favor renting (negative net worth difference)
        assert results.net_worth_difference < 0, "Expected renting to be favorable in this scenario"
        
        # Verify reasonable ranges
        assert results.home_equity_at_exit > 0, "Home equity should be positive"
        assert results.investment_portfolio_value > 0, "Investment portfolio should be positive"
    
    def test_cash_buy_scenario(self):
        """Test edge case with 100% down payment (no mortgage)."""
        tax_params = get_tax_params(self.scenario_cash_buy.location, self.scenario_cash_buy.filing_status)
        results = run_full_analysis(self.scenario_cash_buy, tax_params)
        
        # Should handle cash purchase without errors
        assert results is not None
        
        # Should have zero interest paid
        assert results.total_interest_paid == 0, "Cash purchase should have no interest"
        
        # Should have minimal tax shield (only property tax)
        assert results.total_tax_shield >= 0
    
    def test_detailed_cash_flows(self):
        """Test detailed cash flow generation."""
        tax_params = get_tax_params(self.scenario_nyc_buy.location, self.scenario_nyc_buy.filing_status)
        cash_flows = get_detailed_cash_flows(self.scenario_nyc_buy, tax_params)
        
        # Verify structure
        assert "buy" in cash_flows
        assert "rent" in cash_flows
        assert "derived_inputs" in cash_flows
        
        buy_df = cash_flows["buy"]
        rent_df = cash_flows["rent"]
        
        # Verify DataFrames have expected length
        expected_months = self.scenario_nyc_buy.horizon_years * 12
        assert len(buy_df) == expected_months
        assert len(rent_df) == expected_months
        
        # Verify key columns exist
        expected_buy_cols = ["month", "net_monthly_outflow", "cumulative_net_outflow"]
        for col in expected_buy_cols:
            assert col in buy_df.columns, f"Missing column {col} in buy cash flows"
        
        expected_rent_cols = ["month", "total_rent_outflow", "portfolio_balance"]
        for col in expected_rent_cols:
            assert col in rent_df.columns, f"Missing column {col} in rent cash flows"
        
        # Verify values are reasonable
        assert buy_df["net_monthly_outflow"].min() > 0, "Monthly outflows should be positive"
        assert rent_df["portfolio_balance"].iloc[-1] > 0, "Final portfolio should be positive"
    
    def test_tax_calculation_integration(self):
        """Test tax calculation integration."""
        # Test different locations
        locations = ["NYC, NY", "Hoboken, NJ", "Princeton, NJ"]
        
        for location in locations:
            inputs = self.scenario_nyc_buy.model_copy(update={"location": location})
            tax_params = get_tax_params(inputs.location, inputs.filing_status)
            
            # Should get reasonable tax parameters
            assert 0 <= tax_params.federal_marginal_rate <= 1
            assert 0 <= tax_params.state_marginal_rate <= 1
            assert tax_params.salt_cap > 0
            
            # Should complete calculation without errors
            results = run_full_analysis(inputs, tax_params)
            assert results is not None
    
    def test_property_data_integration(self):
        """Test property data lookup integration."""
        locations = ["NYC, NY", "Hoboken, NJ", "Jersey City, NJ"]
        
        for location in locations:
            property_info = get_property_info(location)
            
            # Should get valid property info
            assert "property_tax_rate" in property_info
            assert 0 <= property_info["property_tax_rate"] <= 0.1
            assert "data_source" in property_info
    
    def test_scenario_consistency(self):
        """Test that similar scenarios produce consistent results."""
        # Create two very similar scenarios
        scenario1 = self.scenario_nyc_buy
        scenario2 = self.scenario_nyc_buy.model_copy(update={"purchase_price": 801000})  # $1K difference
        
        tax_params1 = get_tax_params(scenario1.location, scenario1.filing_status)
        tax_params2 = get_tax_params(scenario2.location, scenario2.filing_status)
        
        results1 = run_full_analysis(scenario1, tax_params1)
        results2 = run_full_analysis(scenario2, tax_params2)
        
        # Results should be very similar
        net_worth_diff = abs(results1.net_worth_difference - results2.net_worth_difference)
        assert net_worth_diff < 10000, "Small input changes should produce similar results"
    
    def test_extreme_scenarios(self):
        """Test handling of extreme but valid scenarios."""
        # Very short horizon
        short_scenario = self.scenario_nyc_buy.model_copy(update={"horizon_years": 1})
        tax_params = get_tax_params(short_scenario.location, short_scenario.filing_status)
        results = run_full_analysis(short_scenario, tax_params)
        
        # Should complete without errors
        assert results is not None
        
        # Very long horizon
        long_scenario = self.scenario_nyc_buy.model_copy(update={"horizon_years": 30})
        results_long = run_full_analysis(long_scenario, tax_params)
        assert results_long is not None
        
        # High appreciation scenario
        high_appreciation = self.scenario_nyc_buy.model_copy(update={"annual_appreciation": 0.08})
        results_high = run_full_analysis(high_appreciation, tax_params)
        assert results_high is not None
        assert results_high.net_worth_difference > results.net_worth_difference


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 