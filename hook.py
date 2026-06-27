#!/usr/bin/env python3
"""Shared low-level keyboard hook for KeySurgeon.

Windows WH_KEYBOARD_LL via ctypes, stdlib only. 64-bit safe (explicit
prototypes so ctypes doesn't truncate pointers). This is the single source of
truth for raw key events; trials and modes build on top of it.

Event timestamps come from time.perf_counter() captured in the callback, NOT
the Windows message tick (kb.time). The message tick has only ~10-16ms timer
resolution and wraps every ~49.7 days - useless for measuring 5-35ms switch
bounce. perf_counter is sub-microsecond and monotonic.
"""

import ctypes
import ctypes.wintypes as wt
import time

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_ESCAPE = 0x1B

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# vk <-> name maps
NAMED_VK = {"SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "BACKSPACE": 0x08,
            "ESC": 0x1B}
NAMED_VK.update({f"F{i}": 0x6F + i for i in range(1, 25)})  # F1=0x70..F24
_VK_TO_NAME = {ord(c): c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
_VK_TO_NAME.update({v: k for k, v in NAMED_VK.items()})


def to_vk(name):
    name = str(name).strip().upper()
    if name in NAMED_VK:
        return NAMED_VK[name]
    if len(name) == 1 and (name.isalpha() or name.isdigit()):
        return ord(name)
    raise ValueError(f"don't know key '{name}' (letters, digits, F1-F24, SPACE)")


def vk_name(vk):
    return _VK_TO_NAME.get(vk, f"vk{vk:02X}")


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wt.DWORD),
        ("scanCode", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),  # ULONG_PTR, pointer-sized on both archs
    ]


HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM
)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wt.HMODULE, wt.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HMODULE
# message-pump prototypes (keep the "explicit prototypes" contract complete)
user32.PeekMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT, wt.UINT]
user32.PeekMessageW.restype = wt.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wt.MSG)]
user32.TranslateMessage.restype = wt.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wt.MSG)]
user32.DispatchMessageW.restype = ctypes.c_ssize_t


class KeyboardHook:
    """Installs the LL hook and queues (vk, is_down, time_ms) events.

    Does NOT swallow keys (always calls the next hook) - KeySurgeon observes,
    it doesn't block. Use the chatterguard tool for live filtering.
    """

    def __init__(self):
        self.events = []
        self._hook = None
        self._proc = HOOKPROC(self._cb)  # keep ref so it isn't GC'd

    def _cb(self, nCode, wParam, lParam):
        if nCode >= 0:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            t = time.perf_counter() * 1000.0  # ms, sub-microsecond res, no wrap
            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self.events.append((kb.vkCode, True, t))
            elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                self.events.append((kb.vkCode, False, t))
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def start(self):
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0
        )
        if not self._hook:
            raise OSError("SetWindowsHookEx failed")
        return self

    def stop(self):
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def pump(self):
        """Drain pending messages so the hook callback fires."""
        msg = wt.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False
