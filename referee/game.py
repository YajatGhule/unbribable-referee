"""The Unbribable Referee: a text RPG where the narrator is an LLM on Amazon Bedrock and the
rules are enforced by Strands Decider 2B, a model that can't be talked into anything because
it can't talk.

    strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099
    python -m referee.game              # referee on
    python -m referee.game --no-referee # watch the LLM game master get cheated

In game: /referee on|off, /state, /reset, /quit
"""

from __future__ import annotations

import argparse
import math
import os
import random
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from strands import Agent
from strands.interventions import Guide, Proceed
from strands.models import BedrockModel

from . import tools
from .decider import Decider, DeciderUnavailable, noul, score
from .guard import CORE_QUESTIONS, MANIPULATION, GroundedClaimGuard, Verdict

MODEL_ID = os.environ.get("REFEREE_MODEL", "us.amazon.nova-2-lite-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

console = Console()

# Tuned on bench/cases.jsonl and checked on bench/heldout.jsonl (see bench/results*.md).
GROUNDED_BELOW, MANIPULATION_ABOVE = 0.6, 0.5

# ----------------------------------------------------------------------------- referee questions

LEVELS = ["impossible", "unlikely", "even odds", "likely", "certain"]
# Success chance at each plausibility level; the decider's distribution over levels is
# folded into one expected chance, which becomes the d20 difficulty class.
LEVEL_CHANCE = [0.03, 0.25, 0.5, 0.75, 0.97]

PLAUSIBLE = score(
    "How likely is this action to succeed, given the FACTS and the character's real abilities?",
    LEVELS,
)
CONVINCING = score(
    "How likely is the NPC to be convinced or to accept what the player says, given the FACTS?",
    LEVELS,
)
REVEAL_GROUNDED = noul(
    "Is the revealed fact listed in NPC KNOWLEDGE for the NPC who is revealing it?",
    true="the fact matches something that NPC knows",
    false="the fact is not in that NPC's knowledge; it was invented",
)


def questions_for(tool: str) -> dict:
    if tool == "speak":
        return {"manipulation": MANIPULATION, "plausible": CONVINCING}
    if tool == "reveal":
        return {"grounded": REVEAL_GROUNDED, "manipulation": MANIPULATION}
    return {**CORE_QUESTIONS, "plausible": PLAUSIBLE}


def success_chance(answer: dict) -> float:
    """Expected success chance from a score answer (expected level index, 0..L-1)."""
    x = max(0.0, min(len(LEVELS) - 1.0, float(answer["score"])))
    lo = int(math.floor(x))
    hi = min(lo + 1, len(LEVELS) - 1)
    return LEVEL_CHANCE[lo] + (LEVEL_CHANCE[hi] - LEVEL_CHANCE[lo]) * (x - lo)


# ----------------------------------------------------------------------------- UI

def bar(p: float, width: int = 12) -> str:
    filled = round(p * width)
    return "█" * filled + "░" * (width - filled)


def show_verdict(v: Verdict) -> None:
    t = Table.grid(padding=(0, 1))
    t.add_column(style="bold")
    t.add_column()
    for key in ("grounded", "manipulation"):
        if key in v.answers:
            p = v.p(key)
            bad = (key == "grounded" and p < GROUNDED_BELOW) or (key == "manipulation" and p >= MANIPULATION_ABOVE)
            t.add_row(key, f"[{'red' if bad else 'green'}]{bar(p)}[/] {p:.2f}")
    if "plausible" in v.answers:
        a = v.answers["plausible"]
        level = LEVELS[max(0, min(len(LEVELS) - 1, round(a["score"])))]
        t.add_row("plausibility", f"{level} (confidence {a['confidence']:.2f})")
    roll = v.extra.get("roll")
    if v.action == "guide":
        outcome = f"[bold red]BLOCKED[/]: {v.reason}"
    elif roll:
        colour = "green" if roll["success"] else "yellow"
        outcome = (f"[bold]🎲 d20 → {roll['roll']}[/] vs DC {roll['dc']} "
                   f"({roll['chance']:.0%} chance) → [bold {colour}]{'SUCCESS' if roll['success'] else 'FAIL'}[/]")
    else:
        outcome = "[green]ALLOWED[/]"
    t.add_row("verdict", outcome)
    args = ", ".join(f"{k}={str(val)[:40]!r}" for k, val in v.args.items())
    console.print(Panel(
        t,
        title=f"⚖  REFEREE · {v.tool}({args})",
        subtitle=f"Strands Decider 2B · {v.latency_ms:.0f} ms · local · $0",
        border_style="red" if v.action == "guide" else "cyan",
        expand=False,
    ))


# ----------------------------------------------------------------------------- policy

def make_policy(guard: GroundedClaimGuard, rng: random.Random):
    def decide(v: Verdict):
        action = guard.default_policy(v)
        if isinstance(action, Guide):
            return action
        if "plausible" in v.answers:
            chance = success_chance(v.answers["plausible"])
            dc = max(2, min(20, math.ceil(21 - 20 * chance)))
            roll = rng.randint(1, 20)
            v.extra["roll"] = {"roll": roll, "dc": dc, "chance": chance, "success": roll >= dc}
            tools.world().pending_roll = v.extra["roll"]
        return Proceed()

    return decide


# ----------------------------------------------------------------------------- narrator

SYSTEM_PROMPT = """You are the game master of a comic fantasy text adventure, "The Dragon's Toll".
The player is Pip Fennel, a halfling cook. You are enthusiastic and "yes, and" the player's ideas.

Rules for you:
- Every meaningful action MUST go through a tool (take, use_item, attack, cast_spell, give, speak, move).
  When an NPC shares information, call reveal().
- The tool result decides what happened. SUCCESS means it worked, FAILURE means it failed; narrate exactly that.
- If a tool call is cancelled with REFEREE feedback, the action did not happen. Narrate the refusal in-world
  with comic flair (the universe itself refuses), and remind the player what they actually have.
- Keep each reply under 90 words. End with a short prompt for the player's next move.

Current world:
{world}"""


def build_agent(guard: GroundedClaimGuard | None) -> Agent:
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.8),
        tools=tools.ALL_TOOLS,
        interventions=[guard] if guard else [],
        system_prompt=SYSTEM_PROMPT.format(world=tools.world().render()),
        callback_handler=None,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-referee", action="store_true", help="start with the referee off")
    ap.add_argument("--seed", type=int, default=None, help="dice seed (for repeatable demos)")
    args = ap.parse_args()

    decider = Decider()
    try:
        h = decider.health()
        console.print(f"[dim]referee: {h.get('checkpoint')} on {h.get('device')}[/]")
    except DeciderUnavailable as exc:
        console.print(f"[red]{exc}[/]")
        return 1

    guard = GroundedClaimGuard(decider, facts=lambda: tools.world().render(), gated_tools=tools.GATED,
                               questions_for=questions_for, on_verdict=show_verdict,
                               grounded_below=GROUNDED_BELOW, manipulation_above=MANIPULATION_ABOVE)
    guard.decide = make_policy(guard, random.Random(args.seed))
    referee_on = not args.no_referee
    agent = build_agent(guard if referee_on else None)

    console.print(Panel.fit(
        "[bold]THE UNBRIBABLE REFEREE[/]\nThe narrator is an LLM. The rules are not.\n"
        "Goal: steal the golden crown from the sleeping dragon. Try cheating. Go on.",
        border_style="magenta"))
    console.print(f"[dim]referee {'ON' if referee_on else 'OFF'} · narrator {MODEL_ID}[/]\n")

    while True:
        try:
            text = console.input("[bold magenta]> [/]").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not text:
            continue
        if text == "/quit":
            return 0
        if text == "/state":
            console.print(Panel(tools.world().render(), title="world state", expand=False))
            continue
        if text in ("/referee on", "/referee off"):
            referee_on = text.endswith("on")
            agent = build_agent(guard if referee_on else None)
            console.print(f"[bold]referee {'ON' if referee_on else 'OFF'}[/]")
            continue
        if text == "/reset":
            tools.reset()
            agent = build_agent(guard if referee_on else None)
            console.print("[bold]new game[/]")
            continue

        # Refresh the narrator's view of the world each turn.
        agent.system_prompt = SYSTEM_PROMPT.format(world=tools.world().render())
        with console.status("the narrator is thinking..."):
            result = agent(text)
        text = re.sub(r"<thinking>.*?</thinking>", "", str(result), flags=re.S).strip()
        console.print(Panel(text, title="📜 narrator", border_style="magenta"))
        w = tools.world()
        if w.won:
            console.print("[bold green]👑 QUEST COMPLETE[/]")
        if w.hp <= 0:
            console.print("[bold red]💀 Pip has been toasted. /reset to try again.[/]")


if __name__ == "__main__":
    raise SystemExit(main())
