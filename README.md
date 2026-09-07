# space-weather-analysis

Tests whether solar flare characteristics predict the strength of the geomagnetic
disturbance that follows, using two years of NASA DONKI event catalogs.

The result is negative, and that is the finding. The hypothesis holds
directionally — stronger flare classes do coincide with higher Kp readings — but
the flare and geomagnetic records overlap too thinly to support the claim. Saying
that is more useful than fitting a model to 41 storms and reporting an R².

## Data

NASA DONKI (Database of Notifications, Knowledge, Information) API,
2023-07-11 to 2025-07-09.

| Catalog | Records |
|---|---:|
| Solar flares | 1,599 |
| High-speed streams | 103 |
| Geomagnetic storms | 41 |
| **Unified event table** | **1,743** |
| CME events, 2 years | 2,851 |

The three event catalogs share a schema and concatenate into
`space_weather_unified.csv`. CMEs carry extra kinematic fields — speed, half-angle,
direction — and stay in their own files.

Count the rows, do not count the lines. Three cells in the `note` field contain
embedded newlines, so `wc -l` reports 1,604 flares, 1,748 events and 2,866 CMEs —
five and fifteen too many, and consistent enough to look plausible. `data/metadata.json` records 1,599
and 1,743, and it is right. Parsing the CSV properly reproduces it exactly.

## Design

Fixed before touching the data, in [`notebooks/01_study_design.ipynb`](notebooks/01_study_design.ipynb):

- **Dependent variable** — `kp_index`, the observed geomagnetic disturbance.
  Continuous, so this is a regression problem rather than the flare-class
  classification it started as.
- **Predictors** — flare class, source location, active region, instruments, and
  temporal features.
- **Confounders** — the two that actually threaten the result, and what to do
  about each:

  *Active-region complexity.* Magnetically complex sunspot regions produce
  stronger flares. The catalog gives a region ID but no complexity class, so the
  recent flare history of that region stands in as a proxy.

  *Disk-position foreshortening.* A flare near the solar limb is observed at a
  steep angle and reads weaker than the identical flare at disk centre. Position
  is correlated with both the predictor and the label, which is what makes it a
  confounder rather than noise — so `source_location` is converted to numeric
  latitude and longitude to test whether limb events skew the estimate.

## What came out

- **Data quality** — clean. Deduplication and numeric coercion only, no
  imputation. Checked for duplicates, missing values, irregular categorical
  entries and outliers before any analysis.
- **Signal** — Kp depends moderately on event type and flare intensity.
- **No signal** — month, hour, and active-region ID have minimal effect.
- **Distribution** — C-class dominates and X-class events are rare, which is the
  constraint the whole analysis runs into.
- **Spatial** — events cluster near the solar equator, consistent with the
  physics rather than with a sampling artifact.

## Limitations

- 41 geomagnetic storms is not enough to fit anything confidently, and the
  overlap between flare records and storm records is thinner still. This is the
  binding constraint, not model choice.
- Two years is a fraction of the 11-year solar cycle, so any periodicity visible
  here is not periodicity.
- The mid-year uptick in activity is weak and should not be read as seasonality.
- Coursework scope (UMD DATA602), so the design was committed before the sparsity
  was known.

## Layout

```
notebooks/01_study_design.ipynb   problem, population, variables, confounders, hypothesis
notebooks/02_analysis.ipynb       profiling, EDA, hypothesis testing, regression
data/                             DONKI catalogs as CSV, plus collection metadata
```

## Next

- Join solar-wind and magnetosphere measurements to get coverage where flares and
  storms currently fail to overlap.
- Extend the window across a full solar cycle before claiming anything periodic.
- Revisit regression once the joint coverage supports it.
