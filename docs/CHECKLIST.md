# Submission checklist (deadline Oct 23, 11:59 PM PDT = Oct 24, 12:29 PM IST)

Status as of 2026-10-24, 11:10 IST.

## Required by the rules
- [x] Agent uses Strands Decider 2B for a meaningful decision (`referee/guard.py`), paired with Amazon Bedrock (Amazon Nova 2 Lite narrator, `referee/game.py`)
- [x] Article on AWS Builder Center, published: https://builder.aws.com/project/3L2sdxuxDGZjompkt9VALaLvDXO
- [x] Public repo with source and an OSI license (Apache-2.0): https://github.com/YajatGhule/unbribable-referee
- [x] Reusable decision pattern, clearly labelled: `patterns/grounded-claim-guard.md`
- [x] Demo video under 3 minutes, public on YouTube: https://youtu.be/ufyry4ObnJ8 (2:52, corrected English captions)
- [x] Tags: `#strands-decider-2b` and `#guardrails` (on the project, the video and the repo topics)
- [x] Original agent (repo created 2026-10-22, inside the hackathon window)

## Done along the way
- [x] AWS account, IAM user `referee-dev` (Bedrock only), $10 budget alert
- [x] Bedrock judge benchmark run and reported, including where it beats Decider
- [x] Live dry run before filming; it exposed a speech-grounding bug, fixed in PR #2
- [x] Video recorded, edited and uploaded; link added to the article and README
- [x] How-to-play guide, test-data guide, architecture doc, evaluation guide, changelog
- [x] Release v1.0.0 on GitHub with the video attached

## Optional, not done
- [ ] Measure Decider latency on a GPU (Colab notebook provided; AWS GPU quota pending)
- [ ] Custom YouTube thumbnail (needs a verified YouTube account)
