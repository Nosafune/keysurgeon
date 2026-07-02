# Security Policy

KeySurgeon observes keyboard events to diagnose hardware faults. Treat issues
around key capture, persistence, process handling, and privacy as security
sensitive even when they look like ordinary bugs.

## Supported Versions

The current public line is `0.2.x`.

## Reporting A Vulnerability

Open a private advisory on GitHub if available, or open an issue with the
minimum safe reproduction details. Do not paste typed private text, credentials,
tokens, or full key logs.

Useful reports include:

- command and version
- Windows and Python versions
- whether `watch`, `watch --bg`, or `app` was running
- stack trace or exact error
- the smallest non-sensitive key labels/timing data needed to reproduce

## Privacy Commitments

KeySurgeon should not store typed text or send telemetry. Runtime JSON belongs
under the local user data folder unless `KEYSURGEON_HOME` is explicitly set.
