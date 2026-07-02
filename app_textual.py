#!/usr/bin/env python3
"""Optional Textual shell for KeySurgeon v2."""

import brand
import boards
import issue_packet
import ks_profile as profile
import proof_report
import watch
from faults import band

ROWS = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

APP_ACTIONS = [
    {"key": "w", "binding": "toggle_watch", "label": "watch", "command": "keysurgeon watch --bg", "safe": True},
    {"key": "r", "binding": "refresh", "label": "refresh", "command": "keysurgeon app", "safe": True},
    {"key": "b", "binding": "show_command('keysurgeon board')", "label": "board", "command": "keysurgeon board", "safe": True},
    {"key": "i", "binding": "show_command('keysurgeon issue')", "label": "issue packet", "command": "keysurgeon issue", "safe": True},
    {"key": "y", "binding": "show_command('keysurgeon ready')", "label": "ready", "command": "keysurgeon ready", "safe": True},
    {"key": "p", "binding": "show_command('keysurgeon proof --json')", "label": "proof", "command": "keysurgeon proof --json", "safe": True},
    {"key": "s", "binding": "show_command('keysurgeon site --open')", "label": "local site", "command": "keysurgeon site --open", "safe": True},
    {"key": "q", "binding": "quit", "label": "quit", "command": "quit app", "safe": True},
]


def _app_bindings():
    return [
        (item["key"], item["binding"], item["label"].title())
        for item in APP_ACTIONS
    ]


def _health_map(snapshot):
    scores = {}
    if snapshot:
        scores = {item["label"]: item["score"] for item in snapshot.get("keys") or []}
    out = ["KEY HEALTH MAP"]
    for offset, row in enumerate(ROWS):
        cells = []
        for key in row:
            score = scores.get(key)
            if score is None:
                cells.append(f"[dim] {key} [/]")
            elif band(score) == "HEALTHY":
                cells.append(f"[green] {key} [/]")
            elif band(score) == "FAILING":
                cells.append(f"[red] {key} [/]")
            else:
                cells.append(f"[yellow] {key} [/]")
        out.append((" " * offset) + "".join(cells))
    return "\n".join(out)


def _status_text():
    running, pid = watch.is_running()
    state = watch.read_state() or {}
    status = "[green]RUNNING[/]" if running else "[dim]STOPPED[/]"
    lines = [
        "WATCH STATUS",
        f"daemon: {status}" + (f" pid {pid}" if running else ""),
        f"updated: {state.get('updated', 'no live state')}",
    ]
    if state.get("keys"):
        lines.append("caught:")
        for name, data in sorted(state["keys"].items()):
            lines.append(f"  [red]{name}[/] {data.get('bounces', 0)} bounce(s)")
    else:
        lines.append("caught: none")
    return "\n".join(lines)


def _signal_text(snapshot):
    running, pid = watch.is_running()
    state = watch.read_state() or {}
    keys = state.get("keys") or {}
    lines = ["WATCH SIGNAL"]
    if running:
        lines.append(f"[green]armed[/]" + (f" pid {pid}" if pid else ""))
    else:
        lines.append("[dim]not running[/]")

    if state.get("updated"):
        lines.append(f"updated: {state['updated']}")
    elif snapshot:
        lines.append(f"last report: {snapshot.get('ts', '?')}")
    else:
        lines.append("no live watcher state")

    if keys:
        lines.append("double-spikes:")
        for name, data in sorted(keys.items(),
                                 key=lambda item: -item[1].get("bounces", 0))[:6]:
            bounces = data.get("bounces", 0)
            presses = data.get("presses", 0)
            lines.append(f"  [red]{name}[/] {bounces} bounce(s) / {presses} press(es)")
    else:
        lines.append("[dim]start: keysurgeon watch --bg[/]")
    return "\n".join(lines)


def _bar(filled, total=18, style="green"):
    filled = max(0, min(total, int(filled)))
    return f"[{style}]" + ("#" * filled) + "[/]" + "[dim]" + ("-" * (total - filled)) + "[/]"


def _signal_rail(snapshot):
    running, _pid = watch.is_running()
    state = watch.read_state() or {}
    live_keys = state.get("keys") or {}
    live_bounces = sum(item.get("bounces", 0) for item in live_keys.values())
    keys = (snapshot or {}).get("keys") or []
    scores = [item.get("score", 0) for item in keys]

    watch_fill = 18 if running else 0
    chatter_fill = min(18, live_bounces)
    lines = ["FORENSIC SIGNAL RAIL"]
    watch_label = "ARMED" if running else "STANDBY"
    watch_style = "green" if running else "dim"
    lines.append(f"watch   {watch_label:<7} {_bar(watch_fill, style=watch_style)}")
    lines.append(f"chatter {live_bounces:>3} hit(s) {_bar(chatter_fill, style='red' if live_bounces else 'dim')}")

    if scores:
        avg = sum(scores) // len(scores)
        health_fill = round((avg / 100) * 18)
        lines.append(f"health  {avg:>3}/100  {_bar(health_fill, style=_band_color(avg))}")
        evidence_fill = min(18, max(1, len(keys)))
        lines.append(f"proof   {len(keys):>3} key(s) {_bar(evidence_fill, style='cyan')}")
    else:
        lines.append("health  no saved report yet")
        lines.append("proof   run: keysurgeon sweep")
    return "\n".join(lines)


def _command_center(snapshot):
    running, _pid = watch.is_running()
    state = watch.read_state() or {}
    live_keys = state.get("keys") or {}
    keys = (snapshot or {}).get("keys") or []
    bad = sorted([item for item in keys if item.get("score", 0) < 90],
                 key=lambda item: item["score"])

    lines = ["COMMAND CENTER"]
    if live_keys:
        worst = sorted(live_keys.items(),
                       key=lambda item: -item[1].get("bounces", 0))[0][0]
        lines.extend([
            f"[red]{worst}[/] is bouncing in watch mode.",
            f"next: keysurgeon fix {worst}",
            "then: keysurgeon test " + worst,
            "ready: keysurgeon ready",
            "proof: keysurgeon proof --json",
        ])
    elif bad:
        worst = bad[0]
        lines.extend([
            f"[yellow]{worst['label']}[/] is the weakest saved key.",
            f"next: keysurgeon fix {worst['label']}",
            "then: keysurgeon report",
            "ready: keysurgeon ready",
            "proof: keysurgeon proof --json",
        ])
    elif running:
        lines.extend([
            "[green]watch is armed[/]; type normally.",
            "press w here to stop and flush.",
            "next: keysurgeon report",
            "ready: keysurgeon ready",
            "proof: keysurgeon proof --json",
        ])
    else:
        lines.extend([
            "no active evidence yet.",
            "press w to arm background watch.",
            "or run: keysurgeon sweep",
            "ready: keysurgeon ready",
            "proof: keysurgeon proof --json",
        ])
    return "\n".join(lines)


def _readiness_text(payload=None):
    payload = payload or proof_report.build_payload()
    proof = payload["local_proof"]
    lines = ["READINESS"]

    demo = proof["demo_assets"]
    lines.append(
        f"assets: [{_status_color(demo['status'])}]{demo['status']}[/] "
        f"{len(demo.get('assets') or [])} generated"
    )

    manual = proof["manual_keyboard_smoke"]
    lines.append(
        f"hardware: [{_status_color(manual['status'])}]{manual['status']}[/] "
        f"{manual['detail']}"
    )

    stack = proof["rich_textual_stack"]
    lines.append(
        f"stack: [{_status_color(stack['status'])}]{stack['status']}[/] "
        f"{stack['detail']}"
    )

    package_build = proof["package_build_gate"]
    lines.append(
        f"package: [{_status_color(package_build['status'])}]{package_build['status']}[/] "
        f"{package_build['command']}"
    )

    package_metadata = proof.get("package_metadata") or {}
    lines.append(
        f"metadata: [{_status_color(package_metadata.get('status', 'missing'))}]{package_metadata.get('status', 'missing')}[/] "
        f"{package_metadata.get('detail', 'pyproject.toml metadata not reported')}"
    )

    matrix = proof.get("proof_matrix") or {}
    summary = payload.get("proof_summary") or {}
    lines.append(
        f"claims: [{_status_color(matrix.get('status', 'missing'))}]{matrix.get('status', 'missing')}[/] "
        f"local {summary.get('local', 0)} / command {summary.get('command_gated', 0)} / blocked {summary.get('blocked', 0)}"
    )

    release = proof["release_package"]
    lines.append(
        f"release: [{_status_color(release['status'])}]{release['status']}[/] "
        f"{release['detail']}"
    )

    blockers = payload.get("public_blockers") or []
    if blockers:
        lines.append("blocked:")
        for item in blockers[:2]:
            lines.append(f"  [yellow]-[/] {item}")
    else:
        lines.append("[green]no public blockers reported[/]")

    actions = payload.get("next_actions") or []
    if actions:
        lines.append("next:")
        for item in actions[:3]:
            remote = "remote" if item.get("changes_remote") else "local"
            lines.append(f"  [green]+[/] {remote}: {item['command']}")

    return "\n".join(lines)


def _hero_text(snapshot):
    running, _pid = watch.is_running()
    state = watch.read_state() or {}
    live_keys = state.get("keys") or {}
    keys = (snapshot or {}).get("keys") or []
    bad = sorted([item for item in keys if item.get("score", 0) < 90],
                 key=lambda item: item["score"])

    if live_keys:
        worst = sorted(live_keys.items(),
                       key=lambda item: -item[1].get("bounces", 0))[0]
        verdict = (f"[red]{worst[0]}[/] bouncing live: "
                   f"{worst[1].get('bounces', 0)} hit(s)")
    elif bad:
        worst = bad[0]
        verdict = (f"[yellow]{worst['label']}[/] saved fault: "
                   f"{worst['fault']} {worst['score']}/100")
    elif keys:
        scores = [item.get("score", 0) for item in keys]
        avg = sum(scores) // len(scores)
        verdict = f"[{_band_color(avg)}]{band(avg)}[/] saved report: {avg}/100"
    elif running:
        verdict = "[green]watch armed[/]: type normally"
    else:
        verdict = "[dim]no active evidence yet[/]: run sweep, test, or watch"

    return (
        f"[bold cyan]{brand.SIGNAL_MARK}  {brand.NAME} v{brand.VERSION}[/]\n"
        f"{brand.TAGLINE}\n"
        f"signal: {verdict}\n"
        "[dim]Auto-updates every 3s. r forces refresh; w toggles watch. No typed text stored.[/]"
    )


def _device_text(keyboard="default"):
    devices = boards.keyboards_only(boards.detect_keyboards())
    _snap, board_type = profile.latest(keyboard)
    board_label = board_type or "unknown"
    lines = ["DEVICE", f"repair model: [bold]{board_label}[/]"]
    if board_type:
        lines.append("[dim]saved for this profile; change with keysurgeon board[/]")
    else:
        lines.append("[yellow]confirm board type with keysurgeon board[/]")
    if not devices:
        lines.extend([
            "[dim]no keyboard identity available[/]",
            "run: keysurgeon board",
        ])
        return "\n".join(lines)
    for item in devices[:3]:
        name = item.get("product") or item.get("vendor") or "Keyboard"
        vid = item.get("vid") or "built-in"
        pid = item.get("pid") or ""
        hint = item.get("hint") or "type unknown"
        tail = f"VID {vid} PID {pid}" if pid else vid
        lines.append(f"[bold]{name}[/]")
        lines.append(f"[dim]{tail}[/]")
        lines.append(f"[dim]{hint}[/]")
    if len(devices) > 3:
        lines.append(f"[dim]+ {len(devices) - 3} more[/]")
    return "\n".join(lines)


def _report_text(keyboard):
    snap, board_type = profile.latest(keyboard)
    if not snap:
        return "BOARD REPORT\n[dim]No saved results yet.[/]\nRun sweep or test first."
    keys = snap.get("keys") or []
    scores = [item.get("score", 0) for item in keys] or [100]
    avg = sum(scores) // len(scores)
    bad = sorted([item for item in keys if item.get("score", 0) < 90],
                 key=lambda item: item["score"])
    lines = [
        "BOARD REPORT",
        f"verdict: [{_band_color(avg)}]{band(avg)}[/] {avg}/100",
        f"type: {board_type}",
        f"snapshot: {snap.get('ts', '?')}",
    ]
    if bad:
        lines.append("needs attention:")
        for item in bad[:8]:
            lines.append(f"  [{_band_color(item['score'])}]{item['label']}[/] "
                         f"{item['fault']} {item['score']}/100")
    else:
        lines.append("[green]all tested keys healthy[/]")
    return "\n".join(lines)


def _band_color(score):
    name = band(score)
    if name == "HEALTHY":
        return "green"
    if name == "FAILING":
        return "red"
    return "yellow"


def _status_color(status):
    if status == "ok":
        return "green"
    if status == "missing":
        return "red"
    return "yellow"


def _repair_ladder():
    return (
        "REPAIR LADDER\n"
        "[cyan]1[/] software filter     block bounce now\n"
        "[cyan]2[/] blow out debris     free, one minute\n"
        "[cyan]3[/] clean contact       alcohol and patience\n"
        "[cyan]4[/] hot-swap switch     cheap real fix\n"
        "[cyan]5[/] desolder switch     skill path\n"
        "[red]6[/] replace keyboard     last resort"
    )


def _commands():
    return (
        "KEYS\n"
        "w start/stop watch\n"
        "r refresh command center\n"
        "q quit\n\n"
        "CLI FLOW\n"
        "keysurgeon triage\n"
        "keysurgeon test E\n"
        "keysurgeon watch --bg\n"
        "keysurgeon report\n"
        "keysurgeon ready\n"
        "keysurgeon proof --json"
    )


def _action_bar():
    rows = [
        f"[cyan]{item['key']}[/] {item['label']}"
        for item in APP_ACTIONS
    ]
    commands = [
        item["command"] for item in APP_ACTIONS
        if item["command"].startswith("keysurgeon")
    ]
    return (
        "ACTION BAR\n"
        f"{rows[0]}     {rows[1]}\n"
        f"{rows[2]}     {rows[3]}\n"
        f"{rows[4]}     {rows[5]}\n"
        f"{rows[6]}\n"
        f"[red]{APP_ACTIONS[-1]['key']}[/] {APP_ACTIONS[-1]['label']}\n\n"
        "SAFE ACTIONS\n"
        f"{', '.join(commands[2:])}\n"
        "No fake repair buttons. No typed text exported."
    )


def _issue_packet_text():
    default_name = issue_packet._default_packet_path().name
    return (
        "ISSUE PACKET\n"
        f"[cyan]keysurgeon issue --out {default_name}[/]\n\n"
        "INCLUDES\n"
        "support summary, proof JSON, redacted export\n\n"
        "PRIVACY BOUNDARY\n"
        f"{issue_packet.PACKET_PUBLIC_PROMISE}; {issue_packet.PACKET_CONTENTS}\n"
        "[yellow]" + issue_packet.PACKET_REVIEW_WARNING + "[/]"
    )


def build_app(keyboard="default"):
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Grid
        from textual.widgets import Footer, Header, Static
    except ImportError:
        return None

    class SignalPanel(Static):
        pass

    class KeySurgeonApp(App):
        CSS = f"""
        Screen {{
            background: {brand.COLORS['ink']};
            color: {brand.COLORS['text']};
        }}
        Header, Footer {{
            background: {brand.COLORS['panel']};
            color: {brand.COLORS['signal']};
        }}
        #hero {{
            background: {brand.COLORS['panel']};
            border: round {brand.COLORS['signal']};
            padding: 1 2;
            margin: 1 2 0 2;
            height: 6;
        }}
        #rail {{
            background: {brand.COLORS['ink']};
            border: round {brand.COLORS['repair']};
            padding: 1 2;
            margin: 1 2 0 2;
            height: 7;
        }}
        #shell {{
            grid-size: 3 4;
            grid-gutter: 1 2;
            margin: 1 2;
        }}
        .panel {{
            border: round {brand.COLORS['probe']};
            padding: 1 2;
            min-height: 8;
        }}
        #map {{
            border: round {brand.COLORS['signal']};
        }}
        #ladder {{
            border: round {brand.COLORS['repair']};
        }}
        #commands {{
            border: round {brand.COLORS['fault']};
        }}
        #actions {{
            border: round {brand.COLORS['repair']};
        }}
        #issue {{
            border: round {brand.COLORS['signal']};
        }}
        #readiness {{
            border: round {brand.COLORS['signal']};
        }}
        #device {{
            border: round {brand.COLORS['probe']};
        }}
        #message {{
            color: {brand.COLORS['repair']};
            min-height: 2;
        }}
        .title {{
            color: {brand.COLORS['signal']};
            text-style: bold;
        }}
        """
        BINDINGS = _app_bindings()

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(_hero_text(None), id="hero")
            yield Static("", id="rail")
            with Grid(id="shell"):
                yield SignalPanel(id="signal", classes="panel")
                yield Static(id="command", classes="panel")
                yield Static(id="status", classes="panel")
                yield Static(id="report", classes="panel")
                yield Static(id="map", classes="panel")
                yield Static(id="device", classes="panel")
                yield Static(id="readiness", classes="panel")
                yield Static(_repair_ladder(), id="ladder", classes="panel")
                yield Static(_action_bar(), id="actions", classes="panel")
                yield Static(_issue_packet_text(), id="issue", classes="panel")
                yield Static(_commands(), id="commands", classes="panel")
            yield Static("", id="message")
            yield Footer()

        def on_mount(self) -> None:
            self.title = brand.NAME
            self._message_token = 0
            self.refresh_data()
            self.set_interval(3.0, self.refresh_data)

        def action_refresh(self) -> None:
            self.refresh_data()

        def action_show_command(self, command: str) -> None:
            self.query_one("#message", Static).update(
                f"[cyan]{command}[/] [dim]run this in your terminal[/]"
            )
            self._message_token += 1
            token = self._message_token
            self.set_timer(5.0, lambda: self._clear_message(token), name="clear-message")

        def action_toggle_watch(self) -> None:
            running, _pid = watch.is_running()
            if running:
                ok, msg = watch.stop_background()
            else:
                ok, msg = watch.start_background(keyboard)
            style = "green" if ok else "yellow"
            self.query_one("#message", Static).update(f"[{style}]{msg}[/]")
            self._message_token += 1
            token = self._message_token
            self.set_timer(4.0, lambda: self._clear_message(token), name="clear-message")
            self.refresh_data()

        def _clear_message(self, token) -> None:
            if token == self._message_token:
                self.query_one("#message", Static).update("")

        def refresh_data(self) -> None:
            snap, _board_type = profile.latest(keyboard)
            self.query_one("#hero", Static).update(_hero_text(snap))
            self.query_one("#rail", Static).update(_signal_rail(snap))
            self.query_one("#signal", SignalPanel).update(_signal_text(snap))
            self.query_one("#command", Static).update(_command_center(snap))
            self.query_one("#status", Static).update(_status_text())
            self.query_one("#report", Static).update(_report_text(keyboard))
            self.query_one("#map", Static).update(_health_map(snap))
            self.query_one("#device", Static).update(_device_text(keyboard))
            self.query_one("#readiness", Static).update(_readiness_text())

    return KeySurgeonApp()


def run_app(keyboard="default"):
    app = build_app(keyboard)
    if app is None:
        print("Textual app mode requires: python -m pip install textual")
        return 1
    app.run()
    return 0
