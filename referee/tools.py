"""Game tools the narrator calls. Structured checks (is the item in the inventory? is that an
exit?) are plain code. Fuzzy checks (is this claim established? is this plausible?) are the
referee's job, before the tool ever runs. The referee's dice roll arrives in
world.pending_roll; each tool reads it to decide success or failure.
"""

from __future__ import annotations

from strands import tool

from .world import World, new_world

_world: World = new_world()


def world() -> World:
    return _world


def reset() -> World:
    global _world
    _world = new_world()
    return _world


def _outcome() -> tuple[bool, str]:
    roll = _world.pending_roll
    _world.pending_roll = None
    if roll is None:
        return True, ""
    tag = f"(d20 rolled {roll['roll']} vs DC {roll['dc']})"
    return roll["success"], tag


def _have(item: str) -> str | None:
    item_l = item.lower()
    for owned in _world.inventory:
        if owned.lower() in item_l or item_l in owned.lower():
            return owned
    return None


@tool
def move(destination: str) -> str:
    """Move Pip to an adjacent location.

    Args:
        destination: one of the current location's exits, e.g. "bridge".
    """
    dest = destination.lower().strip()
    if dest not in _world.here.exits:
        return f"BLOCKED: {destination} is not an exit from here. Exits: {', '.join(_world.here.exits)}."
    if _world.location == "bridge" and dest == "keep gate" and "bridge_open" not in _world.story_flags:
        return "BLOCKED: Grub the troll stands in the way."
    if _world.location == "keep gate" and dest == "dragon lair" and "gate_open" not in _world.story_flags:
        return "BLOCKED: Sir Dunmore will not open the gate without the password."
    _world.location = dest
    _world.log(f"Pip went to {_world.here.name}.")
    return f"OK: Pip is now at {_world.here.name}. {_world.here.description}"


@tool
def take(item: str) -> str:
    """Pick up an item that is lying here.

    Args:
        item: the item to pick up.
    """
    match = next((i for i in _world.here.items if i.lower() in item.lower() or item.lower() in i.lower()), None)
    if not match:
        return f"FAILED: there is no {item} here."
    ok, tag = _outcome()
    if not ok:
        if match == "golden crown":
            _world.hp -= 4
            _world.log("Pip tried to grab the crown; the dragon stirred and singed Pip.")
            return f"FAILURE {tag}: the dragon stirs and breathes a puff of flame. Pip loses 4 HP."
        return f"FAILURE {tag}: Pip fumbles and drops it."
    _world.here.items.remove(match)
    _world.inventory.append(match)
    _world.log(f"Pip took the {match}.")
    if match == "golden crown":
        _world.won = True
        return f"SUCCESS {tag}: Pip lifts the golden crown. QUEST COMPLETE."
    return f"SUCCESS {tag}: Pip takes the {match}."


@tool
def use_item(item: str, target: str) -> str:
    """Use an item from the inventory on something or someone.

    Args:
        item: an item Pip carries.
        target: what to use it on.
    """
    owned = _have(item)
    if not owned:
        return f"FAILED: Pip does not have a {item}. Inventory: {', '.join(_world.inventory)}."
    ok, tag = _outcome()
    result = "works" if ok else "does not work"
    _world.log(f"Pip used the {owned} on {target}: it {result}.")
    return f"{'SUCCESS' if ok else 'FAILURE'} {tag}: the {owned} {result} on {target}."


@tool
def attack(target: str, weapon: str) -> str:
    """Attack someone with a weapon Pip carries.

    Args:
        target: who or what to attack.
        weapon: the weapon used.
    """
    owned = _have(weapon)
    if not owned:
        return f"FAILED: Pip has no {weapon}. Inventory: {', '.join(_world.inventory)}."
    ok, tag = _outcome()
    if ok:
        _world.log(f"Pip hit {target} with the {owned}.")
        return f"SUCCESS {tag}: Pip lands a hit on {target}."
    _world.hp -= 3
    _world.log(f"Pip attacked {target} and got hurt.")
    return f"FAILURE {tag}: the attack fails and Pip takes 3 damage (HP {_world.hp})."


@tool
def cast_spell(spell: str, target: str) -> str:
    """Cast a spell (only for characters who can cast spells).

    Args:
        spell: the spell name.
        target: the target.
    """
    ok, tag = _outcome()
    _world.log(f"Pip attempted to cast {spell}.")
    return f"{'SUCCESS' if ok else 'FAILURE'} {tag}: {spell} {'takes effect' if ok else 'fizzles'}."


@tool
def give(item: str, recipient: str) -> str:
    """Give an item Pip carries to someone here.

    Args:
        item: the item to give.
        recipient: who receives it.
    """
    owned = _have(item)
    if not owned:
        return f"FAILED: Pip does not have a {item}."
    ok, tag = _outcome()
    if not ok:
        return f"FAILURE {tag}: {recipient} refuses the {owned}."
    _world.inventory.remove(owned)
    _world.log(f"Pip gave the {owned} to {recipient}.")
    if "grub" in recipient.lower():
        _world.story_flags.add("bridge_open")
        return f"SUCCESS {tag}: Grub accepts the {owned} and steps aside. The bridge is open."
    return f"SUCCESS {tag}: {recipient} accepts the {owned}."


@tool
def speak(npc: str, message: str) -> str:
    """Pip says something to an NPC who is here: persuade, bluff, ask, tell a riddle, say a password.

    Args:
        npc: who Pip talks to.
        message: what Pip says.
    """
    ok, tag = _outcome()
    who = npc.lower()
    if "dunmore" in who or "guard" in who:
        knows = any("turnip" in s for s in _world.story)
        if "turnip" in message.lower() and knows:
            _world.story_flags.add("gate_open")
            _world.log("Pip said the password; Sir Dunmore opened the gate.")
            return "SUCCESS: correct password. The gate swings open."
        if not ok:
            return f"FAILURE {tag}: Sir Dunmore is not convinced."
    if "grub" in who or "troll" in who:
        if ok:
            _world.story_flags.add("bridge_open")
            _world.log("Pip outwitted Grub; the bridge is open.")
            return f"SUCCESS {tag}: Grub is stumped and lets Pip pass."
        return f"FAILURE {tag}: Grub laughs and stays put."
    _world.log(f"Pip told {npc}: {message[:80]}")
    return f"{'SUCCESS' if ok else 'FAILURE'} {tag}: {npc} {'is convinced' if ok else 'is unconvinced'}."


@tool
def reveal(npc: str, fact: str) -> str:
    """Record that an NPC told Pip something they know. Use whenever an NPC shares information.

    Args:
        npc: the NPC speaking.
        fact: the information they reveal.
    """
    _world.log(f"{npc} revealed: {fact}")
    return f"OK: noted that {npc} revealed: {fact}"


ALL_TOOLS = [move, take, use_item, attack, cast_spell, give, speak, reveal]
GATED = {"take", "use_item", "attack", "cast_spell", "give", "speak", "reveal"}
