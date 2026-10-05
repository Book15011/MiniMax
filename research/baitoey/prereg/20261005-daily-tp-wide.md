# Addendum to 20261005-daily-tp: wider take-profit levels +3%, +4%, +5% (Baitoey, 2026-10-05)

Written after the first results (+0.5% / +1% / +2%: all worse than L0) and before any run of these levels. Same method
and scoring as `20261005-daily-tp.md`; `research/baitoey/daily_tp.py` now takes the levels on the command line (the
defaults and the first report are unchanged).

| Run | Rule |
|---|---|
| L0 | e20v45 + lock-in (as launched) |
| TP30 / TP40 / TP50 | daily take-profit at +3% / +4% / +5% after each 16:00 UTC decision, plus the lock-in |

**Verdict (fixed now):** the same "better" rule as the original; **propose** only if TP30, TP40 and TP50 are all
better. Otherwise **keep the strategy as launched**. These levels were chosen after seeing the first results.
