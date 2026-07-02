# Product

## Register

product

## Users

KeySurgeon is for Windows users who suspect a keyboard is failing and need a
plain answer before replacing hardware. They may be keyboard hobbyists,
repair-minded desktop users, or power users with a flaky laptop or external
board. They are usually in a troubleshooting moment: a key double-types, misses,
sticks, or behaves inconsistently, and they want to know whether the problem is
fixable.

## Product Purpose

KeySurgeon diagnoses keyboard chatter and related key faults, explains the
evidence in human language, and ranks repair steps from free software filtering
and cleaning up to switch replacement. Success means the user understands what
is wrong, trusts the evidence, and tries the cheapest honest repair path before
buying a new keyboard.

## Brand Personality

Forensic, repair-minded, and direct. The product should feel like a compact
diagnostic instrument: confident enough to be trusted, specific enough to stand
out from generic keyboard testers, and calm enough that a failing key does not
feel like a crisis.

## Anti-references

Avoid generic keyboard tester pages that only light up keys and leave the user
to interpret the result. Avoid gamer RGB spectacle, fake precision, alarmist
failure language, template SaaS cards, and polished UI that hides unfinished
diagnostics. Do not imply latency, NKRO, scancode, telemetry, or live repair
actions exist unless the code proves they do.

## Design Principles

1. Lead with the verdict, then show evidence.
2. Make replacement the last rung, never the default answer.
3. Keep the interface terminal-native but product-grade.
4. Treat privacy and plain-text fallback as first-class product behavior.
5. Let real diagnostic state drive every screen; no decorative fake metrics.

## Accessibility & Inclusion

Default terminal output should maintain readable contrast and work without
glyphs or color. Rich and Textual views may add color, panels, and motion, but
the `--plain` and `--no-color` paths remain required for automation, screen
readers, logs, and simple terminals. Landing-page contrast should target WCAG
AA for body text, and any motion must respect reduced-motion preferences.
