# Changelog

## [1.0.0] - unreleased
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
