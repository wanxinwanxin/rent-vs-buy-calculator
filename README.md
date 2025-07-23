# Rent vs. Buy Calculator

A comprehensive Streamlit application to analyze the financial implications of renting versus buying a home.

## Features

- **Complete Financial Analysis**: Monthly cash flows, NPV calculations, IRR analysis, and break-even analysis
- **Tax Optimization**: Mortgage interest and property tax deductions with SALT cap considerations
- **Regional Data**: Built-in tax brackets and property tax rates for NYC/NJ area
- **Investment Comparison**: Models investing rent surplus in alternative investments (stock market)
- **Interactive Visualizations**: Charts showing cost comparisons, net worth progression, and detailed breakdowns
- **Smart Defaults**: Auto-populates tax rates and property data based on location

## Quick Start

### Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** to the URL shown (typically http://localhost:8501)

### Usage

1. **Configure Parameters** in the sidebar:
   - Household income and filing status
   - Purchase price, down payment, and mortgage terms
   - Monthly rent and growth expectations
   - Investment return assumptions

2. **Click Calculate** to run the analysis

3. **Review Results**:
   - Key metrics (net worth difference, break-even time, IRR)
   - Interactive charts and detailed cash flow tables
   - Assumptions and data sources

## Key Calculations

### Buy Scenario
- Monthly mortgage payments (P&I)
- Property taxes, insurance, HOA, maintenance
- Tax shield from itemized deductions
- Home equity buildup through principal payments and appreciation

### Rent Scenario  
- Monthly rent payments with growth
- Investment of surplus cash (down payment + monthly difference)
- Portfolio growth with compound returns

### Comparison Metrics
- **Net Worth Difference**: Buy equity minus investment portfolio at horizon
- **NPV Difference**: Present value of buy costs minus rent costs
- **Break-even Month**: When cumulative buy costs equal rent costs
- **IRR**: Internal rate of return for the buy investment decision

## Data Sources

- **Tax Data**: IRS publications, state tax agencies (2024 rates)
- **Property Tax Rates**: Local assessor offices for NYC/NJ counties
- **Default Assumptions**: National averages for maintenance, appreciation, etc.

## Assumptions

### Default Values
- Home appreciation: 3% annually
- Rent growth: 3% annually  
- Stock market return: 7% annually
- Maintenance: 1.5% of home value annually
- Selling costs: 6% of sale price

### Tax Calculations
- Simplified marginal rate model (24% federal for upper-middle income)
- SALT cap of $10,000 for state/local tax deductions
- Itemized vs. standard deduction optimization

## File Structure

```
rent-vs-buy-calculator/
├── app.py                      # Main Streamlit application
├── calc/                       # Pure calculation engine
│   ├── models.py              # Pydantic data models
│   ├── amortization.py        # Mortgage calculations
│   ├── buy_flow.py            # Buy scenario cash flows
│   ├── rent_flow.py           # Rent scenario cash flows
│   ├── metrics.py             # NPV, IRR, break-even analysis
│   └── engine.py              # Main calculation orchestrator
├── data/                       # Static data files
│   ├── tax_defaults.json      # Tax brackets and parameters
│   ├── property_tax_defaults.csv # Property tax rates by location
│   └── assumptions.yaml       # Default assumptions
├── services/                   # Data lookup services
│   ├── tax_lookup.py          # Tax parameter lookup
│   ├── property_data.py       # Property tax data lookup
│   └── mortgage_rates.py      # Placeholder for rate APIs
├── ui/                         # Streamlit UI components
│   ├── widgets.py             # Input forms and widgets
│   └── charts.py              # Visualization components
└── requirements.txt           # Python dependencies
```

## Customization

### Adding New Locations
1. Add tax rates to `data/tax_defaults.json`
2. Add property tax rates to `data/property_tax_defaults.csv`
3. Update location lists in service files

### API Integration
Replace static data with live APIs by updating the service layer:
- `services/tax_lookup.py` - Tax API integration
- `services/mortgage_rates.py` - Mortgage rate APIs
- `services/property_data.py` - Property data APIs

### Advanced Features
The codebase is designed for easy extension:
- Monte Carlo simulations for sensitivity analysis
- Refinancing optimization
- Multiple property comparison
- Tax law changes modeling

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
ruff check .
ruff format .
```

## Disclaimer

This calculator is for educational and informational purposes only. Results are based on simplified models and assumptions. Consult with financial advisors and tax professionals for personalized advice.

The calculator does not account for:
- Complex tax situations (AMT, phase-outs, etc.)
- Local tax variations beyond property taxes
- Market volatility and timing
- Personal preferences and lifestyle factors
- Regulatory changes

## License

MIT License - see LICENSE file for details. 