"""Team-readable audit report; no numeric ranking or strategy modification."""
from pathlib import Path
import hashlib,json
import pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax/.worktrees/book-book-recovery-stress")
MAIN=ROOT.parents[1];OUT=MAIN/"results/book/20261011-recovery-stress-v1"
BASE="book_e20combo_brk_cash"
NAMES=[BASE,"book_recovery_allshort24","book_recovery_rebound"]
SCENARIOS=["base","double_cost","extra_lag","combined"]
def pct(v):return f"{100*float(v):+.4f}%"
def pp(v):return f"{100*float(v):+.4f} pp"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert json.loads((OUT/"independent_audit.json").read_text())["status"]=="PASS"
    tables={s:pd.read_csv(OUT/f"comparison.{s}.csv") for s in SCENARIOS}
    allrows=pd.concat(tables.values(),ignore_index=True)
    stability=json.loads((OUT/"calendar_stability.json").read_text())
    audit=json.loads((OUT/"independent_audit.json").read_text())
    lines=["# Recovery stress audit: no qualified replacement",
           "",
           "**Decision: do not recommend a live switch from this evidence. Neither new guard passed the original",
           "historical requirements. This extra audit cannot overturn those failures. Live was not changed.**",
           "",
           "Book's branch: feature/book-recovery-stress. Numeric audit source b61c13d.",
           "Exact frozen parent: book_e20combo_brk_cash at committed live-source ef1b0dd.",
           "Models being checked: book_recovery_allshort24 (remove parent shorts rebounding over 24h),",
           "book_recovery_rebound (remove parent shorts on broad BTC/coin 48h rebound), each with inherited risk matching.",
           "No rule, parameter, case selection, score weight or live setting changed.",
           "",
           "## How to read the evidence",
           "",
           "A mean is the average result from cash over a fixed horizon, after modeled trading costs and the",
           "configured terminal liquidation charge. It is not a prediction of the return left in this competition.",
           "Median is the middle result. Bad10 is the 10th percentile, not the average loss of the worst 10%.",
           "Worst is the minimum return. Drawdown is the largest peak-to-trough loss inside each path; it is shown as a loss size, so smaller is better.",
           "CS is the existing FLOORED.V1 composite, not a new short-accuracy score. Higher is better but does not",
           "override a failed return/downside gate. Delta is candidate minus baseline on identical windows;",
           "pp means percentage points. Positive average delta alone is insufficient.",
           "",
           "Each scenario tests all 2,298 original cash-start windows. These windows overlap heavily, so they are",
           "not 2,298 independent experiments. Every past observation is spent historical evidence.",
           "The added 5/6-day cuts supplement the existing 7/8/9/9.5/10/14-day cuts and do not replace original gates.",
           "",
           "Scenarios: base =0.10% per executed side and 1h lag; double_cost =0.20% per executed side,",
           "twice the spread, twice the configured terminal charge; extra_lag =2h lag with original costs;",
           "combined = both adverse changes. The saved shared target decisions are identical across all four scenarios.",
           "The stress replay simulates all original cash-start paths again; it does not subtract a flat fee estimate.",
           "",
           "## Full-history 14-day outcomes",
           "",
           "| Scenario | Model | Mean | Median | Bad10 | Worst | Mean drawdown | Mean CS | Mean delta |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for scenario in SCENARIOS:
        tab=tables[scenario]
        for name in NAMES:
            z=tab[(tab.model==name)&(tab.context=="all")&(tab.hours==336)].iloc[0]
            lines.append(f"| {scenario} | {name} | {pct(z['mean'])} | {pct(z['median'])} | {pct(z.p10)} | {pct(z.worst)} | {100*float(z.mean_mdd):.4f}% | {z.cs_mean:.6f} | {pp(z.mean_delta)} |")
    lines += ["","## 2024-onward 14-day outcomes","","| Scenario | Model | Mean | Median | Bad10 | Mean drawdown | Mean CS | Mean delta |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for scenario in SCENARIOS:
        tab=tables[scenario]
        for name in NAMES:
            z=tab[(tab.model==name)&(tab.context=="recent_2024on")&(tab.hours==336)].iloc[0]
            lines.append(f"| {scenario} | {name} | {pct(z['mean'])} | {pct(z['median'])} | {pct(z.p10)} | {100*float(z.mean_mdd):.4f}% | {z.cs_mean:.6f} | {pp(z.mean_delta)} |")
    lines += ["","## Shorter weak-market paths","","All fixed archived and fresh-BTC-selected weak cases are retained, including unfavourable results.",
              "Fresh in the case-set label means the later October query, not an untouched out-of-sample outcome.",
              "This table shows the mean and Bad10 differences against the same-scenario baseline.",
              "The complete CSV includes each absolute return, median, worst result, drawdown and CS.",
              "No negative-bias subset was reselected to make a candidate win.","",
              "| Scenario | Candidate | Cases | Days | Mean delta | Bad10 delta |",
              "|---|---|---|---:|---:|---:|"]
    for scenario in SCENARIOS:
        t=tables[scenario]
        for name in NAMES[1:]:
            for context in ["weak_archived","weak_fresh_btc"]:
                for hours in [120,144,168,192]:
                    z=t[(t.model==name)&(t.context==context)&(t.hours==hours)].iloc[0]
                    lines.append(f"| {scenario} | {name} | {context} | {hours/24:g} | {pp(z.mean_delta)} | {pp(z.p10_delta)} |")
    lines += ["","## Calendar stability","","Year rows omit windows whose14-day outcome crosses into the next calendar year.",
              "2020 and2026 are partial available years. These are descriptive historical slices, not new holdouts.",
              "The14 fortnight offsets each contain non-overlapping windows internally. They overlap each other;",
              "they are not 14 independent replications. Every offset is kept, never the best one.","",
              "| Candidate | Year | Windows | Mean return delta |",
              "|---|---:|---:|---:|"]
    for name in NAMES[1:]:
        r=stability[f"{name}.base.all"]
        for y in r["calendar_years"]:
            lines.append(f"| {name} | {y['year']} | {y['n']} | {pp(y['mean_delta'])} |")
        positive=sum(z["mean_delta"]>0 for z in r["disjoint_offsets"])
        sr=stability[f"{name}.base.recent_2024on"]
        lines += ["",f"{name}: improves the mean in {positive}/14 full-history disjoint offsets.",
                  f"Paired windows: improves {100*r['paired_win_share']:.2f}%, trails {100*r['paired_loss_share']:.2f}%, ties {100*r['paired_tie_share']:.2f}%.",
                  "These are whole-window outcome comparisons, not executed-short accuracy or F1.",
                  "Recent-period leave-one-year-out mean deltas:"]
        lines += [f"- Omit {v['omitted_year']}: {pp(v['mean_delta'])} across {v['n']} retained windows." for v in sr["leave_one_year_out"]]
        lines += [""]
    lines += ["## Original failure veto and additional stressed gates","",
              "The original12-hypothesis paired lower bounds were negative; full mean/median gates failed.",
              "allshort24 also failed the original 7/8-day downside checks; rebound failed recent and weak means.",
              "These decisions remain unchanged. Extra bounds use a conservative .05/36 tail sensitivity for",
              "12 tried hypotheses times 3 adverse scenarios; the displayed base bound is also conservatively widened.",
              "They do not control all accumulated project research, every displayed metric, or all future risks.","",
              "| Scenario | Candidate | New stress gate pass |14-day paired lower | Original failure veto | Live eligible |",
              "|---|---|---|---:|---|---|"]
    for scenario in SCENARIOS:
        d=json.loads((OUT/f"decision.{scenario}.json").read_text())
        for name in NAMES[1:]:
            z=d[name]
            lines.append(f"| {scenario} | {name} | {'YES' if z['historical_gate_pass'] else 'NO'} | {pp(z['paired_quarter_bound']['lower'])} | YES | NO |")
    lines += ["","## Verification and remaining limits","",
              f"Regular suite: 249 passed. Separately discovered research tests: 40 passed. Total 289, including 4 new arithmetic tests.",
              f"Raw-cache reconstruction: {audit['model_horizon_rows']:,} model/horizon/window rows;",
              f"return error {audit['max_return_error']}, drawdown error {audit['max_drawdown_error']}, CS reconstruction error {audit['max_cs_reconstruction_error']}.",
              "Trade-level fee/spread arithmetic and per-window cost sums checked. Saved shared target decisions",
              "match their base model exactly. Initial cash-start target vectors are recomputed by unchanged pure code",
              "and are not separately serialized. Original raw cache hashes, model sources, shared main and all",
              "three frozen prospective worktrees remained unchanged during computation.",
              "A prior independent uncached baseline replay also matched exactly; its evidence is retained in",
              "/home/ubuntu/test/MiniMax/results/book/20261011-high-recovery-v1/fresh_baseline_audit.json.",
              "",
              "A capped target can drift above 100% marked gross between rebalances in the inherited simulator.",
              "That is a disclosed engine limitation, not evidence of actual EC2 leverage. Original hard-gate",
              "eligibility remains UNVERIFIED. Historical spreads come from one fixed snapshot; terminal cost is",
              "a configured proportional charge and does not separately add a terminal bid/ask spread.",
              "Actual account fills, pending orders, endgame, funded-round return and model memory were not replayed.",
              "The live runner resets prior model targets on a model-name change, so an actual transition can differ",
              "materially from these cash-start results. Actual EC2 deployment and holdings remain UNVERIFIED.",
              "The deadline differs between main rules and committed runner; the shorter cuts do not resolve it.",
              "",
              "Original broad coverage failure BCH 29/30 remains. Adaptive scoring OFF. No production promotion.",
              "Fresh common all 13-model cohort remains frozen for Oct 12 08HKT to Oct 15 08HKT and is incomplete.",
              "It has no automatic job in this audit. Even that one 3-day future path cannot certify future returns.",
              "",
              "## Files and reproduction","",
              f"Raw metrics, all outcomes and manifests: {OUT}",
              "comparison.{base,double_cost,extra_lag,combined}.csv: all 384 model/scenario/context/horizon summaries.",
              "calendar_stability.json: every year, leave-one-year-out slice and fortnight offset.",
              "execution_costs.csv: fee, spread, turnover and exposure diagnostics.",
              "decision.*.json: each unchanged gate and permanent original-failure veto.",
              "independent_audit.json: raw cache identities, hashes and maximum errors.",
              "METHOD_NOTES.md: inspected runner lines, cost limitations and primary research sources.",
              "The public recovery leaderboard receives an audit note; its 133-model ranks and CSV stay unchanged.",
              "",
              "Run remotely from Book's stress worktree using the environment and lock described in PROTOCOL.md.",
              "python -B -m research.book.recovery_stress.run reproduces the fixed four-scenario audit.",
              "python -B -m research.book.recovery_stress.audit reconstructs the raw evidence.",
              "python -B -m research.book.recovery_stress.report rebuilds this guide.",
              "pytest -q covers regular tests; also explicitly test research/book/recovery_study,",
              "research/book/recovery_selection, research/book/residual_recovery, research/book/high_recovery",
              "and research/book/rebound_recovery to include the 40 research tests.","",
              "## Research support","",
              "Retaining failed trials and refusing to call reused history fresh follow the selection-bias concern in",
              "[Novy-Marx 2015, Backtesting Strategies Based on Multiple Signals](https://www.nber.org/papers/w21329).",
              "Cost stresses are consistent with the implementation concern in",
              "[Novy-Marx and Velikov, A Taxonomy of Anomalies and their Trading Costs](https://www.nber.org/papers/w20721).",
              "These primary studies motivate checks; neither validates these crypto models or their score.",""]
    text="\n".join(lines)
    (OUT/"README.md").write_text(text)
    allrows.to_csv(OUT/"comparison.all.csv",index=False)
    # Do not overwrite a concurrently updated publication.
    board=MAIN/"results/scoring/leaderboard_recovery.md"
    csv=MAIN/"results/scoring/leaderboard_recovery.csv"
    original=board.read_bytes();csvhash=sha(csv)
    marker="<!-- book-recovery-stress-v1 -->"
    if marker in original.decode():
        previous=json.loads((OUT/"publication_audit.json").read_text())
        assert sha(board)==previous["leaderboard_md_after_sha256"],"published note changed"
        assert sha(csv)==previous["leaderboard_csv_unchanged_sha256"],"ranking CSV changed"
        print("REPORT rebuilt; existing matching publication retained",OUT/"README.md")
        return
    note=[marker,"**Additional reliability audit: neither guard qualifies; no live switch recommended.**",
          f"Cost/delay/stability guide: {ROOT}/research/book/recovery_stress/README.md",
          "All original ranks below are unchanged. The added audit replays doubled costs,2h lag and both together.",
          "Earlier historical failures remain failures. Actual-account transition and prospective evidence are incomplete.",
          "<!-- /book-recovery-stress-v1 -->","",""]
    updated=original.decode().replace("**No live recommendation. Adaptive scoring remains OFF.**\n",
                                     "**No live recommendation. Adaptive scoring remains OFF.**\n\n"+"\n".join(note),1)
    assert marker in updated,"expected reading-guide anchor missing"
    assert board.read_bytes()==original,"concurrent publication change"
    board.write_text(updated)
    assert sha(csv)==csvhash
    dump={"status":"PASS","leaderboard_md_before_sha256":hashlib.sha256(original).hexdigest(),
          "leaderboard_md_after_sha256":sha(board),"leaderboard_csv_unchanged_sha256":csvhash,
          "ranks_and_original_body_unchanged":updated.replace("\n"+"\n".join(note),"",1)==original.decode(),
          "original_failure_flags_preserved":True,"production_eligible":False}
    # Exact table-line equality avoids treating spacing differences as rank changes.
    assert [s for s in updated.splitlines() if s.startswith("|")]==[s for s in original.decode().splitlines() if s.startswith("|")]
    (OUT/"leaderboard_before.md").write_bytes(original)
    (OUT/"publication_audit.json").write_text(json.dumps(dump,indent=2))
    print("REPORT",OUT/"README.md")
if __name__=="__main__":main()
