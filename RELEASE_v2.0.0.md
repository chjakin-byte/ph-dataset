# ph-dataset v2.0.0 — Analytics

Answer "how did my launch do, which topics are heating up, which weekday works best?" from your own local dataset.

## New
- `ph-dataset score --product SLUG` or `--votes N --topic SLUG`: vote percentile in the topic, with median and p90.
- `ph-dataset momentum --weeks 4`: rising and falling topics (last N weeks vs the N before).
- `ph-dataset best-time`: launches and median votes per UTC weekday, with sample size.
- `ph-dataset export --format sqlite|duckdb` (`pip install "ph-dataset[duckdb]"` for DuckDB).

## Notes
- New commands only read local `data/`; they never call the Product Hunt API.
- Results are correlation, not causation.
- Now requires Python 3.10+.
- Code only: this release ships no Product Hunt data. Tests use generated fake data.
