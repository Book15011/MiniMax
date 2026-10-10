# Why earlier completed shorts lost

Every naturally completed short episode of all six original price models in both fixed25windowweak profiles at228h. These are spent retrospective diagnostics. Separate profiles can overlap; never add them as independent trials.

Gross wins remove only explicit fees from actual fill PnL; spread stays charged. Fee-only loss means gross profit>0but net<=0. Profitable-then-losing means at least one sampled full-cost liquidation value was positive before actual completion at a loss. This latter value uses hindsight and immediate liquidation; it is not an achievable exit signal under1hdelay or a backtest of an exit rule. Multiple entries/partial covers use actual quantities and fees. All completed endpoint PnLs reconcile independently. Censored open shorts are excluded from this question, but remain included in the original portfolio returns.

|Profile|Model|Net wins/closed|Gross wins|Fee-only losses|Profitable then losing|Median hold h|Fees USD|
|---|---|---|---|---|---|---|---|
|weak_archived|book_price_fast_signed|79/418|93|14|224|15.99|14669.10|
|weak_archived|book_price_fast_short|73/399|88|15|220|16.00|14633.52|
|weak_archived|book_price_slow_signed|20/131|23|3|91|64.00|6188.72|
|weak_archived|book_price_slow_short|20/131|24|4|90|64.00|6265.51|
|weak_archived|book_price_channel_signed|76/403|88|12|210|19.99|17805.31|
|weak_archived|book_price_channel_short|74/359|84|10|187|20.00|17866.48|
|weak_fresh_btc|book_price_fast_signed|69/407|86|17|237|15.99|13637.93|
|weak_fresh_btc|book_price_fast_short|65/384|83|18|229|16.00|13564.87|
|weak_fresh_btc|book_price_slow_signed|19/129|22|3|82|52.00|6016.64|
|weak_fresh_btc|book_price_slow_short|19/129|22|3|83|52.00|6113.71|
|weak_fresh_btc|book_price_channel_signed|63/390|80|17|218|16.00|16169.51|
|weak_fresh_btc|book_price_channel_short|59/342|72|13|186|20.00|16162.28|

These measures diagnose possible cost/exit weaknesses. They neither enter the scoring formula nor justify selecting a model without the unchanged return/risk evidence checks. Full observations: completed_cycle_diagnostics.csv.
