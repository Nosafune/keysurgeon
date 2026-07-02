#!/usr/bin/env python3
"""Environment checks for support and release triage."""

import os
import platform
import sys

import brand
import storage
import ui


def _check(label, ok, detail):
    state = "ok" if ok else "check"
    color = "OK" if ok else "WRN"
    print("  " + ui.c(f"{state:<5}", color, "BLD") + " " + f"{label:<18} {detail}")
    return bool(ok)


def _info(label, detail):
    print("  " + ui.c("info ", "DIM", "BLD") + " " + f"{label:<18} {detail}")


def _module_available(name):
    try:
        __import__(name)
        return True
    except Exception:
        return False


def run():
    """Print a compact support report. Does not read typed text or start hooks."""
    ui.banner("doctor")
    print("  " + ui.c(f"{brand.NAME} {brand.VERSION}", "BLD", "ACC"))
    print()

    checks = []
    checks.append(_check("platform", os.name == "nt",
                         f"{platform.system()} {platform.release()}"))
    checks.append(_check("python", sys.version_info >= (3, 10),
                         platform.python_version()))
    checks.append(_check("rich", _module_available("rich"),
                         "installed" if _module_available("rich") else "missing"))
    checks.append(_check("textual", _module_available("textual"),
                         "installed" if _module_available("textual") else "missing"))

    data = storage.data_dir()
    checks.append(_check("runtime dir", os.path.isdir(data), data))
    _info("color", "enabled" if ui.USE_COLOR else "disabled/plain")
    _info("rich ui", "active" if ui.USE_RICH else "fallback active")

    try:
        import app_textual
        app_ok = app_textual.build_app() is not None
    except Exception as exc:
        app_ok = False
        app_detail = f"unavailable: {exc.__class__.__name__}"
    else:
        app_detail = "ready" if app_ok else "textual missing"
    checks.append(_check("textual app", app_ok, app_detail))

    print()
    if all(checks):
        print("  " + ui.c("doctor passed", "OK", "BLD"))
    else:
        print("  " + ui.c("doctor found support notes", "WRN", "BLD"))
        print("  Run with --plain when pasting output into an issue.")
