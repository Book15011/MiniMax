"""Reference (ROT_IV): team_rot_ew with inverse-volatility weights and a 2%/day book-volatility target."""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.baselines.team_rot_ew import RotationEW


class RotationIV(RotationEW):
    spec = ModelSpec(name="team_rot_iv", method="reference", author="team", rebalance_hours=24, band=0.05,
                     description="Top-6 risk-adjusted momentum, inverse-vol weights, book at <= 2%/day volatility (scoring field)")


MODEL = RotationIV()
