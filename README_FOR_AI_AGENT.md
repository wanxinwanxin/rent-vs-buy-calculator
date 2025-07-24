# README FOR AI AGENTS

## 🤖 Agent Briefing: Rent vs. Buy Calculator Codebase

**Current Status**: PRODUCTION-READY IMPLEMENTATION ✅
**Last Updated**: 2024-12-25
**Agent Instructions**: Keep this file updated when making significant changes

---

## 📊 Implementation Status Overview

### ✅ COMPLETED COMPONENTS (100% functional)

1. **Core Calculation Engine** (`calc/`)
   - ✅ Pydantic data models with validation (`models.py`)
   - ✅ Mortgage amortization calculations (`amortization.py`)
   - ✅ Buy scenario cash flows with tax shield (`buy_flow.py`) 
   - ✅ Rent scenario with investment modeling (`rent_flow.py`)
   - ✅ Financial metrics (NPV, IRR, break-even) (`metrics.py`)
   - ✅ Input validation and sanitization (`validation.py`)
   - ✅ Main orchestration engine (`engine.py`)

2. **Streamlit UI Application** (`app.py`)
   - ✅ Complete responsive web interface
   - ✅ Sidebar input forms with smart defaults
   - ✅ Real-time validation and error handling
   - ✅ Results display with recommendations
   - ✅ Exception handling and user feedback

3. **Data Services Layer** (`services/`)
   - ✅ Tax parameter lookup by location (`tax_lookup.py`)
   - ✅ Property tax data lookup (`property_data.py`)
   - ✅ Mortgage rate assumptions loader (`mortgage_rates.py`)
   - ✅ Extensible API-ready interfaces

4. **UI Components** (`ui/`)
   - ✅ Modular input widgets (`widgets.py`)
   - ✅ Interactive charts with Plotly (`charts.py`)
   - ✅ Side-by-side buy vs rent comparison table (`charts.py`)
   - ✅ Sensitivity analysis tools (`sensitivity.py`)
   - ✅ URL sharing functionality (`sharing.py`)

5. **Static Data** (`data/`)
   - ✅ Tax rates for 16 US states including NYC local tax (`tax_defaults.json`)
   - ✅ Property tax rates for 70+ major US cities (`property_tax_defaults.csv`)
   - ✅ Default assumptions (`assumptions.yaml`)

6. **Testing Infrastructure**
   - ✅ 29 comprehensive tests (unit + integration + e2e)
   - ✅ Golden file comparisons for accuracy
   - ✅ Edge case handling
   - ✅ Data service integration tests

7. **Documentation & Setup**
   - ✅ Complete README with usage instructions
   - ✅ Dependency management (`requirements.txt`)
   - ✅ Clear architecture documentation

---

## 🏗️ Architecture Overview

### Directory Structure (24 Python files)
```
rent-vs-buy-calculator/
├── app.py                          # 281 lines - Main Streamlit app
├── calc/                           # Core calculation engine (pure Python)
│   ├── models.py                   # 117 lines - Pydantic data models
│   ├── amortization.py             # 153 lines - Mortgage calculations
│   ├── buy_flow.py                 # 241 lines - Buy scenario cash flows
│   ├── rent_flow.py                # 160 lines - Rent scenario & investment
│   ├── metrics.py                  # Financial analysis (NPV, IRR, etc.)
│   ├── validation.py               # Input validation & sanitization
│   └── engine.py                   # 144 lines - Main orchestrator
├── services/                       # Data lookup abstraction layer
│   ├── tax_lookup.py               # 313 lines - Tax parameter lookup
│   ├── property_data.py            # Property tax data service
│   └── mortgage_rates.py           # Rate assumptions loader
├── ui/                             # Streamlit UI components
│   ├── widgets.py                  # 550+ lines - Input forms
│   ├── charts.py                   # 324 lines - Plotly visualizations
│   ├── sensitivity.py             # Sensitivity analysis tools
│   └── sharing.py                  # URL sharing functionality
├── data/                           # Static data files
│   ├── tax_defaults.json           # Tax brackets & rates
│   ├── property_tax_defaults.csv   # Property tax by location
│   └── assumptions.yaml            # Default parameters
└── tests/                          # 29 tests total
    ├── unit/                       # Core calculation tests
    ├── integration/                # Full system tests
    └── e2e/                        # End-to-end Streamlit app tests
```

### Design Principles
1. **Separation of Concerns**: Pure calculation engine separate from UI
2. **Data-Driven**: All defaults in static files, easily configurable
3. **Service Layer**: External lookups abstracted for API replacement
4. **Type Safety**: Pydantic models for validation and documentation
5. **Testability**: Pure functions with comprehensive test coverage

---

## 💻 Current Functionality

### Calculation Features
- **Mortgage Amortization**: Principal/interest schedules with edge cases
- **Tax Shield Modeling**: Itemization vs. standard deduction with SALT cap
- **Investment Returns**: Compound growth of rent surplus investments
- **Financial Metrics**: NPV, IRR, break-even analysis
- **Regional Support**: Comprehensive coverage for 16 US states (CA, TX, FL, IL, WA, MA, VA, GA, NC, OH, PA, MI, AZ, NV, CO, OR) with NYC local income tax, plus 25+ international cities across Canada, UK, Australia, Singapore, Japan, and Hong Kong

### UI Features
- **Smart Defaults**: Auto-populates based on location and assumptions
- **Real-time Validation**: Input checking with helpful error messages
- **Interactive Charts**: Monthly cash flows, cumulative costs, net worth progression
- **Side-by-Side Comparison**: Monthly breakdown showing how top-line numbers are built up
- **Sensitivity Analysis**: Variable sweeps and tornado charts
- **Results Export**: Detailed tables and assumptions for review
- **Analysis Sharing**: Generate shareable URLs with pre-populated parameters and auto-run results

### Data Integration
- **Tax Lookup**: Federal and state marginal rates by location
- **Property Data**: Tax rates by county/municipality
- **Default Assumptions**: Industry-standard rates for maintenance, appreciation

---

## 🔧 Key Implementation Details

### Data Models (`calc/models.py`)
- `UserInputs`: Complete Pydantic model with validation
- `DerivedInputs`: Calculated values from user inputs
- `TaxParams`: Location-specific tax information
- `CalculationResults`: All analysis outputs

### Calculation Engine (`calc/engine.py`)
- `run_full_analysis()`: Main analysis orchestrator
- `get_detailed_cash_flows()`: Monthly detail for charts
- Handles edge cases: 100% down payment, paid-off loans, etc.

### UI Architecture (`app.py`)
- Sidebar input configuration
- Main content area with tabs
- Session state management
- Error handling with detailed feedback

### Testing Strategy
- **Unit Tests**: Core calculations (amortization, models)
- **Integration Tests**: Full analysis with known scenarios
- **E2E Tests**: Streamlit app startup and UI functionality
- **Golden Files**: Known-good results for regression testing
- **Edge Cases**: Zero loans, extreme values, missing data

---

## 🚀 Usage for New Agents

### To Run the Application
```bash
pip install -r requirements.txt
streamlit run app.py
```

### To Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run E2E tests specifically (MANDATORY before deploying)
pytest tests/e2e/ -v

# Or run E2E smoke tests directly
python3 tests/e2e/test_streamlit_app.py
```

### To Add New Features

1. **New Calculation Logic**: Add to `calc/` directory with unit tests
2. **UI Components**: Add to `ui/` directory, import in `app.py`
3. **Data Sources**: Add to `data/` directory, update service layer
4. **External APIs**: Replace service implementations while keeping interfaces

---

## 🎯 Extension Points for Future Agents

### Immediate Enhancement Opportunities
1. **Monte Carlo Simulation**: Add uncertainty modeling to existing engine
2. **Refinancing Optimization**: Extend buy_flow.py with refi logic
3. **Multi-City Comparison**: Extend UI to compare multiple locations
4. **PDF Export**: Add reporting functionality to existing charts

### API Integration Ready
- Service layer designed for easy API replacement
- Environment variable support for API keys
- Error handling and fallback to static data

### Performance Optimizations
- Streamlit caching already implemented
- Calculation engine optimized for speed
- Ready for async API calls

---

## ⚠️ Known Limitations & Technical Debt

### Calculation Simplifications
- Tax calculations use simplified marginal rate model
- No AMT or tax phase-out considerations
- Property tax assumes linear growth
- No consideration of refinancing optimization

### Data Coverage
- **US Coverage**: 16 major US states with 70+ cities (CA, TX, FL, IL, WA, MA, VA, GA, NC, OH, PA, MI, AZ, NV, CO, OR)
- **International Coverage**: 95+ major international cities across 18 countries/regions:
  - **Canada**: Toronto, Vancouver, Montreal, Calgary, Ottawa, Edmonton (federal + provincial taxes)
  - **United Kingdom**: London, Manchester, Edinburgh, Birmingham, Glasgow, Liverpool (income tax + council tax)
  - **Australia**: Sydney, Melbourne, Brisbane, Perth, Adelaide (federal income tax)
  - **Singapore**: Singapore city-state (progressive income tax, no property tax)
  - **Japan**: Tokyo, Osaka, Yokohama (progressive income tax + property tax)
  - **Hong Kong**: Hong Kong SAR (salaries tax, no property tax)
  - **Germany**: Berlin, Munich, Hamburg, Frankfurt, Cologne, Stuttgart (progressive income tax + property tax)
  - **France**: Paris, Lyon, Marseille, Toulouse, Nice, Bordeaux (progressive income tax + property tax)
  - **Italy**: Rome, Milan, Naples, Turin, Florence, Bologna (progressive income tax + property tax)
  - **Spain**: Madrid, Barcelona, Valencia, Seville, Bilbao, Malaga (progressive income tax + property tax)
  - **Netherlands**: Amsterdam, Rotterdam, The Hague, Utrecht, Eindhoven, Tilburg (progressive income tax + property tax)
  - **Switzerland**: Zurich, Geneva, Basel, Bern, Lausanne, Winterthur (federal + cantonal taxes + low property tax)
  - **Belgium**: Brussels, Antwerp, Ghent, Bruges, Leuven, Liege (progressive income tax + property tax)
  - **Austria**: Vienna, Salzburg, Innsbruck, Graz, Linz, Klagenfurt (progressive income tax + property tax)
  - **Sweden**: Stockholm, Gothenburg, Malmö, Uppsala, Västerås, Örebro (income tax + property tax)
  - **Norway**: Oslo, Bergen, Trondheim, Stavanger, Kristiansand, Fredrikstad (progressive income tax + property tax)
  - **Denmark**: Copenhagen, Aarhus, Odense, Aalborg, Esbjerg, Randers (progressive income tax + property tax)
  - **Finland**: Helsinki, Tampere, Turku, Oulu, Jyväskylä, Lahti (progressive income tax + property tax)
- Includes NYC local income tax separate from NY state tax
- Static data from 2024 (API integration ready)
- Progressive tax bracket calculations for accurate marginal rate determination
- No real-time market data integration

### UI/UX
- Desktop-first design (mobile usable but not optimized)
- No user session persistence
- No shareable URL parameters

### Testing
- No E2E browser testing (Streamlit AppTest could be added)
- No performance/load testing
- Limited property-based testing

---

## 📋 Agent TODO Checklist

When making significant changes, update this file by:

### ✅ REQUIRED UPDATES
- [ ] Update "Last Updated" date at top
- [ ] **MANDATORY**: Run E2E tests and ensure they pass: `pytest tests/e2e/ -v`
- [ ] Update implementation status percentages
- [ ] Add new files to directory structure
- [ ] Document new features in functionality section
- [ ] Update known limitations if fixing issues
- [ ] Add any new dependencies or requirements

### 📝 RECOMMENDED UPDATES
- [ ] Update test count if adding tests (current: 29 tests)
- [ ] Document new extension points
- [ ] Update architecture diagrams if structure changes
- [ ] Add performance notes for significant changes
- [ ] Update line counts in directory structure if files change significantly

### 🚨 CRITICAL UPDATES
- [ ] **MANDATORY**: Always run E2E tests before pushing changes
- [ ] Update this checklist if changing update process  
- [ ] Document breaking changes clearly
- [ ] Update API compatibility notes
- [ ] Mark deprecated features
- [ ] Document any UI/Streamlit compatibility issues

---

## 📚 Key Files for Agent Reference

### Must-Read Files
1. `implementation-instructions.md` - Original specifications and requirements
2. `calc/models.py` - Data structures and validation rules
3. `app.py` - Main application logic and UI flow
4. `tests/integration/test_full_analysis.py` - Golden scenarios and examples

### Architecture References
1. `calc/engine.py` - How calculations are orchestrated
2. `services/tax_lookup.py` - Service layer pattern
3. `ui/widgets.py` - UI component patterns
4. `data/assumptions.yaml` - Default values and sources

### Testing Examples
1. `tests/unit/test_amortization.py` - Unit test patterns
2. `tests/integration/test_data_services.py` - Integration test patterns

---

## 🎖️ Code Quality Standards

### Current Standards (maintain these)
- **Type Hints**: All functions have proper type annotations
- **Docstrings**: All public functions documented
- **Error Handling**: Graceful degradation with user feedback
- **Validation**: Pydantic models for data validation
- **Testing**: >80% test coverage on core calculations
- **Formatting**: Ruff for code formatting and linting

### Performance Benchmarks
- **Calculation Speed**: <200ms for typical analysis
- **UI Responsiveness**: <500ms for form updates
- **Test Suite**: <5 seconds for full test run

---

## 🔄 Future Agent Instructions

### Before Making Changes
1. Run existing tests to ensure nothing breaks: `pytest tests/`
2. **MANDATORY**: Run E2E tests to ensure app works: `pytest tests/e2e/ -v`
3. Review this file to understand current architecture
4. Check `implementation-instructions.md` for original requirements

### When Adding Features
1. Follow existing patterns in code organization
2. Add appropriate tests (unit for logic, integration for workflows)
3. **MANDATORY**: Run E2E tests before deploying: `pytest tests/e2e/ -v`
4. Update this README with changes
5. Consider backward compatibility

### When Fixing Bugs
1. Add regression test if possible
2. **MANDATORY**: Run E2E tests to ensure fix works: `pytest tests/e2e/ -v`
3. Update known limitations section if resolved
4. Check if fix affects other components

### When Refactoring
1. Ensure all tests still pass
2. **MANDATORY**: Run E2E tests to ensure no UI breaks: `pytest tests/e2e/ -v`
3. Update architecture documentation if changed
4. Consider impact on extension points

### 🚨 CRITICAL: UI Changes & Streamlit Compatibility
**MUST READ for any UI modifications:**

- **Format Strings**: Streamlit `st.number_input` does NOT support `format="%,d"` 
  - ❌ WRONG: `format="%,d"` (causes "invalid characters" error)
  - ✅ CORRECT: Remove format parameter entirely or use simple formats like `"%d"`
- **Testing**: ANY UI changes MUST be tested with E2E tests before deployment
- **Validation**: Run `python3 tests/e2e/test_streamlit_app.py` for quick validation

**Fixed Issues:**
- 2024-07-23: Removed invalid `format="%,d"` from all number inputs in `ui/widgets.py`
- 2024-07-23: Enhanced UI with comma-formatted display labels for better dollar amount readability
- 2024-07-24: Added comprehensive buy vs rent comparison table showing monthly breakdown and how top-line metrics are calculated
- 2024-12-19: **MAJOR EXPANSION**: Added support for 16 US states (CA, TX, FL, IL, WA, MA, VA, GA, NC, OH, PA, MI, AZ, NV, CO, OR) with 70+ cities
- 2024-12-19: Implemented NYC local income tax (separate from NY state tax) with proper tax bracket calculation
- 2024-12-19: Enhanced tax lookup system to handle both state and local taxes with income-based marginal rate calculation
- 2024-12-23: **NEW FEATURE**: Added URL sharing functionality allowing users to share analysis scenarios via shareable links
- 2024-12-23: **ENHANCEMENT**: Added auto-run functionality - shared URLs now immediately display full analysis results  
- 2024-12-25: **MAJOR EXPANSION**: Added comprehensive international jurisdiction support for 95+ cities across 18 countries/regions (Canada, UK, Australia, Singapore, Japan, Hong Kong, Germany, France, Italy, Spain, Netherlands, Switzerland, Belgium, Austria, Sweden, Norway, Denmark, Finland)
- 2024-12-25: **CRITICAL FIX**: Fixed international tax logic that incorrectly forced all foreign locations into US federal+state structure - now properly supports single national tax systems (most countries), federal+provincial (Canada), and federal+state (US) with correct UI labels

---

**🤖 Agent Handoff Notes**: This codebase is production-ready and well-tested. The architecture supports easy extension and modification. Focus on the service layer for external integrations and the calc layer for new financial logic. The UI is modular and can be enhanced incrementally.

**⚡ Quick Start**: If you need to understand how calculations work, start with `calc/engine.py` and follow the flow through buy_flow.py and rent_flow.py. For UI changes, start with `app.py` and the relevant ui/ components. 