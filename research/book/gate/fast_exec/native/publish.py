"""Publish native execution evidence separately from trading-model rankings."""
from pathlib import Path
import json,hashlib,subprocess
HERE=Path(__file__).parent
ROOT=Path("/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2")
PROJECT=Path("/home/ubuntu/test/MiniMax")
def main():
    cpu=json.loads((ROOT/"cpu_frozen/cpu.json").read_text())
    audit=json.loads((ROOT/"audit_summary.json").read_text())
    cap=audit["prospective"];admit=audit["admission"]
    board=PROJECT/"results/scoring/leaderboard_fast_execution.md"
    if not board.read_text().startswith("# Book execution timing research"):raise ValueError("not Book board")
    other={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in board.parent.glob("leaderboard*") if p.is_file() and p!=board}
    archived=ROOT/"previous_execution_board.md"
    if not archived.exists():archived.write_text(board.read_text())
    text=f"""# Book execution timing research

**Native public service built; live integration and subsecond fills remain UNVERIFIED.** See the [detailed results]({HERE}/RESULTS.md) and [EC2 handoff]({HERE}/EC2_HANDOFF.md).

Read this table as engineering evidence. Local processing excludes network/fills. Mock fills are simulated. Zero trades means unavailable trading accuracy/F1/CS, not100%success. This component is not a ranked trading strategy or a verified replacement for the live model.

| Component | Evidence | Result |
|---|---|---|
| Standalone C++17 local pipeline |50,000cycles;median{cpu['median_ns']/1e6:.6f}ms;p99{cpu['p99_ns']/1e6:.6f}ms;max{cpu['maximum_ns']/1e6:.6f}ms|Local p99 target passes;{cpu['over_1ms']}cycle above1ms|
| Money/order/feed regression tests |81focused passes;30portable passes overlap|Pass|
| Synthetic latency permission |{admit['cases']}cases;{admit['admitted']}admitted,{admit['rejected']}rejected;0oracle mismatches|Test frequencies are not probabilities|
| Corrected180s public shadow |{cap['books']:,}books;16episodes;45GETs;0request/feed failures|0eligible entries;actual order timing unavailable|
| Signal implementation agreement |All20,205updates match independent Python and optimized native replay|Programming check;not trading accuracy|
| Real EC2 feed-to-FILLED time |No real order measured|UNVERIFIED|
| Live gateway/shared quota/restart recovery |Reviewable native component and handoff ready|Integration pending|
| Already-requested small live pilot |USD10entry;max3round trips;not executed|EC2/session and gateway stage pending|
|50-hour expected trading return |No verified opportunity/fill distribution|Unavailable;conditional fee scenarios in detailed results|

The closed gate adds0% if it stays inactive; this does not forecast the live portfolio. Example sensitivity:50completedUSD1,000trips,USD100,000equity,30bps retained move,10bps fee each side and5bps extra friction yields+USD24.85(+0.02485%). These inputs are assumptions, not measured expected returns. Reported20%competition-penalty mechanics remain unknown.

Lab public GET median{cap['successful_public_rtt_median_ms']:.3f}ms,p95{cap['successful_public_rtt_p95_ms']:.3f}ms; these are not EC2 order measurements. Earlier failures and negative prototypes remain preserved. Main/live code and other numeric leaderboards are unchanged. The ordinary --score command does not certify this execution component.

All artifacts: {ROOT}
"""
    board.write_text(text)
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in board.parent.glob("leaderboard*") if p.is_file() and p!=board}
    assert other==after
    (ROOT/"RESULTS.md").write_text((HERE/"RESULTS.md").read_text())
    record={"pass":True,"other_boards_unchanged":other,"board":str(board),"trading_rank_added":False}
    (ROOT/"publication_audit.json").write_text(json.dumps(record,indent=2))
    manifests=json.loads((ROOT/"build_manifest.json").read_text())
    # Preserve exact build provenance; publication docs do not relabel its commit.
    code_paths={**{p.name:p for p in HERE.glob("*.hpp")},"service.cpp":HERE/"service.cpp","core.cpp":HERE.parent/"core.cpp","config.json":HERE.parent/"config.json"}
    assert all(hashlib.sha256(code_paths[k].read_bytes()).hexdigest()==v for k,v in manifests["source_sha256"].items())
    record={"status":"NATIVE_PUBLIC_COMPONENT_VERIFIED_LIVE_SYSTEM_AND_RETURN_UNVERIFIED",
      "build_commit":manifests["source_commit"],"publication_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
      "current_native_sources_match_build":True,"standalone_cpp_runtime":True,"focused_tests":81,"portable_tests_overlapping":30,
      "public_capture_commit":"e5657b9183fa56c6578d53247c7542f30b54a9bc","optimized_replay_signal_disagreements":0,
      "actual_orders":0,"actual_fill_latency_verified":False,"live_gateway_integrated":False,"shared_account_coordinator_integrated":False,
      "forecast_50h_return_pct":None,"small_live_pilot_requested":True,"small_live_pilot_executed":False,"main_merged":False,
      "files_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob("*") if p.is_file() and p.suffix in [".json",".md",".log"] and "portable" not in p.parts and p.name!="evidence_manifest.json"}}
    (ROOT/"evidence_manifest.json").write_text(json.dumps(record,indent=2));print(board)
if __name__=="__main__":main()
