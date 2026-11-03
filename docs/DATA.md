# Data

The research server held about 36 GB of data and results. This repository holds the code and the record. Market data can be rebuilt from public sources, and the team keeps the remaining results in a private archive.

## What is here

| What | Where |
|---|---|
| Code, docs, model reports, reviews | This repository |
| Leaderboards and scoring registries | [`reports/leaderboards/`](../reports/leaderboards) |
| Tables and charts behind the README | [`docs/assets/`](assets) |
| Bot starting price history | [`deploy/seed/`](../deploy/seed) |

## What is not here

| What | Size | How to get it |
|---|---:|---|
| Binance spot data | 3.2 GB | `python -m src.data.binance_downloader` |
| Research panel, funding and open interest | 122 MB | `python -m src.validation.build`, then the `src/data` jobs |
| Backtest and scoring caches | About 11 GB | Rerun the backtest with `--score` |
| Recorded Roostoo quotes, paper bot logs, full research results | About 3 GB | Private team archive. Roostoo publishes no price history, so the quotes cannot be downloaded again |
| API keys and `.env` | | Never in git. `.env.example` shows the format |

## Rebuild from nothing

```bash
python -m src.data.binance_downloader
python -m src.validation.build
python -m backtest.run --model book_e20combo_brk_cash --score
```

A full rebuild has not been tested end to end. Backtests read each coin's half-spread from a saved Roostoo ticker and use 5 bps when it is unknown, so results without the saved snapshots will differ slightly.

## Redraw the charts

```bash
python3 scripts/report/make_charts.py           # standard library only, from docs/assets/data
.venv/bin/python scripts/report/build_data.py   # rebuilds the tables; needs results/ and data/live*
```
