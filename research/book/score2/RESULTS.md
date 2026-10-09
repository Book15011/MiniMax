# Score2 integration verification

Owner: Book. Branch: feature/book-score2. Not merged into main; no live strategy changes.

The requested automatic secondary board is implemented and populated:

- /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md
- /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv
- /home/ubuntu/test/MiniMax/results/scoring/registry_2.jsonl

The Markdown board begins with reading instructions and evidence gates. It contains all 38 original compatible registered models. The new --score2 flag publishes a full compatible model run automatically; --score --score2 publishes both boards using one scoring computation. --score alone keeps its existing behavior.

## Verification

Final full suite: **325 passed in 194.41 seconds**. Focused score2 suite: **19 passed**.

The actual backtest.run --model pol_switch_vt_tl_e20v45 --score2 command passed, as did frozen-model import. Primary leaderboard.md and registry.jsonl hashes were unchanged. Every original checkpoint JSON/CSV/Parquet/Markdown artifact remained byte-identical.

All 38 new table rows reproduce the prior historical continuation mean, median, p10, p90, positive share and worst result within 1e-12. Maximum observed mean difference was below 1e-16; the other listed statistics matched exactly. Table audit and source fingerprints are in results/book/20261009-score2/table_audit.json.

Tests cover terminal costs and fixed-prefix alignment, rejection of partial/incompatible/inconsistent scores, modified checkpoint/artifact detection, idempotent publication, latest model revision with retained attempt history, concurrent publishers, ineligible-model visibility, revised-model paper attribution and CLI primary-publication behavior.

Protocol identity includes frozen checkpoint and metric/publisher source hashes. Changing scoring definitions creates a distinct protocol rather than silently mixing rows. Immutable source scores and return vectors are content-addressed, and publication uses a separate lock plus atomic Markdown/CSV replacement.

## Evidence status

Active alpha remains zero; mode UNIFORM_BASELINE_FALLBACK. The preserved direction nondegradation, 29/30 BCH coverage and archive confirmation failures remain visible. No thresholds, universe or missing values were changed to force a pass.

Rank cells remain blank and production_eligible=false. Each cached model continues its own historical holdings; common-account switch execution is unvalidated. The short timing score remains NOT_VALIDATED.

A revised model does not inherit the old model revision's paper replay. The paper records do not authenticate the actual EC2 account.

## Reproduction and evidence locations

Detailed command/reading guide: docs/SCORE2.md.

Raw integration evidence:
- /home/ubuntu/test/MiniMax/results/book/20261009-score2/verification_final.json
- /home/ubuntu/test/MiniMax/results/book/20261009-score2/final_full_suite.log
- /home/ubuntu/test/MiniMax/results/book/20261009-score2/final_cli_smoke.log
- /home/ubuntu/test/MiniMax/results/book/20261009-score2/final_import.log
- /home/ubuntu/test/MiniMax/results/book/20261009-score2/smoke_reports/

Generated smoke reports were preserved in Book's results folder rather than committed. Data, caches, registries and logs remain uncommitted. Reviewer sign-off is still required before a main merge.
