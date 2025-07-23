Rent vs. Buy Streamlit PoC

Audience: AI coding agents & senior reviewers
Goal: Ship a maintainable Streamlit PoC that compares renting vs. buying for a household (NYC/NJ initially), with smart defaults and room for API lookups later.

⸻

0. TL;DR (Agent Quickstart)
	1.	Scaffold repo with the structure below.
	2.	Implement the core calc engine (calc/), fully unit-tested.
	3.	Build Streamlit UI (app.py) that:
	•	Collects user-known inputs (income, location, price, rent…).
	•	Auto-fills unknowns from static lookups (tax brackets, prop-tax rates) with clear attribution.
	•	Runs buy vs. rent projections and shows monthly cash flow + summary KPIs.
	4.	Add hooks for future APIs (tax, mortgage, property data). Keep them behind an interface in services/.
	5.	Write integration/e2e tests (golden scenarios) and ship.

⸻

1. Objectives & Scope
	•	Primary output: Monthly cashflow comparison, NPV/IRR, break-even horizon, end net worth for “Buy” vs “Rent + Invest surplus”.
	•	Inputs: Household income, purchase price, mortgage terms, rent, expected returns, taxes, property tax, maintenance, etc.
	•	Defaults/Data: Ship static CSV/JSON with typical values (SALT cap, federal brackets, NYC/NJ property tax averages, maintenance %). Clearly label any assumptions.
	•	Extensibility: Swap static defaults with API calls later (Tax APIs, Zillow-like property tax, rate APIs). Minimal refactor via service layer.

⸻

2. High-Level Architecture

streamlit_app/
├─ app.py                       # Streamlit entry point
├─ calc/                        # Pure python financial math (no Streamlit imports)
│  ├─ amortization.py
│  ├─ rent_flow.py
│  ├─ buy_flow.py
│  ├─ net_worth.py
│  ├─ metrics.py                # NPV, IRR, break-even, sensitivity helpers
│  └─ models.py                 # Pydantic/dataclasses for Inputs/Outputs
├─ data/
│  ├─ tax_defaults.json
│  ├─ property_tax_defaults.csv
│  └─ assumptions.yaml
├─ services/
│  ├─ tax_lookup.py             # Abstraction: get_tax_params(location, year)
│  ├─ mortgage_rates.py         # placeholder for future API
│  └─ property_data.py          # placeholder
├─ ui/
│  ├─ widgets.py                # grouped Streamlit widgets/forms
│  └─ charts.py                 # plotly/matplotlib helpers if needed
├─ tests/
│  ├─ unit/                     # pytest unit tests for calc layer
│  ├─ integration/              # test calc + defaults
│  └─ e2e/                      # streamlit AppTest or playwright scripts
├─ requirements.txt
└─ README.md

Key principles:
	•	Separation: UI ≠ logic. Calc layer is pure, deterministic, and testable.
	•	Data-driven: Defaults live in data/, loaded via lightweight loaders.
	•	Service interfaces: All external lookups hidden behind functions with same signatures (static now, API later).
	•	Caching: Use st.cache_data for expensive/static loads.

⸻

3. Data & Input Model

3.1 Core Input Schema (suggest Pydantic or dataclass)

class UserInputs(BaseModel):
    # Household
    income_you: float
    income_spouse: float
    income_growth: float  # annual %
    filing_status: Literal["single", "married"]
    location: str  # e.g. "NYC, NY" or "Hoboken, NJ"

    # Buy side
    purchase_price: float
    down_payment_pct: float
    closing_costs_buy: float
    mortgage_rate: float
    mortgage_term_years: int
    points_pct: float | None
    property_tax_rate: float
    insurance_hoa_annual: float
    maintenance_pct: float
    other_owner_costs_annual: float
    annual_appreciation: float
    selling_cost_pct: float

    # Rent side
    rent_today_monthly: float
    rent_growth_pct: float
    other_renter_costs_monthly: float

    # Finance
    alt_return_annual: float
    inflation_discount_annual: float
    horizon_years: int

    # PMI, Refi toggles
    pmi_threshold_pct: float | None
    pmi_annual_pct: float | None
    refinance_enabled: bool
    expected_refi_rate: float | None

Add DerivedInputs at runtime (loan_amount, monthly rates, horizon_months) to avoid re-computing.

3.2 Defaults/Lookup Layer
	•	tax_defaults.json: federal + NYS/NJ marginal rates, SALT cap, standard deduction.
	•	property_tax_defaults.csv: rows by county/municipality with average rates.
	•	assumptions.yaml: default maintenance %, selling cost %, etc.

Rule: When a user input is blank, pull from defaults and show a tooltip/expander with the source.

⸻

4. Calculation Engine

4.1 Buy Flow
	1.	Loan amortization schedule (monthly): interest, principal, remaining balance.
	2.	Monthly owner costs: property tax, insurance/HOA, maintenance, other.
	3.	Tax shield: mortgage interest + property tax (subject to SALT cap and itemization logic). Start with simplified model.
	4.	After-tax monthly outflow = (P&I + costs) − tax shield.
	5.	Equity buildup: principal paid + appreciation − selling costs at exit.

4.2 Rent Flow
	1.	Monthly rent path (grow by rent_growth_pct).
	2.	Other renter costs.
	3.	Invested surplus each month = max(0, buy_after_tax_outflow − rent_outflow).
	4.	Portfolio balance with compounding at alt_return_annual.

4.3 Metrics
	•	NPV of after-tax costs (discount at inflation/discount rate).
	•	End net worth: equity (after sale) vs. portfolio balance.
	•	Break-even month: first month cumulative cost of buy <= rent.
	•	IRR of “buy investment” (cash flows = negatives for outflows, positive for sale proceeds).
	•	Sensitivities: run variable sweeps (rate, appreciation, rent growth, alt return).

All math in calc/*.py, unit-tested with known cases.

⸻

5. UI/UX Flow (Desktop-first)
	1.	Header & Intro: Title, one-line goal, link to assumptions.
	2.	Input Section:
	•	Collapsible groups: Household, Buy, Rent, Finance, Advanced.
	•	Pre-fill with defaults (display info icon w/ source).
	•	“Calculate” button (or st.form) to control reruns.
	3.	Results Section:
	•	Key KPIs as st.metric cards: NPV diff, End Net Worth diff, Break-even month.
	•	Monthly cashflow charts (optional): area/line charts.
	•	Tables (expanders) for detailed schedules.
	•	Assumptions & sources expander.
	4.	Sensitivity/Scenario Section (optional in PoC): Data table or multi-select to toggle scenarios.

Use st.cache_data for: loading defaults, heavy recomputations (optional). Use session_state for persistent inputs between reruns.

⸻

6. Implementation Plan (Ticketable Steps)

Phase 0 – Setup
	•	Init repo, venv, requirements.
	•	Add Streamlit, Pydantic (or dataclasses), numpy/pandas, pytest.
	•	Create skeleton folders.

Phase 1 – Calc Engine
	•	Implement amortization.py (amortize(loan_amt, rate, nper) -> DataFrame).
	•	Implement buy_flow.py (monthly cash out, tax shield simplified, equity build).
	•	Implement rent_flow.py (rent path, invested surplus, portfolio growth).
	•	Implement metrics.py (NPV, IRR, break-even).
	•	Add unit tests with golden numbers.

Phase 2 – Defaults & Services
	•	Create data/ files (JSON/YAML/CSV). Fill with 2024 values.
	•	Write services/tax_lookup.py → get_tax_params(location, filing_status) that returns SALT cap, marginal rates, std deduction. For PoC: read from json.
	•	Write services/property_data.py → get_property_tax_rate(location) fallback to national avg if missing.
	•	Tests for service loaders (integrate with calc).

Phase 3 – Streamlit UI
	•	ui/widgets.py: grouped widget creators (returns UserInputs).
	•	app.py: orchestrate inputs → defaults → calc → display.
	•	Add results KPIs + charts + expanders.
	•	Add source/assumption captions.

Phase 4 – Sensitivities & Polish
	•	Minimal sensitivity panel (3 sliders; recalc metrics).
	•	Error handling (invalid combos, zero horizon, etc.).
	•	Refactor & docstrings.

Phase 5 – Testing & Delivery
	•	Pytest CI: unit + integration.
	•	Optional: Streamlit AppTest for E2E.
	•	README with run instructions, data sources.

⸻

7. Testing Strategy

7.1 Unit Tests (pytest)
	•	Amortization: Known loan (e.g., 100k @ 6% 30y) → interest & principal totals match calculator.
	•	Tax Shield: Inputs with/without SALT cap -> expected deduction.
	•	NPV/IRR: Compare to numpy_financial or manually computed values.
	•	Edge Cases: Zero income, 100% down payment (no mortgage), 1-year horizon.

7.2 Integration Tests
	•	Feed a full UserInputs JSON fixture → expect exact KPI outputs (golden file compare).
	•	Swap defaults (NYC vs. NJ) → ensure property tax changes propagate.

7.3 E2E / UI Tests
	•	Manual: Follow script: enter sample values, verify UI cards & tables.
	•	Automated (optional): Streamlit App Testing or Playwright:
	•	Set inputs, click Calculate, assert result text present.

7.4 Property-Based / Fuzz (Optional)
	•	Use Hypothesis to fuzz income, rates, horizon; assert no crashes, monotonic behaviors (e.g., higher mortgage rate ⇒ higher NPV cost, ceteris paribus).

7.5 Performance
	•	Ensure <200ms recompute for typical inputs. If slow, cache heavy calcs.

⸻

8. API & Extensibility Hooks
	•	tax_lookup.py: today reads local JSON; tomorrow call IRS/Taxee API. Keep same return schema.
	•	mortgage_rates.py: placeholder for Freddie Mac API or similar.
	•	property_data.py: placeholder for Zillow/ATTOM.
	•	Add FeatureFlags (env vars) to toggle API vs. static.

⸻

9. Ops & Deployment Notes
	•	Deployment: Streamlit Community Cloud or simple Docker on EC2/Render.
	•	Secrets: Use Streamlit secrets management for API keys later.
	•	Logging: Python logging in calc/service layers; Streamlit st.error/st.warning for user-facing.
	•	Telemetry (optional): simple analytics (count of runs), if allowed.

⸻

10. Definition of Done (DoD)
	•	App runs locally: streamlit run app.py → works end-to-end.
	•	Core KPIs displayed and match unit-tested expectations for fixtures.
	•	Defaults load automatically; missing inputs prompt clear guidance.
	•	Code passes pytest and ruff/flake8 lint.
	•	README documents assumptions & how to extend.

⸻

11. Nice-to-Haves (Backlog)
	•	Monte Carlo simulation of appreciation/rent/returns.
	•	Tornado chart sensitivity (alt return, appreciation, rate, horizon).
	•	PDF/CSV export of schedules.
	•	User session persistence / shareable URL params.
	•	Multi-city comparison matrix.

⸻

Appendix A – Sample Pseudocode Snippets

Amortization

def amortize(loan, rate_annual, term_years):
    n = term_years * 12
    r = rate_annual / 12
    pmt = np.pmt(r, n, -loan)
    bal = loan
    rows = []
    for m in range(1, n+1):
        interest = bal * r
        principal = pmt - interest
        bal -= principal
        rows.append((m, interest, principal, max(bal, 0)))
    return pd.DataFrame(rows, columns=["month","interest","principal","balance"])

Break-even Month

def breakeven_month(cum_buy, cum_rent):
    diff = cum_buy - cum_rent
    idx = np.where(diff <= 0)[0]
    return int(idx[0]+1) if len(idx) else None


⸻

End of Document ✅