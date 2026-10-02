# MiniMax: automated crypto trading bot for the Roostoo APAC Quant Trading Hackathon

Team MiniMax (Pol, Book, Baitoey). The bot trades spot crypto on Roostoo's exchange in competition 538,
**2026-10-04 12:00 UTC to 2026-10-18 12:00 UTC** (20:00 HKT both days), starting from $100,000, with no
leverage and no manual intervention. It runs by itself on one AWS EC2 machine.

## The strategy: `pol_switch_vt_tl_e20v45`

One daily decision at 00:00 HKT (16:00 UTC), choosing between two methods by BTC's trend:

- **BTC in an uptrend** (above its 20-day exponential average by more than 3%; a 3% band against flip-flopping):
  **volume-timed momentum**. Hold the 6 coins with the strongest 7- and 14-day risk-adjusted momentum, keep a
  holding while it stays in the top 12, skip a coin for a day after it breaks its 24-hour low on heavy volume, and
  scale the book so its estimated daily volatility is at most 4.5%.
- **Otherwise: per-coin trend**, long coins in clear up-trends and (when the exchange allows it) short clear
  down-trends, inverse-volatility weights, the book scaled to a volatility target, never above 100% gross.

Every day at 12:00 HKT, if the day has no trade yet, the bot rebalances back to its target weights, so every day
has at least one trade that follows the strategy. If the exchange refuses short positions, the bot continues
long-only by itself; over the backtest the long-only version scores the same.

Code: `src/models/pol/pol_switch_vt_tl_e20v45.py` (the switch), `src/models/baitoey/baitoey_vt_mom.py` (momentum),
`src/models/pol/pol_trend_ls.py` (trend), shared logic in `src/models/pol/_combo.py`; every number in
`config.yaml` under `models:`.

## How it was chosen

- **Data:** Binance public hourly data (data.binance.vision and Binance's REST API), the same prices Roostoo uses
  (checked: Roostoo's quotes equal Binance's).
- **Test:** each candidate replayed on 2,298 fourteen-day windows (one per day, June 2020 to September 2026), from
  $100,000, with Roostoo's fees, bid-ask spreads and a one-hour fill delay, using only information available at each
  decision (an automatic leakage check perturbs future prices).
- **Score (return first, like the competition):** how often a model's 14-day return clears three bars (do not lose
  more than last season's #20 team in falling markets, do not lose money, beat the median of six simple benchmark
  strategies), weighted towards periods that look like the current market and recent ones; the competition's risk
  ratios (Sortino, Sharpe, Calmar) as the tie-break. Definitions: `docs/EVALUATION.md`.
- **Evidence:** `reports/review/20261002-e20v45-readiness.md` (the live bot's code replayed hour by hour: every
  function and every rule), `20261002-recheck.md` (robustness), `20261002-selection-rule.md` (how the pick is made).

## Competition rules the bot follows

No leverage (positions only from free cash; shorts are 1x and collateral-based) · at least one trade every day ·
at most 20 API calls a minute (the limit is 30) · one decision a day plus a daily rebalance (no high-frequency
trading, market-making or arbitrage) · orders at or above the exchange's minimum and precision · no manual trading:
changes only through commits.

## Repository layout

| Path | What is there |
|---|---|
| `src/models/` | Every strategy (`pol/`, `baitoey/`, `book/`, team baselines in `baselines/`); `src/contracts.py` is the interface |
| `src/live/` | The live bot: hourly runner, data feed, broker, self-checks (`runner.py`, `feed.py`, `broker.py`, `selfcheck.py`, `fillcheck.py`) |
| `src/api/` | Roostoo REST client (signing, rate limit, order rules) |
| `src/execution/` | Order planner and paper broker |
| `src/data/`, `src/validation/` | Binance downloader and loaders; the research panel and market-likeness weights |
| `backtest/` | Backtest engine and the competition-style scoring (`backtest/scoring/`) |
| `deploy/` | EC2 setup script, systemd service, pinned packages, the bot's starting price history (`deploy/seed/`) |
| `docs/`, `reports/` | Methods, evaluation rules, every scored model's report and the team's reviews |
| `config.yaml` | All settings: universe, harness, scoring, models, the live bot (`live:`) |

## Running it

Python 3.10 or newer.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r deploy/requirements-lock.txt pytest
pytest -q                                              # the test suite (no network, no keys)
python -m src.live.runner run --mode paper --once      # one hour of the bot with paper money (needs data/live, see deploy/)
```

Backtests need the Binance data in `data/` (`python -m src.data.binance_downloader`, then `python -m src.validation.build`);
then `python -m backtest.run --model pol_switch_vt_tl_e20v45 --score`.

**Deployment on AWS EC2** (Session Manager only, one instance, systemd): `deploy/README.md`. In short: clone into
`/opt/minimax`, run `bash deploy/setup_ec2.sh` (Python 3.11 on Amazon Linux, packages, time sync, seed, service),
check the clock (`python -m src.live.runner clock` must print `RESULT OK`), put the keys in `.env`, start
`minimax-bot`. `live.mode` and `live.model` in `config.yaml` decide what runs; the bot only trades from
`live.start_at`.

## Keys

API keys live only in `.env` on the machine that runs the bot (gitignored, `chmod 600`); `.env.example` shows the
three lines. They are never printed, logged or committed. The competition key is refused anywhere except under the
EC2 service.

## Team process

`AGENTS.md`: every member works in a separate git worktree; a change reaches `main` only after another member's
review; model results are pre-registered before they are scored.
