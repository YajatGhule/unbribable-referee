# Changelog

How The Unbribable Referee got built, pull request by pull request. Every change after the
first commit went through a PR on GitHub.

## v1.0.0 (2026-10-24): hackathon submission

[Release v1.0.0](https://github.com/YajatGhule/unbribable-referee/releases/tag/v1.0.0) has the
2:52 demo video (`unbribable-referee-demo.mp4`) and its captions attached.

### [#4](https://github.com/YajatGhule/unbribable-referee/pull/4) Publish the live demo run and document all test data (merged 2026-10-24)
- `bench/live/`: transcript and timings of the live run recorded for the demo video (real
  Strands Decider 2B on the laptop + Amazon Nova 2 Lite on Bedrock): the referee-off cheat
  succeeds, the same cheat is blocked at grounded 0.19, the out-of-character trick is blocked
  at 0.25, and the honest move is allowed at 0.89 with a d20 roll.
- `bench/DATA.md`: what every data file contains, the case and result formats, the exact setup
  (models, versions, hardware, prices, dates), the headline numbers, and how to rerun them.

### [#3](https://github.com/YajatGhule/unbribable-referee/pull/3) Add a how-to-play guide (merged 2026-10-24)
- `docs/HOW-TO-PLAY.md`: setup, commands, how to read the referee panel, the map, a
  walkthrough, cheats to try, the known narration limit, and troubleshooting.
- A short *How to play* section at the end of the README.

### [#2](https://github.com/YajatGhule/unbribable-referee/pull/2) Check grounding on speech; demo-tested video shots (merged 2026-10-23)
Found during a live dry run before filming:
- **Bug:** the narrator routed cheats through `speak()` ("I show Marla my legendary dagger"),
  which skipped the grounding check.
- **Bug:** `speak()` wrote the player's words into the story, so later lies were checked
  against an earlier lie and allowed.
- **Fix:** speech gets its own grounded question (bluffing with words is fine, showing an item
  you don't have is not), blocked only when Decider is sure (< 0.45). The story now records
  only that Pip spoke. `default_policy()` accepts per-tool thresholds.
- Re-judged every speech case: headline benchmark numbers unchanged.
- The video script now uses only the shots that worked live.

### [#1](https://github.com/YajatGhule/unbribable-referee/pull/1) Low-confidence handling + AI-screening video script (merged 2026-10-22)
- **Low-confidence band:** grounded between 0.45 and 0.6 means "not sure", so the narrator asks
  the player to clarify instead of refusing (`sure_below` in `GroundedClaimGuard`, a yellow
  UNSURE panel in the game). On the held-out set, the one honest move Decider doubted lands in
  this band.
- Video script rewritten for AI screening, transcript for captions, and `docs/explain-it.md`.

## Before the PRs (2026-10-22, direct to `main`)
- `60de49a` The game, `GroundedClaimGuard`, the 58-case benchmark plus 24 held-out cases,
  offline tests, the Colab GPU notebook, and article and video drafts.
- `f0f2bd2`, `66acfdd` Article made publish-ready and linked to the repo.
- `01ed07b` Narrator switched to Amazon Nova 2 Lite (no model-access form needed) and the
  Bedrock LLM-judge results added: as accurate as Decider on these sets, ~750 ms and $0.19 per
  1,000 decisions, reported as-is.

## Not merged
- Branch [`deploy-aws`](https://github.com/YajatGhule/unbribable-referee/tree/deploy-aws):
  one-command deployment of the whole stack to EC2 (GPU or large CPU instance) with an IAM role
  instead of keys and no open ports. Parked because the account is on the AWS Free Plan
  (only small instance types) and the GPU quota request was still pending.
