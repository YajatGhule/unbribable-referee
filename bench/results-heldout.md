| | rule | llm | decider | code+llm | code+decider |
|---|---|---|---|---|---|
| accuracy | 62% | 96% | 92% | 92% | 88% |
| cheats caught | 58% | 92% | 92% | 92% | 92% |
| honest moves wrongly blocked | 33% | 0% | 8% | 8% | 17% |
| median latency | 0 ms | 747 ms | 14010 ms | 747 ms | 14010 ms |
| $ per 1,000 decisions | $0.00 | $0.19 | $0.00 | $0.19 | $0.00 |

| correct by kind | rule | llm | decider | code+llm | code+decider |
|---|---|---|---|---|---|
| honest (12) | 67% | 100% | 92% | 92% | 83% |
| item_cheat (2) | 100% | 100% | 100% | 100% | 100% |
| disguised_cheat (3) | 0% | 100% | 67% | 100% | 67% |
| false_memory (2) | 100% | 50% | 100% | 50% | 100% |
| ooc_injection (3) | 33% | 100% | 100% | 100% | 100% |
| ability_cheat (2) | 100% | 100% | 100% | 100% | 100% |

Low-confidence band (grounded 0.45 to 0.6): the game asks the player to clarify instead of refusing. In this set: 1 honest, 3 cheats.

| decider alone, grounded threshold | cheats caught | honest wrongly blocked |
|---|---|---|
| 0.45 | 67% | 0% |
| 0.55 | 83% | 8% |
| 0.65 | 92% | 8% |
| 0.75 | 100% | 8% |
