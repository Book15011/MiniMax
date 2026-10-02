# Real-market checks, API facts and the launch pick (2026-10-01 evening, Pol)

| | |
|---|---|
| Branch | `feature/realtest` (`.worktrees/pol-realtest`), on Book's `feature/bar-clock-fix` (which stacks on everything before it) |
| Pre-registration | `reports/review/20261001-prereg-realtest.md`, commit `5b3324b`, before anything below was run |
| Scoring version | `56cb5a2e85d45862`: Book's clock-time engine and guard, spreads from the 2026-09-28 snapshot |
| Raw results | `results/pol/20261001-final/`: `bars2_table.csv`, `holdout_table.csv`, `past_leaderboards_numeric.csv` (numbers only), the scripts |

## 1. Summary

1. **The pre-registered rule picks `pol_switch_vt_tl`.** It holds Baitoey's volume-timed momentum (`baitoey_vt_mom`) while BTC trends up, and Pol's long/short trend (`pol_trend_ls`) otherwise.
   - It is eligible and robust, and in the top three under all four bars.
   - It is consistent across periods: SCREEN 1.57, CONFIRM 2.00.
   - It had the best risk profile in the sealed holdout: median +12.7%, worst −4.0%.
2. **Its weak spot is turning points.** In a replay of the previous edition's real competition windows it ranked #27–29 of ~50 and #13 of 16. Every trend switch lags when the market turns, and both real windows were turns.
3. **The previous pick, `baitoey_mr_4h`, no longer qualifies:**
   - it fails G6 by 0.06 pp on Book's engine;
   - it is weak in the holdout (median +1.2%);
   - it ranked #45 of 47 in the real falling round.

   Mean reversion is a calm-market specialist.
4. **Real data moved several assumptions** (section 2):
   - the round starts **Oct 4 12:00 UTC**;
   - the real top-20 cut sat between our two bars;
   - the API's short and order formats differed from what the bot read (fixed).

## 2. Facts from the organizers and the API

| Fact | Value | Source |
|---|---|---|
| Our round | Roostoo competition **538, "APAC Quant Trading Hackathon"**: **2026-10-04 12:00 UTC → 2026-10-18 12:00 UTC** (20:00 HKT), $100,000, taker 0.1% / maker 0.05%, no leverage | `GET /v1/competition_list` |
| Test trading | Opened 2026-10-01 12:00 UTC. The test key signs correctly, but the **test wallet is empty** (balance: 0 entries at 15:07 UTC; `exchangeInfo` says new wallets get $50,000) | self-check `reports/selfcheck/20261001-1507.md` |
| Pairs | 88 listed, all tradable. The 23 not in our config: **21 tokenized stocks** (NVDAB, TSLAB, GOOGLB, MSTRB, …), TON and OMNI (no quotes). Stock tokens have Binance history only from 2026-06-11 | `exchangeInfo`, `ticker`, data.binance.vision |
| Market data | Other data APIs allowed (Q16). Roostoo's prices are Binance's stream (Q17). Roostoo has no OHLCV (Q18). If Binance is blocked, use Roostoo's ticker or Binance's archive (Q43): our feed does exactly that | Official FAQ, Data Sources Pack |
| EC2 | Session Manager only, no SSH (Q12); one instance (Q14) | Official FAQ |
| Changes | Allowed if committed; **manual stops and overrides are prohibited** (Q28); the system liquidates at the end (Q29) | Official FAQ |
| Activity | One trade per day counts (Book, from the organizers) | `docs/EVALUATION.md` |
| API formats | balance → `Wallet`; `/v6/short_positions` → `ShortQty`, `EntryPrice`, `Collateral`, `PositionStatus`; short_open replies `Status: OPEN`; short_close replies `ClosedQty` (no status) | roostoo/Roostoo-API-Documents |

## 3. The real bar: the previous edition's leaderboard

Source: `GET /v1/leader_board`, final returns only. The entries carry names and emails, which were neither kept nor printed.

| Round | Ranked teams | #1 | #5 | #10 | #20 | Median | Teams positive | Traded / capital (median, top 20) |
|---|---|---|---|---|---|---|---|---|
| Round 1 HK, Mar 21–31 | 47 | +6.8% | +0.8% | +0.0% | −1.4% | −2.4% | 21% | 7.1×, 3.1× |
| Round 1 SG, Mar 21–31 | 55 | +10.8% | +0.9% | −0.2% | −1.6% | −2.8% | 11% | 14.0×, 4.3× |
| Final, Apr 4–14 | 16 | +20.5% | +4.6% | −0.8% | — | −0.2% | 50% | — |

- **In a falling week, the real top-20 cut was −1.4%.** That is between our median bar (0%) and our field-best bar (+1.3%, set by MOM-SS that week), so the launch rule now ranks by the mean rank across four bars.
- **Top teams traded less than the rest.** Our models trade about 2.6× their capital per 10 days, in the top-20 range.

## 4. Real-competition replay

Each model ran the previous edition's exact windows from cash, with decisions made only from data up to each decision, then ranked among the real teams.

| Model | Round 1 (BTC −7%) | Rank (HK / SG) | Final (BTC +5.6%) | Rank (of 16) |
|---|---|---|---|---|
| pol_mom_ss | +1.29% | #4 / #5 | +3.46% | #6 |
| pol_trend_ls | +0.88% | #4 / #6 | −2.46% | #13 |
| team_cash | 0.00% | #12 / #8 | +0.02% | #9 |
| baitoey_vt_mom | −1.72% | #21 / #22 | +4.02% | #6 |
| **pol_switch_vt_tl** | −2.64% | #29 / #27 | −2.23% | #13 |
| team_rot_ew | −3.41% | #34 / #31 | +6.92% | #3 |
| pol_switch_rmax_tl | −4.01% | #35 / #34 | −4.34% | #13 |
| pol_switch3 | −4.16% | #35 / #34 | −4.53% | #13 |
| baitoey_mr_4h | −8.46% | #45 / #45 | +2.71% | #6 |

Two windows, both at one market turn (top in March, rebound in April), and both inside our 2020–26 history. Read this as a sanity check on turning points, not as evidence that outweighs 2,245 windows.

## 5. The sealed holdout (opened once, at the team's request)

Windows ending after 2026-08-08 16:00 UTC: 52 starts, Jul 26 – Sep 15 (about 4 independent windows), a rising market (BTC's median 14-day return +3.0%).

| Model | Median R | Worst R | Clears median bar | q67 | q83 | Best |
|---|---|---|---|---|---|---|
| **pol_switch_vt_tl** | +12.7% | **−4.0%** | 83% | 77% | 50% | 37% |
| baitoey_vt_mom | +12.7% | −4.0% | 81% | 73% | 46% | 40% |
| team_rot_ew | +12.7% | −16.6% | 67% | 67% | 56% | 56% |
| pol_switch_rmax_tl | +8.1% | −21.0% | 58% | 56% | 48% | 42% |
| pol_switch_rmax_mr | +13.3% | −23.5% | 52% | 50% | 48% | 42% |
| pol_switch3 | +4.1% | −5.0% | 48% | 42% | 33% | 19% |
| baitoey_mr_4h | +1.2% | −3.3% | 23% | 19% | 13% | 10% |
| pol_trend_ls | +0.5% | −6.0% | 25% | 10% | 8% | 6% |
| pol_mom_ss | +2.9% | −12.0% | 33% | 10% | 0% | 0% |
| team_btc_hold | +3.0% | −5.3% | 27% | 15% | 0% | 0% |

No model clears the field-best bar less often than BTC_HOLD (0%), so the pre-registered flag is empty.

## 6. The launch rule, applied

**Ranking** (eligible and robust, mean rank across the median, q67, q83 and best bars; registered models only):

| Model | Median | q67 | q83 | Best | Mean rank | SCREEN / CONFIRM |
|---|---|---|---|---|---|---|
| baitoey_vt_mom | 1.72 | 2.11 | 3.06 | 2.10 | 3.0 | 0.65 / 2.83 |
| **pol_switch_vt_tl** | 1.54 | 1.95 | 2.94 | 2.29 | 3.5 | **1.57 / 2.00** |
| pol_switch_rmax_mr | 1.65 | 1.92 | 2.82 | 2.13 | 4.0 | 1.83 / 2.42 |
| pol_switch_rmax_tl | 1.40 | 1.76 | 2.75 | 2.31 | 4.75 | 2.67 / 1.84 |
| *baitoey_mr_4h (not eligible, G6)* | 2.08 | 2.43 | 3.69 | 3.03 | — | 2.74 / 2.92 |

**Applying the rule:**
- The top two are within 0.5 of a rank, so it is a tie.
- The tie goes to the higher min(SCREEN, CONFIRM): **`pol_switch_vt_tl`** (1.57) over `baitoey_vt_mom` (0.65, weak in the 2022–24 bear market).

**The new methods:**
- `pol_switch_vt_tl` is the pick.
- `pol_switch3` (calm → MR_4h, up → vt_mom, down → trend_ls) fails G6 and is not robust: REL 1.35 on the best bar.

## 7. Trading-volume study (report-only)

| Variant | Median | q67 | q83 | Best | SCREEN / CONFIRM | Turnover per window |
|---|---|---|---|---|---|---|
| baitoey_vt_mom (band 0.05) | 1.72 | 2.11 | 3.06 | 2.10 | 0.65 / 2.83 | 3.59 |
| band 0.01 | 1.71 | 2.08 | 3.03 | 2.06 | 0.58 / 2.70 | 3.61 |
| band 0.10 | 1.73 | 2.11 | 3.06 | 2.10 | 0.50 / 2.81 | 3.58 |
| pol_switch_rmax_tl (band 0.03) | 1.40 | 1.76 | 2.75 | 2.31 | 2.67 / 1.84 | 4.60 |
| band 0.01 | 1.40 | 1.75 | 2.74 | 2.28 | 2.66 / 1.82 | 4.63 |
| band 0.10 | 1.41 | 1.76 | 2.79 | 2.28 | 2.76 / 1.78 | 4.58 |

- No variant beats its default under all four bars and both periods, so the defaults stay.
- These models change positions wholesale at each daily decision, so the band hardly changes how much they trade.
- **Dropped:** the pre-registered 72-hour decision interval. The model contract allows at most 24 h.

## 8. Engineering done today

- **Book's `src/live` changes reviewed and approved:** the fill check from the account, and the guard at 04:00 UTC with the UTC-day check. The guard covers days starting at 00:00 UTC, 16:00 UTC (HKT) and 12:00 UTC (the round's start).
- **The bot runs on Roostoo's clock**, the clock the round is timed on: machine clock plus an offset re-measured every hour, logged, with a warning above 2 s.
  - `python -m src.live.runner clock` checks the machine against Roostoo and NTP. On the research server it says NOT OK: +1.2 s and NTP not synchronized. Harmless for paper trading, but a required step on EC2.
- **`live.start_at` set to 2026-10-04 12:00 UTC.**
- **Broker fixed to the documented API formats.** The bot would have read every short as unreadable (unknown `ShortQty` field) and silently traded long-only, and it counted a successful short as unfilled.
- **`src/live/fillcheck.py`:** market orders at $100, $1,000 and $10,000 on the test account, to see whether bigger orders fill worse. Waiting for the test wallet to be funded.
- **Runbook:** Session Manager only, so the code goes through GitHub; the clock check; no manual stops.
- **Paper bots on live prices:**

  | tmux session | Model | State directory |
  |---|---|---|
  | `mm-pol-live` | `team_rot_ew` | `data/live` |
  | `mm-pol-paper-mr4h` | `baitoey_mr_4h` | `data/live_mr4h` |
  | `mm-pol-paper-swtl` | `pol_switch_rmax_tl` | `data/live_swtl` |
  | `mm-pol-paper-swvt` | **`pol_switch_vt_tl`** | `data/live_swvt` |

## 9. Other teams' public repos (approaches only, no code taken)

Recent public repos from this edition show:
- 30-minute momentum breakouts confirmed by volume (long only);
- a five-coin EMA 8/24 trend with volatility targeting and a funding filter;
- cointegration (pair-trading) infrastructure;
- an LLM-plus-indicators ensemble;
- generic bot frameworks.

Nobody visible runs mean reversion or a method switch. The benchmarks we score against (momentum rotations, BTC/ETH trend) match what the field does.

## 10. Decisions needed

1. **Launch model:** `pol_switch_vt_tl` (pre-registered pick), or override for a reason the team states.
2. **Turning-point risk.** Accept it, or pre-register a guard against switch lag before Oct 4 (none tested yet).
3. **Test wallet is empty:** ask the organizers. The fill-size test and a live test-account run wait on it. Add `ROOSTOO_ENV=test` to `.env`.
4. **GitHub for deployment:** public now, or private with a read-only deploy token.
5. **Merging:**
   - Baitoey reviews Book's clock and engine commits.
   - Book reviews `feature/realtest`.
   - Then the whole stack merges in order.
6. **Book's PART 0 rerun:** as of Oct 4 12:00 UTC, not Oct 3 16:00.

## 11. Limits

- **Everything is in-sample except the holdout**, which was opened at the team's request and is now spent.
- **The replay is two windows; the holdout is about four independent ones,** all in one up-and-turn period.
- **The real bar is calibrated from one previous round**, with about 50 active teams per region, against about 150 registered now.
- **Not verified:** whether Binance's API is reachable from EC2, the EC2 clock, the EC2 operating system, the test wallet funding, and fills at size.
