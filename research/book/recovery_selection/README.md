# Selection and sizing study: final results

**No tested selection/sizing change passed the pre-registered improvement rule.**

Baseline is the current committed brk-cash model. Source 18b2eb5; tests 257 PASS plus workflow checks. Money results were audited from the raw cached equity and exposure.

| Model | Mean14d | Median | Bad10 | Worst | Mean DD | CS | Improvement pass |
|---|---:|---:|---:|---:|---:|---:|---|
| book_e20combo_brk_cash | +3.732% | +0.283% | -11.522% | -26.049% | 10.770% | 0.15230 | baseline |
| book_recovery_abs | +3.541% | -0.215% | -10.423% | -22.769% | 10.276% | 0.15250 | NO |
| book_recovery_iv | +3.023% | +0.167% | -10.602% | -24.233% | 9.816% | 0.16857 | NO |
| book_recovery_abs_iv | +2.877% | -0.096% | -9.593% | -23.101% | 9.387% | 0.15819 | NO |

Absolute momentum helps several weak/current-horizon diagnostics but loses overall average and median return; its quarter-cluster lower bound is negative. Inverse-vol sizing and the combination reduce risk but lose more average return.
Every unsuccessful rule remains in the evidence. None was retuned, rebranded or promoted after these results.
Historical data is spent. No actual account switch, live endgame, or prospective advantage is validated.
Evidence: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-selection-v1/comparison.base.csv, decision.base.json, independent_audit.json, full_tests.log.
