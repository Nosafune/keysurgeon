#!/usr/bin/env python3
"""Diagnostic trial primitives for KeySurgeon.

Each trial drives the shared hook, collects press/release events for one key,
and returns a raw stats dict. Classification (what the stats *mean*) lives in
faults.py - trials only measure.
"""

import time

from hook import VK_ESCAPE

CHATTER_MS = 35       # re-press faster than this after release = bounce
IDLE_DONE_MS = 2000   # this much silence after >=1 press ends the trial
SHORT_HOLD_MS = 8     # holds shorter than this are suspicious
GRACE_MS = 400        # after hitting target, watch this long for extra bounces
STUCK_MS = 1000       # a "down while down" after this long = we missed a key-up


def chatter_trial(hook, vk, label, expected, on_progress=None):
    """Press a key until the counter hits `expected`. Measures bounce, misses,
    holds. Returns a stats dict (or None if the user pressed ESC to skip).

    on_progress(registered, expected) is called whenever the count changes so
    the UI can draw a live counter.
    """
    hook.events.clear()

    presses = []        # down timestamps (autorepeat filtered out)
    holds = []          # ms each press was held
    regap = []          # ms between a release and the next press
    chatter = 0
    is_down = False
    t_down = None
    t_up = None
    last_activity = None
    done_at = None

    if on_progress:
        on_progress(0, expected)

    t_last_evt = None   # perf ms of the last event for this key (stuck watchdog)

    while True:
        hook.pump()
        while hook.events:
            evk, down, t = hook.events.pop(0)
            # ESC skips - but not when ESC is itself the key under test
            if evk == VK_ESCAPE and down and vk != VK_ESCAPE:
                return None
            if evk != vk:
                continue
            last_activity = time.monotonic()
            since = (t - t_last_evt) if t_last_evt is not None else 0
            t_last_evt = t
            if down:
                # if we're "still down" but it's been quiet a long time, we
                # missed a key-up - recover instead of eating every press
                if is_down and since > STUCK_MS:
                    is_down = False
                if is_down:
                    continue  # autorepeat, not a new press
                is_down = True
                t_down = t
                presses.append(t)
                if t_up is not None:
                    gap = t - t_up
                    regap.append(gap)
                    if gap < CHATTER_MS:
                        chatter += 1
                if on_progress:
                    on_progress(len(presses), expected)
                if len(presses) >= expected and done_at is None:
                    done_at = time.monotonic()
            else:
                if is_down and t_down is not None:
                    holds.append(t - t_down)
                is_down = False
                t_up = t
        if done_at and (time.monotonic() - done_at) * 1000 > GRACE_MS:
            break
        if (presses and last_activity
                and (time.monotonic() - last_activity) * 1000 > IDLE_DONE_MS):
            break
        time.sleep(0.001)

    return {
        "label": label,
        "vk": vk,
        "expected": expected,
        "registered": len(presses),
        "chatter": chatter,
        "min_regap": round(min(regap)) if regap else None,
        "short_holds": sum(1 for h in holds if h < SHORT_HOLD_MS),
        "med_hold": round(sorted(holds)[len(holds) // 2]) if holds else None,
        "max_hold": round(max(holds)) if holds else None,
    }
