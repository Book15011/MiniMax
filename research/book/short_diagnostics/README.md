# Independent diagnosis and next-round validation

Book, 9 October 2026. Worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-short-diagnostics.

The first three new signed-momentum models do not improve the best existing long
baseline. The more selective breakdown model reduces risk and has positive
mean in the weak analog cohort, but its low activity/exposure leaves much less
return. This is a measured risk/return tradeoff, not a demonstrated better model.

## Pinned evidence

Frozen primary protocol603da2948b68ee0f5c8a, tool3036a0d8bfdaa6a0 and checkpoint
results/book/20261009-weak-eval-v2 are unchanged. No shared scoreboard, registry,
model, execution rule or live process is modified by these scripts.

Models and exact published revisions:

| Role | Model | Key |
|---|---|---|
| Strongest existing score2 rank | baitoey_ovl_brk_dual | f30fa79cde92399a |
| Next dual baseline | baitoey_vt_dual | 457a15537cb2cb75 |
| Book dual baseline | book_vt_dual | 5ccb581e175dacbe |
| Frozen incumbent | pol_switch_vt_tl_e20v45 | 0ec3cf0ca1185b36 |
| First frozen candidate A | book_short_trend | e758f48cfbbba861 |
| First frozen candidate B | book_short_rebound | 41ce2438da8f9330 |
| First frozen candidate C | book_short_breakdown | 8b75f0d5cd989604 |

Raw historical close SHA256 is
dca38811d268d2c8a47c2adb47d2caef99bbe477bd38fe9dffbcedd4581b3294;
quote-volume is
aafb8d2f0ed3c7eeebf1b40e4cbd20934827c622f7717251d51a48d59d5afa0a.
Scripts check these frozen hashes and independently record current universe and
spread snapshots before/after. The original universe byte pin was not saved;
current spread proxies are not contemporaneous historical bid/ask.

Output root: results/book/20261009-short-diagnostics.
Use attribution-v2/ (the earlier attribution root preceded the explicit future
outcome split), chron-top/, and baseline_reproduction_v2.json. Each output has
source/cache hashes. Retain earlier evidence; do not overwrite prior reports.

## What failed, and why

Archived weak analogs,25 cash-start228h paths, equal weight across paths:

| Model | Net mean | Gross long PnL | Gross short PnL | Ordinary fees | Mean long exposure | Mean short exposure |
|---|---:|---:|---:|---:|---:|---:|
| Top dual | +2.944% | +3.404% | 0.000% | 0.343% | 65.31% | 0.00% |
| A trend | -0.240% | +0.092% | +0.002% | 0.292% | 14.06% | 21.71% |
| B rebound | -0.305% | +0.096% | -0.037% | 0.326% | 13.90% | 18.97% |
| C breakdown | +0.372% | -0.000% | +0.412% | 0.037% | 0.01% | 4.32% |

Spread and terminal close complete the identity; see window_attribution.csv.
A/B have approximately zero or negative gross short contribution overall before
cost. They also give up most of the long participation that earns during
rebounds. B's rebound exit increases short turnover (2.117 versus A1.767).
C's sparse, lower turnover short book has positive small edge in these cases,
but does not outperform top dual.

For explanation only, use the already saved BTC forward240h return labels:
7 cases fall at least2%,13 rebound at least2%,5 lie between. These outcome labels
are retrospective, cannot be strategy inputs and never change primary case
selection or weights. The attribution return remains228h.

| Model | Mean228h on7 future-fall cases | Mean228h on13 future-rebound cases |
|---|---:|---:|
| Top dual | -3.270% | +6.726% |
| A | +1.715% | -0.706% |
| B | +1.400% | -0.586% |
| C | +1.163% | +0.107% |

The data support testing a small conditional short allocation while preserving
the strong long book. They do not support replacing it with broad negative
exposure on every weak analog, nor using hindsight to select only falls.

Attribution reconstructs every hourly cash/equity/exposure path from the prior
post-fill weights, prices and attested trade ledger. Current fills cannot earn
the price movement preceding entry. Fee/spread amounts are in starting-capital
units; terminal liquidation is charged once. Every hourly equity, gross/net and
pre-fill weight must reproduce within1e-10, then the net PnL identity must hold.
This accounting explains results; it does not identify a causal market driver.

## Fair chronological comparison

chron-top has the same97 nonoverlapping228h cases used previously: globally fixed
14-day starts from2022-07-01 12UTC, dropping cross-half-year windows, eight blocks
2022H2 through2026H1. All history was available during model development; these
are descriptive chronological summaries, not nested training or a pristine
holdout. Market dependence persists despite direct path nonoverlap.

| Model | Mean | P10 | Worst | Mean MDD | Mean CS | Paired mean advantage vs top |
|---|---:|---:|---:|---:|---:|---:|
| Top dual | +1.351% | -7.417% | -17.245% | 7.303% | 0.143 | 0 |
| A | +0.482% | -2.732% | -6.397% | 2.782% | 0.116 | -0.869pp |
| B | +0.488% | -2.695% | -5.397% | 2.697% | 0.115 | -0.863pp |
| C | +0.040% | -1.239% | -3.431% | 0.750% | 0.037 | -1.311pp |

CS is the existing FLOORED.V1 daily-raw HKT composite, 0.4Sortino+0.3Sharpe+
0.3Calmar with original floors; UTC sensitivity is separate. No metric called
CSL is implemented. Cash, BTC hold, equal-weight long and exact frozen e20 remain
visible comparators. paired_summary.csv compares the same starts; fold_summary.csv
shows every block, means, medians, tail10, worst, MDD, CS, activity and turnover.
No new rank is generated from this descriptive table.

Runnable command from this worktree:

    scripts/lock book-chron-NAME -- nice -n 10 .venv/bin/python -B -m research.book.short_validation.run --candidate MODEL=KEY --benchmark baitoey_ovl_brk_dual=f30fa79cde92399a --out /home/ubuntu/test/MiniMax/results/book/UNIQUE_DIR

A compatible full ordinary --score2 publication must exist first. The helper
checks immutable score and cache publication hashes. Candidate decisions are
not retrained or tuned. Existing output manifests cannot be overwritten.

## Baseline source identity audit

The top baseline uses a legacy dynamically generated overlay class. Existing
model_modules sees only src.models.baitoey._overlays, omitting the wrapper and
INNER model sources. This is a real source fingerprint limitation; no frozen
framework patch is made here.

baseline_reproduce.py independently reproduced all2311 saved daily target
decisions and120 fixed sampled cash-start bootstrap fills, both with maximum
error0. The sample covers the full saved cache span. Bootstrap uses the exact
existing activity guard/planner, including0.002BTC keepalive when applicable.
Every published array/trade/score hash is checked. Explicitly traced wrapper,
inner model, signal and rotation source SHA256 values and exact published params
are saved before/after in baseline_reproduction_v2.json. The target parquet
has no original publication byte attestation; its before/after hash and numerical
reproduction are recorded. This empirical proof does not repair that omission.

    scripts/lock book-baseline-proof -- nice -n 10 .venv/bin/python -B research/book/short_diagnostics/baseline_reproduce.py --source-worktree /home/ubuntu/test/MiniMax/.worktrees/baitoey-mom-ss --out /home/ubuntu/test/MiniMax/results/book/UNIQUE_DIR/baseline.json

New wrappers explicitly bind dependency modules to include their constructors,
BASE wrapper, inner model and helpers in cache identity. The proposed two
cash-only hybrid hypotheses keep the same positive long target chain; equal
target weights do not guarantee identical dollar trades after short fees,
equity changes, drift and shared gross fitting.

## Exact executable cost sensitivity

cost_replay.py adapts the prior frozen160-case protocol. Starts are exactly
2020-06-01 12UTC plus multiples of14days,160 cases,228h, verified against the old
cost manifest. Models/parameters/decision targets are identical in original and
doubled scenarios. Every original equity hour must match its published cache
to1e-12 before accepting the doubled-fee/doubled-halfspread simulator rerun.

Full source decisions are computed once, with keep_raw=True, solely to recover
Series order and check every stored target to1e-12. This avoids an unsafe
params['coins'] assumption for broad dynamic models and avoids changing
first_decisions convergence/hysteresis due to parquet column ordering. This is
deterministic decision reproduction, with no parameter fitting. Full baseline
manual source hashes must also match the empirical proof above.

Terminal liquidation uses Simulator._trade on actual final holdings, paying
fees and spread under each scenario once. CS/MDD use that adjusted endpoint
with no extra close fee. This matches the old cost protocol and differs from
primary score2's fee-only endpoint convention; it cannot publish a primary rank.

    scripts/lock book-cost-MODEL -- nice -n 10 .venv/bin/python -B research/book/short_diagnostics/cost_replay.py --source-worktree /home/ubuntu/test/MiniMax/.worktrees/book-book-short-next --model MODEL --key KEY --baseline-evidence /home/ubuntu/test/MiniMax/results/book/20261009-short-diagnostics/baseline_reproduction_v2.json --out /home/ubuntu/test/MiniMax/results/book/20261009-short-next-cost

Outputs per model: paired_windows.MODEL.csv, summary.MODEL.csv,
curves.MODEL.npz and manifest.MODEL.json. Use original versus doubled comparisons
within each identical case and compare candidates against top on the same160
starts. No scenario scales final returns after the fact. No doubled-cost
publication, retraining, fold selection or threshold relaxation is permitted.

## Endpoint, independent samples and limits

Keep the frozen endpoint Oct18 12UTC. Dated public competition538 evidence is
reports/review/20261001-realtest-findings.md:32; deploy/README and docs/EVALUATION
agree. AGENTS' older Oct17 entry conflicts. A credential-free public refresh
returned HTTP451, so fresh verification is unavailable. Do not silently change
the frozen horizon. The failed broad-universe query remains29/30: BCH lacks
competition ticker data; dynamic model breadth does not repair that failure.

Primary weak windows overlap and have clustered/simultaneous bounds in the
frozen evaluator. Do not treat25 analog rows,33 reference trades or individual
orders as independent forecasts. At85% strict matching of33 orders,29 matches
are required (at most4 misses). Timing oracles are structural diagnostics, not
causal cloned strategies, and cannot be reported as85% achievement. Same-period
minute price comparisons remain retrospective and use shared marks/cost rules.

Remaining new-model evaluation should report both hypotheses without replacements,
unchanged primary score, paired97 chronology against top/e20/cash/BTC, identical
160-case executable costs, target-versus-executed short counts and completed
versus censored episodes. Inactive or failed variants must remain visible.
No live changes or current-account-switch claim follows from these diagnostics.

## Completed independent checks

473 tests passed in 199.77s, including 3 causal accounting tests, 4 cost replay money tests and the previous cache/clock/ledger tests. Full log: results/book/20261009-short-diagnostics/full-tests.log.

The strongest baseline actual cost replay reproduced every original equity hour with maximum error 0 on all 160 cases and all 2,311 target decisions. Original versus doubled costs: mean +1.613% versus +1.223%; P10 -7.219% versus -7.517%; worst -18.769% versus -19.099%. Fees and halfspreads were both doubled. This does not demonstrate a reliable edge or establish replacement readiness.

NEW_MODEL_SOURCE_REVIEW.json records the independent read-only review of the two cash-only hybrid sources and their exact source hashes. No causal or sizing defect was found. Candidate outcome and full cache checks remain separate.

Cost replay v2 additionally hashes frozen raw close/volume and current universe/notes/spread before/after, as well as model/framework sources and published caches. The first baseline cost run remains in20261009-short-next-cost; paired new-model runs use20261009-short-next-cost-v2 with the same160 starts and same simulation math.
