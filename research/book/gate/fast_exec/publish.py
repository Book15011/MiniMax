"""Publish a separate execution-status board; never rank it as a profitable model."""
from pathlib import Path
import json,hashlib
from .driver import OUT,HERE
def main():
    root=Path('/home/ubuntu/test/MiniMax');board=root/'results/scoring/leaderboard_fast_execution.md'
    if board.exists() and not board.read_text().startswith('# Book execution timing research'):raise ValueError('Existing board is not ours')
    keep={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in board.parent.glob('leaderboard*') if p.is_file() and p!=board}
    m=json.loads((OUT/'final_cpu/microbenchmark.json').read_text())['complete_supervisor_prepare_us']
    text=f"""# Book execution timing research

**No actual filled-order timing or profitable trading model is qualified here.** Read the [full C++ plan](/home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec/CPP_EXECUTION_PLAN.md) and [research evidence](/home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec/RESEARCH.md).

| Component | Evidence | Status |
|---|---|---|
| C++ timing/risk/money core plus supervisor |20,000 synthetic preparations;p99{m['p99']/1000:.4f}ms;max{m['max']/1000:.3f}ms|Local target passes|
| Admission/fault simulator |200 timing cases;3 duplicate-state cases|Pass;not trading P&L|
| Initial public shadow |31,436 books;0eligible intents|No order/fill evidence|
| Full standalone C++ feed/order service |Architecture and dependency check prepared|Not completed|
| Small live pilot |ProposedUSD10/entry,max3round trips|User-requested;not executed|

51 focused tests pass;19 relocated bundle tests pass, overlapping those counts. All prior156 latency simulation rows and every other numeric board are unchanged.

This is an execution-status board, not a trading-model rank. Return,CS,F1,full-size capacity and actual subsecond fill reliability are unavailable. No model is registered or deployed from these timings. The ordinary --score command does not certify this engine.

Runtime/source/raw evidence: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1. Pilot/EC2 steps are in HANDOFF_FOR_CLAUDE.md. The full C++ implementation and actual live measurements are still outstanding.
"""
    board.write_text(text)
    assert keep=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in board.parent.glob('leaderboard*') if p.is_file() and p!=board}
    (OUT/'publication_audit.json').write_text(json.dumps({'pass':True,'other_boards_unchanged':keep,'new_board':str(board),'trading_rank_added':False},indent=2))
    print(board)
if __name__=='__main__':main()
