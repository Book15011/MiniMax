"""Reference (MOM_SS25): the team's launch candidate, momentum with a 25% short sleeve, frozen for the field.

The definition is TEAM_PLAN v1 section 3: top 15 liquid coins, top 5 long and kept while in the top 10, 25%
short on the 4 weakest coins with negative momentum, long book volatility-capped. The code is pol_mom_ss's
(reused, not copied); the parameters are a frozen copy under `models: team_mom_ss25:` so the benchmark stays
fixed while pol_mom_ss evolves. Two differences from TEAM_PLAN v1, both from the harness: decisions at
16:00 UTC (not 00:05 UTC) and a 3-point drift band (TEAM_PLAN does not give one).
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol.pol_mom_ss import MomentumShortSleeve


class MomSS25(MomentumShortSleeve):
    spec = ModelSpec(name="team_mom_ss25", method="reference", author="team", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="MOM-SS v1 frozen: top-5 momentum long, 25% short on the 4 weakest falling coins (scoring field)")


MODEL = MomSS25()
