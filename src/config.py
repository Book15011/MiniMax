from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config.yaml"


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def universe(cfg: dict) -> list[str]:
    pairs = cfg.get("universe") or []
    if not pairs:
        raise ValueError("config.yaml has an empty 'universe'")
    if len(set(pairs)) != len(pairs):
        raise ValueError("config.yaml 'universe' contains duplicates")
    bad = [p for p in pairs if not isinstance(p, str) or not p.endswith("/USD")]
    if bad:
        raise ValueError(f"universe entries must look like COIN/USD: {bad}")
    return pairs


def binance_symbol(pair: str) -> str:
    coin, _quote = pair.split("/")
    return f"{coin}USDT"


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p
