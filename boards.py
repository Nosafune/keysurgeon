#!/usr/bin/env python3
"""Keyboard identity + model knowledge base for KeySurgeon.

Auto-detects connected keyboards via the Windows Raw Input API (stdlib ctypes,
no extra deps), reads each device's VID/PID from its interface name, and maps
the vendor id to a make. Lets KeySurgeon pre-fill the board type instead of
always asking.

Honesty rule (same as the fix engine): we only assert what the VID actually
tells us. Vendor is reliable from the VID; hot-swap vs soldered usually is NOT
knowable from VID/PID alone, so we hint and still let the user confirm rather
than guessing wrong.
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import re

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
hid = ctypes.windll.hid

HERE = os.path.dirname(os.path.abspath(__file__))
BOARDTYPES = os.path.join(HERE, "keysurgeon_boards.json")

RIM_TYPEKEYBOARD = 1
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000B
# a real keyboard reports ~100+ keys; a mouse's media/macro HID collection
# reports a handful - this is how we tell the physical keyboard from a mouse
# that merely exposes a keyboard interface
MIN_REAL_KEYS = 30


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [("hDevice", wt.HANDLE), ("dwType", wt.DWORD)]


class _RID_KEYBOARD(ctypes.Structure):
    _fields_ = [("dwType", wt.DWORD), ("dwSubType", wt.DWORD),
                ("dwKeyboardMode", wt.DWORD), ("dwNumberOfFunctionKeys", wt.DWORD),
                ("dwNumberOfIndicators", wt.DWORD), ("dwNumberOfKeysTotal", wt.DWORD)]


class _RID_MOUSE(ctypes.Structure):
    _fields_ = [("dwId", wt.DWORD), ("dwNumberOfButtons", wt.DWORD),
                ("dwSampleRate", wt.DWORD), ("fHasHorizontalWheel", wt.BOOL)]


class _RID_HID(ctypes.Structure):
    _fields_ = [("dwVendorId", wt.DWORD), ("dwProductId", wt.DWORD),
                ("dwVersionNumber", wt.DWORD), ("usUsagePage", wt.USHORT),
                ("usUsage", wt.USHORT)]


class RID_DEVICE_INFO(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("keyboard", _RID_KEYBOARD), ("mouse", _RID_MOUSE),
                    ("hid", _RID_HID)]
    _anonymous_ = ("u",)
    _fields_ = [("cbSize", wt.DWORD), ("dwType", wt.DWORD), ("u", _U)]


user32.GetRawInputDeviceList.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICELIST), ctypes.POINTER(wt.UINT), wt.UINT]
user32.GetRawInputDeviceList.restype = wt.UINT
user32.GetRawInputDeviceInfoW.argtypes = [
    wt.HANDLE, wt.UINT, ctypes.c_void_p, ctypes.POINTER(wt.UINT)]
user32.GetRawInputDeviceInfoW.restype = wt.UINT

kernel32.CreateFileW.argtypes = [
    wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE]
kernel32.CreateFileW.restype = wt.HANDLE
hid.HidD_GetProductString.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.ULONG]
hid.HidD_GetProductString.restype = wt.BOOLEAN
_INVALID_HANDLE = wt.HANDLE(-1).value

# VID (hex, uppercase) -> vendor. Vendor from VID is reliable; model is not.
VENDORS = {
    "1532": "Razer", "046D": "Logitech", "1B1C": "Corsair",
    "1038": "SteelSeries", "320F": "Glorious", "3434": "Keychron",
    "0B05": "ASUS", "045E": "Microsoft", "05AC": "Apple", "004C": "Apple",
    "413C": "Dell", "03F0": "HP", "17EF": "Lenovo", "048D": "ITE",
    "04D9": "Holtek", "0C45": "Microdia", "258A": "SINO WEALTH",
    "FEED": "QMK/custom", "04F2": "Chicony", "1A2C": "China Resource",
    "0951": "Kingston/HyperX", "2516": "Cooler Master", "0C70": "Wooting",
}

# Vendors whose boards are overwhelmingly mechanical (still don't know
# hot-swap vs soldered from VID alone, so we say "mechanical" and ask which).
MECH_VENDORS = {"Razer", "Corsair", "SteelSeries", "Glorious", "Keychron",
                "Cooler Master", "Kingston/HyperX", "Wooting", "QMK/custom"}
# Vendors whose boards are commonly hot-swap (a stronger hint, still confirm).
HOTSWAP_LEANING = {"Glorious", "Keychron", "Wooting", "QMK/custom"}

_NAME_RE = re.compile(r"VID_([0-9A-Fa-f]{4}).*?PID_([0-9A-Fa-f]{4})")


def _device_name(handle):
    size = wt.UINT(0)
    user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, None,
                                  ctypes.byref(size))
    if not size.value:
        return ""
    buf = ctypes.create_unicode_buffer(size.value)
    ret = user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, buf,
                                        ctypes.byref(size))
    # success returns chars copied (<= size); any 0 or oversized value (incl.
    # the (UINT)-1 / -2 error sentinels) means failure
    if ret == 0 or ret > size.value:
        return ""
    return buf.value or ""


def _key_count(handle):
    """dwNumberOfKeysTotal the device reports, or None."""
    info = RID_DEVICE_INFO()
    info.cbSize = ctypes.sizeof(RID_DEVICE_INFO)
    size = wt.UINT(ctypes.sizeof(RID_DEVICE_INFO))
    ret = user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICEINFO,
                                        ctypes.byref(info), ctypes.byref(size))
    if ret == 0 or ret == 0xFFFFFFFF:
        return None
    if info.dwType != RIM_TYPEKEYBOARD:
        return None
    return info.keyboard.dwNumberOfKeysTotal


def _product_name(path):
    """The device's real HID product string (e.g. 'Razer BlackWidow V3'), or ''.
    Opened with 0 access since Windows blocks read access to input devices."""
    if not path:
        return ""
    h = kernel32.CreateFileW(path, 0, 3, None, 3, 0, None)  # share R/W, OPEN_EXISTING
    if not h or h == _INVALID_HANDLE:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(126)  # 252 bytes
        if hid.HidD_GetProductString(h, buf, ctypes.sizeof(buf)):
            return (buf.value or "").strip()
        return ""
    finally:
        kernel32.CloseHandle(h)


def _looks_like_mouse(product, keys_total):
    """A device Windows lists as a keyboard but is really a mouse/other: it
    reports too few keys, or its product name says so."""
    if keys_total is not None and keys_total < MIN_REAL_KEYS:
        return True
    pl = (product or "").lower()
    return any(w in pl for w in (
        "mouse", "deathadder", "viper", "basilisk", "naga", "mamba",
        "orochi", "lancehead", "cobra", "deathstalker mouse"))


def detect_keyboards():
    """Return a deduped list of input devices Windows reports as keyboards:
        {vid, pid, vendor, product, name, keys_total, role, hint}
    role is 'keyboard' (a real physical keyboard) or 'other' (e.g. a mouse that
    merely exposes a keyboard HID collection for its macro/media keys). vid/pid
    are uppercase hex or None (built-in PS/2-ACPI boards have no VID). Returns
    [] on any API hiccup - detection is best-effort."""
    try:
        num = wt.UINT(0)
        size = ctypes.sizeof(RAWINPUTDEVICELIST)
        if user32.GetRawInputDeviceList(None, ctypes.byref(num), size) == 0xFFFFFFFF:
            return []
        if not num.value:
            return []
        arr = (RAWINPUTDEVICELIST * num.value)()
        got = user32.GetRawInputDeviceList(arr, ctypes.byref(num), size)
        if got == 0xFFFFFFFF:
            return []
        seen = set()
        out = []
        for i in range(got):
            if arr[i].dwType != RIM_TYPEKEYBOARD:
                continue
            name = _device_name(arr[i].hDevice)
            if not name:
                continue
            m = _NAME_RE.search(name)
            vid = m.group(1).upper() if m else None
            pid = m.group(2).upper() if m else None
            # one physical device exposes several HID collections under the same
            # VID/PID - collapse to one entry
            key = (vid, pid) if vid else ("?", name)
            if key in seen:
                continue
            seen.add(key)
            keys_total = _key_count(arr[i].hDevice)
            product = _product_name(name)
            role = "other" if _looks_like_mouse(product, keys_total) else "keyboard"
            out.append({
                "vid": vid, "pid": pid,
                "vendor": VENDORS.get(vid) if vid else None,
                "product": product,
                "name": name,
                "keys_total": keys_total,
                "role": role,
                "hint": _hint(vid),
            })
        return out
    except Exception:
        return []


def keyboards_only(devices):
    """Just the real keyboards from a detection list."""
    return [d for d in devices if d.get("role", "keyboard") == "keyboard"]


# Known models -> board type, so for these we never have to ask. Substrings
# matched against the HID product string, most-specific first. Only confident
# entries belong here (honesty rule); unknown models fall through to asking.
MODEL_BOARD_TYPE = [
    ("blackwidow v4 75", "hotswap"),    # the hot-swap BlackWidow
    ("blackwidow v4 pro", "soldered"),  # V4 Pro is soldered
    ("blackwidow v4", "soldered"),
    ("blackwidow v3", "soldered"),
    ("blackwidow", "soldered"),         # BlackWidows are historically soldered
    ("huntsman", "soldered"),
    ("gmmk", "hotswap"),                # Glorious GMMK line is hot-swap
    ("keychron q", "hotswap"),
    ("keychron v", "hotswap"),
    ("keychron k pro", "hotswap"),
]


def infer_from_model(product):
    """board_type for a known model from its product string, or None."""
    pl = (product or "").lower()
    for sub, bt in MODEL_BOARD_TYPE:
        if sub in pl:
            return bt
    return None


def _hint(vid):
    if vid is None:
        return ("looks built-in (no USB id) - probably a laptop / PS-2 "
                "board, so likely laptop type")
    vendor = VENDORS.get(vid)
    if vendor is None:
        return f"USB keyboard (VID {vid}); type unknown - pick below"
    if vendor in HOTSWAP_LEANING:
        return f"{vendor} - often hot-swappable mechanical (confirm below)"
    if vendor in MECH_VENDORS:
        return f"{vendor} - mechanical; hot-swap vs soldered varies, confirm below"
    return f"{vendor} keyboard - pick the type below"


def best_guess_type(devices):
    """A conservative default board_type for the menu pre-select, or None.
    Only returns laptop (built-in) confidently; mechanical brands stay None
    because hot-swap vs soldered isn't VID-knowable."""
    kbs = keyboards_only(devices) or devices
    if not kbs:
        return None
    primary = next((d for d in kbs if d["vid"]), kbs[0])
    if primary["vid"] is None:
        return "laptop"
    return None  # don't guess hot-swap/soldered - let the user confirm


# ---------- remembered board type per detected hardware ----------
# We can't read hot-swap vs soldered from the USB id, so we ask ONCE and
# remember it keyed by the detected device signature - never ask again.

def device_signature(devices):
    """Stable id for this machine's real keyboards, e.g. '1532:006C'.
    Ignores mice/other devices so plugging a mouse doesn't change it."""
    ids = sorted({f"{d['vid']}:{d['pid']}" for d in devices
                  if d["vid"] and d.get("role", "keyboard") == "keyboard"})
    return "+".join(ids) if ids else "no-usb-id"


def _load_types():
    try:
        with open(BOARDTYPES, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def recall_board_type(signature):
    """The saved board_type for this signature, or None if we've never asked."""
    bt = _load_types().get(signature)
    return bt or None


def remember_board_type(signature, board_type):
    data = _load_types()
    data[signature] = board_type
    try:
        with open(BOARDTYPES, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def forget_board_type(signature):
    data = _load_types()
    if signature in data:
        del data[signature]
        try:
            with open(BOARDTYPES, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass
