"""Independent archive-prefix provenance, causal quotes and signed-cash audit.
Adapted from the saved independent v1 audit. Dataset counts are derived from
the frozen plan, not changed strategy thresholds. No fitting or broker imports.
"""
from decimal import Decimal
from pathlib import Path
import argparse,hashlib,json,re
import numpy as np,pandas as pd
PROJECT=Path("/home/ubuntu/test/MiniMax")
REPORT={"checks":[],"scope":"independent saved-artifact arithmetic; no performance selection"}
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(name, passed, **evidence):
    REPORT["checks"].append({"name": name, "passed": bool(passed), **evidence})


def account_events(events, seed):
    cash = Decimal(str(seed))
    longs, shorts = {}, {}
    for r in events:
        a = r["asset"]
        qty, price, fee = (Decimal(str(r[k])) for k in ("quantity", "price_usd", "fee"))
        assert qty > 0 and price > 0 and fee >= 0
        cash -= fee
        action = r["action"]
        if action == "Buy Long":
            cash -= qty * price
            longs[a] = longs.get(a, Decimal(0)) + qty
        elif action == "Sell Long":
            cash += qty * price
            longs[a] = longs.get(a, Decimal(0)) - qty
            assert longs[a] >= Decimal("-1e-8")
        elif action == "Open Short":
            cash += qty * price
            shorts[a] = shorts.get(a, Decimal(0)) + qty
        elif action == "Cover Short":
            cash -= qty * price
            shorts[a] = shorts.get(a, Decimal(0)) - qty
            assert shorts[a] >= Decimal("-1e-8")
        else:
            raise AssertionError("Unknown action")
    return cash, longs, shorts


def canonical_quotes(raw):
    columns = ["ts_utc", "pair", "max_bid", "min_ask", "last_price"]
    raw = raw[columns].copy()
    raw["ts_utc"] = pd.to_datetime(raw.ts_utc, utc=True)
    unique = raw.drop_duplicates()
    ambiguous = unique.loc[unique.duplicated(["ts_utc", "pair"], keep=False), ["ts_utc", "pair"]]
    keys = pd.MultiIndex.from_frame(ambiguous.drop_duplicates())
    bad = pd.MultiIndex.from_frame(raw[["ts_utc", "pair"]]).isin(keys)
    return unique.loc[~pd.MultiIndex.from_frame(unique[["ts_utc", "pair"]]).isin(keys)].sort_values(
        ["ts_utc", "pair"]).reset_index(drop=True), raw.loc[bad].copy()


def independent_universe(close, volume, t, declared):
    cfg = declared["validation"]
    u = cfg["universe"]
    c, q = close.loc[:t], volume.loc[:t]
    labels = (c.index - pd.Timedelta(hours=cfg["grid_hour_utc"])).ceil("D") + pd.Timedelta(
        hours=cfg["grid_hour_utc"])
    exists = c.notna().groupby(labels).sum() > 0
    qdaily = q.groupby(labels).sum(min_count=1)
    days = pd.date_range(exists.index[0], exists.index[-1], freq="D")
    exists = exists.reindex(days, fill_value=False)
    qdaily = qdaily.reindex(days)
    previous = exists.cumsum().shift(1, fill_value=0).loc[t]
    ok = exists.loc[t] & (previous >= u["min_history_days"])
    allowed_coins = {s.replace("/USD", "USDT") for s in declared["pairs"]}
    eligible = []
    for c in close.columns:
        symbol = c.split("~", 1)[0]
        if ok[c] and symbol not in u["exclude"] and symbol not in u["stablecoins"] and not re.match(
                u["leveraged_regex"], symbol):
            eligible.append(c)
    sums = qdaily.rolling(u["volume_days"], min_periods=1).sum().loc[t]
    ranked = sorted(eligible, key=lambda c: (-sums[c], c))[:u["top_n"]]
    return sorted(c for c in ranked if c in allowed_coins)


def gate_rows(plan, close, qv):
    p = plan["models"]["book_cashshort_confirm"]["params"]
    rows = []
    grids = sorted(pd.Timestamp(t) for t in plan["universe"])
    for stamp, weights in plan["models"][NAMES[0]]["targets"].items():
        t = pd.Timestamp(stamp)
        grid = max(g for g in grids if g <= t)
        universe = plan["universe"][str(grid)]
        symbols = sorted(set(universe).intersection(qv.columns))
        pastq = qv.reindex(index=pd.date_range(end=t, periods=p["liquidity_hours"], freq="h"), columns=symbols)
        eligible = np.isfinite(pastq).all() & (pastq >= 0).all() & (pastq.sum() > 0)
        selected = pastq.sum()[eligible].sort_index().sort_values(ascending=False, kind="mergesort").head(
            p["breadth_top_n"]).index.tolist()
        endpoints = close.reindex(index=[t - pd.Timedelta(hours=p["breadth_hours"]), t], columns=selected)
        bad_endpoints = [c for c in selected if not (np.isfinite(endpoints[c]).all() and (endpoints[c] > 0).all())]
        breadth = float(((endpoints.iloc[-1] / endpoints.iloc[0] - 1) > 0).mean()) if not bad_endpoints else None
        warm = p["btc_ema_days"] * 24 * p["btc_ema_warmup_spans"] + 1
        btc = close[p["btc_symbol"]].reindex(pd.date_range(end=t, periods=warm, freq="h"))
        btc_complete = bool(np.isfinite(btc).all() and (btc > 0).all())
        ema = float(btc.ewm(span=p["btc_ema_days"] * 24, adjust=False).mean().iloc[-1]) if btc_complete else None
        ret = float(btc.iloc[-1] / btc.loc[t - pd.Timedelta(hours=p["btc_return_hours"])] - 1) if btc_complete else None
        under = bool(btc_complete and btc.iloc[-1] < ema)
        negative = bool(btc_complete and ret < 0)
        longgross = sum(v for v in weights.values() if v > 0)
        cash = max(0., 1. - longgross)
        enough = len(selected) >= p["breadth_min_coins"]
        weak = bool(breadth is not None and breadth <= p["breadth_max_positive"])
        reasons = []
        if cash <= 1e-12:
            reasons.append("no_unused_target_cash")
        if not enough:
            reasons.append("fewer_than20_liquid")
        if bad_endpoints:
            reasons.append("missing_selected_breadth_endpoint")
        if not btc_complete:
            reasons.append("BTC_warmup_incomplete")
        if btc_complete and not under:
            reasons.append("BTC_not_below_EMA20")
        if btc_complete and not negative:
            reasons.append("BTC168h_return_nonnegative")
        if breadth is not None and not weak:
            reasons.append("breadth_positive_fraction_above40pct")
        rows.append({"time_utc":stamp, "universe_grid_utc":str(grid), "long_gross":longgross,
                     "unused_cash":cash, "short_budget":min(p["short_gross_cap"], cash),
                     "universe_size":len(universe), "volume_eligible":int(eligible.sum()),
                     "breadth_selected":len(selected), "breadth_positive_fraction":breadth,
                     "missing_breadth_endpoints":",".join(bad_endpoints),
                     "btc_warmup_required":warm, "btc_warmup_nonmissing":int(btc.notna().sum()),
                     "btc_close":float(btc.iloc[-1]), "btc_ema20":ema, "btc_under_ema20":under,
                     "btc_return168h":ret, "btc_return168h_negative":negative,
                     "market_gate":enough and not bad_endpoints and btc_complete and under and negative and weak,
                     "blocked_reasons":",".join(reasons)})
    return rows


def raw_recorded_quotes(plan):
    end = pd.Timestamp(plan["end"])
    pairs = {a + "/USD" for a in plan["assets"]}
    parts = []
    for day in pd.date_range("2026-10-05", "2026-10-09"):
        path = PROJECT / "results/book/scalp/quotes" / (day.strftime("%Y%m%d") + ".csv")
        for chunk in pd.read_csv(path, chunksize=150000):
            stamps = pd.to_datetime(chunk.ts_utc, utc=True)
            selected = chunk[(stamps <= end) & chunk.pair.isin(pairs)]
            if len(selected):
                parts.append(selected.copy())
            if stamps.min() > end:
                break
    return pd.concat(parts, ignore_index=True)


def quote_arrays(times, assets, prices, quotes, cfg):
    ns = pd.DatetimeIndex(times).asi8
    pi = prices.index.asi8
    j = np.searchsorted(pi, ns, side="right") - 1
    page = (ns - pi[np.maximum(j, 0)]) / 1e9
    result = {}
    for a in assets:
        q = quotes[quotes.pair == a + "/USD"].sort_values("ts_utc")
        qi = pd.DatetimeIndex(q.ts_utc).asi8
        k = np.searchsorted(qi, ns, side="right") - 1
        age = (ns - qi[np.maximum(k, 0)]) / 1e9
        recorded = (k >= 0) & (age <= cfg["quote_max_age"])
        mark = prices[a + "USDT"].to_numpy()[np.maximum(j, 0)]
        bid = np.where(recorded, q.max_bid.to_numpy()[np.maximum(k, 0)], mark * (1 - cfg["proxy_half_spread"]))
        ask = np.where(recorded, q.min_ask.to_numpy()[np.maximum(k, 0)], mark * (1 + cfg["proxy_half_spread"]))
        valid = recorded | ((j >= 0) & (page <= cfg["minute_max_age"]))
        assert valid.all() and np.isfinite(bid).all() and np.isfinite(ask).all() and (bid > 0).all() and (ask >= bid).all()
        result[a] = {"bid":bid, "ask":ask,
                     "source":np.where(recorded, "recorded_roostoo", "verified_archive_proxy"),
                     "age":np.where(recorded, age, page),
                     "stamp_ns":np.where(recorded, qi[np.maximum(k, 0)], pi[np.maximum(j, 0)])}
    return result


def marked(cash, longs, shorts, endpoint_quotes):
    eq = cash
    gross = Decimal(0)
    for a, qty in longs.items():
        value = qty * Decimal(str(endpoint_quotes[a + "/USD"]["bid"]))
        eq += value
        gross += value
    for a, qty in shorts.items():
        value = qty * Decimal(str(endpoint_quotes[a + "/USD"]["ask"]))
        eq -= value
        gross += value
    return float(eq), float(gross)


def audit_replay(plan):
    audit = json.loads((INPUT / "prefix_audit.json").read_text())
    cfg = audit["config"]
    fine = json.loads((INPUT / "fine_data_manifest.json").read_text())
    check("fine frozen plan hash", fine["plan_sha256"] == sha(INPUT / "prefix_plan.json"))
    for n, h in fine["files"].items():
        check("fine immutable " + n, sha(INPUT / n) == h)
    for r in fine["archives"]:
        check("archive checksum " + r["symbol"] + " " + r["day"], sha(r["path"]) == r["sha256"])
    check("five verified archives per selected asset", len(fine["archives"]) == 5*len(plan["assets"]))
    raw = pd.read_parquet(INPUT / "prefix_minutes.parquet")
    check("7200 unique complete archive minutes per asset", len(raw) == 7200*len(plan["assets"]) and
          not raw.duplicated(["timestamp", "symbol"]).any() and (raw.groupby("symbol").size() == 7200).all())
    prices = raw.pivot(index="timestamp", columns="symbol", values="close").sort_index()
    quotes = pd.read_parquet(INPUT / "prefix_quotes.parquet")
    quotes["ts_utc"] = pd.to_datetime(quotes.ts_utc, utc=True)
    canonical, bad = canonical_quotes(raw_recorded_quotes(plan))
    actual = quotes.sort_values(["ts_utc", "pair"]).reset_index(drop=True)
    check("full quote quarantine independently reproduced", canonical.equals(actual),
          canonical_rows=len(canonical), quarantined_rows=len(bad))
    check("all conflict quarantine counts agree with receipt", len(bad) == fine["quote_policy"]["conflicting_rows_quarantined"] and
          len(bad[["ts_utc", "pair"]].drop_duplicates()) == fine["quote_policy"]["conflicting_keys_quarantined"])
    check("quote canonical has no duplicate keys", not actual.duplicated(["ts_utc", "pair"]).any())
    summary = pd.read_csv(INPUT / "prefix_comparison.csv").set_index("model")
    endpoint_values = {}
    for name in (*NAMES, "observed_literal_ledger"):
        events = pd.read_csv(INPUT / (name + "_prefix_events.csv"))
        path = pd.read_csv(INPUT / (name + "_prefix_equity.csv"))
        endpoint = json.loads((INPUT / (name + "_prefix_endpoint.json")).read_text())
        stage = events[events.phase != "terminal"].copy()
        stage["time_utc"] = pd.to_datetime(stage.time_utc, utc=True)
        path["time_utc"] = pd.to_datetime(path.time_utc, utc=True)
        check(name + " event times within prefix", (stage.time_utc >= pd.Timestamp(plan["start"])).all()
              and (stage.time_utc <= pd.Timestamp(plan["end"])).all())
        check(name + " complete common path endpoints", path.time_utc.iloc[0] == pd.Timestamp(plan["start"])
              and path.time_utc.iloc[-1] == pd.Timestamp(plan["end"]))
        cash, longs, shorts = account_events(stage.to_dict("records"), cfg["seed"])
        eq, gross = marked(cash, longs, shorts, endpoint["endpoint_quotes"])
        full = eq - cfg["fee"] * gross
        endpoint_values[name] = full
        check(name + " endpoint marked independent signed cash", abs(eq - endpoint["marked_equity"]) < 1e-6)
        check(name + " endpoint full-close costs", abs(full - endpoint["full_cost_liquidated_equity"]) < 1e-6)
        check(name + " published full-cost return", abs(full / cfg["seed"] - 1 -
              summary.loc[name, "full_cost_liquidated_return"]) < 1e-12)
        # Independent vector path reconstruction from cumulative signed notional.
        ev_ns = pd.DatetimeIndex(stage.time_utc).asi8
        where = np.searchsorted(ev_ns, pd.DatetimeIndex(path.time_utc).asi8, side="right") - 1
        signs = stage.action.map({"Buy Long":-1, "Sell Long":1, "Open Short":1, "Cover Short":-1}).to_numpy()
        changes = signs * stage.quantity.to_numpy() * stage.price_usd.to_numpy() - stage.fee.to_numpy()
        cash_steps = cfg["seed"] + np.cumsum(changes)
        cash_path = np.where(where >= 0, cash_steps[np.maximum(where, 0)], cfg["seed"])
        qp = quote_arrays(path.time_utc, cfg["assets"], prices, actual, cfg)
        calculated_eq, calculated_gross = cash_path.copy(), np.zeros(len(path))
        for a in cfg["assets"]:
            buy = np.where((stage.asset == a) & (stage.action == "Buy Long"), stage.quantity,
                           np.where((stage.asset == a) & (stage.action == "Sell Long"), -stage.quantity, 0.))
            short = np.where((stage.asset == a) & (stage.action == "Open Short"), stage.quantity,
                             np.where((stage.asset == a) & (stage.action == "Cover Short"), -stage.quantity, 0.))
            lp = np.where(where >= 0, np.cumsum(buy)[np.maximum(where, 0)], 0.)
            sp = np.where(where >= 0, np.cumsum(short)[np.maximum(where, 0)], 0.)
            calculated_eq += lp * qp[a]["bid"] - sp * qp[a]["ask"]
            calculated_gross += lp * qp[a]["bid"] + sp * qp[a]["ask"]
            check(name + " signed position " + a, np.allclose(lp - sp, path[a], rtol=0, atol=1e-8))
        check(name + " full equity path signed-cash identity",
              np.allclose(calculated_eq, path.equity, rtol=0, atol=1e-6),
              maximum_error_usd=float(np.max(np.abs(calculated_eq - path.equity))))
        check(name + " full gross path identity", np.allclose(calculated_gross, path.gross, rtol=0, atol=1e-6))
        if name=="observed_literal_ledger":
            check(name+" signed cash path identity",np.allclose(cash_path,path["signed_cash"],rtol=0,atol=1e-6))
        else:
            basis,bound=short_basis_steps(stage,cfg["precisions"])
            basis_path=np.where(where>=0,basis[np.maximum(where,0)],0.)
            bound_path=np.where(where>=0,bound[np.maximum(where,0)],0.)
            # Signed ledger cash includes short proceeds; free broker cash excludes both proceeds and locked collateral.
            check(name+" free cash within independent quantity-rounding interval",((path.cash>=cash_path-2*basis_path-bound_path-1e-6)&(path.cash<=cash_path-2*basis_path+1e-6)).all())
            check(name+" reported locked collateral within independent entry-basis interval",((path.locked_collateral>=basis_path-1e-6)&(path.locked_collateral<=basis_path+bound_path+1e-6)).all())
            check(name+" free plus locked cash reconciles short basis",np.allclose(path.cash+path.locked_collateral+basis_path,cash_path,rtol=0,atol=1e-6))
        check(name + " reported MDD", abs(float(-(path.equity / path.equity.cummax() - 1).min()) -
              summary.loc[name, "maximum_drawdown"]) < 1e-12)
        check(name + " reported fees/turnover", abs(stage.fee.sum() - summary.loc[name, "fees"]) < 1e-8 and
              abs((stage.quantity * stage.price_usd).sum() / cfg["seed"] -
                  summary.loc[name, "notional_turnover_seed"]) < 1e-12)
        if name != "observed_literal_ledger":
            audit_cycles(name, stage, summary.loc[name])
            check(name + " 1h causal execution lag", ((stage.time_utc -
                  pd.to_datetime(stage.decision_utc, utc=True)).dt.total_seconds() >= 3600).all())
            check(name + " quote sources never future", (pd.to_datetime(stage.source_time, utc=True) <= stage.time_utc).all())
            qfills = quote_arrays(stage.time_utc, cfg["assets"], prices, actual, cfg)
            expected_price, expected_source, expected_age, expected_stamp = [], [], [], []
            for i, r in stage.reset_index(drop=True).iterrows():
                q = qfills[r.asset]
                expected_price.append(q["ask" if r.action in ["Buy Long", "Cover Short"] else "bid"][i])
                expected_source.append(q["source"][i])
                expected_age.append(q["age"][i])
                expected_stamp.append(q["stamp_ns"][i])
            check(name + " every fill correct asof bidask", np.allclose(stage.price_usd, expected_price, rtol=0, atol=1e-10))
            check(name + " every fill exact source/age/stamp", (stage.source.to_numpy() == expected_source).all() and
                  np.allclose(stage.source_age_seconds, expected_age) and np.array_equal(
                      pd.DatetimeIndex(pd.to_datetime(stage.source_time, utc=True)).asi8, expected_stamp))
            check(name + " each fee10bps", np.allclose(stage.fee, stage.quantity * stage.price_usd * .001, rtol=0, atol=1e-9))
            allcash, alllong, allshort = account_events(events.to_dict("records"), cfg["seed"])
            practical, _ = marked(allcash, alllong, allshort, endpoint["endpoint_quotes"])
            check(name + " practical terminal independent cash", abs(practical - endpoint["liquidated_equity"]) < 1e-6)
        else:
            supplied = pd.read_csv(PROJECT / "results/book/20261009-observed-baseline/revisions/t001-confirmed/observed_trades_corrected.csv")
            cols = ["trade_id", "asset", "action", "quantity", "price_usd"]
            check("observed exact unscaled original fills", supplied[cols].equals(stage[cols]))
            check("observed T001 confirmed19.98fee", float(stage.loc[stage.trade_id == "T001", "fee"].iloc[0]) == 19.98)
            other = stage[stage.trade_id != "T001"]
            check("observed other fees conditional10bps", np.allclose(other.fee, other.quantity * other.price_usd * .001))
            after5, _, _ = account_events(stage.iloc[:5].to_dict("records"), cfg["seed"])
            check("observed literal initial cash deficit preserved", float(after5) < 0 and
                  abs(-float(after5) - endpoint["initial_signed_cash_deficit"]) < 1e-6,
                  deficit_usd=-float(after5))
    check("all endpoint outcomes finite", np.isfinite(list(endpoint_values.values())).all())
    check("zero execution/valuation failures", sum(audit["failure_counts"].values()) == 0)
    check("empty completed-cycle samples have no hit rate", summary.loc[summary.short_cycles_completed==0,"short_cycle_hit_rate"].isna().all())
    REPORT["results"] = {name: {"full_cost_equity": value,
                                "full_cost_return": value / cfg["seed"] - 1}
                         for name, value in endpoint_values.items()}
    REPORT["scope_warnings"] = audit["warnings"]


def short_basis_steps(events,precisions):
 states={};basis=[];bound=[]
 for r in events.itertuples():
  if r.action=="Open Short":
   a=states.setdefault(r.asset,{"qty":0.,"basis":0.,"bound":0.})
   a["qty"]+=r.quantity;a["basis"]+=r.quantity*r.price_usd
   a["bound"]+=r.price_usd*10.**(-precisions[r.asset])
  elif r.action=="Cover Short":
   a=states[r.asset];f=min(1.,r.quantity/a["qty"])
   a["qty"]-=r.quantity;a["basis"]*=1-f;a["bound"]*=1-f
   if a["qty"]<1e-8:del states[r.asset]
  basis.append(sum(x["basis"] for x in states.values()))
  bound.append(sum(x["bound"] for x in states.values()))
 return np.asarray(basis),np.asarray(bound)

def audit_cycles(name,stage,row):
 active={};pnls=[];onsets=0
 for r in stage.itertuples():
  if r.action=="Open Short":
   if r.asset not in active:active[r.asset]={"qty":0.,"net":0.};onsets+=1
   active[r.asset]["qty"]+=r.quantity
   active[r.asset]["net"]+=r.quantity*r.price_usd-r.fee
  elif r.action=="Cover Short":
   a=active[r.asset];a["qty"]-=r.quantity;a["net"]-=r.quantity*r.price_usd+r.fee
   if abs(a["qty"])<1e-8:pnls.append(a["net"]);del active[r.asset]
 expected=float(np.mean(np.array(pnls)>0)) if pnls else np.nan
 check(name+" completed/censored cycles independently counted",len(pnls)==row.short_cycles_completed and len(active)==row.short_cycles_censored)
 check(name+" completed-cycle hit rate",bool(np.isnan(expected) and pd.isna(row.short_cycle_hit_rate)) or abs(expected-row.short_cycle_hit_rate)<1e-12)
 check(name+" completed-cycle after-cost cash PnL",abs(sum(pnls)-row.completed_short_net_pnl)<1e-6)
def audit_plan():
 plan=json.loads((INPUT/"prefix_plan.json").read_text());m=json.loads((INPUT/"data_manifest.json").read_text())
 for n,r in m["files"].items():check("pinned data "+n,sha(INPUT/n)==r["sha256"])
 check("plan data receipt",sha(INPUT/"data_manifest.json")==plan["data_manifest_sha256"])
 close=pd.read_parquet(INPUT/"hourly_close.parquet");qv=pd.read_parquet(INPUT/"hourly_qv.parquet")
 check("aligned unique complete hourly grid",close.index.equals(qv.index) and close.columns.equals(qv.columns) and close.index.is_unique and close.index.is_monotonic_increasing and close.index[-1]==pd.Timestamp(m["hourly_complete_through"]))
 declared=json.loads((PROJECT/"results/book/20261010-short-next-prefix-v3/universe_config.json").read_text())
 for stamp,u in plan["universe"].items():check("causal daily universe "+stamp,independent_universe(close,qv,pd.Timestamp(stamp),declared)==u)
 for name,recipe in plan["models"].items():
  for p,h in recipe["source_hashes"].items():check(name+" source "+Path(p).name,sha(p)==h)
  times=pd.DatetimeIndex(pd.to_datetime(list(recipe["targets"]),utc=True))
  expected=len(pd.date_range(pd.Timestamp(plan["start"]),pd.Timestamp(plan["end"]).floor("h"),freq="4h")) if recipe["spec"]["rebalance_hours"]==4 else 6
  check(name+" declared decision count",len(times)==expected,actual=len(times))
  for stamp,w in recipe["targets"].items():
   check(name+" target gross "+stamp,sum(abs(v) for v in w.values())<=1+1e-12 and all(np.isfinite(v) for v in w.values()))
   if recipe["spec"]["uses_shorts"]:
    p=recipe["params"];neg=pd.Series({c:-v for c,v in w.items() if v<0},dtype=float)
    check(name+" short caps "+stamp,neg.sum()<=p["short_gross_cap"]+1e-12 and (neg<=p["short_coin_cap"]+1e-12).all())
 if "book_cashshort_confirm" in plan["models"]:
  rows=gate_rows(plan,close,qv);pd.DataFrame(rows).to_csv(OUTPUT/"prefix_regime_diagnostics.csv",index=False)
  check("all lookback volume and breadth endpoints complete",all(r["breadth_selected"]>=20 and not r["missing_breadth_endpoints"] and r["btc_warmup_nonmissing"]==r["btc_warmup_required"] for r in rows))
 return plan
def main():
 global INPUT,OUTPUT,NAMES
 ap=argparse.ArgumentParser();ap.add_argument("--input",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
 INPUT=a.input;OUTPUT=a.out;OUTPUT.mkdir(parents=True,exist_ok=True)
 NAMES=tuple(json.loads((INPUT/"prefix_plan.json").read_text())["models"])
 plan=audit_plan();audit_replay(plan)
 REPORT["passed"]=all(r["passed"] for r in REPORT["checks"]);REPORT["count"]=len(REPORT["checks"])
 REPORT["analysis_sha256"]=sha(__file__);REPORT["input_plan_sha256"]=sha(INPUT/"prefix_plan.json")
 (OUTPUT/"audit.json").write_text(json.dumps(REPORT,indent=2))
 print(json.dumps({"passed":REPORT["passed"],"count":REPORT["count"],"failed":[r for r in REPORT["checks"] if not r["passed"]],"results":REPORT.get("results")},indent=2),flush=True)
 if not REPORT["passed"]:raise SystemExit(1)
if __name__=="__main__":main()
