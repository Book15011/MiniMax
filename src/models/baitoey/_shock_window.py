"""Research only (not a registered model): Pol's pol_abl_shock with the crash window as a parameter.

pol_abl_shock fixes the window at 4 hours (BTC falls at least shock_4h over 4 hours). This subclass reads the window
from `shock_hours` (default 4, which is pol_abl_shock exactly), so the crash-rule robustness check
(research/baitoey/prereg/20261002-crash-rule-plateau.md) can nudge it without changing Pol's file.
"""
from __future__ import annotations

from dataclasses import replace

from src.contracts import MarketView
from src.models.pol.pol_abl_shock import ShockOverride


class ShockWindow(ShockOverride):
    spec = replace(ShockOverride.spec, name="baitoey_shock_window", author="baitoey",
                   description="research only: pol_abl_shock with the crash window as a parameter")

    @staticmethod
    def shocked(view: MarketView, p: dict) -> bool:
        k = int(p.get("shock_hours", 4))
        n = int(p["cooldown_hours"]) + k
        if "BTCUSDT" not in view.close.columns:
            return False
        btc = view.close["BTCUSDT"].iloc[-(n + 1):]
        r = btc / btc.shift(k) - 1.0
        return bool((r.iloc[-int(p["cooldown_hours"]):] <= -float(p["shock_4h"])).any())
