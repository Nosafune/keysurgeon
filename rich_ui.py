#!/usr/bin/env python3
"""Rich rendering for KeySurgeon.

The diagnostic engine stays plain Python; this module owns the v2 presentation
skin and can be bypassed by --plain / --no-color.
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

import brand
from faults import band

console = Console(theme=Theme(brand.RICH_THEME))


def band_style(score):
    return brand.BAND_STYLES.get(band(score), "ks.muted")


def banner(subtitle=""):
    title = Text()
    title.append(brand.SIGNAL_MARK + "  ", style="ks.signal")
    title.append(brand.NAME, style="ks.name")
    if subtitle:
        title.append("  /  ", style="ks.muted")
        title.append(subtitle, style="ks.muted")
    console.print()
    console.print(title)
    console.print()


def menu(items):
    banner("choose a diagnostic path")
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style="ks.signal", no_wrap=True)
    table.add_column(style="bold")
    table.add_column(style="ks.muted")
    for num, _mode, title, blurb in items:
        table.add_row(num, title, blurb)
    table.add_row("q", "quit", "")
    console.print(table)
    console.print()


def tour(payload):
    banner("first-run tour")
    proof = payload["local_proof"]
    summary = payload.get("proof_summary") or {}

    lead = Table.grid(padding=(0, 2))
    lead.add_column(style="bold")
    lead.add_column(style="ks.muted")
    lead.add_row("What it is", "keyboard chatter and fault diagnosis")
    lead.add_row("Core loop", "watch -> test -> fix -> proof")
    lead.add_row("App shell", "keysurgeon app")
    lead.add_row("Privacy", "local JSON only; no typed text exported")
    console.print(Panel(
        lead,
        title=" command center ",
        border_style="ks.signal",
        box=box.ROUNDED,
        padding=(1, 2),
    ))

    flow = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="ks.signal")
    flow.add_column("Step", no_wrap=True)
    flow.add_column("Command", no_wrap=True)
    flow.add_column("Why")
    for step, command, why in (
        ("1", "keysurgeon watch --bg", "catch double-fires while you type normally"),
        ("2", "keysurgeon test E", "turn suspicion into a timed verdict"),
        ("3", "keysurgeon fix E", "show the cheapest-first repair ladder"),
        ("4", "keysurgeon proof --json", "see exactly what is and is not proved"),
        ("5", "keysurgeon issue", "write a redacted GitHub-ready packet"),
    ):
        flow.add_row(f"[ks.signal]{step}[/]", command, why)
    console.print(flow)

    gates = Table(box=box.SIMPLE, show_header=True, header_style="ks.signal")
    gates.add_column("Surface", no_wrap=True)
    gates.add_column("Status", no_wrap=True)
    gates.add_column("Detail")
    for label, item in (
        ("Rich/Textual", proof["rich_textual_stack"]),
        ("Public assets", proof["demo_assets"]),
        ("Hardware smoke", proof["manual_keyboard_smoke"]),
    ):
        status = item["status"]
        gates.add_row(label, f"[{_proof_style(status)}]{status}[/]", item["detail"])
    console.print(Panel(
        gates,
        title=(
            " readiness "
            f" local {summary.get('local', 0)} "
            f" command {summary.get('command_gated', 0)} "
            f" blocked {summary.get('blocked', 0)} "
        ),
        border_style="ks.repair",
        box=box.ROUNDED,
        padding=(1, 2),
    ))

    blockers = payload.get("public_blockers") or []
    if blockers:
        text = "\n".join(f"[ks.probe]-[/] {item}" for item in blockers)
        console.print(Panel(
            text,
            title=" not claimed yet ",
            border_style="ks.probe",
            box=box.ROUNDED,
            padding=(1, 2),
        ))


def live_counter(label, n, expected):
    done = n >= expected
    style = "ks.repair" if done else "ks.signal"
    filled = int((n / max(expected, 1)) * 12)
    bar = "[" + ("#" * min(filled, 12)).ljust(12, ".") + "]"
    console.print(
        f"\r[{style}]{label}[/] {bar} [bold {style}]{n:>2}[/]/{expected}"
        "  [ks.muted]ESC skips[/]",
        end="",
        soft_wrap=True,
    )


def card(verdict, rungs, closer):
    label = verdict["label"]
    score = verdict["score"]
    bnd = band(score)
    style = band_style(score)

    body = Table.grid(padding=(0, 1))
    body.add_column(ratio=1)
    body.add_row(f"[bold]{verdict['headline']}[/]")
    body.add_row(f"[ks.text]{verdict['detail']}[/]")

    if verdict.get("confidence") == "low":
        body.add_row("[ks.probe]Only a few presses seen. Run it again for a confident read.[/]")

    evidence = verdict.get("evidence") or []
    if evidence:
        body.add_row("")
        body.add_row("[ks.muted]evidence[/]")
        for item in evidence:
            body.add_row(f"[ks.muted]  {brand.ASCII_ICONS['signal']} {item}[/]")

    if rungs:
        ladder = Table.grid(padding=(0, 1))
        ladder.add_column(justify="right", style="ks.signal", no_wrap=True)
        ladder.add_column(style="bold")
        ladder.add_column(style="ks.muted")
        for n, title, blurb in rungs:
            ladder.add_row(str(n), title, blurb)
        body.add_row("")
        body.add_row("[bold]What to do, easiest first:[/]")
        body.add_row(ladder)

    if closer:
        body.add_row("")
        body.add_row(f"[{style}]{closer}[/]")

    console.print(Panel(
        body,
        title=f" {label} ",
        subtitle=f" {bnd} {score}/100 ",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def heatmap(score_by_label, title="board health"):
    banner(title)
    rows = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    for offset, row in enumerate(rows):
        line = Text(" " * offset)
        for key in row:
            score = score_by_label.get(key)
            if score is None:
                line.append(f" {key} ", style="ks.muted")
            else:
                line.append(f" {key} ", style=band_style(score))
            line.append(" ")
        console.print(line)
    console.print()
    console.print(
        "[ks.repair]+ healthy[/]   [ks.probe]! watch[/]   "
        "[ks.fault]x failing[/]   [ks.muted]. untested[/]"
    )
    console.print()


def report(snapshot, board_type):
    banner("board report")
    if not snapshot:
        console.print(Panel(
            "[ks.muted]No saved results yet.[/]\nRun a sweep or test first.",
            border_style="ks.muted",
            box=box.ROUNDED,
        ))
        return

    keys = snapshot["keys"]
    scores = [k["score"] for k in keys] or [100]
    avg = sum(scores) // len(scores)
    bnd = band(avg)
    style = band_style(avg)

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column(style="ks.muted")
    summary.add_row("Verdict", f"[{style}]{bnd}[/]  {avg}/100")
    summary.add_row("Keyboard", board_type)
    summary.add_row("Snapshot", snapshot["ts"])
    console.print(Panel(summary, border_style=style, box=box.ROUNDED))

    bad = sorted([k for k in keys if k["score"] < 90], key=lambda k: k["score"])
    if not bad:
        console.print("[ks.repair]Every tested key is healthy. Nothing to fix.[/]")
        return

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="ks.signal")
    table.add_column("Key", no_wrap=True)
    table.add_column("Fault")
    table.add_column("Health")
    for item in bad:
        progress = Progress(
            TextColumn(""),
            BarColumn(bar_width=18, complete_style=band_style(item["score"])),
            TextColumn("{task.percentage:>3.0f}%"),
            expand=False,
        )
        progress.add_task("", total=100, completed=item["score"])
        table.add_row(item["label"], item["fault"], progress)
    console.print(table)
    worst = bad[0]
    console.print(
        f"[ks.signal]>[/] Next: run [bold]keysurgeon fix {worst['label']}[/] "
        f"for the {worst['fault']} repair ladder."
    )


def _proof_style(status):
    if status == "ok":
        return "ks.repair"
    if status == "missing":
        return "ks.fault"
    return "ks.probe"


def proof_report(payload):
    banner("proof")
    proof = payload["local_proof"]

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column(style="ks.muted")
    summary.add_row("Version", payload["version"])
    summary.add_row("Privacy", payload["privacy"])
    console.print(Panel(
        summary,
        title=" local proof surface ",
        border_style="ks.signal",
        box=box.ROUNDED,
        padding=(1, 2),
    ))

    gates = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="ks.signal")
    gates.add_column("Gate", no_wrap=True)
    gates.add_column("Status", no_wrap=True)
    gates.add_column("Detail")
    for label, item in (
        ("Rich/Textual demos", proof["demo_assets"]),
        ("Manual keyboard smoke", proof["manual_keyboard_smoke"]),
        ("Stack proof", proof["rich_textual_stack"]),
        ("Claim matrix", proof["proof_matrix"]),
    ):
        status = item["status"]
        gates.add_row(label, f"[{_proof_style(status)}]{status}[/]", item["detail"])
    console.print(gates)

    matrix = payload.get("proof_matrix") or []
    if matrix:
        summary = payload.get("proof_summary") or {}
        table = Table(box=box.SIMPLE, show_header=True, header_style="ks.signal")
        table.add_column("Tier", no_wrap=True)
        table.add_column("Claim")
        table.add_column("Verifier")
        for item in matrix[:8]:
            tier = item["tier"]
            style = "ks.probe" if tier == "blocked" else ("ks.signal" if tier == "command_gated" else "ks.repair")
            table.add_row(
                f"[{style}]{tier}[/]",
                item["claim"],
                item["verifier"],
            )
        console.print(Panel(
            table,
            title=(
                " claim matrix "
                f" local {summary.get('local', 0)} "
                f" command {summary.get('command_gated', 0)} "
                f" blocked {summary.get('blocked', 0)} "
            ),
            border_style="ks.signal",
            box=box.ROUNDED,
            padding=(1, 2),
        ))

    assets = proof["demo_assets"].get("assets") or []
    if assets:
        table = Table(box=box.SIMPLE, show_header=True, header_style="ks.signal")
        table.add_column("Asset")
        table.add_column("Status", no_wrap=True)
        table.add_column("Bytes", justify="right", no_wrap=True)
        table.add_column("Source")
        for item in assets:
            status = item["status"]
            table.add_row(
                item["kind"],
                f"[{_proof_style(status)}]{status}[/]",
                str(item["bytes"]),
                item["generator"],
            )
        console.print(Panel(
            table,
            title=" generated public assets ",
            border_style="ks.repair",
            box=box.ROUNDED,
            padding=(1, 2),
        ))

    blockers = payload.get("public_blockers") or []
    if blockers:
        blocker_text = "\n".join(f"[ks.probe]{brand.ASCII_ICONS['watch']}[/] {item}"
                                 for item in blockers)
        console.print(Panel(
            blocker_text,
            title=" not proved yet ",
            border_style="ks.probe",
            box=box.ROUNDED,
            padding=(1, 2),
        ))
