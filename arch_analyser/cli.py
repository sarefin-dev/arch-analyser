import argparse
import json
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def render(result: dict) -> None:
    output = result["raw"]

    console.print(
        Panel(
            output.get("system_summary", ""),
            title="System summary",
            border_style="blue",
        )
    )

    components = output.get("components", [])
    patterns = output.get("patterns", [])
    risks = output.get("risks", [])
    p1_risks = [r for r in risks if r["severity"] == "P1-BLOCKING"]
    p2_risks = [r for r in risks if r["severity"] == "P2-HIGH"]
    cross = [r for r in risks if r["branch"] == "CROSS-BRANCH"]

    console.print(
        Panel(
            f"Components : {len(components)}\n"
            f"Patterns   : {len(patterns)}\n"
            f"Risks      : {len(risks)} total · "
            f"[red]{len(p1_risks)} P1-BLOCKING[/red] · "
            f"[yellow]{len(p2_risks)} P2-HIGH[/yellow] · "
            f"[cyan]{len(cross)} CROSS-BRANCH[/cyan]",
            title="Counts",
            border_style="dim",
        )
    )

    if p1_risks:
        table = Table(title="P1-BLOCKING risks", border_style="red", show_lines=True)
        table.add_column("Risk", style="bold red", no_wrap=False, ratio=3)
        table.add_column("Branch", style="dim", ratio=1)
        table.add_column("Mitigation", ratio=4)
        for r in p1_risks:
            table.add_row(r["name"], r["branch"], r.get("mitigation") or "—")
        console.print(table)

    unresolved = output.get("unresolved_assumptions")
    if unresolved:
        console.print(
            Panel(
                "\n".join(f"• {u}" for u in unresolved),
                title="[yellow]Unresolved assumptions — re-run with these specified[/yellow]",
                border_style="yellow",
            )
        )


def render_md(result: dict, system_input: str) -> str:
    output = result["raw"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    components = output.get("components", [])
    patterns = output.get("patterns", [])
    risks = output.get("risks", [])
    p1_risks = [r for r in risks if r["severity"] == "P1-BLOCKING"]
    p2_risks = [r for r in risks if r["severity"] == "P2-HIGH"]
    p3_risks = [r for r in risks if r["severity"] == "P3-MEDIUM"]
    cross = [r for r in risks if r["branch"] == "CROSS-BRANCH"]
    unresolved = output.get("unresolved_assumptions") or []

    lines = []

    # Header
    lines += [
        "# Architecture analysis report",
        "",
        f"**Input:** `{system_input}`  ",
        f"**Generated:** {ts}  ",
        "**Pipeline:** P1 context > P2 decompose > P3 patterns > P4 risks > P5 synthesis",
        "",
        "---",
        "",
    ]

    # System summary
    lines += [
        "## System summary",
        "",
        output.get("system_summary", ""),
        "",
        "---",
        "",
    ]

    # Counts
    lines += [
        "## Counts",
        "",
        "| | |",
        "|---|---|",
        f"| Components | {len(components)} |",
        f"| Patterns | {len(patterns)} |",
        f"| Risks (total) | {len(risks)} |",
        f"| P1-BLOCKING | {len(p1_risks)} |",
        f"| P2-HIGH | {len(p2_risks)} |",
        f"| P3-MEDIUM | {len(p3_risks)} |",
        f"| CROSS-BRANCH | {len(cross)} |",
        "",
        "---",
        "",
    ]

    # Components
    lines += [
        "## Components",
        "",
        "| Component | Responsibility | State | Source |",
        "|---|---|---|---|",
    ]
    for c in components:
        lines.append(
            f"| {c['name']} | {c['responsibility']} | {c['state_class']} | {c['source']} |"
        )
    lines += ["", "---", ""]

    # Patterns — grouped by classification
    lines += ["## Patterns", ""]
    for classification in ["REQUIRED", "RECOMMENDED", "OPTIONAL"]:
        group = [p for p in patterns if p["classification"] == classification]
        if not group:
            continue
        lines += [f"### {classification}", ""]
        lines += [
            "| Pattern | Applies to | Rationale |",
            "|---|---|---|",
        ]
        for p in group:
            applies = ", ".join(p.get("applies_to", []))
            lines.append(f"| {p['name']} | {applies} | {p['rationale']} |")
        lines += [""]
    lines += ["---", ""]

    # Risks — grouped by severity
    lines += ["## Risks", ""]
    for severity, label in [
        ("P1-BLOCKING", "P1 — blocking"),
        ("P2-HIGH", "P2 — high"),
        ("P3-MEDIUM", "P3 — medium"),
    ]:
        group = [r for r in risks if r["severity"] == severity]
        if not group:
            continue
        lines += [f"### {label}", ""]
        for r in group:
            branch_tag = f"`{r['branch']}`"
            lines += [
                f"**{r['name']}** {branch_tag}  ",
                f"{r['description']}",
            ]
            if r.get("mitigation"):
                lines += [f"> **Mitigation:** {r['mitigation']}"]
            lines += [""]
    lines += ["---", ""]

    # Unresolved assumptions
    if unresolved:
        lines += [
            "## Unresolved assumptions",
            "",
            "Re-run with these specified to sharpen the analysis:",
            "",
        ]
        for u in unresolved:
            lines.append(f"- {u}")
        lines += ["", "---", ""]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="arch-analyser", description="5-prompt architecture analysis pipeline"
    )
    parser.add_argument(
        "system",
        nargs="?",
        help='System description e.g. "DCS, 500 check-ins, PostgreSQL, Kafka"',
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5",
        help="Anthropic model to use (default: claude-sonnet-4-5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of rich console display",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached responses and re-run all prompts",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Save full JSON output to file e.g. --output reports/dcs.json",
    )

    args = parser.parse_args()

    if not args.system:
        parser.print_help()
        sys.exit(1)

    if args.no_cache:
        import shutil
        from pathlib import Path

        cache_dir = Path(".cache/responses")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print("[dim]Cache cleared.[/dim]")

    console.print(
        Panel(
            f"[bold]{args.system}[/bold]",
            title="arch-analyser · input",
            border_style="dim",
        )
    )

    from arch_analyser.pipeline import run

    result = run(args.system, model=args.model)

    if args.json:
        print(json.dumps(result["raw"], indent=2))
    else:
        render(result)

    if args.output:
        from pathlib import Path

        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result["raw"], indent=2), encoding="utf-8")
        console.print(f"[dim]Saved JSON → {args.output}[/dim]")

        # Always save a markdown report alongside the JSON
        md_path = out.with_suffix(".md")
        md_path.write_text(render_md(result, args.system), encoding="utf-8")
        console.print(f"[dim]Saved report → {md_path}[/dim]")


if __name__ == "__main__":
    main()
