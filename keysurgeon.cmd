@echo off
REM KeySurgeon launcher - guided keyboard diagnostic.
REM Run with no args for the menu, or pass a mode: triage/sweep/watch/test/report/fix
python "%~dp0keysurgeon.py" %*
