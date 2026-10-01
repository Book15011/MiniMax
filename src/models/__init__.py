"""Model registry: every module src/models/<package>/<name>.py that defines MODEL is a model.

Packages: `baselines` (team references, never compete) and one package per member.
"""
from __future__ import annotations

import importlib
import pkgutil

from src.contracts import MEMBERS, Model

PACKAGES = ("baselines",) + MEMBERS


def discover() -> dict[str, Model]:
    found: dict[str, Model] = {}
    for pkg_name in PACKAGES:
        pkg = importlib.import_module(f"{__name__}.{pkg_name}")
        for info in pkgutil.iter_modules(pkg.__path__):
            if info.name.startswith("_"):
                continue
            mod = importlib.import_module(f"{pkg.__name__}.{info.name}")
            model = getattr(mod, "MODEL", None)
            if model is None:
                continue
            spec = model.spec
            spec.validate()
            expected = "team" if pkg_name == "baselines" else pkg_name
            if spec.author != expected:
                raise ValueError(f"{spec.name}: lives in src/models/{pkg_name}/ but author is '{spec.author}'")
            if spec.name != info.name:
                raise ValueError(f"{spec.name}: module file must be named {spec.name}.py (is {info.name}.py)")
            if spec.name in found:
                raise ValueError(f"duplicate model name {spec.name}")
            found[spec.name] = model
    return found


def get(name: str) -> Model:
    models = discover()
    if name not in models:
        raise SystemExit(f"unknown model '{name}'. Registered: {', '.join(sorted(models))}")
    return models[name]


def by_method(method: str) -> dict[str, Model]:
    return {n: m for n, m in discover().items() if m.spec.method == method}
