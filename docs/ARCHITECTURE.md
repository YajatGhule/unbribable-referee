# Architecture

## Components

```
                 ┌──────────────────────────────────────────────────────────┐
 player text ──► │ Strands Agent  (referee/game.py)                         │
                 │   model: BedrockModel → Amazon Nova 2 Lite (Bedrock)     │
                 │   tools: move, take, use_item, attack, cast_spell,       │
                 │          give, speak, reveal       (referee/tools.py)    │
                 │   interventions: [GroundedClaimGuard] (referee/guard.py) │
                 └──────────────┬───────────────────────────────────────────┘
                                │ before_tool_call(event)
                                ▼
                 ┌──────────────────────────────────────────────────────────┐
                 │ GroundedClaimGuard                                       │
                 │   state = FACTS (world.render) + player message          │
                 │           + proposed tool call                           │
                 │   questions_for(tool) → grounded / manipulation /        │
                 │                         plausible                        │
                 └──────────────┬───────────────────────────────────────────┘
                                │ POST /v1/systemone  (referee/decider.py)
                                ▼
                 ┌──────────────────────────────────────────────────────────┐
                 │ strands-decider serve  (local, port 8099)                │
                 │   Strands Decider 2B → probabilities per question        │
                 └──────────────┬───────────────────────────────────────────┘
                                ▼
            policy (plain Python): Guide (block / ask) or Proceed + d20 roll
                                ▼
            tool runs (or not) → narrator tells the result → terminal UI panels
```

## Request flow for one turn

1. The player types a move; `game.py` refreshes the narrator's system prompt with the current
   world facts.
2. Nova 2 Lite (via Strands' `BedrockModel`) picks a tool and arguments.
3. Strands calls `GroundedClaimGuard.before_tool_call`. Ungated tools (`move`) proceed; gated
   tools continue.
4. The guard renders one state string and sends all questions for that tool in one
   `/v1/systemone` request, so the state is encoded once.
5. Decider returns `noul` probabilities and a `score` distribution with confidence.
6. `make_policy` → `default_policy` decides:
   - `Guide` with refusal feedback (manipulation ≥ 0.5 or grounded < 0.45),
   - `Guide` with a clarifying-question request (0.45 ≤ grounded < 0.6; not used for speech),
   - `Proceed`: the plausibility distribution becomes a success chance and a d20 difficulty,
     stored in `world.pending_roll` for the tool to read.
7. The tool applies structured checks (item held, item present, exits, password actually
   learned) and the roll, then returns SUCCESS or FAILURE text.
8. The narrator writes the outcome; the UI prints a referee panel (probabilities, verdict,
   latency) and the narration.

## Files

| File | Responsibility |
|---|---|
| `referee/guard.py` | The reusable pattern: questions, state rendering, default policy, the intervention |
| `referee/decider.py` | stdlib HTTP client for `strands-decider serve`; `noul()`, `choice()`, `score()` helpers |
| `referee/game.py` | Narrator agent, per-tool questions, thresholds, dice policy, terminal UI |
| `referee/tools.py` | Game actions with structured checks; reads the dice roll |
| `referee/world.py` | World state and its compact text rendering (the source of truth) |
| `bench/run_bench.py` | Benchmark: rules vs Decider vs Bedrock judge on labelled cases |
| `tests/` | Offline tests: guard policy, dice, tool behaviour, and a real Strands agent loop with a scripted model |
| `colab/decider_gpu_server.ipynb` | Optional: serve Decider on a free GPU and tunnel it |

## Design decisions

- **The narrator never judges cheating.** It is the component being persuaded; the verdict is a
  number from a model that cannot generate text, and code owns the threshold.
- **Code first, model second.** Exact facts (inventory, exits, password learned) are checked in
  the tools. Decider handles claims code cannot parse (smuggled properties, false history,
  out-of-character instructions).
- **Guide, not Deny.** A cancelled call returns feedback to the narrator so the story continues
  in character instead of erroring.
- **Never store a player's claim as a fact.** `speak()` logs that Pip spoke, not what was said,
  so later checks are not made against earlier lies (a bug found in a live dry run; see
  `CHANGELOG.md`, PR #2).
- **Short state.** Only the current location, inventory, relevant NPC knowledge and the last few
  story events are sent, because CPU inference cost grows with input length.

## Security

- No credentials in the repository. Bedrock access uses the standard AWS credential chain
  (`~/.aws/credentials` locally; an IAM role in the unmerged `deploy-aws` scripts).
- The Decider server listens on localhost. The Colab notebook opens a public tunnel only while
  it runs, and says so.
