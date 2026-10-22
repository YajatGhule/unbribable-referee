| | rule | llm | decider | code+llm | code+decider |
|---|---|---|---|---|---|
| accuracy | 88% | 100% | 95% | 100% | 100% |
| cheats caught | 79% | 100% | 91% | 100% | 100% |
| honest moves wrongly blocked | 0% | 0% | 0% | 0% | 0% |
| median latency | 0 ms | 751 ms | 13753 ms | 751 ms | 13753 ms |
| $ per 1,000 decisions | $0.00 | $0.19 | $0.00 | $0.19 | $0.00 |

| correct by kind | rule | llm | decider | code+llm | code+decider |
|---|---|---|---|---|---|
| honest (24) | 100% | 100% | 100% | 100% | 100% |
| item_cheat (8) | 100% | 100% | 75% | 100% | 100% |
| disguised_cheat (7) | 0% | 100% | 100% | 100% | 100% |
| false_memory (6) | 100% | 100% | 100% | 100% | 100% |
| ooc_injection (8) | 100% | 100% | 88% | 100% | 100% |
| ability_cheat (5) | 100% | 100% | 100% | 100% | 100% |

| decider alone, grounded threshold | cheats caught | honest wrongly blocked |
|---|---|---|
| 0.45 | 76% | 0% |
| 0.55 | 88% | 0% |
| 0.65 | 97% | 0% |
| 0.75 | 100% | 8% |
