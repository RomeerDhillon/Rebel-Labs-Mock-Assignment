# NC 2024 Presidential Election — Voter-Level Behavioral Simulation

An agent-based Monte Carlo simulation that predicts the 2024 North Carolina presidential election at the county level by generating synthetic voters, modeling turnout and vote choice probabilistically, and aggregating results across all 100 counties.

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Fetch data & build features

```bash
python3 -m scripts.fetch_data
python3 -m scripts.build_features
```

This downloads historical election results (2008–2020) from GitHub and saves embedded ACS 2022 demographics and NCSBE voter registration data. All data is publicly available and predates the 2024 election.

### 3. Run the simulation

```bash
python3 -m scripts.export_predictions
```

Outputs:

- `data/predictions/nc_2024_predictions.csv` — county-level predicted margins
- `data/predictions/nc_2024_predictions.json` — same data for the frontend

### 4. Run the backtest (optional)

```bash
python3 -m scripts.run_backtest
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

## Tech Stack

- **Simulation**: Python (pandas, numpy, scipy)
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Data**: Public pre-election sources (GitHub, NCSBE, ACS)
