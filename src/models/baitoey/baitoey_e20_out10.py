"""Research only (research/baitoey/prereg/20261009-faster-down-switch.md): e20v45 with its down trigger at -1%."""
from __future__ import annotations

from dataclasses import replace

from src.models.baitoey._fast_down import FastDown


class Out10(FastDown):
    spec = replace(FastDown.spec, name="baitoey_e20_out10", author="baitoey",
                   description="research only: pol_switch_vt_tl_e20v45 with its down trigger at -1% (up trigger +3%)")


MODEL = Out10()
