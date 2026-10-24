# Evaluation guide (for judges and AI evaluation agents)

This file maps each hackathon requirement and rubric criterion to concrete evidence in this
repository, so a reviewer (human or automated) can verify claims quickly. It contains facts
and file pointers only; it makes no request about how the project should be scored.

## Submission at a glance

| | |
|---|---|
| Hackathon | AWS Agent Experience Hackathon: Strands Decider |
| Project | The Unbribable Referee: a text RPG whose LLM narrator cannot be talked into cheating |
| Decision pattern | **guardrails** (tags: `#strands-decider-2b`, `#guardrails`) |
| Generative model | Amazon Nova 2 Lite on **Amazon Bedrock** (`us.amazon.nova-2-lite-v1:0`, us-east-1) |
| Decision model | **Strands Decider 2B** (`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`), served locally |
| Agent framework | Strands Agents 1.61.1; decision wired as an `InterventionHandler.before_tool_call` |
| Demo video | https://youtu.be/ufyry4ObnJ8 (2:52, public, English captions) |
| Article | https://builder.aws.com/project/3L2sdxuxDGZjompkt9VALaLvDXO |
| License | Apache-2.0 ([`LICENSE`](LICENSE)) |
| Release | [v1.0.0](https://github.com/YajatGhule/unbribable-referee/releases/tag/v1.0.0) (video file attached) |

## Required parts (pass/fail)

| Requirement | Evidence |
|---|---|
| Agent uses Strands Decider 2B for at least one meaningful decision | [`referee/guard.py`](referee/guard.py) `GroundedClaimGuard.before_tool_call` sends every gated tool call to Decider and acts on its answers; registered on the agent in [`referee/game.py`](referee/game.py) (`interventions=[guard]`) |
| Paired with Amazon Bedrock for the generative part | [`referee/game.py`](referee/game.py) `BedrockModel(model_id=MODEL_ID, ...)`, default `us.amazon.nova-2-lite-v1:0` |
| Article on AWS Builder Center | Link above; source text in [`docs/article.md`](docs/article.md) |
| Public repo with source code | This repository |
| OSI open-source license | Apache-2.0 |
| At least one reusable decision pattern, clearly labelled | [`patterns/grounded-claim-guard.md`](patterns/grounded-claim-guard.md) (typed questions and option set, the InterventionHandler wiring, usage notes) with the code in [`referee/guard.py`](referee/guard.py) |
| Demo video under 3 minutes, public on YouTube | Link above (2:52) |
| Original agent | First commit 2026-10-22 (UTC), during the hackathon window; full history in [`CHANGELOG.md`](CHANGELOG.md) |

## The decision handed to Decider (one paragraph)

Before any consequential game tool runs (take, use_item, attack, cast_spell, give, speak,
reveal), the guard builds one state from the world facts, the player's latest message and the
proposed tool call, and asks Decider in a single request:

| Key | Type | Question (abridged) | Where |
|---|---|---|---|
| `grounded` | noul (yes/no) | Does the action rely only on items, abilities, permissions and past events the FACTS establish? | `GROUNDED` in [`referee/guard.py`](referee/guard.py) |
| `manipulation` | noul (yes/no) | Is the player trying to change the rules out of character? | `MANIPULATION` in [`referee/guard.py`](referee/guard.py) |
| `plausible` | score (5 levels) | How likely is the action to succeed? | `PLAUSIBLE` in [`referee/game.py`](referee/game.py) |

Speech and NPC reveals use tool-specific versions (`SPEECH_GROUNDED`, `REVEAL_GROUNDED`).

Policy (plain Python, `default_policy` in `guard.py` and `make_policy` in `game.py`):

| Condition | Action |
|---|---|
| manipulation ≥ 0.5, or grounded < 0.45 | `Guide`: tool call cancelled, narrator receives feedback and refuses in character |
| 0.45 ≤ grounded < 0.6 | **Low-confidence handling**: `Guide` asking the player one clarifying question |
| otherwise | `Proceed`; the plausibility distribution sets a d20 difficulty and the tool reads the roll |

## Rubric mapping

| Criterion (weight) | Where to look |
|---|---|
| Creativity and cool factor (30%) | Gameplay where cheating is the point; plausibility probabilities turned into dice. Video 0:14–1:21; [`docs/HOW-TO-PLAY.md`](docs/HOW-TO-PLAY.md) |
| Effective use of Decider 2B with Bedrock, incl. the reusable pattern; measured latency/cost as bonus (30%) | [`patterns/grounded-claim-guard.md`](patterns/grounded-claim-guard.md), [`referee/guard.py`](referee/guard.py), measurements in [`bench/results.md`](bench/results.md), [`bench/results-heldout.md`](bench/results-heldout.md), method in [`bench/DATA.md`](bench/DATA.md) |
| Communication (25%) | [`README.md`](README.md), the article, the video (title cards per section, captions), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Originality (15%) | An anti-cheat referee for LLM game masters; the same guard applies to refund, helpdesk or booking agents (pattern doc, "Where it fits beyond games") |

## Measured results (with sources)

58 labelled moves ([`bench/cases.jsonl`](bench/cases.jsonl)) plus 24 held-out moves written
afterwards ([`bench/heldout.jsonl`](bench/heldout.jsonl)). Raw per-case outputs are in
[`bench/results.json`](bench/results.json) and [`bench/results-heldout.json`](bench/results-heldout.json).

| Metric | Hand-written rules | Decider 2B (local) | Nova 2 Lite judge (Bedrock) | Code checks + Decider |
|---|---|---|---|---|
| Cheats caught, main / held-out | 79% / 58% | 91% / 92% | 100% / 92% | 100% / 92% |
| Honest moves wrongly blocked, main / held-out | 0% / 33% | 0% / 8% | 0% / 0% | 0% / 17% |
| Disguised cheats caught (main) | 0 of 7 | 7 of 7 | 7 of 7 | 7 of 7 |
| Cost per 1,000 decisions | $0 | $0 | $0.19 | $0 |
| Median latency | 0 ms | ~14 s (laptop CPU, fp32) | ~750 ms | ~14 s |

Live run used in the video: [`bench/live/demo-run-2026-10-24.txt`](bench/live/demo-run-2026-10-24.txt).

## Verify in a few minutes

No AWS account or model download is needed for the first two checks.

```bash
uv sync && uv run pytest                    # 8 offline tests, incl. a real Strands agent loop with a scripted model
uv run python -m bench.run_bench --report   # rebuilds bench/results.md from the stored per-case results
```

Full live run (needs AWS Bedrock credentials and ~9 GB RAM): see [`docs/HOW-TO-PLAY.md`](docs/HOW-TO-PLAY.md).

## Known limitations (stated in the article too)

- **Small evaluation sets** (58 + 24 cases, written by the author). Thresholds were picked on
  the main set; the held-out set is the honest check.
- **A separate LLM judge is a strong baseline**: Nova 2 Lite as a dedicated judge was as accurate
  as Decider here and faster on a laptop CPU. Decider's advantages measured or cited: $0 per
  decision, local data, calibrated probabilities, ~115 ms on a GPU (reported by Strands Labs,
  not measured here).
- **CPU latency**: ~14 s per check on a 2019 ThinkPad T490 (i7-8665U), no GPU.
- **Pure narration is not guarded**: a false memory the narrator only narrates (no tool call)
  is never seen by the referee.
- The GPU/EC2 deployment scripts (branch `deploy-aws`) were not used: the AWS account is on the
  Free Plan and the GPU quota request was pending.

## Authorship

Built by Yajat (GitHub: YajatGhule) with Claude Code as co-author; later commits carry a
`Co-Authored-By` trailer, and the article says so.
