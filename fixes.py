#!/usr/bin/env python3
"""Fix ladders for KeySurgeon - the honest "try this before you replace it" brain.

Maps a fault to an ordered list of fixes, cheapest/easiest first. Board type
reshapes which rungs apply (a laptop scissor switch is not a hot-swap MX). The
whole point: 'replace the keyboard' is the LAST rung and usually unnecessary.
"""

from faults import OK, CHATTER, DEAD, INTERMITTENT, STICKY, EXTRA

# board types
LAPTOP = "laptop"
MEMBRANE = "membrane"
HOTSWAP = "hotswap"
SOLDERED = "soldered"
UNKNOWN = "unknown"

BOARD_CHOICES = [
    (LAPTOP, "Laptop / built-in keyboard"),
    (MEMBRANE, "External membrane / rubber-dome"),
    (HOTSWAP, "Mechanical, hot-swappable switches"),
    (SOLDERED, "Mechanical, soldered switches"),
    (UNKNOWN, "Not sure"),
]

# Each rung: (boards_that_apply or None=all, title, blurb)
# Listed easiest-first; the renderer filters by board type.
_AIR = (None, "Blow it out",
        "Compressed air under and around the key - debris can mimic chatter, "
        "dead, and sticky faults. Free, 1 minute, always worth trying first.")
_FILTER = (None, "Software filter",
           "A debounce filter blocks the bounce in software right now - free, "
           "instant. Good stopgap while you sort the hardware.")
_CLEAN = ({LAPTOP, MEMBRANE, SOLDERED, HOTSWAP, UNKNOWN}, "Clean the contact",
          "Pop the keycap and clean the contact/stem with isopropyl alcohol. "
          "Free, ~5 min. Fixes a lot of dirty-contact misses.")
_HOTSWAP = ({HOTSWAP}, "Hot-swap the switch",
            "Pull the keycap and switch, drop in a fresh one - no soldering. "
            "~$0.30 and 2 minutes. Your board supports it. This is the real fix.")
_DESOLDER = ({SOLDERED}, "Desolder + replace the switch",
             "Soldered board: desolder the bad switch and fit a new one. Needs "
             "an iron and some skill, ~20 min, but cheaper than a new board.")
_LUBE = ({HOTSWAP, SOLDERED}, "Lube or re-spring",
         "If it sticks rather than chatters, a thin lube or a fresh spring on "
         "that switch smooths it out.")
_LAPTOP_NOTE = ({LAPTOP}, "Reseat the keycap / clean under it",
                "Laptop keys use a scissor clip - gently pry the cap, clean "
                "under it, reseat. If the scissor or dome is torn, a single "
                "replacement keycap+clip is cheap vs a whole board.")
_REPLACE = (None, "Replace the keyboard",
            "Last resort - only if the controller is dead, there's spill "
            "corrosion across many keys, or a PCB trace is gone. Not needed "
            "for a single bad key.")

LADDERS = {
    CHATTER: [_FILTER, _AIR, _CLEAN, _HOTSWAP, _DESOLDER, _LAPTOP_NOTE, _REPLACE],
    DEAD: [_AIR, _CLEAN, _HOTSWAP, _DESOLDER, _LAPTOP_NOTE, _REPLACE],
    INTERMITTENT: [_AIR, _CLEAN, _HOTSWAP, _DESOLDER, _LAPTOP_NOTE, _REPLACE],
    STICKY: [_AIR, _CLEAN, _LUBE, _HOTSWAP, _DESOLDER, _LAPTOP_NOTE, _REPLACE],
    EXTRA: [_FILTER, _AIR, _CLEAN, _HOTSWAP, _DESOLDER, _REPLACE],
}

# the reassuring closer per fault
CLOSER = {
    CHATTER: "You do NOT need a new keyboard for a single chattering key.",
    DEAD: "A dead key is usually debris or a swappable switch - try the cheap rungs first.",
    INTERMITTENT: "Flaky keys are very often just dirty. Clean before you replace.",
    STICKY: "Sticky usually means gunk, not a dead board.",
    EXTRA: "This is early chatter - cheap to fix now, before it gets worse.",
}


def ladder_for(fault, board_type=UNKNOWN):
    """Return (rungs, closer) where rungs is a list of (n, title, blurb),
    numbered after board filtering. board_type=UNKNOWN shows everything with
    a hint. OK faults return ([], '')."""
    if fault == OK:
        return [], ""
    rungs = []
    n = 0
    for boards, title, blurb in LADDERS.get(fault, []):
        if boards is not None and board_type != UNKNOWN and board_type not in boards:
            continue
        n += 1
        rungs.append((n, title, blurb))
    return rungs, CLOSER.get(fault, "")
