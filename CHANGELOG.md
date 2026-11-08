# Changelog

## [2.0.0] - 2026-10-22
"Analytics" release. All new commands read only local data; no extra API calls.
### Added
- `score` (vote percentile of a product or a vote count inside a topic, with median and p90).
- `momentum` (rising / falling topics, last N weeks vs previous N weeks).
- `best-time` (launches and median votes per UTC weekday; correlation, not causation).
- `export --format sqlite|duckdb` (DuckDB via the optional `[duckdb]` extra).
- `ph_dataset.demo.fake_products()` deterministic FAKE data generator for tests and demos.
### Changed
- Requires Python 3.10+ (CI: 3.10 and 3.12).
- `.gitignore` now also covers `*.db`, `*.sqlite*`, `*.duckdb`, `*.jsonl`, `*.parquet`.

## [1.0.0] - 2026-10-21
First public release as **ph-dataset** (rewrite of the private "Jules" prototype).
### Added
- `ph_dataset` package with `ph-dataset` CLI: `fetch`, `update`, `export`, `trends`.
- PH GraphQL v2 client: token or client-credentials auth (no mock fallback), rate-limit header throttling, 429/5xx backoff.
- Resumable day-by-day collection with saved cursor; JSONL store with dedup by id.
- CSV / JSON / Parquet (optional `pyarrow`) export; opt-in comments and maker names.
- pytest suite with mocked HTTP; GitHub Actions CI (ruff + pytest); Dockerfile.
- MIT license, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates.
- `--featured-only`, `--max-products` on `update`; stable `NEWEST` ordering.
### Fixed (found in live API test)
- `--max-products` now exact (was rounded up to a full page).
- Duplicate posts across pages (unstable default ranking order).
- `update` no longer marks the still-running UTC day as complete.
- Tests no longer read real credentials from the environment; clearer 401 message.
### Removed
- Collected data, logs, report dumps, scratch scripts, compiled files, hourly Gemini "ops assistant" workflow.
