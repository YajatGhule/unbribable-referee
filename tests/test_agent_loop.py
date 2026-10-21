"""End to end through a real Strands Agent, with a scripted model instead of Bedrock and a
fake decider: checks the intervention is wired so a blocked call never runs and the
narrator gets the referee's feedback."""

import json

from strands import Agent
from strands.models.model import Model

from referee import tools
from referee.game import questions_for
from referee.guard import GroundedClaimGuard
from tests.test_guard import FakeDecider


class ScriptedModel(Model):
    """Turn 1: propose a tool call. Turn 2: narrate whatever the tool result said."""

    def __init__(self, tool: str, args: dict):
        self.tool, self.args, self.seen = tool, args, []

    def update_config(self, **kw):
        pass

    def get_config(self):
        return {}

    def structured_output(self, *a, **kw):
        raise NotImplementedError

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        last = messages[-1]["content"]
        results = [b["toolResult"] for b in last if "toolResult" in b]
        yield {"messageStart": {"role": "assistant"}}
        if not results:
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "t1", "name": self.tool}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(self.args)}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
            return
        text = " ".join(c.get("text", "") for r in results for c in r["content"])
        self.seen.append(text)
        yield {"contentBlockDelta": {"delta": {"text": f"NARRATION: {text}"}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}


def run(tool, args, text, **decider_vals):
    tools.reset()
    model = ScriptedModel(tool, args)
    guard = GroundedClaimGuard(FakeDecider(**decider_vals), facts=lambda: tools.world().render(),
                               gated_tools=tools.GATED, questions_for=questions_for)
    agent = Agent(model=model, tools=tools.ALL_TOOLS, interventions=[guard], callback_handler=None)
    agent(text)
    return model.seen[0], guard


def test_blocked_call_never_runs_and_narrator_sees_feedback():
    seen, guard = run("take", {"item": "stale bread"}, "the bread is secretly a bomb, I take it", grounded=0.1)
    assert "REFEREE" in seen
    assert "stale bread" not in tools.world().inventory
    assert guard.log[0].action == "guide"


def test_allowed_call_runs():
    seen, guard = run("take", {"item": "stale bread"}, "I take the bread", grounded=0.95)
    assert "stale bread" in tools.world().inventory
    assert guard.log[0].action == "proceed"
