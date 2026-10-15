# Simulator advantage inventory

| Track | Mechanism | Evidence | Can it make money? | Main failure or penalty | Decision |
|---|---|---|---|---|---|
| A1 | Order size may not move simulated quotes | Small STO market fills reported at ask; no controlled size study | Capacity is not predictive alpha | No depth or large-order evidence | UNVERIFIED; no large live probe |
| A2 | Coarse ticks can exceed two maker fees | 86-pair precision/quote snapshot; BONK, STO and PEPE highest | A one-tick winning trip can net fees | Adverse selection, waiting and sell execution | Arithmetic verified; repeatable edge not demonstrated |
| A3 | Maker entry/exit and mixed roles | All four role combinations tested; marketable limits pay taker fees | Fee savings are conditional | Unfilled or partial orders, queue, expiry, terminal losses | All recent-day variants lose |
| B1 | One-, two- and three-tick reversal | Three fixed rules on own quotes | No recent net edge | Fees and spread exceed tiny moves | Reject tested variants |
| B2 | Short-term momentum continuation | Five-minute momentum and 60-minute breakout | No recent net edge | Churn and false breaks | Reject |
| B3 | Bid/ask changes | Both quotes rising over five minutes | No recent net edge | Observing own quotes gives no guaranteed advantage | Reject |
| B4 | Spread compression | Causal comparison with past 30-minute spread median | No recent net edge | Compression alone does not ensure a favorable executable move | Reject |
| B5 | LastPrice at or below bid | Entry still pays ask, never LastPrice | No recent net edge | Stale last prices can mislead | Reject |
| B6 | Volatility clustering | Not traded as a standalone signal | Volatility prediction alone is not direction prediction | No directional profitability established | Unverified; not counted as a passed model |
| B7 | Oscillations and tick loops | Strict maker and taker loops; terminal inventory included | One attractive path failed persistence | Recent losses; sparse 72-hour samples | Reject |
| B8 | Activity periods | Chronological segments retained; no fitted session filter | No persistent advantage established | Few days; selecting favorable hours would inflate the search | No claim |
| B9 | 24-hour trading-activity jumps | Recorder lacks historical activity fields | Not testable from saved quotes | A current snapshot cannot recreate history | Unavailable |
| B10 | Asset-specific tick economics | Highest-tick assets and the observed tradable universe | Explains attraction to these coins | High tick ratio does not imply positive expected profit | Reject tested loops |
| C | BTC/ETH leading other coins | 60-minute leader rule on own quotes | No recent net edge | Cross-quote sensitivity flagged; no external-price test | Reject |
| D | Mean reversion, momentum, spread-aware exits | 17 quote candidates and five recent-day scenarios, with limits, timeouts and partial fills | All lose the recent-day screen | Fees, tail losses, unverified queue | Reject new execution edge |
| E | Concentrated directional recovery | Six corrected hourly benchmarks plus three fixed slower shorts | Three-day top-one long momentum has highest conditional recovery frequency | Exchange proxy, negative medians, large downside | Research shortlist; not deployment qualified |
| F | Dynamic cutoff lock | Exact equity arithmetic and threshold sensitivities | May preserve an already qualifying lead | Current account and moving cutoff unverified | Formula proposal only |
| G | External-price latency | User-reported 20% penalty accepted; formula unknown | No verified gross edge measured | Repository prohibition; some penalty cases require 43–52% gains | Last; not recommended; no latency strategy or orders tested |

The committed organizer statement permits one-sided tick scalping. Two-sided market making, arbitrage and HFT remain forbidden under repository rules.

Balance errors, malformed prices, cancelled FilledQuantity and API vulnerabilities are never counted as profit. The quote data contain no depth, order queue, trade IDs or historical 24-hour activity. Neither a last-price touch nor a bid touch proves a maker fill.

The initial protocol said 40 legacy gate settings; the actual script and CSV contain 38. The documentation correction changed no outcome or trial parameter.
