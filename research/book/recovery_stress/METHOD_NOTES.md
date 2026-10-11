# Audit support and implementation limits

Prepared during the fixed stress replay; no new model or parameter selected from these diagnostics.

Primary methodological source rechecked 2026-10-11:
Robert Novy-Marx (2015), Backtesting Strategies Based on Multiple Signals, NBER Working Paper 21329.
https://www.nber.org/papers/w21329
The paper shows that selecting combinations of signals can inflate apparent historical significance.
This supports retaining every failed trial and declining to interpret repeated historical reuse as new evidence.
It does not certify our bootstrap, any crypto forecast, or any proposed recovery rule.

Robert Novy-Marx and Mihail Velikov, A Taxonomy of Anomalies and their Trading Costs.
https://www.nber.org/papers/w20721
The primary abstract reports that costs reduce measured profitability/significance and that buy/hold bands
can mitigate turnover in its equity setting. Our existing band is kept fixed; no new band is tuned here.
This paper does not establish a suitable crypto threshold or validate our simulator.

Committed live source inspected read-only: pol-live-brk ef1b0dd.
src/live/runner.py lines145-147 reset prev_targets, standing and last_decision on a model-name change.
Therefore changing the model name can induce an immediate fresh decision and a different book, even when the
parent and candidate would agree if evaluated with preserved memory. No restart/state patch is authorized.
src/live/runner.py lines185-204 implement a persistent endgame lock using actual round_start and
round_start_equity, from_day10, lock_return3%; a pre-existing lock remains active while enabled.
Cash-start research paths have neither actual funded-round state nor the deployed EC2 position snapshot.
A cost-inclusive cash-start result therefore cannot be described as a verified account-switch result.
config.yaml committed live.end_at is2026-10-18 12:00UTC; main:AGENTS.md saysOct17. Actual deadline UNVERIFIED.
The added5/6-day cuts describe horizon sensitivity; they do not resolve the official deadline.

Backtests use hourly prices and a single fixed historical spread snapshot. They model executed-side fees,
including opening and closing shorts, and the configured terminal liquidation charge.
The terminal charge is one configured proportional amount; an additional terminal bid/ask spread is not
separately added by the inherited reporting formula. Stress doubles this charge, but cannot prove exact final
exchange execution cost, order latency, partial fills, refusal behaviour or account-specific slippage.
Marked exposure can drift above100% between capped target decisions; original hard-gate verification remains
incomplete. No target expansion or price/cost input is changed in this audit.
Actual EC2 holdings, deployed config, long-only fallback, locked_at, active days, pending orders,
exchange precision/minimums and API health all remain UNVERIFIED. No signed API or live action is performed.

All past observations are spent calibration/diagnostics. Original three frozen prospective cohorts remain
unchanged and incomplete. Common all13 cohort:Oct12 00UTC throughOct15 00UTC, i.e.Oct12 08HKT toOct15 08HKT.
That one future three-day path, when complete and valid, still is not a guarantee or a large independent sample.
Original broad-universe coverage failure remains BCH29/30; adaptive scoring OFF.
