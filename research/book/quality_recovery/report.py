"""Readable evidence report; no strategy tuning or eligibility override."""
from pathlib import Path
import json,hashlib
import pandas as pd
from research.book.recovery_stress.metrics import paired_stability

ROOT=Path(__file__).resolve().parents[3];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-quality-recovery-v1"
PUB=MAIN/"results/book/20261011-quality-current-context-v1"
BASE="book_e20combo_brk_cash"
NAMES=[BASE,"book_recovery_quality","book_recovery_quality_blend"]
def pct(x):return f"{float(x)*100:+.4f}%"
def pp(x):return f"{float(x)*100:+.4f} pp"
def main():
    audit=json.loads((OUT/"independent_audit.json").read_text())
    real=json.loads((OUT/"real_causal_audit.json").read_text())
    assert audit["status"]==real["status"]=="PASS"
    decision=json.loads((OUT/"decision.base.json").read_text())
    tab=pd.read_csv(OUT/"comparison.base.csv")
    frames={n:pd.read_parquet(OUT/f"{n}.base.parquet") for n in NAMES}
    stability={}
    for n in NAMES[1:]:
        a=frames[n];b=frames[BASE]
        stability[n]=paired_stability(a[a.hours==336],b[b.hours==336])
    (OUT/"calendar_stability.json").write_text(json.dumps(stability,indent=2))
    lines=["# Continuous-trend recovery research",
           "",
           "**No live switch recommended.** These are two fixed research candidates, with every failed check retained.",
           "Historical requirements passed: "+str([n for n,d in decision.items() if d["historical_gate_pass"]])+".",
           "Passing code tests or a point-estimate leaderboard rank cannot establish future profits.",
           "",
           "Book branch feature/book-quality-recovery; frozen numeric implementation1aaa397, protocol79f963f.",
           "Parent reference book_e20combo_brk_cash from committed live-source ef1b0dd; actual EC2 deployment remains UNVERIFIED.",
           "",
           "## What changed and why",
           "",
           "The existing momentum score already divides trend return by volatility. This pair instead refines long selection:",
           "require positive7/14-day returns, keep top12 parent-momentum coins, then prefer more positive daily steps.",
           "book_recovery_quality ranks by daily sign consistency; book_recovery_quality_blend uses an equal rank blend with momentum.",
           "Select6/retain12, volume and breakdown rules, daily decisions, costs and risk matching stay fixed.",
           "Short targets remain exactly the parent output given the same decision view. Later paths can differ through carried portfolio memory.",
           "The UP-regime long overlay does not introduce a new short entry/cover strategy; DOWN mode is the exact parent.",
           "Q averages (positive days minus negative days)/days over7/14-day formation. Zero days count in the denominator.",
           "Q measures historical path consistency, not future win probability, short accuracy, F1 or clone agreement.",
           "No eligible candidates or missing risk evidence => exact parent fallback. New long covariance risk and full signed variance cannot increase.",
           "This estimate does not guarantee lower realized losses; equal allocation can concentrate when few coins qualify.",
           "",
           "## Research basis",
           "",
           "[Da/Gurun/Warachka2014 author paper](https://academicweb.nd.edu/~zda/Frog.pdf) studies continuous-information momentum in stocks.",
           "Its formation/holding horizons are far longer than ours. Applying sign counts to7/14-day crypto is an unverified adaptation.",
           "The paper conditions on momentum first; a smooth flat coin is not a momentum signal. Sign counts do not measure jump magnitude.",
           "[Grobys/Shahzad publisher abstract](https://onlinelibrary.wiley.com/doi/10.1002/ijfe.70036) discusses heavy-tailed crypto momentum risk.",
           "Only its abstract was read. It supports caution about variance-based metrics; it does not establish a trading rule or prove our return mean undefined.",
           "",
           "## How to read the results",
           "",
           "Mean = average after modeled trading costs and terminal charge. Median = middle outcome. Bad10 =10th percentile, not worst-decile average.",
           "Worst = minimum return. Drawdown is peak-to-trough loss; smaller is better. CS is the existing FLOORED.V1 composite.",
           "Delta = candidate minus baseline on exactly the same starts; pp means percentage points.",
           "There are2298 heavily overlapping cash-start14-day windows, NOT2298 independent tests. Historical data are spent calibration.",
           "A conditional purged-quarter bootstrap uses20000 draws and tail0.05/14 to retain all fourteen recovery hypotheses.",
           "This is not project-wide post-selection control, a joint bound on every metric, or fresh evidence.",
           "",
           "## Full-history and recent14-day results",
           "",
           "| Context | Model | Mean | Median | Bad10 | Worst | Mean drawdown | CS | Mean delta |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for context in ["all","recent_2024on"]:
        for name in NAMES:
            r=tab[(tab.model==name)&(tab.context==context)&(tab.hours==336)].iloc[0]
            lines.append(f"| {context} | {name} | {pct(r['mean'])} | {pct(r['median'])} | {pct(r.p10)} | {pct(r.worst)} | {pct(r.mean_mdd)} | {r.cs_mean:.6f} | {pp(r.mean_delta)} |")
    lines+=["","## Unchanged historical gates",""]
    for n,d in decision.items():
        failed=[g for g,passed in d["gates"].items() if not passed]
        lines+=[f"- {n}: historical pass={d['historical_gate_pass']}; failures={failed}; paired lower difference={pp(d['paired_quarter_bound']['lower'])}."]
    lines+=["","No failed trial is promoted by a newer diagnostic rank. Cost/delay extensions run only for original historical passes.",
            "Earlier guard stress audit remains available: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-stress-v1/README.md",
            "",
            "## Fixed weak-market windows",
            "",
            "Archived and later BTC-selected weak cases are reused without reselecting. 'Fresh' in that legacy label does not mean untouched outcomes.",
            "Full absolute returns, drawdowns and CS for every horizon are in comparison.base.csv.",
            "",
            "| Candidate | Case set | Days | Mean delta | Bad10 delta |",
            "|---|---|---:|---:|---:|"]
    for n in NAMES[1:]:
        for context in ["weak_archived","weak_fresh_btc"]:
            for h in [168,192,216,228,240]:
                r=tab[(tab.model==n)&(tab.context==context)&(tab.hours==h)].iloc[0]
                lines.append(f"| {n} | {context} | {h/24:g} | {pp(r.mean_delta)} | {pp(r.p10_delta)} |")
    lines+=["","## Calendar and concentration checks","","Year rows remove paths crossing the calendar year;2020/2026 are partial.",
            "All14 disjoint-fortnight offsets are saved; offsets overlap one another and are not14 independent replications.",
            "",
            "| Candidate | Year | Windows | Mean delta |","|---|---:|---:|---:|"]
    for n,s in stability.items():
        for y in s["calendar_years"]:
            lines.append(f"| {n} | {y['year']} | {y['n']} | {pp(y['mean_delta'])} |")
        lines+=["",f"{n}: improves{s['paired_win_share']:.2%} of complete paths, trails{s['paired_loss_share']:.2%}, ties{s['paired_tie_share']:.2%}. These are paired portfolio outcomes, not short-trade accuracy.",
                f"Positive full-history disjoint offsets: {sum(x['mean_delta']>0 for x in s['disjoint_offsets'])}/14.",""]
    lines+=["## Independent verification","",
            f"All298 regular/research tests passed. Raw reconstruction checked{audit['model_horizon_rows']} return/drawdown/CS rows and{audit['trades_checked']} trade cost rows.",
            f"Maximum return/drawdown/CS discrepancy={max(audit['max_return_error'],audit['max_mdd_error'],audit['max_cs_error']):.3g}; maximum summary discrepancy={audit['max_summary_error']:.3g}.",
            f"Maximum fee/spread discrepancyUSD={max(audit['max_fee_usd_error'],audit['max_spread_usd_error']):.3g}.",
            "24 real historical decisions passed extreme-future append, short-target, gross and covariance checks.",
            "Baseline raw hashes, inherited live-source files, old frozen future worktrees and fixed historical inputs were preserved.",
            "An initial manifest attempt failed because two nonnumeric reporting files were added mid-run; its outputs/logs are preserved in attempt1_integrity_failure.",
            "The repair reran identical cache keys after freezing reporting files. No strategy, parameter, gate, case or numeric input was changed.",
            "Per-window first decisions are recomputed by the shared pure code but are not separately serialized in the cache.",
            "",
            "## Leaderboard and future evidence","",
            "Shared recovery guide: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md",
            "CSV includes CS and drawdown; rank compares the worse of7/8-day means on the SAME25 BTC-only matched cases.",
            "Both new trials are added to135-model joint diagnostics, including failures. Ranked means are not promotion scores.",
            "The uniform lower differences cover135models*2horizons with23 purged cases in14quarters; broad BCH coverage still fails29/30.",
            "Adaptive stays OFF. --score does not refresh this separate diagnostic automatically.",
            "Reproduce from this worktree: python -B -m research.book.quality_recovery.run; then audit, publish_review and report modules.",
            "These commands are offline research and write results; avoid duplicate runs while an owned job is active.",
            "",
            "Separate frozen future cohort: baseline plus these two models, Oct12 00UTC toOct15 00UTC (Oct12 08HKT toOct15 08HKT).",
            "Original three future cohorts are unchanged. No future scores exist yet; no automatic future job was created.",
            "After all required bars validate, run forward only from /home/ubuntu/test/MiniMax/.worktrees/book-book-quality-recovery.",
            "One3-day path is insufficient to certify an edge and cannot erase historical failures.",
            "",
            "## Practical limits","",
            "Actual EC2 holdings, deployment, endgame memory, pending orders, fills, refusal/fallback/precision and official endpoint remain UNVERIFIED.",
            "The inherited cash-start simulator uses one historical spread snapshot and a proportional terminal charge, without a separately added terminal bid/ask spread.",
            "Marked gross can drift above100% between capped targets. This is not proof of live rule compliance or an actual EC2 violation.",
            "Original full competition eligibility for these research models remains UNVERIFIED; no model is production eligible here.",
            "Clone imitation85% remains unmet; this study makes no new clone or short-accuracy claim.",
            "The intended reliable better-model goal remains incomplete.",""]
    guide="\n".join(lines)
    (OUT/"README.md").write_text(guide)
    (ROOT/"research/book/quality_recovery/README.md").write_text(guide)
    print("Research report saved; no live recommendation.")
if __name__=="__main__":main()
