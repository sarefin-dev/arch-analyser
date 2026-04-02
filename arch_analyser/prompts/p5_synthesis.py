import json
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("CRITICAL: ANTHROPIC_API_KEY not found in environment.")
    sys.exit(1)

client = Anthropic()
console = Console()

DEFAULT_MODEL = "claude-sonnet-4-5"

PROMPT = """ROLE: Staff Technical Writer synthesizing a multi-analyst architecture review.

CONTEXT:
Context block:
{context_block}

Component inventory:
{component_inventory}

Pattern analysis:
{pattern_analysis}

Risk analysis:
{risk_analysis}

TASK:
Synthesize all findings into a single structured architecture breakdown.
Do not add analysis not present in the provided findings.
Do not omit P1-BLOCKING risks.
Do not present OPTIONAL patterns at the same level as REQUIRED patterns.
For any field where the analysis produced no findings, return null.

Call the architecture_breakdown tool with the exact schema defined."""


def _trim(text: str, max_lines: int) -> str:
    """Keep the first max_lines lines — enough structure, less token cost."""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + "\n[truncated for synthesis]"


def run(
    context_block: str,
    component_inventory: str,
    pattern_analysis: str,
    risk_analysis: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    from arch_analyser.cache import get as cache_get
    from arch_analyser.cache import set as cache_set
    from arch_analyser.schema import ARCHITECTURE_TOOL

    cached = cache_get(
        "p5_synthesis",
        context_block,
        component_inventory,
        pattern_analysis,
        risk_analysis,
    )
    if cached:
        return cached

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        tools=[ARCHITECTURE_TOOL],
        tool_choice={"type": "tool", "name": "architecture_breakdown"},
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(
                    context_block=context_block,
                    component_inventory=component_inventory,
                    pattern_analysis=_trim(pattern_analysis, 120),
                    risk_analysis=_trim(risk_analysis, 150),
                ),
            }
        ],
    )

    # Extract tool_use block — tool_choice: forced guarantees exactly one
    tool_block = next(block for block in response.content if block.type == "tool_use")

    result = {
        "raw": tool_block.input,
        "prompt_id": "p5_synthesis",
    }
    cache_set(
        "p5_synthesis",
        result,
        context_block,
        component_inventory,
        pattern_analysis,
        risk_analysis,
    )
    return result


if __name__ == "__main__":
    from arch_analyser.prompts.p1_context import run as p1_run
    from arch_analyser.prompts.p2_decompose import run as p2_run
    from arch_analyser.prompts.p3_patterns import run as p3_run
    from arch_analyser.prompts.p4_risks import run as p4_run

    test_input = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "departure control system, 500 concurrent check-ins, "
            "PostgreSQL, Redis, Kafka, SITA integration"
        )
    )

    console.print(
        Panel(f"[bold]Input:[/bold] {test_input}", title="P5 — Structured Synthesis")
    )

    p1 = p1_run(test_input)
    p2 = p2_run(p1["raw"])
    p3 = p3_run(p1["raw"], p2["raw"])
    p4 = p4_run(p1["raw"], p2["raw"], p3["raw"])

    console.print("[dim]P1–P4 loaded from cache[/dim]")

    try:
        result = run(p1["raw"], p2["raw"], p3["raw"], p4["raw"])

        output = result["raw"]

        # P1 risks summary
        p1_risks = [
            r for r in output.get("risks", []) if r["severity"] == "P1-BLOCKING"
        ]
        cross = [r for r in output.get("risks", []) if r["branch"] == "CROSS-BRANCH"]

        console.print(
            Panel(
                output.get("system_summary", ""),
                title="System summary",
                border_style="blue",
            )
        )
        console.print(
            Panel(
                f"Components: {len(output.get('components', []))}\n"
                f"Patterns:   {len(output.get('patterns', []))}\n"
                f"Risks:      {len(output.get('risks', []))} total · "
                f"{len(p1_risks)} P1-BLOCKING · "
                f"{len(cross)} CROSS-BRANCH",
                title="Counts",
                border_style="dim",
            )
        )

        # P1 risks
        if p1_risks:
            p1_text = "\n\n".join(
                f"[bold red]{r['name']}[/bold red]\n"
                f"{r['description']}\n"
                f"[yellow]Mitigation:[/yellow] {r.get('mitigation', 'N/A')}"
                for r in p1_risks
            )
            console.print(Panel(p1_text, title="P1-BLOCKING risks", border_style="red"))

        # Unresolved assumptions
        unresolved = output.get("unresolved_assumptions")
        if unresolved:
            console.print(
                Panel(
                    "\n".join(f"• {u}" for u in unresolved),
                    title="Unresolved assumptions — re-run with these specified",
                    border_style="yellow",
                )
            )

        # Full JSON
        console.print(
            Panel(
                json.dumps(output, indent=2),
                title="Full JSON output",
                border_style="dim",
            )
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise
