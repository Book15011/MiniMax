# Mid-round switch from e20v45: STAY under the pre-registered rule (2026-10-04, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261004-prereg-midround-switch.md` (`509608a`), committed before computing |
| Script, output | `results/book/20261004-midround-switch/switch.py`, `switch.json` (not committed) |
| Scope | Report-only. Nothing registered, switched or deployed; the live bot, its config and EC2 are untouched |

**The question.** The live bot started the round at 20:00 HKT with e20v45 and holds its coins. Every earlier score
starts a model from cash for 14 days. Here, e20v45 runs for k days, then X takes over **from e20v45's holdings**
(the runner keeps the coins and trades only the difference) for the remaining 14 − k days. That is compared with
staying with e20v45, over 2,291 to 2,297 past rounds.

**The result.** Under the pre-registered rule, the label is **STAY WITH e20v45** for every X and every k.

**Why it is not a clean "stay":**
- In rounds where the market at the switch looks like today (e20v45's BTC switch up and breadth ≥ 0.60, about 850
  rounds), switching on day 1 or 2 to `pol_abl_shock`, vt_mom or H1 **raised HEADLINE_RET by about +0.06, and the
  90% interval excludes zero.**
- Each one fails the risk part of the rule: **the worst round gets deeper** than e20v45's (−26.2%), because e20v45
  moves to its long/short trend sleeve in a downturn while these stay long.

## 1. Switch on day 1 or day 2 (the realistic case)

- **(b) like now** = rounds whose state at the switch matches this round's start.
- **(a) all** = every round.
- Differences are HEADLINE_RET, switch minus stay, with the 90% month-block bootstrap interval.

| Switch to | Day | (b) like now: switch vs stay | (a) all: switch vs stay | Worst R, switch / stay | 5th pct R, switch / stay | Cost | Fails |
|---|---|---|---|---|---|---|---|
| pol_abl_shock | 1 | 0.651 vs 0.591, **+0.060 [+0.005, +0.129] ahead** | 0.581 vs 0.566, +0.016, tied | −28.5% / −26.2% | −16.2% / −15.4% | 0.09% | worst R 2.3 pp deeper (limit 2) |
| vt_mom | 1 | 0.655 vs 0.591, **+0.064 ahead** | +0.014, tied | −32.4% / −26.2% | −15.8% / −15.4% | 0.09% | worst R 6.2 pp deeper |
| H1 | 1 | 0.653 vs 0.591, **+0.062 ahead** | +0.029, tied | −31.6% / −26.2% | −15.1% / −15.4% | 0.09% | worst R 5.4 pp deeper |
| pol_abl_shock | 2 | 0.664 vs 0.598, **+0.066 [+0.021, +0.120] ahead** | 0.584 vs 0.563, +0.022, tied | **−27.3% / −26.2%** | −16.6% / −15.4% | 0.10% | 5th pct 1.2 pp deeper (limit 1) |
| vt_mom | 2 | 0.664 vs 0.598, **+0.066 ahead** | +0.018, tied | −31.3% / −26.2% | −15.8% / −15.4% | 0.10% | worst R 5.1 pp deeper |
| H1 | 2 | 0.663 vs 0.598, **+0.065 ahead** | **+0.039 [+0.010, +0.072] ahead** | −30.5% / −26.2% | −15.3% / −15.4% | 0.09% | worst R 4.3 pp deeper |

**With the live lock-in on**, report-only, view (b), day 1:
- `pol_abl_shock`: 0.677 vs 0.617 for stay;
- H1: 0.677;
- vt_mom: 0.683.

## 2. Later switch days (k = 3, 5, 7)
- **Day 3 and day 5:** in view (b), all three are still ahead by +0.04 to +0.06 (`pol_abl_shock` on day 3 is only
  tied), and H1 is also ahead in (a). In view (a) the worst round is deeper, by 2.2 pp (`pol_abl_shock`, day 3) to
  6.2 pp (vt_mom, day 3). That fails the rule.
- **Day 7:** every switch is only tied with staying. Half the round is gone, so a switch then changes little.

## 3. What the numbers say
- **Gain:** a switch to the momentum family in an up, broad market adds hits (more rounds above the bars). Mean R moves
  much less (view b: +0.1 to +0.6 pp), and the switch ends higher than staying in only 43–49% of rounds. The gain is
  mostly that more rounds finish just above the bars.
- **Cost of trading:** small. About 0.07–0.10% of equity, and less today because every model holds the same 6 coins.
- **Price:** tail risk. In the worst rounds e20v45's switch to its trend sleeve protects better than staying long.
  Of the three, `pol_abl_shock` gives up the least (its crash rule), and only by 1.1 to 2.3 pp.

**Suggestion (only):**
- Keep e20v45. By the rule fixed before computing, no switch is worth it.
- If the team still wants a switch for the higher hit rate in today's market, the least risky candidate is
  `pol_abl_shock` on day 1 or 2. It misses the risk limits by 0.2 to 0.3 pp.
- Watch the live paper comparison (`results/book/paper-live/latest.md`, updated hourly) before any decision.

## 4. Caveats (UNVERIFIED)
- **View (b) is the state at the switch, not a forecast.** The 14-day direction is not predictable.
- **The rounds overlap:** 850 rounds is about 60 distinct 14-day periods. The month-block bootstrap allows for that
  only in part.
- **The path is a composite:** e20v45's path to the switch, then X's own window from the switch, with X's entry cost
  replaced by the switch's own cost. In the switch hour itself, the switched account still holds e20v45's coins; the
  composite does not count that hour's return.
- **The most recent rounds drop out.** The last k rounds are excluded, and they carry the largest recency weights.
  That is why "stay" reads 0.566 here instead of 0.568.
- **In-sample.** These are the same 2,298 windows the models were chosen on.
