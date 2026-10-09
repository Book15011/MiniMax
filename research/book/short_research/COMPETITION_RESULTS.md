# Competition-prefix comparison: reading the evidence
Owner: Book. Retrospective research only. No strategy was deployed.

The comparison covers4October2026 20:00HKT through9October09:15HKT (UTC12:00Oct4→01:15Oct9), with100000USD cash.
New models use their frozen completed-hour signals and1-hour execution lag. The original clone keeps its original5-minute lag and initial equal basket. Actual observed orders use supplied timestamps. These are descriptive comparators, not identical execution recipes.

| Model | After full closing costs | Sampled maximum drawdown | Mean gross exposure |
|---|---:|---:|---:|
| book_short_trend |+1.03%|2.00%|33.60%|
| book_short_rebound |+1.03%|2.00%|33.60%|
| book_short_breakdown |+0.70%|0.57%|6.44%|
| Original frozen clone |+4.65%|2.91%|71.88%|
| Observed literal ledger |+5.18%|2.87%|72.03%|

None of the three new models beats the observed portfolio on this already inspected period. A/B have identical executions: no rebound exit activated. Lower drawdowns accompany lower exposure; this is not proof of better timing.
All organic short cycles remain open/censored at cutoff. No completed-cycle hit rate can be claimed. Terminal forced closes do not turn censored events into successful signals.

Read /home/ubuntu/test/MiniMax/results/book/20261009-short-competition/comparison.csv first.
full_cost_liquidated_return applies a common hypothetical fee to all remaining gross positions, including tiny subprecision dust; liquidated_return separately shows practical shared-broker closes.
Each model has *_events.csv, *_equity.csv, *_endpoint.json, *_short_cycles.csv and *_failures.csv. Check provenance.json and independent_audit.json.

Price evidence uses65 publisher-checksum-verified daily archives for five assets September26–October8. There are194 complete warmup rows before the start, with no missing close/volume cells. All decisions see only completed information.
First-session pricing predates recorded Roostoo quotes and uses a USD/USDT minute-price proxy with1bp halfspread. Later fills use as-of recorded bid/ask. These are simulated fills; no actual market execution claim.
Source model helper/config is317a600; wrappers02b06ff. Final wrapper rerun has identical event files/equity to the first pass. Independent Decimal signed-cash reconstruction agrees to floating-point tolerance;40 independent checks pass. Full comparison-worktree suite:271tests passed.

Fine replay includes no activity-guard trades; the full hourly leaderboard simulation includes its unchanged guard. Their P&L should not be expected to match.

Reproduce remotely in /home/ubuntu/test/MiniMax/.worktrees/book-book-short-research:
```bash
.venv/bin/python -B -m pytest -q tests/test_short_competition.py tests/test_observed_baseline.py
nice -n10 .venv/bin/python -B -m src.validation.short_competition
.venv/bin/python -B research/book/short_research/audit_competition.py
```
Check the module's --help before a fresh data preparation; existing snapshots and original revisions remain preserved.
