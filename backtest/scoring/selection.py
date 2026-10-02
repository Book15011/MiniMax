"""Leaderboard pick rules (report layer: not a tool-version file, so changing the rule rescores nothing).

The return-first pick order (backtest.scoring.returnfirst.pick_order) takes the best CS_HIT inside the top model's
tie group. Two ways to form that group, chosen by the top-level `selection:` block of config.yaml:

- legacy  (pre-registered, reports/review/20261002-prereg-return-first.md): tied when the 90% month-bootstrap interval
          of the HEADLINE_RET difference to the top contains 0.
- margin  (Pol's proposal, reports/review/20261002-selection-rule.md): tied when that interval contains 0 AND the
          difference is within `tie_margin` of the top. The interval is wide for a model that moves differently
          from the top and narrow for one that moves with it, so without the margin a model far below the top can be
          "tied" and win on CS_HIT. Walk-forward over 17 quarters: legacy's picks scored 0.417 in the next quarter
          (below the average candidate, 0.434), margin 0.03's 0.470.

The leaderboard always shows both picks; `rule` only sets which one orders the table.
"""
from __future__ import annotations

RULES = ("legacy", "margin")


def settings(cfg: dict) -> tuple[str, float | None]:
    """(rule, margin) from cfg["selection"]; legacy without the block. margin is None for legacy."""
    s = cfg.get("selection") or {}
    rule = str(s.get("rule", "legacy"))
    if rule not in RULES:
        raise ValueError(f"selection.rule must be one of {RULES}, not {rule!r}")
    if rule == "legacy":
        return rule, None
    m = float(s["tie_margin"])
    if not 0.0 <= m < 1.0:
        raise ValueError("selection.tie_margin must be in [0, 1)")
    return rule, m


def proposal_margin(cfg: dict) -> float:
    """The margin the leaderboard reports alongside legacy, whatever the active rule."""
    return float((cfg.get("selection") or {}).get("tie_margin", 0.03))


def apply_margin(ties: dict[str, dict], margin: float | None) -> dict[str, dict]:
    """Tie results with the margin applied: tied only if tied before AND diff >= -margin (the top keeps diff 0).
    Each entry keeps the legacy verdict as `tied_legacy`. margin None returns the results unchanged."""
    if margin is None:
        return ties
    return {n: {**v, "tied_legacy": bool(v["tied"]), "tied": bool(v["tied"] and v["diff"] >= -margin)}
            for n, v in ties.items()}
