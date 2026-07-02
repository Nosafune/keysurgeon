# Keyboard Tester Vs KeySurgeon

Most browser keyboard testers answer one question: did a key register? That is
useful for a dead key, but it can miss the failure that makes people replace
otherwise repairable boards: one physical press registering twice.

KeySurgeon is built for that second question.

## What A Keyboard Tester Shows

| Need | Browser keyboard tester | KeySurgeon |
|---|---|---|
| Confirm a key can register | Good fit | Supported by `test` and `sweep` |
| Catch fast double-fires | Usually weak | Primary diagnostic target |
| Explain timing evidence | Usually no | Shows repeat timing and bounce counts |
| Track normal typing chatter | Usually no | `keysurgeon watch` and `watch --bg` |
| Suggest cheapest repair path | Usually no | Repair ladder before replacement |
| Export redacted issue evidence | Usually no | `keysurgeon export --json` |
| Prove local demo/readiness state | Usually no | `keysurgeon proof --json` |

## When To Use Each Tool

Use a browser keyboard tester when you need a quick visual check that a key
fires at all.

Use KeySurgeon when the keyboard sometimes double-types, misses presses, sticks,
or behaves differently after cleaning, swapping a switch, or changing the board
profile.

## What KeySurgeon Does Not Claim Yet

KeySurgeon has synthetic hook replay, selftests, local release proof, a
headless Textual mount/action smoke, real headless landing screenshots, and
hash-verified workflow/Rich/Textual demo assets with browser-rasterized demo
PNGs. Broad real-hardware claims still require the manual keyboard smoke report
to record `hardware-smoke-pass`.

GitHub repository, CI, Pages, and the v0.2.0 release are live. Broad
real-hardware proof still requires a recorded manual keyboard smoke pass.
