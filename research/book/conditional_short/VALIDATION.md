# Source and implementation validation

Worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-conditional-short-research
Branch: feature/book-conditional-short-research. Author: Book.

Two candidates only: book_cashshort_confirm and book_cashshort_pullback.
No candidate performance outcomes have been inspected or parameters retuned.

25 focused tests PASS (2.89s). Tests were written before implementation and first
failed on the absent model import. Checks cover exact positive long targets at
12UTC bootstrap/16UTC regular calls, future-row exclusion, positive-only long
previous targets, liquidity/breadth coverage boundaries, no missing-endpoint
replacement, negative momentum, causal failed-rebound ordering, unusedcash/gross/
percoin/risk limits, and source dependency identity.

The full pytest suite is PENDING at this commit. One existing run continues in
mm-book-conditional-short-tests under scripts/lock, nice-n10; no repeat run.
Evidence: results/book/20261009-conditional-short-research/pytest.log and pytest.exit.
Publication must await its successful completion.

The reproducible source audit passes:
PYTHONPATH=. .venv/bin/python -B research/book/conditional_short/source_audit.py
It saves results/book/20261009-conditional-short-research/source_audit.json.
Every existing YAML field/model equals immutable base320984e, excluding only
the two new model blocks. Each long_base exactly equals published f30fa79cde92399a
score.json model.params. Six own-team source helpers exactly match pinned
0b2c2630da058eab8abb0c8881cdbcbb1b54a1ff. Explicit new wrapper classes and global
helper module dependencies make both new model source identities complete.

The worktree adds three own-team baseline dependency files absent on main.
The parent integration worktree already has these same files, so integrate
only new Book files/tests/docs and the two YAML blocks there, preserving its
other model blocks and field/scoring implementation.

No main merge, shared leaderboard write, live change, signed API, secret read,
or strategy performance claim was made. The original metric protocol remains
603da2948b68ee0f5c8a and original broad query remains FAILED29/30.
Independent historical target reproduction and performance validation remain
the parent study's responsibility; focused synthetic tests alone cannot establish
real performance, target stability across all historical contexts, or deployment
readiness.
