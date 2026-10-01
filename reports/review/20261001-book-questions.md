# Answers to Book's eight exchange questions (2026-10-01, Pol)

Evidence:
- public Roostoo and Binance endpoints;
- the official API docs (roostoo/Roostoo-API-Documents);
- read-only calls with the TEST key (it signs correctly; the wallet is empty, so no order has been placed yet).

Scripts: `results/pol/20261001-final/px_compare.py`, `api_probe.py`, `api_snapshot.py`.

| # | Question | Answer | Status |
|---|---|---|---|
| 1 | Do Roostoo prices match Binance's, and how far behind? | **Yes, exactly.** 86 pairs on both, 12 simultaneous snapshots 10 s apart: median mid difference **0.00 bps**, 90% within 1.8 bps (the fetches were 1.9 s apart), last prices identical. The lag is below our snapshot spacing (≈ 2 s) and irrelevant for hourly decisions, so backtests on Binance data are valid. Matches FAQ Q17 | Answered (a 24 h minute log would only refine the lag below 2 s; not worth the calls) |
| 2 | Bid-ask spread per coin, especially small alts? | **The same as Binance's top of book** (Roostoo / Binance spread ratio 1.00). Median half-spread 1.5 bps. Widest: BONK 13.6, STO 11.8, PEPE 11.5, 1000CHEEMS 9.3, WLFI 9.1, SHIB 8.8 bps. The engine already charges each coin's half-spread (from the 2026-09-28 snapshot, median 4.0 bps, higher than today), so the backtests are on the conservative side | Answered |
| 3 | Where does a market order fill? Partial fills? | Docs: a market order is a TAKER fill with `FilledAverPrice` and `FilledQuantity` (no partial-fill example for market orders); a short close fills at `MinAsk`. Not measured: `python -m src.live.fillcheck` (market BUY/SELL at $100, $1,000, $10,000, fill vs the quote just before) is ready | **Waits for the test wallet to be funded** |
| 4 | Do limit orders fill, how fast, at 0.05%? | Docs: a LIMIT order stays PENDING (MAKER) until the market reaches the price. Round 538's fees from the API: **taker 0.1%, maker 0.05%**. The docs' examples show other rates (0.012% / 0.008%), so the test account may differ from the round | Partly answered; timing not measured |
| 5 | Does shorting work? | Docs: shorts go through `/v6/short_open` (sized by USD collateral, 0.1% open fee) and `/v6/short_close` (0.1% close fee, reduce-only). A spot SELL needs coins you hold; shorting is not "selling what you don't have" on the spot endpoint. Free USD must cover collateral plus fee; positions show in `/v6/short_positions` (`ShortQty`, `EntryPrice`, `Collateral`). FAQ Q31: long and short are allowed. The bot's broker now reads these documented formats (fixed today: it did not know `ShortQty`) | Docs answered; **live test waits for funding** |
| 6 | Minimum order and precision per pair? | `MiniOrder` (price × quantity) is **$1 on all 88 pairs**. Amount precision 0–5 decimals; the largest one-step quantity is about $1.39 (ZEC), BTC $0.84. Our smallest trade is $10 and the keep-alive $200, so neither can be rejected for size | Answered |
| 7 | API response time; what happens past the rate limit? | From the research server: **≈ 730 ms median** (public and signed alike), one 8.2 s spike in 20 calls. **A burst of 40 signed calls in 25 s all succeeded:** the 30/min limit is not enforced on the test account. The bot stays at ≤ 20/min regardless | Answered for the test account; the competition key is unknown |
| 8 | Last round's leaderboard; other teams' values this round? | **Yes:** public `/v1/leader_board?competition_id=…&lb_level=OVERALL` (previous edition: 455, 456, 469; ours: **538**) gives every ranked team's balance, return and traded volume. This round's will be visible the same way once it starts (and in the app, FAQ Q33). We keep numbers only: the entries also carry names and emails | Answered (see `reports/review/20261001-realtest-findings.md` section 3) |

**Also settled today:**
- **Deployment goes through a public GitHub repo.** The organizers' AWS guide says "Clone your code from GitHub … `git clone <your-bot-repo>`", and FAQ Q35 says the submission repo "must be open-source".
- **The EC2 template is Amazon Linux** (`dnf`, git preinstalled), on a `t3.medium` in Sydney with a 30 GB disk. Only one instance is allowed, and no other AWS services (no S3). `deploy/setup_ec2.sh` handles Amazon Linux.
- **Jev** (an external decision API) is parked as an optional extra, not started.
