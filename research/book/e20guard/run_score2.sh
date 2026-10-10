#!/usr/bin/env bash
# score2 for the four e20v45 short-guard variants, one after another (feature/e20-shortguard)
cd /home/ubuntu/test/MiniMax/.worktrees/book-e20-shortguard
for m in book_e20guard_pullback book_e20guard_confirm book_e20guard_pullback40 book_e20guard_confirm40; do
  echo "=== $m $(date -u +%FT%TZ)"
  nice -n 10 ../../.venv/bin/python -B -m backtest.run --model $m --score2 2>&1 | tail -25
done
echo "=== done $(date -u +%FT%TZ)"
