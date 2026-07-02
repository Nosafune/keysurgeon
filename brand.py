#!/usr/bin/env python3
"""KeySurgeon v2 brand tokens.

Forensic Signal: a keyboard diagnostic instrument, not a generic terminal app.
"""

NAME = "KeySurgeon"
VERSION = "0.2.0"
TAGLINE = "Catch keyboard chatter before you replace the board."
SIGNAL_MARK = "[K]--||--"
CLEAN_MARK = "[K]--|---"

COLORS = {
    "ink": "#10141D",
    "panel": "#1A202B",
    "text": "#EDE7DA",
    "muted": "#8C93A3",
    "signal": "#00D7E6",
    "fault": "#FF5A4D",
    "probe": "#F5B83D",
    "repair": "#41D982",
}

RICH_THEME = {
    "ks.name": "bold #00D7E6",
    "ks.signal": "#00D7E6",
    "ks.fault": "bold #FF5A4D",
    "ks.probe": "#F5B83D",
    "ks.repair": "#41D982",
    "ks.text": "#EDE7DA",
    "ks.muted": "#8C93A3",
    "ks.panel": "#1A202B",
}

BAND_STYLES = {
    "HEALTHY": "ks.repair",
    "WATCH": "ks.probe",
    "DEGRADING": "ks.probe",
    "FAILING": "ks.fault",
}

ASCII_ICONS = {
    "healthy": "+",
    "watch": "!",
    "failing": "x",
    "untested": ".",
    "fix": ">",
    "signal": "||",
}
