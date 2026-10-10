# Pre-registration: e20v45 plus a failed-rally short on other coins (Baitoey, 2026-10-10)

Written and committed before any code runs on data; not edited after results; no tuning after results.
Research only; the live bot is frozen. Follows `20261009-btc-short.md` (rule C, add-on design) unchanged except the
coin(s) shorted.

## Variants (all gated by e20v45's switch reading down, as baitoey_e20_btcs_c)

| Model | Coins that may be shorted | Size |
|---|---|---|
| baitoey_e20_shortc_eth | ETHUSDT | 40% |
| baitoey_e20_shortc_sol | SOLUSDT | 40% |
| baitoey_e20_shortc_alts | at each 16:00 UTC decision, the 6 coins of the point-in-time universe with the largest 30-day quote volume, excluding BTCUSDT and ETHUSDT | 10% each, at most 4 open (40%); if more qualify, the larger-volume ones |

Coins are chosen by liquidity, not by recent performance: ETH and SOL are the next most traded after BTC; the basket
is ranked by volume each day (the hand-picked AAVE / WLD / SUI / FIL results of 2026-10-10 are hindsight and not
used). Each coin runs rule C on its own hourly closes: close < its EMA40, close < the mean of its previous 20 daily
closes, a touch of that mean in the previous 72 hours; stop at min(entry x 1.045, bounce high x 1.005); 168-hour time
stop; no new short within 12 hours before CPI / FOMC minutes; 90-day replay; re-arm as before. While shorts are
open, e20v45's book is scaled to at most 1 - (total short) gross. Between daily decisions only the shorts' stops act.
Known approximation: if e20v45's own sleeve holds the same coin long, a stop between decisions may wait for the next
decision.

## Scoring and reading

`backtest.run --model <name> --score2` for each; compared with e20v45 and baitoey_e20_btcs_c. Reported: weak-board
median / p10 / p90 and rank, all-round median / p10 / p90, HEADLINE_RET, REL SCREEN / CONFIRM, gates, fees; per-coin
trade statistics (hit rate, worst trade, squeeze rate +5% and +10% within 72 hours); this round on live prices; and
recovery from our situation (e20v45 within 3 points of -6.6% on day 6, the latest replay figure; last 8 days).

**Better than e20v45** if the weak 228 h median and p10 are both at least e20v45's, REL SCREEN and CONFIRM each at
least e20v45's minus 0.05, and no hard gate fails (the rule of the previous add-ons).
