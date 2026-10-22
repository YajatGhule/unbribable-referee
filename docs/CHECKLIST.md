# Submission checklist (deadline Oct 23, 11:59 PM PDT = Oct 24, 12:29 PM IST)

Budget: about 6 hours of your time. The code, benchmark, pattern, article draft and video
script already exist.

## 1. AWS + Bedrock (45 min)
- [ ] Create an AWS account; turn on MFA for the root user.
- [ ] Billing → Budgets: monthly budget of $10 with an email alert.
- [ ] IAM → create user `referee-dev` with `AmazonBedrockFullAccess` → create an access key (CLI).
- [ ] `sudo pacman -S aws-cli-v2` → `aws configure` (region `us-east-1`, output `json`).
- [x] Bedrock: Amazon Nova 2 Lite works with no form (Claude needs Anthropic's use-case form; not required).
- [ ] Check: `aws bedrock-runtime converse --model-id us.amazon.nova-2-lite-v1:0 --messages '[{"role":"user","content":[{"text":"hi"}]}]'`

## 2. Run it and fill the numbers (45 min)
- [ ] Optional but recommended: Colab GPU referee (`colab/decider_gpu_server.ipynb`), then `export STRANDS_DECIDER_URL=...`.
  Otherwise: `uv run strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099` (≈14 s per check, 9 GB RAM; close Chrome).
- [ ] `uv run python -m referee.game` and play once start to finish. Note two real DCs for the article.
- [ ] Bedrock judge numbers: `uv run python -m bench.run_bench --only llm` and `uv run python -m bench.run_bench --only llm --cases heldout` (about 82 cheap Haiku calls).
- [ ] If you used the GPU: time it, e.g. `uv run python -m bench.run_bench --only decider --cases heldout` → median latency.
- [ ] Paste the new numbers into README.md and docs/article.md (the [brackets]).

## 3. Video, face + voice, under 3:00 (1.5–2 h)
- [ ] Follow docs/video-script.md. Use `--seed 7` for repeatable dice. Big terminal font.
- [ ] Cut the waits. Say the CPU latency once, honestly.
- [ ] Upload as **public** (Public is the safest reading of "publicly available").

## 4. Publish (1 h)
- [x] Public GitHub repo: https://github.com/YajatGhule/unbribable-referee
- [ ] Builder Center article from docs/article.md, rewritten in your voice, with a GIF or screenshots, the repo link and video link.
- [ ] Tags on the submission: `#strands-decider-2b` and `#guardrails`.
- [ ] Submit the project on the hackathon page before the deadline. Re-open it and check every link works logged out.
