#!/usr/bin/env python3
"""Background + foreground chatter watch for KeySurgeon.

One hook loop (run_loop) shared by both:
  - foreground: prints bounces live, returns tallies on Ctrl+C
  - background: runs hidden (pythonw, detached), writes a live state file and
    periodically saves to the profile, until `watch --stop`

Background control mirrors chatterguard's proven pid pattern (no kill-by-name).
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import sys
import time

import faults
import profile
import trials
from hook import KeyboardHook, vk_name, VK_ESCAPE

kernel32 = ctypes.windll.kernel32

HERE = os.path.dirname(os.path.abspath(__file__))
PIDFILE = os.path.join(HERE, "keysurgeon_watch.pid")
STATEFILE = os.path.join(HERE, "keysurgeon_watch.json")
STOPFILE = os.path.join(HERE, "keysurgeon_watch.stop")

STATE_EVERY = 3.0      # seconds between state-file writes + stop-flag checks
PROFILE_EVERY = 60.0   # seconds between profile saves (background)


# ---------- pid helpers (same shape as chatterguard) ----------

def _read_pid():
    try:
        with open(PIDFILE) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid):
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    code = wt.DWORD()
    alive = (kernel32.GetExitCodeProcess(h, ctypes.byref(code))
             and code.value == 259)  # STILL_ACTIVE
    kernel32.CloseHandle(h)
    return bool(alive)


def is_running():
    pid = _read_pid()
    return bool(pid and _pid_alive(pid)), pid


# ---------- live state file ----------

def _write_state(keyboard, started, bounces, presses):
    data = {
        "keyboard": keyboard,
        "started": started,
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "keys": {vk_name(vk): {"bounces": bounces[vk],
                               "presses": presses.get(vk, 0)}
                 for vk in bounces},
    }
    # atomic write so a concurrent --status reader never sees a torn file
    tmp = STATEFILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, STATEFILE)
    except OSError:
        pass


def read_state():
    try:
        with open(STATEFILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _save_profile(keyboard, bounces):
    if not bounces:
        return
    verdicts = [{"label": vk_name(vk), "fault": faults.CHATTER, "score": 35}
                for vk in bounces]
    profile.save_results(verdicts, keyboard, "unknown")


# ---------- the shared loop ----------

def run_loop(keyboard="default", on_bounce=None, write_state=False):
    """Hook loop. on_bounce(name, gap_ms, count, presses) fires per detected
    bounce (foreground prints; background passes None). When write_state, also
    dumps the live state file and periodically saves the profile. Returns
    (bounces, presses) dicts keyed by vk. Stops on ESC / KeyboardInterrupt."""
    last_up, is_down, bounces, presses, last_evt = {}, {}, {}, {}, {}
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    next_state = time.monotonic() + STATE_EVERY
    next_profile = time.monotonic() + PROFILE_EVERY

    hook = KeyboardHook().start()
    try:
        while True:
            hook.pump()
            while hook.events:
                vk, down, t = hook.events.pop(0)
                if vk == VK_ESCAPE:
                    raise KeyboardInterrupt
                since = (t - last_evt[vk]) if vk in last_evt else 0
                last_evt[vk] = t
                if down:
                    if is_down.get(vk) and since > trials.STUCK_MS:
                        is_down[vk] = False  # missed a key-up; recover
                    if is_down.get(vk):
                        continue
                    is_down[vk] = True
                    presses[vk] = presses.get(vk, 0) + 1
                    lu = last_up.get(vk)
                    if lu is not None and 0 <= (t - lu) < trials.CHATTER_MS:
                        bounces[vk] = bounces.get(vk, 0) + 1
                        if on_bounce:
                            on_bounce(vk_name(vk), round(t - lu),
                                      bounces[vk], presses[vk])
                else:
                    is_down[vk] = False
                    last_up[vk] = t
            now = time.monotonic()
            if write_state and now >= next_state:
                if os.path.exists(STOPFILE):
                    break  # clean shutdown -> finally flushes state + profile
                _write_state(keyboard, started, bounces, presses)
                next_state = now + STATE_EVERY
            if write_state and now >= next_profile:
                _save_profile(keyboard, bounces)
                next_profile = now + PROFILE_EVERY
            time.sleep(0.002)
    except KeyboardInterrupt:
        pass
    finally:
        hook.stop()
        if write_state:
            _write_state(keyboard, started, bounces, presses)
            _save_profile(keyboard, bounces)
    return bounces, presses


# ---------- background control ----------

def start_background(keyboard="default"):
    """Spawn a hidden, detached watcher. Returns (ok, message)."""
    running, pid = is_running()
    if running:
        return False, f"already running (pid {pid}) - use watch --stop first"
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pyw if os.path.exists(pyw) else sys.executable
    script = os.path.join(HERE, "keysurgeon.py")
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    try:
        subprocess.Popen(
            [exe, script, "watch", "--bg-run", "--keyboard", keyboard],
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            close_fds=True,
        )
    except OSError as e:
        return False, f"could not start: {e}"
    return True, "background watch started - it'll flag dying keys as you type"


def bg_run(keyboard="default"):
    """Entry for the detached child: write our pid, run the loop silently."""
    for stale in (STOPFILE,):  # clear any leftover stop request
        try:
            os.remove(stale)
        except OSError:
            pass
    try:
        with open(PIDFILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    try:
        run_loop(keyboard, on_bounce=None, write_state=True)
    finally:
        for f in (PIDFILE, STOPFILE):
            try:
                os.remove(f)
            except OSError:
                pass


def stop_background():
    """Stop the running watcher gracefully so it flushes its last data, then
    verify. Falls back to terminate only if it won't exit. Returns (ok, msg)."""
    running, pid = is_running()
    if not running:
        for f in (PIDFILE, STOPFILE):
            try:
                os.remove(f)
            except OSError:
                pass
        return False, "not running"
    # ask for a clean stop; the loop checks STOPFILE and runs its finally
    try:
        with open(STOPFILE, "w") as f:
            f.write("1")
    except OSError:
        pass
    clean = False
    for _ in range(int((STATE_EVERY + 2) / 0.1)):  # wait a bit past one check
        if not _pid_alive(pid):
            clean = True
            break
        time.sleep(0.1)
    if not clean:  # didn't exit on its own - force it
        h = kernel32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
        if h:
            kernel32.TerminateProcess(h, 0)
            kernel32.CloseHandle(h)
    for f in (PIDFILE, STOPFILE):
        try:
            os.remove(f)
        except OSError:
            pass
    return True, (f"stopped (pid {pid})" if clean
                  else f"force-stopped (pid {pid}); some recent data may be lost")
