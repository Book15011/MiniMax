# Short protection for e20v45: every short model checked, a live data bug, and combined models (2026-10-10, Book)

EXPERIMENTAL and research only. Branch `feature/e20-shortguard`. No live change, no order, no signed call.

| | |
|---|---|
| Question | Keep e20v45 as the return engine for the rest of the round, and add something that shorts if the market drops more |
| Code | `src/models/book/_e20guard.py`, `_e20combo.py` and 11 thin models. Baitoey's overlays are cherry-picked from `feature/mom-ss` (`7c2c017`, her authorship kept). Tests: `tests/test_book_e20guard.py`, `tests/test_book_e20combo.py` |
| Scripts | `research/book/e20guard/`: `guard_live.py` (live round), `guard_regime.py` (the trigger's three conditions), `compare.py` (board rows), `run_score2.sh` |
| Evidence | **Live round:** the paper-live engine, from cash at Oct 4 12:00 UTC to Oct 10 15:00 UTC (BTC −2.7%). **Weak-market board:** `results/scoring/leaderboard_2.csv` (228 h from 25 weak checkpoints like Oct 9, two data profiles). **Full history:** each run's standard report (2,245 windows) |

## Bottom line

1. **Every protective variant costs rebound upside; none dominates e20v45 on all evidence.** The choice is how much
   upside to trade for protection if the market keeps falling.
2. **The component that protects is Baitoey's alt-vs-BTC overlay, not a short.**
   - It moved e20v45's alts to cash at the Oct 7 00:00 HKT decision, ten hours before the plunge.
   - Live round: −2.4% vs −6.1%.
   - Weak-market board: −4.3% vs −10.3% if the market keeps falling.
   - It has a cost in a rebound: +4.1% vs +6.5%, and a slow re-entry.
3. **The short leg adds money only if the drop repeats.**
   - Added to the overlay: Oct 7 again +1.2% (vs −4.7%).
   - It cost 0.3 points in the Oct 8–10 bounce.
   - Alone on e20v45, funded by trimming longs, it barely changes e20v45 on history. Live it cut the round's max drawdown
     by 2.5 points (confirm_r).
4. **A live data bug blocks the cash-short trigger this round** (§2). Only the `_r` versions can short before Oct 11
   08:00 UTC.
5. **Candidates for the team:**

| If the priority is | Model | Live round | Oct 7 again | Full history: median / bad 10% / best 10% / worst |
|---|---|---|---|---|
| Keep every bit of rebound upside | e20v45 (no change) | −6.14% | −4.74% | +0.09% / −12.1% / **+23.3%** / −26.6% |
| **Middle: half protection, most of the upside** | **`book_e20combo_alt_half_cash`** | **−4.46%** | **−1.16%** | −0.18% / −9.5% / +18.9% / **−21.8%** |
| Stop further losses, earn a little if it drops | `book_e20combo_alt_cash` | **−2.69%** | **+1.21%** | −0.41% / **−8.9%** / +15.0% / −22.9% |

   **Book's pick, pending the board rows:** the middle option.
   - It halves the loss if Oct 7 repeats, keeps about 80% of e20v45's best-decile upside, and has the best worst case.
   - When alts are not lagging BTC it is exactly e20v45. So it is an integration, not a change of strategy.
   - **Switching would trade 69% of the book (about 0.10%).**

## 1. Every short model we have researched

The weak-market board scores **99 models**. **71 of them actually open shorts** in its tests.

| Group | Examples | Weak-market result | Reading |
|---|---|---|---|
| Stand-alone shorts (Book) | `book_short_*`, `book_bear_*` (13) | Mean −0.5% to +0.4%; all FAIL in `leaderboard_short_ranked.md` | Positions too small to protect anything |
| e20v45 + coin shorts (Baitoey) | `baitoey_e20_shortc_*`, `baitoey_e20_btcs_*` | If it keeps falling: −6.8% to −10.9% (e20v45 −10.3%) | They short only in e20v45's own down mode. This round: never |
| Fast large-cap trend L/S (Baitoey) | `baitoey_mjt_*` (6) | Positive this round, 0.30–0.35 on full history | They lower the chance of finishing at +1% or better |
| e20v45 switch variants (Pol) | lower down trigger, dual filter, `baitoey_e20_out10/15` | Fail their pre-registered full-history checks | Better tails, less upside |
| Permanent short sleeves | `pol_mom_ss`, `baitoey_tg_mom`, `pol_trend_ls` | If falling −1.2% / +0.5% / −3.1%; if rebound only +1.9% / +0.4% / +0.9% | They protect but give up most of a rebound |
| **e20v45 overlays (Baitoey)** | `baitoey_ovl_altbtc_b_e20` (alts to cash when they lag BTC), `baitoey_ovl_brk_e20` | altbtc_b: if falling −4.3%, if rebound +4.1% | The best e20v45-based protection on the board |
| **Dual momentum (+ cash shorts)** | `baitoey_ovl_brk_dual` (#1), `book_cashshort_pullback` (#3) | Mean +2.8–2.9%; if falling −3.3 to −3.5%; if rebound +6.6–6.7% | Better than e20v45 on every column in weak markets |

**Not run on this board yet:** Pol's `pol_ext_*` baselines, his band and dual variants (they have full-history results, all fail), and Baitoey's `baitoey_{fastswitch,hour,stop,vexit}_e20v45`.

## 2. A live data bug: the cash-short trigger cannot fire this round

**The trigger** (`src/models/book/_cashshort.py`) needs all three:
- BTC below its 20-day EMA;
- BTC's 7-day return below 0;
- at most 40% of the 30 most liquid coins up over 48 h ("breadth").

**What breaks it.** Breadth drops any coin with a single missing hour of quote volume in the last 168 h. The H1 shadow store (`results/book/shadow/h1`, the live runner's bars) has **one 8-hour gap, Oct 4 01:00–08:00 UTC, in 75 of 90 coins**. That leaves 14 of the 29 live coins, against the 20 required, so breadth is undefined at every hour of the round and the trigger stays off.

**Who it affects.** `book_cashshort_pullback`/`confirm` (board #3–4) and anything else using `liquid_breadth` live. Their board results assume complete historical data.

**When it clears.** The gap leaves the 168 h window on **Oct 11 08:00 UTC**. Whether the EC2 bot's own store has the same gap is UNVERIFIED.

**The fix (the `_r` variants).** The short leg's view carries volume forward over gaps of at most 12 h; the long side keeps the raw view. It is identical on complete data. With it, all three conditions held at the Oct 8, 9 and 10 decisions (breadth 10%, 0%, 7%). Breadth is back to 55% now.

## 3. What was built

| Model | Long side | Short leg (cash-short rules, cap 25%, `_r` volume fill) |
|---|---|---|
| `book_e20guard_confirm_r` / `pullback_r` | e20v45, unchanged | Funded by trimming e20v45's longs |
| `book_e20combo_alt_cash` (`_pb`: pullback filter) | e20v45 + alts to cash when the alt basket's 10-day return is below BTC's | Funded only by unused cash |
| `book_e20combo_alt_trim` | same | Funded by trimming if there is no cash |
| `book_e20combo_alt_half_cash` | Half e20v45, half the alt book: half the alts go to cash when they lag | Unused cash |
| `book_e20combo_brk_cash` | e20v45 + Baitoey's breakdown exits | Unused cash |

**Rules common to all:**
- The short leg never shorts a coin the long side holds.
- It is off while e20v45 is in its own long/short mode.
- Gross stays at or below 1.
- e20v45 only reads which coins it held long before, so its own decisions are unchanged.

## 4. Live round (paper-live engine, Oct 4 12:00 → Oct 10 15:00 UTC)

"Oct 7 again" marks each model's current book with each coin's actual move from Oct 7 01:00 to Oct 8 06:00 UTC (BTC −3.3%, median coin −5.9%). "Switch" means trading from e20v45's current paper book at 0.15% of the weight traded.

| Model | Round | Max DD | Book now | Oct 7 again | Switch traded / cost |
|---|---|---|---|---|---|
| e20v45 (live) | −6.14% | −16.9% | 96% long | −4.74% | – |
| `book_e20guard_confirm_r` | −6.54% | −14.4% | 76% long, 20% short | −2.56% | 40% / 0.06% |
| `book_e20guard_pullback_r` | −7.80% | −16.7% | 76% long, 20% short | −2.56% | 40% / 0.06% |
| `baitoey_ovl_altbtc_b_e20` | −2.37% | −4.0% | cash | 0.00% | 96% / 0.14% |
| **`book_e20combo_alt_cash`** | **−2.69%** | **−4.3%** | **21% short** (UNI, XPL, ETH) | **+1.21%** | 117% / 0.18% |
| `book_e20combo_alt_cash_pb` | −2.85% | −4.4% | 21% short | +1.21% | 117% / 0.18% |
| **`book_e20combo_alt_half_cash`** | **−4.46%** | **−9.6%** | **48% long, 21% short** | **−1.16%** | 69% / 0.10% |
| `book_e20combo_brk_cash` | −6.20% | −16.9% | 96% long, 4% short | −4.52% | 7% / 0.01% |
| `baitoey_ovl_brk_dual` / `book_cashshort_pullback` | −6.52% | −11.7% | 50% long | −2.75% | 53% / 0.08% |
| `baitoey_ovl_altbtc_b_dual` | −1.69% | −2.9% | cash | 0.00% | 96% / 0.14% |

**Reading:**
- **The alt-vs-BTC overlay is what saved money this round.** It moved e20v45's alts to cash at the **Oct 7 00:00 HKT** decision, ten hours before the plunge.
- **The short legs opened near the bottom** (Oct 8–10) and lost 0.3–0.4 points in the bounce. They are what makes money if the drop repeats.
- **Re-entry is slow.** The alt book returns only when the alt basket's 10-day return beats BTC's: now −4.6% vs −1.0%, a 3.6-point gap. A fast rebound would be partly missed; the half version keeps half of it.

## 5. Scores (weak-market board and full history)

**Full history** (each run's standard report; 14-day windows from cash at 00:00 HKT):

| Model | ALL (2,245): median / bad 10% / best 10% / worst / share > 0 | LOOKALIKE25: median / best 10% | RECENT25: median / best 10% |
|---|---|---|---|
| e20v45 | +0.09% / −12.08% / +23.25% / −26.57% / 50% | −2.32% / +21.76% | +1.16% / +9.29% |
| `book_e20guard_pullback` | +0.06% / −12.04% / +23.25% / −25.06% / 50% | −2.32% / +21.76% | +1.16% / +9.14% |
| `book_e20combo_alt_cash` | −0.41% / −8.89% / +14.95% / −22.85% / 47% | −3.38% / +6.87% | −1.25% / +1.60% |
| `book_e20combo_alt_cash_pb` | −0.46% / −8.61% / +14.95% / −22.92% / 47% | −3.38% / +6.87% | −1.19% / +1.29% |
| `book_e20combo_alt_half_cash` | −0.18% / −9.54% / +18.92% / −21.83% / 49% | −3.72% / +12.46% | −0.12% / +4.45% |

**Weak-market board** (`leaderboard_2.csv`: next 228 h from weak checkpoints like Oct 9):

| Model | Rank | Mean | Median | Bad 10% | Worst | If it keeps falling | If it rebounds |
|---|---|---|---|---|---|---|---|
| e20v45 | 42 | +0.74% | −2.88% | −11.75% | −15.20% | −10.26% | +6.52% |
| `book_e20guard_pullback` | 41 | +0.56% | −2.88% | −11.75% | −15.11% | −10.07% | +6.24% |
| `baitoey_ovl_altbtc_b_e20` | 21 | +0.66% | −0.89% | −10.38% | −12.14% | −4.34% | +4.13% |
| `baitoey_ovl_brk_e20` | 35 | +1.06% | −2.88% | −11.23% | −13.38% | −9.14% | +6.49% |
| `book_cashshort_pullback` | 3 | +2.76% | +3.18% | −8.35% | −15.67% | −3.50% | +6.56% |
| `baitoey_ovl_brk_dual` | 1 | +2.94% | +3.63% | −8.35% | −15.67% | −3.27% | +6.73% |
| `pol_mom_ss` | 47 | +0.58% | −0.39% | −5.94% | −6.55% | −1.18% | +1.89% |
| `book_e20combo_*`, `book_e20guard_confirm` | PENDING (score2 runs in tmux `mm-book-e20q1..3`; rows added in a follow-up commit) | | | | | | |

**Reading:**
- **On full history, every alt-overlay combo gives up upside.** Best-decile 14-day return falls from +23% to +15–19%
  for a 3–5-point better worst case.
- **On the weak-market board the dual family leads every column.** Live, its long side lost as much as e20v45
  (−6.5%), and its shorts were blocked by the §2 bug.

## 6. Before anything goes live (team decision)
1. **Shorts have never been tested on the competition account.** The live runner launched with "shorts not needed". A small manual short order is needed first.
2. **Check the EC2 bot's store for the Oct 4 volume gap.** If present, only the `_r` versions can short before Oct 11 08:00 UTC.
3. **The board's stronger replacement-evidence checks pass for no model,** these included. Its numbers come from 25 historical cases.
4. **A switch trades from the live book** (costs above) and is a team decision.
