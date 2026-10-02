# Pre-registration: sensitivity of the launch pick and of pol_mr_cap (2026-10-02, Pol), before any run

**Purpose:** check that the chosen settings sit on a plateau, not a peak, and test two structural questions. This is
**report-only**: no result here changes the launch pick by itself (a neighbour that scores higher was found after
looking, so adopting it would be selection on the same data). Scored with the full harness on tool version
56cb5a2e85d45862, not registered on the leaderboard (`results/pol/20261002-volume/sens.py`, `register=False`).

| Variant | Change (one at a time) | Question |
|---|---|---|
| `pol_sens_ema20` / `ema30` / `ema60` | switch EMA 20 / 30 / 60 days (pick: 40) | Is the switch speed on a plateau? Faster could help at turning points |
| `pol_sens_hys1` / `hys5` | hysteresis 1% / 5% (pick: 3%) | Same, for the band |
| `pol_sens_vol45` / `volnone` | up-state momentum volatility cap 4.5%/day / none (pick: 3%) | Does more risk pay under a top-20 return gate (a convex payoff)? |
| `pol_sens_dncash` | no down-state sleeve: cash out of trend (pick: long/short trend) | Does the short side earn its place? |
| `pol_sens_cap08` / `cap12` / `cap15` | pol_mr_cap entry volume ratio 0.8 / 1.2 / 1.5 (chosen: 1.0) | Is the capitulation filter on a plateau? |

**Reading, fixed now:** a setting is on a plateau if every neighbour is eligible and keeps a best-bar REL within 25%
of the chosen setting's. A neighbour more than 25% below is a **cliff** (flagged as a fragility). A neighbour more
than 25% above is reported as a lead for after the round, not adopted. `dncash` above the pick would mean the short
side costs more than it earns; `volnone` above the pick would support taking more risk; both go to the team as
findings, not changes.
