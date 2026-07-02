#!/usr/bin/env python3
"""User-data paths for KeySurgeon runtime state."""

import os

APPNAME = "KeySurgeon"


def data_dir():
    """Return a writable per-user data directory.

    Override with KEYSURGEON_HOME for portable installs or tests.
    """
    override = os.environ.get("KEYSURGEON_HOME")
    if override:
        root = override
    elif os.name == "nt":
        root = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                            APPNAME)
    else:
        root = os.path.join(os.path.expanduser("~"), ".keysurgeon")
    try:
        os.makedirs(root, exist_ok=True)
    except OSError:
        root = os.getcwd()
    return root


def path(name):
    return os.path.join(data_dir(), name)
