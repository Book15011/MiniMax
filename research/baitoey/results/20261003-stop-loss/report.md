# A per-coin stop-loss on e20v45? (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-stop-loss.md`. Scored like `--score`, not registered.
Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)
and in the most volatile windows.

| Run | Change | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | none (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass | — |
| C0 | stop 100% (never fires) | **0.547** | -0.022 | 0.497 | 0.400 | 36% | 41% | 56% | 80% | 34% | +1.6% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass | — |
| S5 | stop 5% | **0.529** | -0.039 | 0.467 | 0.388 | 35% | 45% | 49% | 77% | 36% | +0.9% / +4.4% | -25.7% | +2.9% #3/47 · -3.0% #13/16 | +0.77% | pass | worse |
| S10 | stop 10% | **0.526** | -0.042 | 0.483 | 0.406 | 31% | 41% | 52% | 79% | 30% | +1.2% / +4.4% | -31.8% | +3.4% #2/47 · +0.2% #9/16 | +0.57% | pass | worse |

- S5 against C0: changed 95% of rounds (helped 42%, hurt 53%), mean change there -1.13%.
- S10 against C0: changed 72% of rounds (helped 28%, hurt 44%), mean change there -1.23%.
- S5 worse, S10 worse -> **DO NOT PROPOSE**.

Tool version(s): 3036a0d8bfdaa6a0.

Note: the control C0 (the same hourly wrapper with a stop that never fires) scores 0.022 below E0 with almost the same
returns (median, worst, replays and fees unchanged; the gap sits in the post-holdout windows: 0.497 vs 0.501 without
them). Its cause is not investigated here; the verdict does not depend on it, since S5 and S10 are also below C0 and
hurt more rounds than they help against C0.
