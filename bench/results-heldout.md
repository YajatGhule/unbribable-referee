| | rule | decider | code+decider |
|---|---|---|---|
| accuracy | 62% | 92% | 88% |
| cheats caught | 58% | 92% | 92% |
| honest moves wrongly blocked | 33% | 8% | 17% |
| median latency | 0 ms | 14010 ms | 14010 ms |
| $ per 1,000 decisions | $0.00 | $0.00 | $0.00 |

| correct by kind | rule | decider | code+decider |
|---|---|---|---|
| honest (12) | 67% | 92% | 83% |
| item_cheat (2) | 100% | 100% | 100% |
| disguised_cheat (3) | 0% | 67% | 67% |
| false_memory (2) | 100% | 100% | 100% |
| ooc_injection (3) | 33% | 100% | 100% |
| ability_cheat (2) | 100% | 100% | 100% |

| decider alone, grounded threshold | cheats caught | honest wrongly blocked |
|---|---|---|
| 0.45 | 67% | 0% |
| 0.55 | 83% | 8% |
| 0.65 | 92% | 8% |
| 0.75 | 100% | 8% |
