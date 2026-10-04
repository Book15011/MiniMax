# Pre-registration: skim profits to cash and keep trading only the original money (Baitoey, 2026-10-05)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261005-profit-skim/` and a report committed under `research/baitoey/results/`.

## Question

Whenever the account is up X% on the round's starting money, sell the profit above the starting money to cash and keep
trading only the starting money. Does it beat e20v45 as launched (with the lock-in)?

## Method

On e20v45's cached v2 equity paths (2,298 windows; the unmodified path must reproduce the score file), hour by hour:
the strategy's return applies to the invested part I only; cash C is never reinvested. Whenever I >= 1 + X (start = 1),
the excess I - 1 moves to cash at the next hour at fee + half-spread (0.13%) on the amount moved, and I = 1. If I falls
below 1 there is no top-up. Equity = I + C; gross = the model's gross x I / equity. The live lock-in (+3% from day 10,
all to cash) is applied on top where stated. Scored by the method of Pol's endgame2.py: HEADLINE_RET, CS_HIT (V1
FLOORED composite), Pol's ~150-team cut (top-20 proxy), mean and worst R_liq. Script: `research/baitoey/profit_skim.py`.

| Run | Rule |
|---|---|
| L0 | e20v45 + lock-in (as launched) |
| S2 / S3 / S5 | skim at +2% / +3% / +5%, plus the lock-in |
| N3 | skim at +3%, no lock-in (report-only) |

## Verdict (fixed now)

- **Propose** only if S2, S3 and S5 all score HEADLINE_RET >= L0 + 0.03 and a top-20 proxy >= L0's (no picking the
  threshold). Otherwise **keep the strategy as launched**.
- Report-only: N3, CS_HIT, mean and worst R, how often the skim fires.

## Known limits, stated before running

- The skim is applied to the stored hourly paths: it assumes the invested part keeps the model's hourly returns at a
  smaller size, which holds for a proportional cut of every coin.
- The idea came from looking at the same history; the three thresholds limit picking.
- The round is live; nothing here changes the live bot. A change would be live code (Pol) and the team rule for
  upgrades before the 2026-10-10 freeze.
