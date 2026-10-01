# Project map

Where everything lives. Read `AGENTS.md` first; `docs/STRATEGY_GUIDE.md` explains how to build and test a model.

## Flow

```
data.binance.vision ──► src/data (download, verify, load) ──► data/binance_spot/…
                                    │
                                    ▼
             src/validation/build ──► data/validation/ (hourly panel, point-in-time universe, features, outcomes)
                                    │                    reports/validation_set_v1.md · validation/validation_set_v1.json
                                    ▼
src/models/<member>/<model>.py ──► backtest/ (harness) ──► reports/<model>/<YYYYMMDD-HHMM>.md
                                    │                       reports/compare/<method>/<YYYYMMDD-HHMM>.md
                                    ▼
             src/api + src/execution + src/live (planned) ──► EC2 bot ──► Roostoo
```

## Code

| Path | What it is |
|---|---|
| `AGENTS.md` | Rules for every agent and teammate. Read at the start of every session |
| `config.yaml` | Every tunable number: universe, data jobs, validation, `harness:`, `scoring:` and `models:` (one block per model, grouped by member) |
| `src/config.py` | Loads `config.yaml`; symbol helpers (`BTC/USD` ↔ `BTCUSDT`) |
| `src/contracts.py` | **Shared contract**: `ModelSpec`, `MarketView`, `check_targets`. Changes need both other members' review |
| `src/models/` | The model registry (`discover`, `get`, `by_method`) and `_template.py` |
| `src/models/baselines/` | Team references, never compete: `team_btc_hold`, `team_cash`, and the scoring field `team_ew_daily`, `team_rot_ew`, `team_rot_iv`, `team_trend_2`, `team_mom_ss25` |
| `src/models/<member>/` | Each member's models: one file per model, file name = model name |
| `src/data/` | Binance archive downloader (locked, append-only manifest, checksums), loader (ms/µs), integrity sweep, FRED, futures, hourly panel |
| `src/validation/` | Lookalike validation: state features, outcomes, pre-registered selection, walk-forward skill, report |
| `backtest/data.py` | Loads the hourly panel, point-in-time universe and Roostoo spreads for the harness |
| `backtest/engine.py` | Runs a model's decisions through one 14-day window from cash: fees, spread, 1-bar lag, band, activity guard |
| `backtest/metrics.py` | Return, max drawdown, Sharpe/Sortino/Calmar and the composite under conventions A and B |
| `backtest/evaluate.py` | Scores a model on every window; periods, scenario sets, must-pass checks, result cache |
| `backtest/report.py` | Writes `reports/<name>/<stamp>.md` and the `.log` |
| `backtest/run.py` | `python -m backtest.run --model <name>` · `--list` · `--holdout` (frozen launch model only) |
| `backtest/compare.py` | `python -m backtest.compare --method <method>`: the pre-registered per-method rule |
| `backtest/scoring/` | Competition-style score (`docs/EVALUATION.md`): metrics V1–V4 × FLOORED/POL, live-like and recency weights, return gate, HEADLINE, gates G1–G6, leakage check, registry and leaderboard, SVG report. `--score` on `backtest.run`; `python -m backtest.scoring compare/leaderboard/field` |
| `scripts/wt`, `scripts/lock`, `scripts/status` | Worktrees per member and task, single-copy jobs, a status screen |
| `tests/` | `pytest -q`: downloader, loader, leakage, validation units, harness (metrics by hand, engine accounting, contracts), scoring (golden values, an independent re-implementation, toy tables, determinism, registry, leakage) |
| `docs/` | `TEAM_PLAN.md` (plan and decisions), `STRATEGY_GUIDE.md`, `EVALUATION.md` (the score and its sign-off checklist), this map |

**Planned** (build list in `docs/TEAM_PLAN.md` §4.1):
- `backtest/selection.py`: the selection ladder.
- `src/api/`: Roostoo client.
- `src/execution/`: order planner, paper broker.
- `src/live/`: the bot loop.
- `deploy/`: systemd, EC2 setup.

## Data (gitignored, on the server only)

| Path | Content |
|---|---|
| `data/binance_spot/` | Raw archive zips (1m for the Roostoo universe, 1h since 2018/2020), manifests, parquet cache |
| `data/external/` | BTC perp funding and open interest |
| `data/validation/` | `panel_close_1h.parquet`, `panel_quote_volume_1h.parquet` (97 series, close-time index), `universe.parquet` (point-in-time top-30 per day), features, outcomes, walk-forward tables |
| `data/harness/<model>/` | Cached window results, keyed by model code, parameters, harness config and data |
| `data/roostoo_snapshots/` | Saved `exchangeInfo`, `ticker` and coverage snapshots (the ticker gives the spreads) |

## Outputs

| Path | Committed? |
|---|---|
| `reports/<model>/<YYYYMMDD-HHMM>.md` | Yes: the record of each run |
| `reports/<model>/<YYYYMMDD-HHMM>.log` | No |
| `reports/compare/<method>/…` | `.md` yes, `.log` no |
| `reports/<model>/<YYYYMMDD-HHMM>-score.md` and its chart folder | Yes (`--score`) |
| `reports/compare/headline/…` | `.md` yes, `.log` no (`python -m backtest.scoring compare`) |
| `reports/validation_set_v1.md`, `validation/validation_set_v1.json` | Yes (written by `src.validation.build`) |
| `results/<member>/` | No: scratch, and each scoring run's `score.json` and `trades.csv.gz` |
| `results/scoring/` | No: the shared scoring registry (`registry.jsonl`), `leaderboard.md` and cache |
