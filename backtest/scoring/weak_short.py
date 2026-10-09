"""Hourly short-onset diagnostics from window-specific cached fills.

The ledger records weights, not executed quantities. Labels are unit-short price
proxies with predeclared fees and spread stress, never account sleeve PnL. Cached
fills already include the engine lag. Hourly closes cannot identify intrahour TP/SL
order or validate minute/second trading. Guard onsets are counted separately.
"""
from __future__ import annotations
import numbers
import numpy as np
import pandas as pd

TRADE_COLUMNS = {"window_start", "hour", "time_utc", "kind", "series", "w_before",
                 "w_after", "notional_usd", "fee_usd", "spread_usd"}
KINDS = {"entry", "decision", "guard"}


def _utc(values, name):
    try:
        idx = pd.DatetimeIndex(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} needs timezone-aware timestamps") from exc
    if idx.tz is None or idx.hasnans:
        raise ValueError(f"{name} needs timezone-aware timestamps without missing values")
    idx = idx.tz_convert("UTC")
    if not idx.equals(idx.floor("h")):
        raise ValueError(f"{name} needs whole clock hours")
    return idx


def _configuration(config):
    required = {"fee_rate", "half_spread", "horizons_hours", "take_profit", "stop_loss",
                "barrier_max_hours", "tolerance", "minimum_episodes"}
    if not isinstance(config, dict) or required - set(config):
        raise ValueError("short configuration must predeclare all assumptions")
    c = dict(config)
    for key in ("fee_rate", "half_spread", "take_profit", "stop_loss", "tolerance"):
        if isinstance(c[key], bool) or not isinstance(c[key], numbers.Real) or not np.isfinite(c[key]):
            raise ValueError(f"invalid short configuration: {key}")
        c[key] = float(c[key])
    if not 0 <= c["fee_rate"] < 1 or not 0 <= c["half_spread"] < 1:
        raise ValueError("short fee_rate and half_spread must lie in [0, 1)")
    if c["take_profit"] <= 0 or c["stop_loss"] <= 0 or not 0 < c["tolerance"] < 1:
        raise ValueError("short barriers and tolerance must be positive")
    for key in ("barrier_max_hours", "minimum_episodes"):
        if isinstance(c[key], bool) or not isinstance(c[key], numbers.Integral) or c[key] <= 0:
            raise ValueError(f"short {key} must be a positive integer")
    hs = c["horizons_hours"]
    if not isinstance(hs, (list, tuple)) or not hs:
        raise ValueError("short horizons_hours must be nonempty")
    if any(isinstance(h, bool) or not isinstance(h, numbers.Integral) or h <= 0 for h in hs):
        raise ValueError("short horizons_hours must contain positive integers")
    if len(set(hs)) != len(hs) or list(hs) != sorted(hs):
        raise ValueError("short horizons_hours must be unique and increasing")
    c["horizons_hours"] = [int(h) for h in hs]
    return c


def _proxy(entry, covers, c):
    ratio = np.asarray(covers, dtype=float) * (1 + c["half_spread"]) / (entry * (1 - c["half_spread"]))
    return 1 - ratio - c["fee_rate"] * (1 + ratio)


def _path(close, symbol, start, end):
    grid = pd.date_range(start, end, freq="h")
    return (close[symbol].reindex(grid).to_numpy(dtype=float) if symbol in close
            else np.full(len(grid), np.nan))


def _valid(path):
    return bool(np.isfinite(path).all() and (path > 0).all())


def short_diagnostics(trades, close, starts, hours, config):
    """Return windows, episodes, summary for complete cash-start ledgers.

    Correct/valid is after-cost fixed-horizon proxy precision. Missing prices and
    horizons after the endpoint are unresolved. Rebound losses are sampled profitable
    opportunities followed by nonpositive endpoint proxies. First-touch barriers apply
    to the after-cost proxy and always retain intrahour ambiguity. Episode cover proxies
    ignore additions/partial-cover sizes; full account attribution is unavailable.
    """
    c = _configuration(config)
    if isinstance(hours, bool) or not isinstance(hours, numbers.Integral) or hours <= 0:
        raise ValueError("hours must be a positive integer")
    starts = _utc(starts, "starts")
    if not len(starts) or not starts.is_unique or not starts.is_monotonic_increasing:
        raise ValueError("starts must be nonempty, unique and monotonic")
    if not isinstance(close, pd.DataFrame) or not close.columns.is_unique:
        raise ValueError("close needs unique symbol columns")
    close = close.copy(deep=False)
    close.index = _utc(close.index, "close index")
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError("close index must be unique and monotonic")
    if not isinstance(trades, pd.DataFrame) or set(trades.columns) != TRADE_COLUMNS:
        raise ValueError("unknown trade cache schema")
    tr = trades.copy()
    if len(tr):
        tr["window_start"] = _utc(tr["window_start"], "trade window_start")
        tr["time_utc"] = _utc(tr["time_utc"], "trade time_utc")
        if not tr["kind"].isin(KINDS).all():
            raise ValueError("unknown trade kind")
        if not tr["series"].map(lambda x: isinstance(x, str) and bool(x)).all():
            raise ValueError("trade series must be a symbol")
        try:
            vals = tr[["hour", "w_before", "w_after", "notional_usd", "fee_usd", "spread_usd"]].to_numpy(dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError("nonnumeric trade ledger schema") from exc
        if not np.isfinite(vals).all():
            raise ValueError("trade ledger values must be finite")
        hs = vals[:, 0]
        if (hs < 1).any() or (hs != np.floor(hs)).any():
            raise ValueError("trade hour must be a positive integer")
        if (vals[:, 3:] < 0).any():
            raise ValueError("negative trade notional, fee or spread")
        expected = pd.DatetimeIndex(tr["window_start"]) + pd.to_timedelta(hs, unit="h")
        if not expected.equals(pd.DatetimeIndex(tr["time_utc"])):
            raise ValueError("trade timestamp disagrees with window hour")
        if tr.duplicated(["window_start", "time_utc", "series"]).any():
            raise ValueError("duplicate coin fill in a clock hour")
        tr = tr[tr["window_start"].isin(starts) & (tr["hour"] <= hours)]
        for _, group in tr.groupby("window_start", sort=False):
            if not group["time_utc"].is_monotonic_increasing:
                raise ValueError("trade ledger must be monotonic within windows")
    count_names = ["onsets", "guard_onsets", "closed_episodes", "terminal_censored",
                   "reweighted_episodes", "cover_proxy_wins", "cover_proxy_valid",
                   "cover_rebound_losses", "barrier_take_profit_sampled",
                   "barrier_stop_loss_sampled", "barrier_no_sampled_touch",
                   "barrier_censored", "barrier_missing_price", "barrier_intrahour_ambiguous"]
    for h in c["horizons_hours"]:
        count_names += [f"{key}_{h}h" for key in ("valid", "correct", "loss", "wrong_direction",
                                                "cost_only_loss", "unresolved", "rebound_losses")]
    wrs = {t: {key: 0 for key in count_names} for t in starts}
    episodes = []
    tol = c["tolerance"]

    def finish(ep, cover_row, t0):
        wr, e = wrs[t0], dict(ep)
        end = t0 + pd.Timedelta(hours=hours)
        eligible = e["eligible_onset"]
        e["terminal_censored"] = cover_row is None
        e["cover_hour"] = int(cover_row["hour"]) if cover_row else None
        e["cover_time"] = cover_row["time_utc"] if cover_row else pd.NaT
        e["duration_hours"] = (int(cover_row["hour"]) if cover_row else hours) - e["entry_hour"]
        e["account_short_pnl_available"] = False
        e["cover_proxy_net"], e["cover_proxy_rebound_loss"] = np.nan, False
        if eligible:
            wr["onsets"] += 1
            wr["terminal_censored"] += int(e["terminal_censored"])
            wr["closed_episodes"] += int(not e["terminal_censored"])
            wr["reweighted_episodes"] += int(e["reweighted"])
        else:
            wr["guard_onsets"] += 1
        if cover_row:
            path = _path(close, e["series"], e["entry_time"], e["cover_time"])
            if _valid(path):
                net = _proxy(path[0], path, c)
                e["cover_proxy_net"] = float(net[-1])
                e["cover_proxy_rebound_loss"] = bool(np.max(net[1:]) > 0 and net[-1] <= 0) if len(net) > 1 else False
                if eligible:
                    wr["cover_proxy_valid"] += 1
                    wr["cover_proxy_wins"] += int(net[-1] > 0)
                    wr["cover_rebound_losses"] += int(e["cover_proxy_rebound_loss"])
        for h in c["horizons_hours"]:
            target = e["entry_time"] + pd.Timedelta(hours=h)
            e[f"proxy_net_{h}h"], e[f"gross_short_return_{h}h"] = np.nan, np.nan
            e[f"rebound_loss_{h}h"] = False
            if target > end:
                status = "CENSORED"
            else:
                path = _path(close, e["series"], e["entry_time"], target)
                status = "VALID" if _valid(path) else "MISSING_PRICE"
                if status == "VALID":
                    net = _proxy(path[0], path, c)
                    gross = 1 - float(path[-1] / path[0])
                    rebound = bool(np.max(net[1:]) > 0 and net[-1] <= 0)
                    e[f"proxy_net_{h}h"], e[f"gross_short_return_{h}h"] = float(net[-1]), gross
                    e[f"rebound_loss_{h}h"] = rebound
                    if eligible:
                        wr[f"valid_{h}h"] += 1
                        wr[f"correct_{h}h"] += int(net[-1] > 0)
                        wr[f"loss_{h}h"] += int(net[-1] <= 0)
                        wr[f"wrong_direction_{h}h"] += int(gross <= 0)
                        wr[f"cost_only_loss_{h}h"] += int(gross > 0 and net[-1] <= 0)
                        wr[f"rebound_losses_{h}h"] += int(rebound)
            e[f"status_{h}h"] = status
            if eligible and status != "VALID":
                wr[f"unresolved_{h}h"] += 1
        target = e["entry_time"] + pd.Timedelta(hours=c["barrier_max_hours"])
        path = _path(close, e["series"], e["entry_time"], min(target, end))
        e["barrier_hour"], e["barrier_intrahour_order_unverified"] = None, True
        if not _valid(path):
            label = "MISSING_PRICE"
        else:
            net = _proxy(path[0], path, c)
            hit = np.flatnonzero((net[1:] >= c["take_profit"]) | (net[1:] <= -c["stop_loss"]))
            if len(hit):
                at = int(hit[0]) + 1
                e["barrier_hour"] = e["entry_hour"] + at
                label = "TAKE_PROFIT_SAMPLED" if net[at] >= c["take_profit"] else "STOP_LOSS_SAMPLED"
            else:
                label = "CENSORED" if target > end else "NO_SAMPLED_TOUCH"
        e["barrier_label"] = label
        if eligible:
            key = {"TAKE_PROFIT_SAMPLED": "barrier_take_profit_sampled",
                   "STOP_LOSS_SAMPLED": "barrier_stop_loss_sampled",
                   "NO_SAMPLED_TOUCH": "barrier_no_sampled_touch",
                   "CENSORED": "barrier_censored", "MISSING_PRICE": "barrier_missing_price"}[label]
            wr[key] += 1
            wr["barrier_intrahour_ambiguous"] += 1
        episodes.append(e)

    for t0, group in tr.groupby("window_start", sort=False):
        active = {}
        for row in group.to_dict("records"):
            symbol = row["series"]
            before, after = float(row["w_before"]) < -tol, float(row["w_after"]) < -tol
            if before != (symbol in active):
                raise ValueError("cash-start short ledger is incomplete or position sign is inconsistent")
            if not before and after:
                active[symbol] = {"window_start": t0, "series": symbol, "entry_hour": int(row["hour"]),
                                  "entry_time": row["time_utc"], "entry_kind": row["kind"],
                                  "eligible_onset": row["kind"] in {"entry", "decision"},
                                  "reweighted": False, "rebalance_rows": 0}
            elif before and not after:
                finish(active.pop(symbol), row, t0)
            elif before and after:
                active[symbol]["reweighted"] = True
                active[symbol]["rebalance_rows"] += 1
        for ep in active.values():
            finish(ep, None, t0)
    windows = pd.DataFrame.from_dict(wrs, orient="index").reindex(starts)
    windows.index.name = "window_start"
    episode_columns = ["window_start", "series", "entry_hour", "entry_time", "entry_kind",
                       "eligible_onset", "reweighted", "rebalance_rows", "terminal_censored",
                       "cover_hour", "cover_time", "duration_hours", "account_short_pnl_available",
                       "cover_proxy_net", "cover_proxy_rebound_loss", "barrier_hour",
                       "barrier_intrahour_order_unverified", "barrier_label"]
    for h in c["horizons_hours"]:
        episode_columns += [f"proxy_net_{h}h", f"gross_short_return_{h}h",
                            f"rebound_loss_{h}h", f"status_{h}h"]
    episodes = pd.DataFrame(episodes, columns=episode_columns)
    if len(episodes):
        episodes = episodes.sort_values(["window_start", "entry_time", "series"]).reset_index(drop=True)
        for t0, group in episodes[episodes["eligible_onset"]].groupby("window_start"):
            for h in c["horizons_hours"]:
                vals = group.loc[group[f"status_{h}h"] == "VALID", f"proxy_net_{h}h"]
                windows.loc[t0, f"mean_proxy_net_{h}h"] = float(vals.mean()) if len(vals) else np.nan
    for h in c["horizons_hours"]:
        if f"mean_proxy_net_{h}h" not in windows:
            windows[f"mean_proxy_net_{h}h"] = np.nan
        den = windows[f"valid_{h}h"].to_numpy()
        windows[f"precision_{h}h"] = np.divide(windows[f"correct_{h}h"].to_numpy(dtype=float), den,
                                              out=np.full(len(windows), np.nan), where=den > 0)
    totals = {key: int(windows[key].sum()) for key in count_names}
    summary = dict(totals)
    summary.update({"resolution": "hourly", "fine_resolution_supported": False,
                    "account_short_pnl_available": False,
                    "quote_source": "hourly close with fixed predeclared spread stress",
                    "execution_lag_source": "cached engine fills already include engine execution lag",
                    "barriers": "after-cost sampled close barriers; intrahour order UNVERIFIED",
                    "windows_with_onsets": int((windows["onsets"] > 0).sum()),
                    "minimum_episodes_met": totals["onsets"] >= c["minimum_episodes"],
                    "independence_claim": "none; uncertainty must cluster by historical windows",
                    "covered_proxy_scope": "first entry to final cover; reweights unweighted",
                    "config": c})
    for h in c["horizons_hours"]:
        summary[f"precision_{h}h"] = (totals[f"correct_{h}h"] / totals[f"valid_{h}h"]
                                     if totals[f"valid_{h}h"] else None)
        if len(episodes):
            vals = episodes.loc[episodes["eligible_onset"] & (episodes[f"status_{h}h"] == "VALID"),
                                f"proxy_net_{h}h"]
            summary[f"mean_proxy_net_{h}h"] = float(vals.mean()) if len(vals) else None
        else:
            summary[f"mean_proxy_net_{h}h"] = None
    return {"windows": windows, "episodes": episodes, "summary": summary}
