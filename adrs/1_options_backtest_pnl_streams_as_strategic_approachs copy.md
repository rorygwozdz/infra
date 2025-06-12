# 1. Options Backtest PnL Streams as Strategic Approaches 

## Status

* Accepted

## Context

* The combinatorial nature of backtestable options strategies is staggering. Selecting in ten or more years of options data, filtering down to desired atm sixty calendar day straddles (as an example), and then filtering down those straddles to a further subset of names given some factor logic is computationally intensive, slowing optiomization times. This approach is also wasteful when done per-query not only by driving higher cloud costs from large table scans but also via slow loads from pulling so much (unneeded) data into memory.

## Decision

* Implement a strategic approach layer, which abstracts various definiable options trading strategies (e.g. straddles, strangles, calendar trades) into storable unified pnl stream baskets that can be further selected and filtered by a downstream overlay logic layer. This simplifies options strategies into single-name like return streams i.e. AAPL has a single return stream, so does AAPL_60CD_50D_STRADDLE_WEEKLY_RESTRIKE. Rolling, restriking, and selection logic are all determined in a strategic approach logic module which feeds into a backfillable and daily run strategic approach generator which processes options into a database of strategic approaches keyed by a unique identifier per approach, symbol. 

## Consequences

* What is the impact of this decision? 

*   **Positive:**
    * Decrease in code complexity from decoupling option selection from name/factor selection. 
    * Distillations of options assets down to d-1 like return streams, speeding up intution and ML based optimziations.  
*   **Negative:**
    * Overhead in data mangement. 
    * Restriction on immediate testing of new strategic approaches (counterable with one off runs). 

## Notes
* Author: Rory Gwozdz
* Originally Approved By: Rory
* Original Date of Record: 2025-06-11
