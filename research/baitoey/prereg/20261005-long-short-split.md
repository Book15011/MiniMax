# Pre-registration: momentum long-short at 60/40 and 50/50 (Baitoey, 2026-10-05)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261005-long-short-split/` and a report committed under `research/baitoey/results/`.

## Question

`pol_mom_ss` (cross-sectional momentum: long the top 5, short the bottom 4 of the 15 most liquid coins) runs at 75%
long / 25% short and scores 0.458 (top-20 proxy 0.195). How does it do at 60/40 (net long 20%, allowed: directional)
and at 50/50 (market-neutral: research only, never live under AGENTS.md)?

## Runs

`pol_mom_ss` with `long_gross` / `short_gross` changed, everything else as in config.yaml; scored with `score_model`
like `--score`, not registered (the leaderboard is untouched). Script: `research/baitoey/long_short_split.py`.

| Run | Long / short | Role |
|---|---|---|
| L75 | 0.75 / 0.25 | the registered `pol_mom_ss` (read from the registry) |
| L60 | 0.60 / 0.40 | candidate (net long 20%) |
| L50 | 0.50 / 0.50 | reference only: market-neutral, never live |

## Verdict (fixed now)

- L60 is a **candidate** only if, with the live lock-in, it beats e20v45 + lock-in by at least 0.03 on HEADLINE_RET and
  is not lower on the top-20 proxy. Otherwise **no candidate**.
- Report-only: L50, hit rates by market type, worst R, the real-round replays, and all numbers next to e20v45.

## Known limits, stated before running

- One setting changed; the post-holdout windows are in the pool and were already seen.
- The round is live; nothing here changes the live bot. The 2026-10-10 freeze applies.
