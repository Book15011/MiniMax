# Research queue: derivatives positioning, not another price threshold

This note adds NO trading candidate, parameter test, score or recommendation. Current finite trial remains the two quality models.
The next economically distinct question is whether derivative crowding improves downside timing beyond price/volume alone.

## Reliable source distinctions

- BIS Crypto carry, working paper1087, official summary and linked54-pagePDF:
  https://www.bis.org/publications/working-paper-1087-crypto-carry
  Summary reports high dated-futures/spot carry predicts crash risk in BTC/ETH. This motivates a directional warning hypothesis.
  A perpetual funding rate is NOT the same instrument or quantity. A funding-only rule would be a separate unverified adaptation.
  The PDF reports1-to3-month risk horizons, not minute-level entry timing; realized skew significance is exchange-dependent.
  Nothing here establishes today's positioning or predicts the next10days. No cash-and-carry, arbitrage or pair trading is proposed.
- Official Binance public-data documentation:
  https://github.com/binance/binance-public-data
  Daily archives arrive next day; monthly files at first Monday. Files can later be revised; checksum integrity is not historical publication proof.
- Official USD-M market data:
  https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data
  Funding-history responses have fundingTime/rate and associated markPrice. Funding intervals can change.
  Open-interest history is a different stream; historical coverage and contemporaneous publication must be checked separately.
- Additional scoped negative-result preprint:
  https://arxiv.org/abs/2608.25348
  Only landing abstract reviewed; do not treat as established alpha or a fully replicated study.

## Actual feasibility check

One public BTCUSDT Jan2024 monthly funding ZIP was fetched on metallurgy-server, with matching official SHA256:
3e0d30870672aa8f0f937881056e3cfd55913ae5c780cd50b33f2763aa0ba58e.
It has93 records, columns calc_time, funding_interval_hours, last_funding_rate.
Raw sample and feasibility JSON: /home/ubuntu/test/MiniMax/results/book/20261011-quality-recovery-v1.
No signed API, competition account query, current quote or outcome test was made.
This proves ONE archive is accessible. Multi-year/all-coin coverage, revised vintages and publication time remain UNVERIFIED.
Existing validation panels and original BCH29/30 failure are untouched. This sample is not used by the quality models.

## Gate before a new strategy

1. Audit coverage of contemporaneously tradable coins and exact units/intervals. Do not annualize every record as8h by assumption.
2. Separate funding settlement/event time, data publication time and the time we could have observed it.
   A conservative lag helps but does not prove a monthly archive was available at its individual event timestamp.
3. For dated carry, align actual expiry, spot, mark/index and trade prices; avoid maturity rolls being labeled signals.
4. Freeze a SMALL finite hypothesis family and economic sign before inspecting matched returns.
   Retain all14 previous recovery trials and widen task/family bounds for any new candidates.
5. Use only permitted directional orders. Do not simulate funding payments as income for the competition's spot-style short account.
6. Compare after fees/lag on identical cases, all years/tails/CS, with separate profitable-short opportunity F1 and adequate trade count.
7. Prefreeze future evidence and validate actual account transition before any live recommendation.

Do not infer that more API requests create an edge. Timely causal information and post-cost improvement must both be demonstrated.
