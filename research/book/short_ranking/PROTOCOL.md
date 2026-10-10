# Sample-aware return and short-opportunity ranking

This protocol is frozen before extracting the new classification labels. It changes research presentation, not trading models, case selection, existing profit gates, live deployment or the 85% clone criterion. Parent: thirteen-model combined v3, uniform 27-hypothesis conservative return bounds. All history is spent. This is an exploratory composite rank, not a newly validated profit claim.

## Why F1 is distinct from completed-trade accuracy

Completed accuracy is wins divided by fully closed short episodes. Two wins from four and 25 from 50 are both 50%, but the first has much weaker evidence. The accuracy component uses the smaller of the existing quarter-cluster 90% lower bound and the one-sided Wilson 90% lower bound, taking the worse of the two profiles. Wilson treats episodes as independent and is only a descriptive sample-size penalty; it does not replace dependence-aware uncertainty or evidence gates.

F1 needs missed positive opportunities. It is not definable from just profitable and losing executed trades. Define nonoverlapping six-hour blocks for each of the four benchmark coins, starting one minute after the common one-hour execution lag. A positive block means a hypothetical standalone short at its start would finish profitable after both fees and spread. An actual audited short at block start counts as a prediction only when its notional is at least 1% of account equity. Existing held shorts qualify; repeated entries are not required. Dust cannot manufacture recall. Incomplete final blocks are censored, not classified.

TP: meaningful short and profitable future block. FP: meaningful short and nonprofitable block. FN: no meaningful short and profitable block. Precision=TP/(TP+FP); recall=TP/(TP+FN); F1=2TP/(2TP+FP+FN). Zero denominators score zero. This measures decision coverage at fixed block starts, not entry-fill accuracy, actual block PnL, all possible intrablock falls, probability calibration or live forecasting. It ignores later position changes within a block.

Per-profile F1 lower bounds resample start-date quarters 20,000 times. Both profiles retain every preselected window. The worse lower bound enters the score. Future labels are diagnostic only and never enter the model or choose windows. Raw blocks, TP/FP/FN/TN and censoring are saved.

## Combined rank

50 points: percentile rank of the existing worst of six simultaneous conservative mean-return lower bounds, among this fixed 13-model cohort. This rewards after-cost return with uncertainty, not gross headline return. It is relative: a top percentile can still lose money. Equal return values share their component.

30 points: worse-profile quarter-cluster 90% lower bound on six-hour opportunity F1.

20 points: completed-episode accuracy reliability component described above.

Higher is a research priority. All original reliability flags remain unchanged; a high score never overrides FAIL. The composite score is unrelated to the 85% clone agreement target. Fifty trades are not automatically better than four: return, missed opportunities, loss rate and dependence still matter. Counts are always visible.

Old results are immutable. A new model needs an equal-protocol frozen audit batch and an expanded uniform hypothesis correction before admission into a new combined cohort/rank version. Normal --score2 auto-updates its own leaderboard; this fixed comparative study does not silently ingest new registrations.
