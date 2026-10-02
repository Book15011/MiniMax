# Amendment to the v2 pick order: a 0.03 margin on the tie group (2026-10-02, Pol; pending Book's confirmation)

| | |
|---|---|
| Changes | Step 3 of the pre-registered pick order (`20261002-prereg-return-first.md`, 0e9280b): a model is in the top model's tie group only if the 90% month-bootstrap interval of its HEADLINE_RET difference contains 0 **and** the difference is within 0.03 |
| Does not change | Any score, bar, weight, gate or the bootstrap itself; the tool version stays `3036a0d8bfdaa6a0` (the rule is report-layer code) |
| Where | `selection: {rule: margin, tie_margin: 0.03}` in config.yaml; `backtest/scoring/selection.py`; the leaderboard prints the legacy pick under each pick |
| Decided | After the v2 results were known, at Pol's request in the team chat. This is a post-hoc amendment, recorded as such |
| Owner of the rule | Book (scoring v2). Until he merges it into `feature/return-first`, a registered run from his branch rewrites the shared leaderboard with the legacy rule |

**Why.** The legacy tie group is set by how differently a model moves from the top, not by how close its score is:
`pol_mr_cap` (0.509) was tied with `baitoey_vt_mom` (0.609) and won on CS_HIT, while `pol_switch_vt_tl_e20v45`
(0.568) was not tied. Evidence (`20261002-selection-rule.md`): over 4 bar settings x 2 pools the legacy rule picks
3 different models, the margin rule one; in a 17-quarter walk-forward (pick from the past, score the next quarter)
legacy's picks averaged 0.417, below the average candidate (0.434), the margin's 0.470 (better in 8 quarters, worse
in 2, the same in 7). The value 0.03 was the one proposed before that check; 0.02 did equally well, 0.05 worse.

**Effect today.** Pick (full pool and without the post-holdout windows): `baitoey_vt_mom` (legacy: `pol_mr_cap` and
`baitoey_mr_4h`). The launch model is still a separate team decision (`live.model`).
