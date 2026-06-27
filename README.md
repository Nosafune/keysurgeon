# KeySurgeon

Guided keyboard diagnostic that finds **fixable** problems before you replace
the board. It catches the failures dumb testers miss - especially **chatter**
(a key registering twice) - and gives you an honest, board-aware fix ladder that
starts free and only ends at "buy a new keyboard" when nothing cheaper works.

Windows only. Python 3, stdlib only. No installs.

## Run it

```
keysurgeon                 # menu - pick a mode (you don't need to remember verbs)
```

or jump straight to a mode:

```
keysurgeon triage          # "what's wrong?" wizard -> targeted test -> fix ladder
keysurgeon sweep           # walk the whole board, live heatmap, board report
keysurgeon watch           # watch you type, flag keys that double-fire (Ctrl+C to stop)
keysurgeon watch --bg      # run hidden in the background all day
keysurgeon watch --status  # is the background watcher running? what has it caught?
keysurgeon watch --stop    # stop the background watcher
keysurgeon test E R T      # test specific keys right now
keysurgeon report          # last results + board health + trend
keysurgeon fix E           # show the fix ladder for one key
```

(From this folder use `keysurgeon.cmd ...`, or `python keysurgeon.py ...`.)

Config / maintenance:

```
keysurgeon board           # set your keyboard type (asked once, then remembered)
keysurgeon selftest        # validate the logic (no keyboard needed) - run after edits
```

It reads each device's real HID product name + key count to tell your actual
keyboard apart from a mouse that merely exposes a keyboard interface (gaming mice
do this for their macro keys). For **known models** it resolves the board type
itself and never asks (e.g. *Razer BlackWidow V4 Pro -> soldered*). For unknown
models it asks **once**, then remembers it per device. Use `keysurgeon board` to
change it.

### Flags (any mode)
- `--plain` / `--ai` - no color, structured output for piping
- `--no-color` - plain text, keep layout
- `--keyboard <name>` - track a specific board's profile separately
- `--presses <n>` - presses required per key in a trial (default 20)

## What it detects

| Fault | Meaning |
|---|---|
| chatter | one press registers twice (failing switch bounce) |
| dead | key doesn't respond at all |
| intermittent | key skips some presses |
| sticky | holds register oddly - mushy/sticking switch |
| extra | late bounces after you let go (early chatter) |

It auto-detects your connected keyboards (vendor via USB VID) and pre-fills the
board type where it safely can; it asks you to confirm hot-swap vs soldered
because that isn't knowable from the USB id alone.

## How it picks a fix

The fix ladder is board-aware and cheapest-first:

```
software filter -> blow out debris -> clean contact -> hot-swap switch
   -> desolder+replace switch -> (last resort) replace keyboard
```

A laptop board gets scissor-clip advice; a membrane board gets cleaning; a
hot-swap mechanical board gets the ~$0.30 switch swap. "Replace the keyboard" is
always last and usually unnecessary.

## Files

| File | Role |
|---|---|
| `keysurgeon.py` | entry, menu, mode dispatch |
| `hook.py` | shared low-level keyboard hook (perf_counter timing) |
| `trials.py` | diagnostic trial primitives |
| `faults.py` | fault classification + health scoring |
| `fixes.py` | board-aware fix ladders |
| `boards.py` | keyboard auto-detect + vendor knowledge base |
| `watch.py` | foreground + detached background chatter watch |
| `profile.py` | per-keyboard result history + trend |
| `ui.py` | terminal rendering (cards, heatmap, report) |

See `DESIGN.md` for the full design and roadmap.

## Related tools

- `keytest` - the original per-key chatter trial KeySurgeon's engine grew from
- `chatterguard` - live system-wide debounce filter (the "software filter" rung)
