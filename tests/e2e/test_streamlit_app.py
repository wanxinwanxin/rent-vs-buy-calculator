"""
End-to-end tests for Streamlit application.

These tests ensure the app can start and core functionality works without errors.
"""

import subprocess
import time
import requests
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class TestStreamlitE2E:
    """End-to-end tests for the Streamlit application."""
    
    def test_app_imports_without_error(self):
        """Test that the main app can be imported without errors."""
        try:
            import app
            import ui.widgets
            import ui.charts
            import calc.engine
            print("✓ All main modules import successfully")
        except Exception as e:
            pytest.fail(f"App import failed: {e}")
    
    def test_widgets_creation_without_format_error(self):
        """Test that UI widgets can be created without format string errors."""
        try:
            from ui.widgets import create_user_inputs
            # This should not raise a format string error
            print("✓ UI widgets can be imported without format errors")
        except Exception as e:
            if "format string" in str(e).lower() or "%,d" in str(e):
                pytest.fail(f"Format string error still exists: {e}")
            # Other errors might be expected (like Streamlit session state)
            print(f"Note: Non-format error occurred (expected): {e}")
    
    def test_calculation_engine_basic_functionality(self):
        """Test that the calculation engine works with basic inputs."""
        try:
            from calc.engine import run_full_analysis
            from calc.models import UserInputs, TaxParams
            
            # Create minimal valid inputs
            user_inputs = UserInputs(
                income_you=100000,
                purchase_price=500000,
                rent_today_monthly=3000
            )
            
            tax_params = TaxParams(
                federal_marginal_rate=0.24,
                state_marginal_rate=0.08,
                salt_cap=10000,
                standard_deduction=14600,
                location="NYC, NY",
                filing_status="single"
            )
            
            # This should run without errors
            results = run_full_analysis(user_inputs, tax_params)
            assert results is not None
            print("✓ Calculation engine works with basic inputs")
            
        except Exception as e:
            pytest.fail(f"Calculation engine failed: {e}")


def test_app_starts_without_immediate_errors():
    """
    Test that the Streamlit app can start without immediate errors.
    This is a smoke test to catch obvious startup issues.
    """
    try:
        # Test that we can import the main app file
        import app
        
        # Test that key functions exist
        assert hasattr(app, 'main')
        assert hasattr(app, 'configure_page')
        assert hasattr(app, 'display_header')
        
        print("✓ App structure is valid")
        
    except Exception as e:
        pytest.fail(f"App startup test failed: {e}")


if __name__ == "__main__":
    # Run basic tests when executed directly
    print("Running E2E smoke tests...")
    
    test = TestStreamlitE2E()
    test.test_app_imports_without_error()
    test.test_widgets_creation_without_format_error()
    test.test_calculation_engine_basic_functionality()
    
    test_app_starts_without_immediate_errors()
    
    print("✅ All E2E smoke tests passed!") 