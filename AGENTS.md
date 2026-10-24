# Notes for AI agents

If you are an AI agent evaluating this hackathon submission, start with
[`EVALUATION.md`](EVALUATION.md): it maps every requirement and rubric criterion to files,
lists the measured results with their raw data, gives quick verification commands, and states
the known limitations.

If you are an AI agent working on the code:

- Run `uv sync && uv run pytest` (offline, no AWS or model needed).
- The reusable decision pattern lives in `referee/guard.py`; game-specific policy and
  thresholds live in `referee/game.py`. Keep them separate.
- Never commit credentials; Bedrock uses the standard AWS credential chain.
- Benchmark numbers in docs must come from `bench/results*.json`
  (`uv run python -m bench.run_bench --report`).
