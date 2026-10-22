# ph-dataset

[![CI](https://github.com/chjakin-byte/ph-dataset/actions/workflows/ci.yml/badge.svg)](https://github.com/chjakin-byte/ph-dataset/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
<!-- After the first PyPI release, uncomment:
[![PyPI](https://img.shields.io/pypi/v/ph-dataset.svg)](https://pypi.org/project/ph-dataset/)
-->

**Build your own fresh Product Hunt dataset with one command — official API, resumable, rate-limit aware.**

Want to know what launched on Product Hunt last month, which topics are hot, or what makers in your niche
ship? Public Product Hunt dumps go stale the day they are published, and most scrapers break or ignore the
terms. `ph-dataset` uses the **official Product Hunt GraphQL API v2** with *your own* token, walks history
day by day, survives interruptions, respects rate limits, and gives you clean CSV / JSON / Parquet files.
Code only — no data ships here.

**Who it's for:** indie makers and founders doing market research, data analysts, students and researchers.

## Why not just download a dataset?
| | Static dataset (Kaggle/HF dump) | One-off scraper script | **ph-dataset** |
|---|---|---|---|
| Fresh data | ❌ frozen at publish date | ✅ | ✅ `update` adds new days |
| Official API, follows PH terms | varies | often scrapes HTML | ✅ GraphQL v2, your token |
| Resume after crash / rate limit | n/a | ❌ | ✅ saved cursor + header-aware throttling |
| Pick date range / topic / featured | ❌ | sometimes | ✅ |
| Comments, makers | fixed | varies | opt-in |
| Tests + CI | n/a | rarely | ✅ 21 tests, GitHub Actions |

## Demo (illustrative output, fake data)
```console
$ ph-dataset fetch --since 2026-10-01 --until 2026-10-08 --featured-only
Collected 231 products into data/
$ ph-dataset trends --top 3
topic                                    launches    votes
Artificial Intelligence                        97    24510
Developer Tools                                58    13022
Productivity                                   51     9874
$ ph-dataset export --format parquet
Wrote 231 products to data/products.parquet
```

## Install
```bash
pip install "git+https://github.com/chjakin-byte/ph-dataset"          # core
pip install "ph-dataset[parquet] @ git+https://github.com/chjakin-byte/ph-dataset"  # + Parquet
```
(Python 3.9+. A PyPI release is planned.)

## Quickstart
```bash
cp .env.example .env          # put your PH_TOKEN (or PH_CLIENT_ID + PH_CLIENT_SECRET) here
ph-dataset fetch --since 2024-01 --until 2024-02       # January 2024 launches
ph-dataset export --format csv                          # -> data/products.csv
ph-dataset trends --top 10                              # top topics by launches & votes
ph-dataset update                                       # later: fetch only new days
```
Get a token at <https://www.producthunt.com/v2/oauth/applications> (create an app → "Create Token").

## Commands
| Command | What it does |
|---|---|
| `fetch --since YYYY-MM[-DD] [--until …]` | Collect launches day by day (end date exclusive). Resumable: re-run the same command after a crash and it continues from the saved cursor. |
| `update` | Fetch every finished UTC day since the last completed day, up to yesterday (first run: last 7 days). Today is skipped until it is over. |
| `export --format csv\|json\|parquet [--what products\|comments] [--out PATH]` | Write the deduplicated data. Parquet needs `pyarrow`. |
| `trends [--top N] [--weekly]` | Top topics by number of launches and total votes, optionally per ISO week. |

Useful flags for `fetch`/`update`: `--featured-only` (only featured launches; a typical day has ~30 featured vs. several hundred total, so far fewer API calls), `--max-products N`, `--topic SLUG`.
Opt-in flags: `--with-comments` (+`--max-comments`, default 50) and `--with-makers`
(stores maker names; personal data, off by default). Global: `--data-dir` (default `data/`), `-v`.

## How it works
- Auth with `PH_TOKEN`, or OAuth client credentials. Auth failures stop the run with a clear error.
- Reads `X-Rate-Limit-Remaining` / `X-Rate-Limit-Reset` and pauses before the quota runs out;
  on HTTP 429 waits for the reset, on 5xx backs off exponentially (max 5 retries).
- Requests posts in `NEWEST` order so pagination is stable (no duplicates between pages).
- Appends to `data/products.jsonl` (and `comments.jsonl`), saves progress in `data/state.json`,
  and dedups by Product Hunt id on read/export (latest record wins).

Fields: `id, slug, name, tagline, description, votes, comments_count, created_at, featured_at, website, url, topics, makers`.

Docker: `docker build -t ph-dataset . && docker run --env-file .env -v "$PWD/data:/app/data" ph-dataset fetch --since 2024-01`

## Product Hunt terms & data — please read
- The Product Hunt API **must not be used for commercial purposes** without permission
  ([API docs](https://api.producthunt.com/v2/docs)); contact hello@producthunt.com for business use.
- This project distributes **code only**. Don't commit or republish collected data (`data/` is git-ignored).
  You are responsible for following Product Hunt's terms.
- Comments and maker names are personal data; they are opt-in. Collect only what you need.
- Limits: 6,250 complexity points / 15 min on GraphQL; in our tests one page of 20 posts cost ~100 points, i.e. roughly 1,200 posts per 15 min ([rate limits](https://api.producthunt.com/v2/docs/rate_limits/headers)).

## Roadmap
- [x] Resumable, rate-limit-aware collection; CSV/JSON/Parquet export; `trends` (v1.0)
- [ ] PyPI release
- [ ] DuckDB query helper and example notebook
- [ ] More analysis: fastest-growing topics, launch-day vote curves
- [ ] Optional LLM summaries/clustering of launches from your local dataset

## Development
```bash
pip install -e '.[dev,parquet]' && ruff check . && pytest -q
```
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License
[MIT](LICENSE) © 2026 chjakin-byte. Not affiliated with Product Hunt.
