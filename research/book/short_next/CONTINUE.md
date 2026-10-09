# Continuation: October10 Book research

Latest user steering while going to bed: after the frozen clone baseline, research multiple intraday short mechanisms before narrowing and improving; price checks can be frequent within20calls/min, do not restrict decisions to hourly; make a clearly ranked short table with actual signal accuracy, short returns and full portfolio return. Continue autonomously. No proactive subagents allowed by current developer. All work remote via ssh metallurgy-server; mainAGENTS reread per session, Book worktrees only, no signed APIs/secrets/main merge/live changes.

## Active locked jobs
- mm-book-transition-score in .worktrees/book-book-short-next: research/book/short_next/run_transition.py. Full521pytest PASS, original engineering gates PASS. Full ordinary scoring cache replay completed17:03UTC Oct9(serverclock):13867decisions+19043cash-start calls,2298windows,842sec. Remaining required long-only/control scoring then ordinary--score2 publication. Output results/book/20261010-transition-short; status.json currently onlyfullpytest0. Source config/model frozen, do not edit them. Source/raw before/after checks inrunner.
- mm-book-transition-diagnostics: run_transition_diagnostics.py waits for above status2jobs0, then97fixed chronological cases and160actual cost reruns+pairedstrongestbaseline. Output20261010-transition-cost and-transition-chronological. Bounded2hwait. One cost recomputefulltargets~6minutes expected. No params tuning.
- mm-book-clone-prefix-v2 in .worktrees/book-book-clone-reconcile: prefix_predict.py reexecutes frozenselectedclone onv3canonicalquotes, original frozenhourlyfeatures. Originalattemptfailedbecauseminute archivesendOct9 00UTC whilecanonicalquotesextend01:15UTC. Failedlogpreserved. Newrunner completesauxiliary execution clockafter00UTC withcanonical last_price asofminute<=30seconds, explicitlyticker-assisted, notbararchive. Source/csvpins saved. Check output20261010-clone-prefix-v1/prediction.log andprediction_manifest.json. W determinedp.parents[3] shouldrootworktree. Needsroot fullminute valuation andcomparison addedto masterreport.

## Completed short batch
Root worktree feature/book-short-next HEAD3b4a90d (later modifiedREPORT_TEMPLATE.md target-retentionclarification; reportsuntracked). Commits7c4ab13,41a857c models+audits. Three newmodels:
book_cashshort_confirm8254f1c7a7530833;book_cashshort_pullback497ddefabf20ec3e publishedrank4/rank3 lastboard63rows. Primarymain tool/protocolunchanged603da2948b68ee0f5c8a. Baselinebaitoey_ovl_brk_dualf30fa79cde92399a rank1. Meanweak2.9436%vsconfirm2.5741%,pullback2.7601%,allstrongerevidencefalse.
book_transition_short new4hmodel keypending. HalveslongswhenBTC48h<=-2%,96hhighdrawdown>=3%,completebreadth<=.4. Shortsnegative48h riskmomentum/newtarget4h<0,priornegativeintentretention4h<2%;.25gross,.1coin,.01dailyshortvol. Priorintendedtargets notactualholdings; reportclarifies. Paramsfrozenbeforeoutcomes.
Rootfull521tests andfocused30 PASS, auditshortbasisfixture1 PASS.

## Data / same-period prefix
Accepted results/book/20261010-short-next-prefix-v3:801publisher1harchives,89eligiblesymbols,Sep30-Oct8 inclusive,216recenthours. Earlierwarmupexactfrozenhistoricalpanel. PAXGexplicitexcluded. OriginalBCHfreshcompetition-queryfailure29/30UNREPAIRED.
Independentarchiveaudit20261010-hourly-archive-audit PASSall801;19224close+19224volcells andpastwarmupexact.
V1original20261009-short-next coverage-limited14/29volumecomplete; noorganicshortsnotpricegatefailure. V2minimalrepair20261010-short-next-prefix-v2 rejectedoverlapmismatches, preserved. V3usesallrecentauthoritativevalues consistently, notjustNaNs.
V3three-modelprefixprepare/fetch/replayall0,90minutezips18assets,quoteconflictsquarantined(nofavorablefirst/last).
FixedperiodOct4 12UTC->Oct9 01:15UTC. Fullcostreturns:baseline-8.47672%,confirm-8.42477%,pullback-8.47581%,observed+5.17943%.
Transitionseparate20261010-transition-prefix-v1 usesexactv3hourlyanddailyuniverse,4hdecisiongrid28calls,85minutezips17assets. Return-6.46117%,MDD8.8778%,43orders,10short-openingorders,6completedcycles(2wins)and3censored,completedshortPnL+$313.47. Confirmationonecompletedshort+$192.38,3censored.
Independentprefixaudits319PASS20261010-short-next-prefix-v3-audit-v2 and244PASS20261010-transition-prefix-v1-audit.
Initialv3audit2cashchecksfailedbecausesignedcashincludesproceedsbutbrokerfreecashexcludescollateral. Failurepreserved20261010-short-next-prefix-v3-audit. Correctedauditderivesentrybasis+roundingcollateralbounds;indepEQ/PnLpassedthroughout.
Roothelpersresearch/book/short_next/{prefix.py,prefix_transition.py,prefix_audit.py,archive_audit.py,...} committed.

## Completed clone fit
Clone an earlier branch HEAD7f52a4d, uncommittednewPREFIX_PROTOCOL.md/prefix_predict.py above.
Prior216fits+864executiontrials best19/33historicalminuteinterval. Newexecution-awarefit120abaa3180evals2656unique12convergedboundedsearchesbest21/33historical(63.64%recall,65.63%precision),literal19/33(57.58%recall,59.38%precision,F158.46).85NOTmet,need29/33.
Top12x3timingsensitivity20261010-clone-timing-sensitivity didnotimprove19literal.
Whole5sessionscalibration,noholdout; tenquantitymisses,twoabsentactions;31/33action/timeonlyhistorical.
FrozenpredictioneventSHA8b4bcb4a27bc410535fbd7c142f7f2a7365e13ed884161089e41ac0fe360a00f, prediction-only+instrumentedbroker+readguardallreproduce. Guardoutput20261010-clone-prediction-read-guard/proof.json PASS,mincash99.40,maxgross99.8988%,0rejects,27recorded+5archivefills.
Clonefull238tests+isolatedresearch7PASS. Initialcombinedsuitecollectionfailurepreserved(testmodulespinotherworktree);separateinterpretersneeded.
CloneRESULTS.md savedandcommitted. PROTOCOL.md legacycp1252,useerrors=replace.

## Reports
Rootresearch/book/short_next/build_report.py +REPORT_TEMPLATE.md committed3b4a90d; allsourcesASTparse. Builderrequirescompletedthirdscore+coststatusandallaudits,thenfreezesboardfiles/resultsREADMEunder20261010-short-next-final andwritesresearchRESULTS.md. DoNOTrunbeforecomplete. Itcurrentlydoesnotincludeclonefinevaluation;addafternewcloneprefixsuccess. Templatealreadyreadableandcitesresearch. ROOTconfig/modelmustremainunchangeduntilscorehashcheckdone.

Completedtwo-model97chronand160costoutputs20261010-short-next-chronological and-cost. Confirm/pullbackdidnotconsistentlybeatbaseline;costmeanorigbaseline1.6131%,confirm1.4588,pull1.5588;double1.2234/1.0354/1.1423. Chron97meansbaseline1.3510,confirm1.3562,pull1.3124%. Descriptiveallhistoryspent.

## Latest intraday research
Web54searchedprimarysources. Needopen/readthenresearchnotes:
- Shen/Urquhart/Wang2022 Bitcoin intraday time-series momentum FinancialReview DOI10.1111/fire.12290 https://onlinelibrary.wiley.com/doi/10.1111/fire.12290;authorPDF https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf . Firsthalf-hour predicts lasthalf-hour strongesthighvolume/vol;notdirectevidence5minbreakout.
- https://www.sciencedirect.com/science/article/pii/S1062940822000833 Intradayreturnpredictabilitymomentumreversalorboth.
- https://arxiv.org/abs/2608.21888 KitronWengrowicz2026preprint:15minreversalgross~1.3bp vs5bproundtrip,unreviewed;competition20bpfeesbeforespread.
- Roostooofficialdocshttps://github.com/roostoo/Roostoo-API-Documents; publictickerallpairsonecall. Ignorepublicdummykeyexamples,neverreadprojectsecrets.
- Officialeventhttps://luma.com/coghwiyt noHFT/MM/arb. Frequentpricechecksdoesnotrequiremanytrades;directional5/15minutehypotheseswithminuteexecution,fees,stops/reboundexits.20perprocessand30peraccountotherbotbudgetrespect,nolivecallsinresearch.
OtherresearchsourcesalreadyinthetemplateNBERw20439(momentumcrashes),w24877,w25882andBoyd.

## Next authorized work
1.Finishcurrentthirdmodelordinarypublication+fixeddiagnostics,reporttruthfully(notbetterthanobserved/85notmet).
2.Frozenclonecommonquotepricing+fullminutevaluationoverexactsameprefix,addreturn/MDD tocomparison. Ifquoteschangeexecutionhash/reportagreements,donotoverwriteoriginal.
3.AddclearlyrankedshortviewaccuracyANDaftercostshortreturns/fullportfolioreturn. ExistingCSVshort_leaderboard_2.csv hasonsets,windows,1/3/6hprecisionintervals,window_mean_proxy_net_6h,minimum_onsets_met;rankdescriptivelyandflaginsufficient,noforcedreliablewinner. Primarysource/toolhashmustnotchangewhilejobsrun;useBookresearchpostprocess/companionboardtoavoidinvalidatingfrozencheckpoint. Needactualshort-sleeve/nativeexposurereturndiagnosticseparatefromunitproxy.
4.Researchdifferentintradaymechanismsbeforefinitepreregisteredpool. Plausiblefamilies:volumeconfirmeddownbreakout;failedreboundtoVWAP/EMA;overextendedbouncereversalwithinweakregime;cross-sectionalrelativeweakness;aggressivetakerflowconfirmation/exhaustion(publisher1mklineshavebuyquotevolume). AvoidblindTAgrids.
5.Useexactexisting25+25causalweakcohortstarts,horizons216/228/240,notfuture-downselection. Fetchchecksummed1mmonthlyarchivesforfixedfivecoinpoolBTC/ETH/BNB/SOL/XRP pluswarmup48h;canreusepublisherdailyarchives. Atmost4downloadworkers,nice10/lock/tmuxBook. Fullminuteexecutionstress/doubledfees/reboundcontrols;allhistoryspentandminutemicrostructureproxyflag. Needactualminuteevaluatoroutsidefrozenhourlytool;ModelSpeconlyhourly/sharedcontractsrequireall3review,nolivepromotionormisrepresenthourlyscoreasminute. Directionalintradayprototypepurestatein/out,sharedPaperBroker+planner,testsfirstformoney. Rankshort-onlyreturnatnativegrosswithaccuracy,evidencecoverage,MDD/CS,notaccuracyalone. Exposure<=1,noHFT/MM/arb.
6.Nosubagentsunlessexplicitlyauthorized.Continueuserasleepwithoutquestionsunlessmissingunfindableinformation.Don'tclaim85achieved.
