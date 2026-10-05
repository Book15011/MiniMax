# Pre-registration: after the lock-in fires, switch to another strategy instead of cash? (Baitoey, 2026-10-05)

Written and committed before any run. Not edited after results exist; results go to `results/baitoey/20261005-after-lock/`
and a report committed under `research/baitoey/results/`.

## Question

The live lock-in (from day 10, once equity is +3% on the round start, sell everything and hold cash) adds +0.040
HEADLINE_RET and lifts CS_HIT 0.384 -> 0.470 for e20v45. Would running a calmer strategy for the rest of the round,
instead of cash, do better?

## Method

On the cached v2 paths (2,298 windows; the unmodified e20v45 path must reproduce its score file): at the hour the
lock exits (as live: the hour after equity first reaches +3% from day 10, 0.13% on the gross sold), the account
either holds cash (L0) or buys into an alternative at that hour (0.13% on its gross) and follows that model's hourly
path in the same window, scaled to the account, to the end. Scored by the method of Pol's endgame2.py: HEADLINE_RET,
CS_HIT, Pol's ~150-team cut (top-20 proxy), mean and worst R_liq. Script: `research/baitoey/after_lock.py`.

| Run | After the lock fires |
|---|---|
| L0 | cash (as launched) |
| AMR | pol_mr_cap (mean reversion, low exposure) |
| ATR | team_trend_2 (BTC/ETH trend, low exposure) |
| AHALF | keep half in e20v45, sell the other half |

## Verdict (fixed now)

An alternative is **better** if HEADLINE_RET >= L0 + 0.03, or HEADLINE_RET >= L0 - 0.01 with CS_HIT at least 0.02
higher or the worst round at least 2 points better; and its top-20 proxy is not lower than L0. **Propose** an
alternative only if it is better; if several are, report all. Otherwise **keep cash after the lock**.

## Known limits, stated before running

- The alternative's path is its own run from the window start; joining it mid-window assumes we can buy its holdings
  at that hour (approximation; the entry cost is charged).
- The post-holdout windows are in the pool and were already seen. The round is live; nothing here changes the bot.
