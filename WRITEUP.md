# Methodology Writeup: NC 2024 Voter-Level Behavioral Simulation

## 1. Problem Statement

Predict the two-candidate (Republican minus Democratic) vote margin for each of North Carolina's 100 counties in the 2024 presidential election, using only information publicly available before Election Day. The prediction must come from a voter-level behavioral simulation—not a regression or lookup table.

## 2. Approach

### 2.1 Agent-Based Monte Carlo Simulation

Rather than fitting a county-level regression, the model generates **synthetic voters** for each county and simulates their behavior:

1. Each voter is assigned demographic attributes (age, sex, race, education, party registration, urban/rural) drawn from the county's known distribution.
2. A **turnout model** determines whether each voter participates.
3. A **vote choice model** assigns each participating voter a probabilistic vote (R or D).
4. County margins emerge from aggregating individual votes.

This is repeated across 50 Monte Carlo iterations per county with fixed random seeds, producing mean predictions and uncertainty estimates.

### 2.2 Why Agent-Based?

- **Interpretability**: Every coefficient has a concrete meaning (e.g., "registered Republicans are X% more likely to vote R").
- **Compositionality**: County-level results emerge from individual behaviors, not fitted county-level parameters.
- **Scenario analysis**: Changing a single parameter (e.g., Black voter turnout) propagates naturally through the simulation.
- **Uncertainty quantification**: Monte Carlo variation directly estimates prediction uncertainty.

## 3. Data Sources

All pre-election, publicly available:

| Source | Data | Time Period |
|--------|------|-------------|
| tonmcg/US_County_Level_Election_Results_08-16 | County presidential returns (wide format) | 2008, 2012, 2016 |
| tonmcg/US_County_Level_Election_Results_08-24 | County presidential returns | 2020 |
| NC State Board of Elections | Voter registration by county and party | Oct 12, 2024 |
| US Census ACS 5-Year | Demographics: population, race, education, age, income, land area | 2022 |

**No 2024 election results are used for training, tuning, or feature engineering.**

## 4. Feature Construction

Raw data is merged into a county feature table with these categories:

- **Election history**: Two-candidate margin for 2008, 2012, 2016, 2020; margin trends; average margin
- **Turnout history**: Total votes cast per county per year; turnout growth rates
- **Demographics**: Population, racial composition (% white, Black, Hispanic), % college-educated, median age, median household income
- **Geography**: Land area, population density, urban/suburban/rural classification
- **Registration**: Party registration counts and shares (D, R, Unaffiliated)

## 5. Model Architecture

### 5.1 Synthetic Population Generator (`sim/population.py`)

For each county, generates N synthetic voters (default 2,000) by sampling from the county's demographic profile:

- **Age**: 6 bands (18-24 through 65+), distributed using national age pyramids adjusted by county median age
- **Sex**: 51% F / 49% M (census default)
- **Race**: Sampled from county's racial composition (white, Black, Hispanic, other)
- **Education**: Binary (college / no college) based on county's % bachelor's+
- **Party registration**: Sampled from county's registration shares (D, R, unaffiliated)
- **Urban/rural**: Assigned based on county density classification

### 5.2 Turnout Model (`sim/turnout.py`)

A logistic model assigns each voter a turnout probability:

```
logit(P_turnout) = county_baseline_logit + Σ(demographic_coefficients)
```

The county baseline is derived from the county's historical turnout rate (e.g., 2020 turnout). Demographic coefficients shift the probability:

| Factor | Direction | Rationale |
|--------|-----------|-----------|
| Age 65+ | +turnout | Highest historical turnout group |
| Age 18-24 | −turnout | Lowest historical turnout group |
| College educated | +turnout | Strong education-turnout correlation |
| Registered R/D | +turnout | Partisans vote more than unaffiliated |
| Rural | slight −turnout | Historical rural turnout slightly lower |

### 5.3 Vote Choice Model (`sim/vote_choice.py`)

Voters who turn out receive a Republican vote probability:

```
logit(P_vote_R) = county_baseline_logit + Σ(demographic_coefficients)
```

**County baseline** is the primary anchor: a weighted average of the county's 2020 margin (60%) and 2016 margin (40%), converted to logit space. This captures the bulk of county-level partisan lean.

**Demographic coefficients** provide small modulations:

| Factor | Direction | Magnitude | Rationale |
|--------|-----------|-----------|-----------|
| Registered R | +R | moderate | Party loyalty effect |
| Registered D | +D | moderate | Party loyalty effect |
| Black | +D | moderate | Strong D alignment nationally |
| Hispanic | +D | small | D lean nationally |
| College | +D | small | Education realignment post-2016 |
| Age 65+ | +R | small | Generational lean |
| Rural | +R | small | Rural-urban divide |
| Male | +R | small | Gender gap |

**Key design choice**: Coefficients are deliberately small because the county baseline already encodes most of the information that demographics would predict. Large demographic effects would double-count and distort margins.

### 5.4 Statewide Shift

A uniform statewide shift parameter (default: +0.01 for 2024, reflecting pre-election polling showing a slight R shift from 2020) is added to every county's partisan baseline.

## 6. Validation

### 6.1 Backtest Design

To validate without data leakage:
- **Training period**: 2008–2016 election results
- **Test period**: 2020 county margins
- The model pretends 2020 hasn't happened: 2016 margin replaces 2020 as "most recent," 2012 replaces 2016 as "prior."

### 6.2 Backtest Results

| Metric | Behavioral Sim | Baseline (2016→2020) |
|--------|---------------|---------------------|
| Pearson correlation | 0.97 | 0.99 |
| Mean Absolute Error | 0.066 | 0.035 |
| RMSE | 0.087 | 0.043 |
| Directional accuracy | 93% | 97% |

### 6.3 Interpretation

The prior-margin baseline is exceptionally hard to beat because county partisanship is highly stable (correlations above 0.98 between consecutive elections). This is a well-documented finding in political science.

The behavioral simulation achieves strong absolute performance (0.97 correlation, 93% directional accuracy) while providing genuine voter-level mechanics that the baseline cannot:
- Interpretable coefficients for every demographic group
- Natural uncertainty quantification
- Counterfactual scenario capability

## 7. Limitations

1. **Coefficients from national data**: Demographic effects are calibrated from national exit polls and political science literature, not NC-specific models.
2. **No candidate-specific effects**: The model doesn't capture individual candidate appeal, campaign spending, or late-breaking events.
3. **Static demographics**: Uses 2022 ACS data; does not model population changes between 2022 and 2024.
4. **Registration as proxy**: Party registration is an imperfect proxy for vote choice (crossover voting, registration lag).
5. **No within-county variation**: Cannot capture precinct-level patterns.

## 8. Reproducibility

- All random processes use `numpy.random.RandomState(42)`
- Running the pipeline with identical parameters produces identical output
- Full pipeline: `fetch_data.py` → `build_features.py` → `export_predictions.py`
