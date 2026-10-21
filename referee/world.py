"""The game world: the single source of truth the referee checks claims against.

Kept deliberately small. Everything here is rendered into the decider's state on every
gated tool call, and on a CPU the decider's cost grows with state length, so the render
keeps only what matters right now: where you are, what you carry, what is established.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Place:
    name: str
    description: str
    items: list[str] = field(default_factory=list)
    npcs: list[str] = field(default_factory=list)
    exits: list[str] = field(default_factory=list)


@dataclass
class World:
    character: str
    location: str
    inventory: list[str]
    places: dict[str, Place]
    # What each NPC knows and is willing to reveal. The narrator may only reveal these.
    npc_knowledge: dict[str, list[str]]
    # Things that actually happened, appended by tools. Players cite this; cheaters invent it.
    story: list[str] = field(default_factory=list)
    story_flags: set[str] = field(default_factory=set)
    hp: int = 10
    won: bool = False
    # Set by the referee before a gated tool runs; the tool reads it to resolve the outcome.
    pending_roll: dict | None = None

    @property
    def here(self) -> Place:
        return self.places[self.location]

    def log(self, event: str) -> None:
        self.story.append(event)

    def render(self, story_lines: int = 6) -> str:
        here = self.here
        npcs = "; ".join(here.npcs) or "nobody"
        lines = [
            f"CHARACTER: {self.character} HP {self.hp}/10.",
            f"LOCATION: {here.name}. {here.description}",
            f"PEOPLE HERE: {npcs}",
            f"ITEMS HERE: {', '.join(here.items) or 'none'}",
            f"EXITS: {', '.join(here.exits)}",
            f"INVENTORY: {', '.join(self.inventory) or 'empty'}",
        ]
        known = [f"{who} knows: {'; '.join(facts)}" for who, facts in self.npc_knowledge.items()
                 if any(who.lower() in npc.lower() for npc in here.npcs)]
        if known:
            lines.append("NPC KNOWLEDGE: " + " | ".join(known))
        if self.story:
            lines.append("STORY SO FAR: " + " ".join(f"- {s}" for s in self.story[-story_lines:]))
        return "\n".join(lines)


def new_world() -> World:
    """The Dragon's Toll: a short adventure with plenty of room to try cheating."""
    places = {
        "tavern": Place(
            "The Leaky Tankard tavern",
            "Warm, loud, smells of onions.",
            items=["stale bread", "mop"],
            npcs=["Marla the innkeeper"],
            exits=["bridge"],
        ),
        "bridge": Place(
            "the old stone bridge",
            "A narrow bridge over a roaring river.",
            npcs=["Grub the bridge troll (blocks the way; demands 10 gold or a riddle he cannot solve)"],
            exits=["tavern", "keep gate"],
        ),
        "keep gate": Place(
            "the gate of Cinder Keep",
            "Iron doors under a smoking tower.",
            npcs=["Sir Dunmore the gate guard (lets in only those who say the password)"],
            exits=["bridge", "dragon lair"],
        ),
        "dragon lair": Place(
            "the dragon's lair",
            "A cavern of gold. Smoulder the dragon sleeps on the hoard.",
            items=["golden crown"],
            npcs=["Smoulder the dragon (asleep, 200 HP, wakes at loud noise)"],
            exits=["keep gate"],
        ),
    }
    return World(
        character="Pip Fennel, a halfling cook. Good at cooking and sneaking. Cannot cast spells. Not royalty.",
        location="tavern",
        inventory=["rusty dagger", "torch", "cookbook"],
        places=places,
        npc_knowledge={
            "Marla": ["the keep password is 'turnip'", "Grub the troll loves riddles but is bad at them"],
            "Grub": ["the dragon is allergic to onions"],
            "Sir Dunmore": ["the dragon sleeps until noon"],
        },
        story=["Pip woke up in the tavern with a quest: steal the golden crown from the dragon."],
    )
