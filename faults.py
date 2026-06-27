#!/usr/bin/env python3
"""Fault taxonomy + classification for KeySurgeon.

Turns a raw trial stats dict into a human verdict: what's wrong, in plain
words, how sure we are, and a 0-100 health score for the key. The headline is
for a person ("This key is double-typing"); the numbers are evidence.
"""

# fault ids used to look up fix ladders in fixes.py
OK = "ok"
CHATTER = "chatter"
DEAD = "dead"
INTERMITTENT = "intermittent"
STICKY = "sticky"
EXTRA = "extra"

# board-health bands by score
BANDS = [
    (90, "HEALTHY"),
    (70, "WATCH"),
    (40, "DEGRADING"),
    (0, "FAILING"),
]


def band(score):
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "FAILING"


def _confidence(registered):
    if registered >= 60:
        return "high"
    if registered >= 12:
        return "medium"
    return "low"


def classify(stats):
    """stats -> verdict dict:
        {fault, label, headline, detail, evidence[list], score, confidence}
    """
    label = stats["label"]
    reg = stats["registered"]
    exp = stats["expected"]
    chatter = stats["chatter"]
    conf = _confidence(reg)
    ev = []

    # CHATTER - bounce wins; it's the most actionable and most common failure.
    # Score scales with how often it bounces: a lone bounce is milder than
    # bouncing on half your presses.
    if chatter:
        if stats["min_regap"] is not None:
            ev.append(f"re-press {stats['min_regap']}ms (human floor ~60ms)")
        ev.append(f"{chatter} bounce{'s' if chatter != 1 else ''} in {reg} presses")
        ev.append(f"confidence: {conf}")
        score = max(10, 60 - round(60 * chatter / max(reg, 1)))
        return {
            "fault": CHATTER, "label": label,
            "headline": "This key is double-typing.",
            "detail": ("The switch is bouncing - that's hardware wear, not "
                       "anything you're doing wrong."),
            "evidence": ev, "score": score, "confidence": conf,
        }

    # DEAD - nothing registered at all
    if reg == 0:
        ev.append("0 presses registered")
        ev.append(f"confidence: {conf}")
        return {
            "fault": DEAD, "label": label,
            "headline": "This key isn't responding.",
            "detail": ("Nothing registered. Could be debris in the switch, a "
                       "dirty contact, or a dead switch - often cleanable."),
            "evidence": ev, "score": 0, "confidence": conf,
        }

    # INTERMITTENT - some presses didn't land
    if reg < exp:
        miss = exp - reg
        rate = round(100 * miss / exp)
        ev.append(f"{reg}/{exp} registered ({miss} missed)")
        if stats["short_holds"]:
            ev.append(f"also {stats['short_holds']} very short holds "
                      f"(may be sticking too)")
        ev.append(f"confidence: {conf}")
        return {
            "fault": INTERMITTENT, "label": label,
            "headline": "This key skips sometimes.",
            "detail": ("Some presses didn't register. Usually a dirty or worn "
                       "contact - cleaning often brings it back."),
            "evidence": ev, "score": max(5, 100 - rate), "confidence": conf,
        }

    # EXTRA - more registered than asked: late bounces after the last press
    if reg > exp:
        extra = reg - exp
        ev.append(f"{extra} extra press{'es' if extra != 1 else ''} after you stopped")
        if stats["short_holds"]:
            ev.append(f"also {stats['short_holds']} very short holds "
                      f"(may be sticking too)")
        ev.append(f"confidence: {conf}")
        return {
            "fault": EXTRA, "label": label,
            "headline": "This key fires extra presses.",
            "detail": ("It registered bounces after you let go - early-stage "
                       "chatter. Worth keeping an eye on."),
            "evidence": ev, "score": 60, "confidence": conf,
        }

    # STICKY - registered fine but holds look abnormal
    if stats["short_holds"]:
        ev.append(f"{stats['short_holds']} suspiciously short holds "
                  f"(<8ms)")
        ev.append(f"confidence: {conf}")
        return {
            "fault": STICKY, "label": label,
            "headline": "This key feels off.",
            "detail": ("Holds registered oddly short - can mean a sticky or "
                       "mushy switch. Cleaning or lube usually helps."),
            "evidence": ev, "score": 70, "confidence": conf,
        }

    # OK
    ev.append(f"{reg}/{exp} clean, no bounce")
    ev.append(f"confidence: {conf}")
    return {
        "fault": OK, "label": label,
        "headline": "This key is healthy.",
        "detail": "Clean presses, no double-firing, no misses. Nothing to fix.",
        "evidence": ev, "score": 100, "confidence": conf,
    }
