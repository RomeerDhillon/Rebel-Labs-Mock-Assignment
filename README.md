# NC 2024 Presidential Election — Voter-Level Behavioral Simulation

An agent-based Monte Carlo simulation that predicts the 2024 North Carolina presidential election at the county level by generating synthetic voters, modeling turnout and vote choice probabilistically, and aggregating results across all 100 counties.

## Quick Start

### 1. Install Python dependencies

```bash
# macOS / Linux
python3 -m pip install -r requirements.txt

# Windows
python -m pip install -r requirements.txt
```

> **Note:** On Windows, use `python` instead of `python3` throughout this guide. Using `python -m pip` (instead of bare `pip`) ensures packages install into the same Python that runs the scripts. If you have multiple Python versions, ensure you're using Python 3.10+.

### 2. Fetch data & build features

```bash
python3 -m scripts.fetch_data      # macOS / Linux
python3 -m scripts.build_features   # macOS / Linux

python -m scripts.fetch_data         # Windows
python -m scripts.build_features     # Windows
```

This downloads historical election results (2008–2020) from GitHub and saves embedded ACS 2022 demographics and NCSBE voter registration data. All data is publicly available and predates the 2024 election.

### 3. Run the simulation

```bash
python3 -m scripts.export_predictions   # macOS / Linux
python -m scripts.export_predictions    # Windows
```

Outputs:

- `data/predictions/nc_2024_predictions.csv` — county-level predicted margins
- `data/predictions/nc_2024_predictions.json` — same data for the frontend

### 4. Run the backtest (optional)

```bash
python3 -m scripts.run_backtest   # macOS / Linux
python -m scripts.run_backtest    # Windows
```

Validates the model by predicting 2020 results using only 2008–2016 data.

### 5. Launch the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to explore predictions, county details, and methodology.

---

## Project Structure

```
├── scripts/
│   ├── fetch_data.py          # Downloads raw election, demographic, registration data
│   ├── build_features.py      # Merges raw data into county feature table
│   ├── nc_county_data.py      # Embedded ACS 2022 demographics (100 counties)
│   ├── nc_registration_data.py# Embedded NCSBE Oct 2024 registration stats
│   ├── run_backtest.py        # Backtests model: predict 2020 from 2008-2016
│   └── export_predictions.py  # Generates final 2024 predictions
├── sim/
│   ├── population.py          # Synthetic voter generation
│   ├── turnout.py             # Logistic turnout model
│   ├── vote_choice.py         # Logistic vote choice model
│   ├── run_simulation.py      # Monte Carlo simulation orchestrator
│   └── metrics.py             # Evaluation metrics
├── frontend/                  # Next.js app (Home, Counties, Methodology)
├── data/
│   ├── raw/                   # Downloaded/embedded source data
│   ├── processed/             # County features, backtest results
│   └── predictions/           # Final 2024 predictions
├── requirements.txt
└── README.md
```

## How It Works

### Data (pre-election only)

| Source                   | Description                                         | Years        |
| ------------------------ | --------------------------------------------------- | ------------ |
| tonmcg GitHub repos      | County presidential returns                         | 2008–2020    |
| NCSBE voter registration | Party registration by county                        | Oct 12, 2024 |
| ACS 5-Year               | Demographics: race, education, age, income, density | 2022         |

**No 2024 election results are used anywhere.**

### Simulation Pipeline

1. **Feature construction** — Merge election margins, turnout rates, demographics, and registration shares into a county feature table.

2. **Synthetic population** — For each county, sample ~2,000 voters per iteration with attributes drawn from county distributions: age band, sex, race, education, party registration, urban/rural.

3. **Turnout model** — Logistic model anchored on the county's historical turnout rate, with additive demographic shifts (age, education, party, etc.).

4. **Vote choice model** — Logistic model anchored on the county's historical partisan margin, with small demographic modulations (party registration, race, education, age, urbanicity, sex).

5. **Monte Carlo aggregation** — 50 iterations per county. Predicted margin = mean across iterations. Uncertainty captured via standard deviation and 95% CI.

6. **Statewide aggregation** — County margins are weighted by 2020 vote totals to produce a population-weighted statewide result: **R 51.0% — D 49.0% (R+1.9%)**.

### Key Design Decisions

- **County history as primary anchor** — Historical margins dominate. Demographics provide interpretable but modest modulations to avoid double-counting (voter demographics correlate with county history).
- **Logit-space coefficients** — All effects are additive in logit space, keeping probabilities bounded and interpretable.
- **Fixed seeds** — All randomness uses seed 42 for full reproducibility.

### Backtest Results (predicting 2020 from 2008–2016)

| Metric    | Simulation | Baseline (prior margin) |
| --------- | ---------- | ----------------------- |
| Pearson r | 0.98       | 0.99                    |
| MAE       | 0.048      | 0.035                   |
| RMSE      | 0.061      | 0.043                   |
| Direction | 94%        | 97%                     |

The prior-margin baseline is extremely strong because county partisanship is highly stable. The behavioral simulation trades a small accuracy gap for voter-level mechanics, interpretable coefficients, and scenario analysis capability.

## Scenario Controls

Two parameters allow counterfactual exploration:

- **Turnout sensitivity** — Scales demographic turnout effects. Higher = more group-level turnout differentiation.
- **Partisan elasticity** — Scales demographic vote-choice effects. Higher = more demographic polarization.

## Model Mechanics

### Turnout Model

The turnout model assigns each synthetic voter a probability of voting based on:

1. **County baseline** — Historical turnout rate (2020) converted to logit space
2. **Demographic shifts** — Additive logit adjustments for:
   - **Age**: Older voters (+0.15 logit for 65+, -0.10 for 18-24)
   - **Education**: College-educated (+0.08 logit)
   - **Party registration**: Republicans and Democrats (+0.12 logit vs. unaffiliated)
   - **Race**: Modest effects calibrated from national exit polls

**Formula** (simplified):

```
turnout_logit = county_baseline_logit + age_effect + education_effect + party_effect + ...
turnout_prob = sigmoid(turnout_logit)
```

### Vote Choice Model

The vote choice model determines how voters who turn out vote (R, D, or abstain):

1. **County baseline** — Historical partisan margin (2020) converted to logit space, scaled by `RESIDUAL_SCALE = 0.98` to avoid double-counting
2. **Statewide shift** — Urbanicity-aware shift for 2024:
   - Urban: -0.5% (slight D shift)
   - Suburban: +1.0% (slight R shift)
   - Rural: +1.5% (continued R shift)
3. **Demographic modulations** — Small additive logit shifts for:
   - **Party registration**: Republicans (+0.10 logit), Democrats (-0.10 logit)
   - **Race**: Black voters (-0.12 logit), Hispanic voters (-0.08 logit)
   - **Education**: College-educated (-0.06 logit)
   - **Age**: 65+ voters (+0.04 logit)
   - **Urbanicity**: Urban voters (-0.03 logit)
   - **Sex**: Male voters (+0.02 logit)

**Why small coefficients?** County baseline margins already encode most demographic variation. Large demographic effects would double-count the same signal and distort predictions.

### Monte Carlo Aggregation

For each county:

1. Generate 50 independent iterations (fixed seed for reproducibility)
2. Each iteration: 2,000 synthetic voters → turnout simulation → vote choice simulation → county margin
3. Aggregate: mean margin, std dev, 95% CI (2.5th/97.5th percentiles)

### Population Weighting

County margins are weighted by 2020 vote totals to compute the statewide result:

```
statewide_margin = Σ(county_margin × county_votes_2020) / Σ(county_votes_2020)
```

This is critical because NC's 100 counties vary enormously in population (Wake: ~550K votes, Tyrrell: ~1.6K votes). The unweighted county average is ~R+19.7% (most counties are small and rural), but the population-weighted statewide prediction is **R 50.95% — D 49.05%**, consistent with 2020's R+1.4% plus a small predicted R shift.

## Model Coefficients (Detailed)

All coefficients are in logit space and calibrated from:

- National exit polls (2016, 2020)
- Political science literature
- Pre-2024 data only (no 2024 results used)

### Turnout Coefficients

| Factor       | Logit Shift | Interpretation                    |
| ------------ | ----------- | --------------------------------- |
| Age 65+      | +0.15       | Seniors vote at higher rates      |
| Age 18-24    | -0.10       | Young voters less reliable        |
| College      | +0.08       | Education correlates with turnout |
| Republican   | +0.12       | Partisan voters more engaged      |
| Democrat     | +0.10       | Partisan voters more engaged      |
| Unaffiliated | baseline    | Reference group                   |

### Vote Choice Coefficients

| Factor     | Logit Shift | Interpretation                      |
| ---------- | ----------- | ----------------------------------- |
| Republican | +0.10       | Party registration strong predictor |
| Democrat   | -0.10       | Party registration strong predictor |
| Black      | -0.12       | Strong D lean nationally            |
| Hispanic   | -0.08       | D lean nationally                   |
| College    | -0.06       | Education realignment post-2016     |
| Age 65+    | +0.04       | Modest R lean among seniors         |
| Rural      | +0.03       | Rural-urban divide                  |
| Male       | +0.02       | Gender gap                          |
| Urban      | -0.03       | Urban-D lean                        |

## Limitations

1. **National coefficients** — Demographic effects are calibrated from national-level data, not NC-specific micro-targeting models. NC-specific coefficients would be more accurate but require fitting to 2024 results (which violates the pre-election constraint).

2. **Static demographics** — Uses 2022 ACS data; does not model population changes between 2022 and 2024. Large demographic shifts (e.g., major migration) would not be captured.

3. **No candidate effects** — The model does not capture individual candidate appeal, campaign spending, late-breaking events, or mobilization efforts. It assumes 2024 will follow historical partisan patterns.

4. **Registration as proxy** — Party registration is an imperfect proxy for vote choice. Crossover voting, registration lag, and independent voters' actual behavior introduce noise.

5. **County-level only** — Cannot capture within-county variation (e.g., precinct-level patterns, urban vs. rural splits within a county).

6. **Residual scale trade-off** — Using `RESIDUAL_SCALE = 0.98` avoids double-counting but also means the model is heavily anchored to county history. This explains why it doesn't beat the naive baseline on accuracy.

## Testing

The project includes **82 pytest tests** covering:

- **Utils** (16 tests): Sigmoid, logit, data validation
- **Turnout** (20 tests): Baseline computation, probability calculation, vectorization
- **Vote choice** (28 tests): Baseline computation, demographic effects, vectorization
- **Population** (18 tests): Synthetic voter generation, demographic distributions, reproducibility
- **Simulation** (14 tests): End-to-end county simulation, output validity, fallbacks
- **Metrics** (6 tests): Evaluation metrics (MAE, RMSE, correlation, directional accuracy)

Run all tests:

```bash
python3 -m pytest tests/ -v              # macOS / Linux
python -m pytest tests/ -v               # Windows
```

Run a specific test file:

```bash
python3 -m pytest tests/test_vote_choice.py -v   # macOS / Linux
python -m pytest tests/test_vote_choice.py -v    # Windows
```

## Advanced Usage

### Custom Scenario Analysis

Modify parameters in `scripts/export_predictions.py`:

```python
results = run_full_simulation(
    features_path=features_path,
    n_voters=2000,           # Synthetic voters per iteration
    n_iterations=50,         # Monte Carlo iterations
    seed=42,                 # Random seed for reproducibility
    turnout_sensitivity=1.5, # Scale demographic turnout effects (>1 = more differentiation)
    partisan_elasticity=1.2, # Scale demographic vote-choice effects (>1 = more polarization)
    statewide_shift=0.02,    # Uniform R shift (for counterfactuals)
)
```

### Backtesting with Custom Parameters

```bash
# Edit scripts/run_backtest.py to modify parameters, then:
python3 -m scripts.run_backtest   # macOS / Linux
python -m scripts.run_backtest    # Windows
```

The backtest predicts 2020 results using only 2008–2016 data, validating the model without data leakage.

### Reproducibility

All randomness is deterministic:

- Master seed: 42 (configurable)
- Per-county seed: `seed + int(county_fips) * 7 + iteration * 1000`
- Running the pipeline twice with the same seed produces identical results

## Frontend Features

The interactive dashboard includes:

- **Home**: Statewide summary (projected winner, vote %, county counts, closest race, largest margin)
- **Counties**: Interactive map with hover tooltips, click-to-select county details
- **Results**: Sortable/searchable table of all 100 counties
- **County detail pages**: Full statistics, margin visualization, similar counties
- **Methodology**: Plain-language explanation of the model

## Data Files

After running the pipeline:

```
data/
├── raw/
│   ├── nc_election_history.csv          # 2008-2020 county returns
│   ├── nc_county_demographics.csv       # ACS 2022 demographics
│   └── nc_voter_registration.csv        # NCSBE Oct 2024 registration
├── processed/
│   ├── county_features.csv              # Merged feature table (100 counties)
│   └── backtest_results.json            # Backtest metrics
└── predictions/
    ├── nc_2024_predictions.csv          # Final predictions (CSV)
    └── nc_2024_predictions.json         # Final predictions (JSON for frontend)
```

## Tech Stack

- **Simulation**: Python 3.12+ (pandas, numpy, scipy)
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Data**: Public pre-election sources (GitHub, NCSBE, ACS)
- **Testing**: pytest (82 tests)

## References

- **County-level election data**: [tonmcg/US_County_Level_Election_Results](https://github.com/tonmcg/US_County_Level_Election_Results)
- **Voter registration**: [NC State Board of Elections](https://www.ncsbe.gov/)
- **Demographics**: [US Census Bureau ACS 5-Year](https://www.census.gov/programs-surveys/acs/)
- **Exit polls**: [Roper Center for Public Opinion Research](https://ropercenter.cornell.edu/)
- **Political science**: Abramowitz & Saunders (2016), Enten (2020), Wasserman (2021)
