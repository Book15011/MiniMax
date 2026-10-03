# e20v45 switch read from altcoins or the momentum basket (scoring v2)

Pre-registration: `research/baitoey/prereg/20261004-alt-switch.md`. Scored like `--score`, not registered. Type
columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the
most volatile windows.

| Run | Switch | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | BTC (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| A15 | alts, EMA 15 d | **0.468** | -0.101 | 0.366 | 0.409 | 32% | 34% | 43% | 75% | 33% | -0.5% / +3.2% | -26.2% | -1.3% #20/47 · +12.4% #2/16 | +0.59% | pass |
| A20 | alts, EMA 20 d | **0.478** | -0.090 | 0.380 | 0.378 | 32% | 35% | 44% | 77% | 34% | -0.3% / +3.1% | -28.2% | -1.3% #20/47 · +12.4% #2/16 | +0.58% | pass |
| A25 | alts, EMA 25 d | **0.462** | -0.106 | 0.358 | 0.414 | 21% | 35% | 45% | 77% | 35% | -0.8% / +3.2% | -26.6% | -1.3% #20/47 · +12.4% #2/16 | +0.56% | pass |
| M15 | momentum, EMA 15 d | **0.521** | -0.047 | 0.450 | 0.392 | 28% | 35% | 57% | 81% | 35% | +0.6% / +4.4% | -28.2% | -2.4% #25/47 · +12.4% #2/16 | +0.58% | pass |
| M20 | momentum, EMA 20 d | **0.550** | -0.019 | 0.467 | 0.399 | 28% | 45% | 60% | 78% | 37% | +1.6% / +4.5% | -27.3% | -2.4% #25/47 · +12.4% #2/16 | +0.57% | pass |
| M25 | momentum, EMA 25 d | **0.556** | -0.012 | 0.474 | 0.393 | 30% | 47% | 59% | 77% | 35% | +2.1% / +4.5% | -34.0% | -2.4% #25/47 · +12.4% #2/16 | +0.56% | pass |
| AB | both, EMA 20 d | **0.494** | -0.074 | 0.407 | 0.371 | 41% | 36% | 47% | 73% | 34% | +0.3% / +3.4% | -23.6% | -1.3% #20/47 · +0.2% #9/16 | +0.59% | pass |

- altcoin index: A20 not better than E0; neighbours do not hold -> **KEEP THE BTC SWITCH**.
- momentum basket: M20 not better than E0; neighbours do not hold -> **KEEP THE BTC SWITCH**.

Tool version(s): 3036a0d8bfdaa6a0.
