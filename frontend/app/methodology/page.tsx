export default function MethodologyPage() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>Methodology</h1>

      <h2>Overview</h2>
      <p>
        This project predicts the 2024 North Carolina presidential election at
        the county level using an <strong>agent-based behavioral simulation</strong>.
        Instead of fitting a top-down regression, we generate synthetic voters
        with demographic attributes, then probabilistically model each
        voter&apos;s turnout and vote choice.
      </p>

      <h2>Data Sources</h2>
      <p>
        All data was publicly available <em>before</em> Election Day 2024. No
        2024 election results are used for training or tuning.
      </p>
      <ul>
        <li>
          <strong>Historical election results (2008&ndash;2020)</strong> &mdash;
          County-level presidential returns from
          tonmcg/US_County_Level_Election_Results repos on GitHub.
        </li>
        <li>
          <strong>NC voter registration (Oct 12 2024)</strong> &mdash; Party
          registration counts by county from the NC State Board of Elections.
        </li>
        <li>
          <strong>ACS 2022 5-Year demographics</strong> &mdash; Population,
          race, education, median age, income, and land area from the US Census
          Bureau American Community Survey.
        </li>
      </ul>

      <h2>Simulation Pipeline</h2>
      <ol>
        <li>
          <strong>Feature construction</strong> &mdash; Merge election history,
          demographics, and registration data into a single county feature
          table. Derived features include margin trends, turnout growth, party
          registration shares, and population density / urban-rural
          classification.
        </li>
        <li>
          <strong>Synthetic population generation</strong> &mdash; For each
          county, draw ~2,000 synthetic voters per Monte Carlo iteration. Each
          voter is assigned age band, sex, race/ethnicity, education level,
          party registration, and urban/rural status by sampling from the
          county&apos;s known demographic distribution.
        </li>
        <li>
          <strong>Turnout model</strong> &mdash; A logistic model assigns each
          voter a turnout probability. The county&apos;s historical turnout
          rate anchors a baseline logit; additive demographic coefficients
          shift the probability based on age, education, party registration,
          race, and urban/rural status.
        </li>
        <li>
          <strong>Vote choice model</strong> &mdash; Voters who turn out
          receive a probability of voting Republican via a second logistic
          model. The county&apos;s historical partisan margin anchors the
          baseline; small demographic logit shifts modulate around it based on
          party registration, race, education, age, urbanicity, and sex.
        </li>
        <li>
          <strong>Monte Carlo aggregation</strong> &mdash; Each county is
          simulated across 50 independent iterations (with fixed seeds for
          reproducibility). The predicted margin is the mean across iterations;
          uncertainty is captured via standard deviation and 95% confidence
          intervals.
        </li>
      </ol>

      <h2>Key Design Decisions</h2>
      <ul>
        <li>
          <strong>County history as primary anchor</strong> &mdash; The county
          partisan baseline (weighted average of 2020 and 2016 margins) is the
          dominant signal. Demographic modulations are intentionally small to
          avoid double-counting, since voter demographics already correlate
          heavily with county history.
        </li>
        <li>
          <strong>Logit-space coefficients</strong> &mdash; All effects are
          additive in logit space, ensuring probabilities stay bounded in
          [0, 1] and allowing interpretable direction/magnitude for each
          demographic group.
        </li>
        <li>
          <strong>No 2024 data leakage</strong> &mdash; Coefficients are set
          from pre-2024 exit polls and political science literature, not fitted
          to 2024 results.
        </li>
      </ul>

      <h2>Validation</h2>
      <p>
        The model is backtested by predicting 2020 county margins using only
        2008&ndash;2016 data. Results:
      </p>
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Simulation</th>
            <th>Baseline (2016&rarr;2020)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Pearson correlation</td>
            <td>0.97</td>
            <td>0.99</td>
          </tr>
          <tr>
            <td>MAE</td>
            <td>0.066</td>
            <td>0.035</td>
          </tr>
          <tr>
            <td>Directional accuracy</td>
            <td>93%</td>
            <td>97%</td>
          </tr>
        </tbody>
      </table>
      <p>
        The prior-margin baseline is a very strong predictor because county
        partisanship is highly stable. The behavioral simulation trades a small
        accuracy gap for genuine voter-level mechanics, interpretable
        coefficients, and the ability to run counterfactual scenarios.
      </p>

      <h2>Scenario Controls</h2>
      <p>Two parameters allow exploration of alternative scenarios:</p>
      <ul>
        <li>
          <strong>Turnout sensitivity</strong> &mdash; Scales the demographic
          turnout effects. Higher values amplify group-level turnout
          differences; lower values flatten them toward the county baseline.
        </li>
        <li>
          <strong>Partisan elasticity</strong> &mdash; Scales the demographic
          vote-choice effects. Higher values amplify polarization; lower
          values push all voters toward the county baseline margin.
        </li>
      </ul>

      <h2>Limitations</h2>
      <ul>
        <li>
          Coefficients are set from national-level exit poll data, not
          NC-specific micro-targeting models.
        </li>
        <li>
          The model does not capture candidate-specific effects, campaign
          spending, late-breaking events, or mobilization efforts.
        </li>
        <li>
          County-level predictions cannot capture within-county variation
          (e.g., precinct-level patterns).
        </li>
      </ul>

      <h2>Reproducibility</h2>
      <p>
        All random processes use fixed seeds (default: 42). Running the
        simulation with the same parameters produces identical results. See
        the README for full instructions.
      </p>
    </article>
  );
}
