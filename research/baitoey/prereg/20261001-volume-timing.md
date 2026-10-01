# Pre-registration: volume-confirmed timing on top of momentum (Baitoey, 2026-10-01)

Written and committed before any run of these variants. Not edited after results exist; results go to
`results/baitoey/20261001-vt-study/` and a separate report.

## Question

Does volume-confirmed entry and exit timing add net return on top of momentum rotation, and at which rebalance
interval (1, 4 or 24 hours)?

## Variants

Code: `src/models/baitoey/baitoey_breakout.py` (A), `src/models/baitoey/baitoey_vt_mom.py` (B0, B, C), signals in
`src/models/baitoey/_volume_signals.py`. Parameters: `config.yaml` → `models: baitoey_breakout / baitoey_vt_mom`.

| Variant | Rule |
|---|---|
| A breakout | Enter when close > 72 h high AND 24 h volume ratio > 1.5; exit when close < 24 h low OR below a 2 × ATR trailing stop |
| B0 core (control, added) | The momentum core alone, so the effect of B and C’s timing can be separated from the core |
| B early exit | Core + skip a coin for 24 h after a close < 24 h low on volume ratio > 1.5 |
| C no chase | B + skip a coin after a 24 h return > 15% on volume ratio > 3 until it pulls back 5% |

## Definitions (hourly closes and quote volume only: the view has no OHLC)

- **Volume ratio** R24(t) = quote volume of the last 24 h / (quote volume of the last 7 days × 24/168). A missing
  volume in either window makes R24 missing, and every condition on it is then false.
- **72 h high / 24 h low** = highest / lowest hourly close of the previous 72 / 24 hours, excluding the current hour.
- **ATR** = mean, over the last 14 consecutive 24-hour blocks ending now, of each block’s range of hourly closes
  widened to the previous block’s last close. **Trailing stop** = highest close of the last 72 h − 2 × ATR. The view
  carries no entry time, so the stop trails the 72 h high (a Chandelier-style stop), not the high since entry.
- **A sizing:** held = previous holdings not exited; free slots (k = 6) filled by new entries in order of 7/14-day
  risk-adjusted momentum (the ROT_EW score). Each slot 1/6 of the book; the book is scaled down to ≤ 3%/day estimated
  volatility (30-day hourly covariance × 24).
- **Momentum core (B0):** `team_rot_ew`’s `rotation_targets` with lookbacks 7 and 14 days (ROT_EW uses 3, 7, 14):
  top 6 of the day’s universe, kept while in the top 12, equal weights, book ≤ 3%/day.
- **B:** a coin is removed before ranking (the next coin takes the slot) for 24 h after any hour with close < 24 h low
  AND R24 > 1.5.
- **C:** B, plus a coin is removed while, within the last 72 h, it had a 24 h return > 15% AND R24 > 3, until its close
  is at least 5% below its highest close since the latest such spike.
- Universe: the harness point-in-time universe (top 30 by volume, Roostoo-listed). Long only. Band 5 points (as
  ROT_EW). Fees, spread, 1 h lag, activity guard and keep-alive trade: harness defaults (tool version `ce40153`).

## Grid

Each of A, B0, B, C at `rebalance_every_hours` ∈ {1, 4, 24}: 12 runs. No other parameter is varied.

## The only tuning: choosing the interval, on SCREEN only

SCREEN = windows starting 2022-07-01 … 2024-06-30 (16:00 UTC). For each variant, its three intervals are ranked on
four SCREEN scores (higher is better): median 14-day return R, worst-10% R, share of windows with R > 0, median V1
FLOORED composite. Lowest mean rank wins; a tie goes to the lower turnover. Phase 1 (`python -m
research.baitoey.vt_study screen`) prints only SCREEN numbers and writes the choice to `choice.json`.

## The one CONFIRM look

Phase 2 (`... vt_study confirm`) runs only after `choice.json` exists, and only once. For all 12 runs it reports:
median R and worst-10% R on SCREEN and CONFIRM (windows from 2024-07-01), REL (HEADLINE REL FLOORED), gates G1–G6,
turnover per day, exchange fees and spread as % of equity per window, max orders per decision, and `compare` against
`team_rot_ew` (paired REL CS difference, 90% block-bootstrap interval, blocks of 56). REL leans on 2025–26 windows
through the live-like and recency weights, so it is part of this CONFIRM look and is not used for any choice.
Report-only robustness for the four chosen runs: REL of the live-like layer, the recency layer and the flat mean.
No parameter or rule changes after phase 2. The holdout stays sealed.

## Known limits, stated before running

- Highs, lows and ATR come from hourly closes (no OHLC in the view; `feature/contracts-view-fields` would add it).
- Live volume: the live feed (`feature/live-runner`, `src/live/feed.py`) has exact hourly volume only if Binance REST
  is reachable from EC2 (UNVERIFIED; it is blocked on this server). Otherwise the newest ~1–2 days come from the
  next-day archive and from Roostoo prices with no volume, and every volume condition here is silently false.
  Roostoo’s ticker carries a 24 h `UnitTradeValue`, probably Roostoo’s own volume rather than Binance’s (UNVERIFIED).
- Universe = coins Roostoo lists today (survivorship; flatters momentum).
- B0 is close to ROT_EW by design, so `compare` against ROT_EW mostly measures the lookback change plus the timing.
