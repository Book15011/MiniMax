# Independent reconstruction matcher audit

Book,9October2026. Audit source is clone_matching.py in this folder.
The predictor/matcher/reconstruction outputs were read only. No matching rule
or quantity/timing tolerance was modified.

The frozen result is numerically correct under its existing interval-distance
implementation:19/33 observed executions matched,31 predictions,
recall57.58%,precision61.29%,F159.375%. Independent unit-capacity maximum flow
(BFS augmenting paths) returns exactly the same19 pairs. No project matching
function was imported. Every published pair independently passed same asset,
same action, timing and quantity criteria, with no duplicated observations or
predictions.

The action/time-only frozen result is30/33,31 predictions,F193.75%.
This ignores quantity and cannot satisfy the strict85% objective.

## Material timestamp boundary

The corrected CSV gives minute precision. The original protocol describes each
minute as [minute,minute+60s) and uses distance to that interval. Frozen code is:

    max(observed_start-predicted, predicted-(observed_start+60s),0) <=120s

For a prediction at09:05:00 and recorded observed minute09:02, this gives120s
from the minute's END, although it is180s from the displayed START. The infimum
distance to the half-open interval includes its unattained upper limit.
No actual instant in [09:02:00,09:03:00) is within120s of09:05:00. The existing
distance implementation nevertheless includes that exact upper boundary.

All five Oct9 predictions sit on it. Three also meet quantity tolerance:
T030 SOL cover, T032 BNB short, T033 BTC short. Two fail quantity as well:
T029 ETH cover and T031 XRP cover.

| Diagnostic timing convention | Strict matches | Precision | Recall | F1 | Action/time-only matches |
|---|---:|---:|---:|---:|---:|
| Frozen interval distance, inclusive boundary |19/33|61.29%|57.58%|59.375%|30/33|
| Literal half-open existential match |16/33|51.61%|48.48%|50.00%|25/33|
| Displayed-minute timestamp ±120s |16/33|51.61%|48.48%|50.00%|25/33|

These two additional lines are declared sensitivity diagnostics, not a replacement
primary matcher. The result remains well below85% under every interpretation.
The frozen statement "no timing-only misses" is correct under that code but must
be accompanied by this boundary limitation. Under the sensitivities, two existing
sizing misses also fail timing and three formerly matched rows fail timing alone.

The earlier28/33 ceiling for a single09:05 batch assumed displayed-minute or
literal half-open timing:five09:02 rows fail,leaving at most28 of33 even with
perfect actions/quantities. That ceiling does not apply to the frozen code's
inclusive interval-distance boundary. It cannot establish cloning impossibility.

## Evidence and verification

Output: /home/ubuntu/test/MiniMax/results/book/20261009-short-diagnostics/clone-matcher.

Read matcher_audit.json and maximum_matching_sensitivity.csv.
published_pair_audit.csv verifies all19 reported pairs.
upper_boundary_pairs.csv lists the five Oct9 boundary pairs and quantity tests.
all_same_action_pairs.csv retains the full candidate-edge diagnostics.

The audit pins corrected33-row CSV, selected31-event prediction, selected metrics,
selection freeze and existing matcher source SHA256 before/after. Source branch
under review is5bfea89. The independent matcher uses nanosecond integer timestamp
inequalities and Decimal quantity relative errors with the existing1e-12 tolerance
margin. Two focused tests verify nongreedy graph allocation and the exact upper
boundary. Previous full suite:473 passed; these two added audit tests also pass.

All five dates were calibrated. This verifies retrospective numerical agreement,
not forecast independence, strategy identification, future profit, or85% success.
Twenty-nine observed matches are needed for85% recall; extra predicted orders also
must be counted in precision. Preserve all33 observations, including tiny covers.

Reproduce from this Book worktree:

    .venv/bin/python -B -m research.book.short_diagnostics.clone_matching --out /home/ubuntu/test/MiniMax/results/book/UNIQUE_DIR

Always choose a new output directory. This audit will not overwrite a prior
matcher_audit.json.
