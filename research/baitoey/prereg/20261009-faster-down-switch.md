# Pre-registration: a faster down switch for pol_switch_vt_tl_e20v45 (Baitoey, 2026-10-09)

Written and committed before any code runs on data; not edited after results; no tuning after results.
Exploratory research for the team; nothing here changes the live bot.

## The change (Baitoey's question)

e20v45 is in its up state (vt_mom sleeve) after a 6-hourly BTC close above its 20-day EMA x 1.03 and in its down
state (pol_trend_ls sleeve) after one below EMA x 0.97; between the two it keeps its state. The variants change only
the down trigger: below EMA x 0.99 (**out10**) or EMA x 0.985 (**out15**). The up trigger stays at x 1.03. Everything
else is e20v45 as registered.

| Model | Up trigger | Down trigger |
|---|---|---|
| pol_switch_vt_tl_e20v45 (base) | +3% | -3% |
| baitoey_e20_out10 | +3% | -1% |
| baitoey_e20_out15 | +3% | -1.5% |

Context known before running: BTC closed 1.5% below its 20-day EMA on 2026-10-08 20:00 UTC (both variants would be in
the down state now); the base's switch has not fired. Pol's 2026-10-02 sensitivity check included a symmetric 1% band
and kept 3% (its results file was not located; UNVERIFIED).

## Scoring and reading (as research/baitoey/prereg/20261009-overlays.md)

`backtest.run --model <name> --score2` (Book's weak-market board, protocol 603da2948b68ee0f5c8a). Reported: weak-case
median / p10 / p90 at 216 / 228 / 240 h, board rank; REL SCREEN / CONFIRM and HEADLINE_RET; gates G1-G6; turnover
and fees; and, from our situation, e20v45 for the first 5 days then the variant for the last 9 (the 125 rounds where
e20v45 was down 5.4-11.4% on day 5 with BTC 0 to -6%): our total's p10 / median / p90 and the share at +1% or better.

**Better than the base** if: archived 228 h median and p10 both at least the base's; REL SCREEN and CONFIRM each at
least the base's minus 0.05; no hard gate fails that the base passes. Otherwise not better.

## Known limits

The idea was raised during a falling market, with the trigger already known to have fired; the history is spent
research, not a holdout. The weak cases are 25 per profile.
