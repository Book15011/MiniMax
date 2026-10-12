# Amendment 1: the baseline is the model now live, from the account's real loss

Written 2026-10-12 06:15 UTC. This amends `20261012-short-models-rest-of-round.md` (3c5bdd8) before any result against the new baselines was computed.

**Why.** The team reports that the live bot switched on 2026-10-11, and that the account now stands at -3.8%. The test asked against e20v45 (328437e) used the wrong baseline and a replay estimate of the loss.

## What changes

**Baseline.** The primary baseline is `book_e20combo_brk_cash`: `config.yaml` on `feature/launch-brk-cash` says "LIVE from 2026-10-11 (team decision)". The team described the live model as the alt-coin half-cash combo, so the same test is also run with `book_e20combo_alt_half_cash` as the baseline. The EC2 configuration itself is UNVERIFIED.

**Starting state.** Round hour 186 (2026-10-12 06:00 UTC), with 150 hours left. The account is at **-3.8%** (team-reported). BTC is at -1.53% since the round start.

**Similar past rounds.** At hour 186, the baseline's own return is within 3 points of -3.8%, and BTC's is within 3 points of -1.53%.

**Comparison.** Per round, d = R(model) - R(baseline). Every model except the baseline pays the 0.20% switching cost; e20v45 is now a challenger.

**Final account.** (1 - 3.8%)(1 + R) - 1.

## What stays the same

The primary sample, the excluded models, the outcome, the bootstrap, the four "better" conditions and the context items are all as in the original pre-registration. k is the number of models tested against the baseline.

## Caveat

The e20v45-baseline results (328437e) were already seen. This amendment changes only the facts of the starting state and the baseline. No threshold, sample rule or decision rule changes.
