# Research-led short study — frozen candidates
Declared before reading these candidates' outcomes. All history and the observed ledger are spent research.
No claim of untouched holdout or prospective validation is made.

Primary research report: research/book/short_research/RESEARCH.md (commit48498aa).
Papers motivate mechanisms; all hourly lookbacks, thresholds and risk settings are engineering priors.
Exactly three variants. No parameter sweep and no outcome-based parameter changes in this study.

* book_short_trend: five liquid majors; daily01UTC causal signed trend over24/72/168h divided by168h hourly logreturn volatility times sqrt(h), average then clip[-1,1]. Inverse-volatility base shares, per-coin cap25%, gross1, conservative perfectly-correlated dailyvolatility cap1.25%. Band3percentagepoints.
* book_short_rebound: identical daily entries and sizing. Check01/07/13/19UTC; close short if current completed close exceeds prior24h close-high, excluding current. Exit has priority at daily re-entry time. Re-entry allowed only at a strictly later daily01UTC fresh signal; no intervening short re-entry. Longs remain governed by daily trend.
* book_short_breakdown: check01/07/13/19UTC, short a fresh72h completed-close low (excluding current) with latest24h average quotevolume at least1.5 times preceding168h average excluding those24h. Require BTC48h return negative and at most40% of valid five-major48h returns positive (at least3 valid). Existing shorts exit above prior24h completed-close high with exit priority; otherwise retain direction with updated risk weights. No new long positions.

All prices are completed UTC hourly closes. The registered models use hourly cadence to implement phase01UTC without altering the frozen harness. Non-decision hours retain previous targets; first bootstrap does not bypass the configured clock. Minimum history192h, all current bars and risk-window observations required. Parameters live in config.yaml.

Use unchanged scorer checkpoint603da2948b68ee0f5c8a. Do not refresh profiles, loosen gates, alter global config or open sealed holdout.
Ordinary --score2 publishes every candidate, including failures, into the separate leaderboard. Save independent historical panel/universe/spread hashes before/after runs.
Primary conditional result: existing minimum simultaneous lower advantage bound vs cash/fixede20, both profiles, all216/228/240h horizons.
Show original risk CS, short diagnostic table, chronological nonoverlapping fixed-window summaries and fees/spread limitations.
Same observed competition period comparison must use shared planner/paper broker and common start/end; hourly scores cannot certify minute matching.
Original frozen clone and refined inverse-volatility-cap clone are distinct revisions. Retrospective Oct8–9 is already seen and cannot become a fresh test.
Observed fees partly uncertain: onlyT001 market0.1% confirmed. Do not claim exact observed net return without this caveat.
No deployment, main merge, live process, signed API or secret access.

Cache identity repair before first publication: wrapper subclasses now fingerprint the mechanism constructor. Trading rules and parameters unchanged;72 synthetic causal cases match exactly. The partial first run is preserved/excluded at results/book/20261009-short-study. Final run artifacts use results/book/20261009-short-study-v2.
