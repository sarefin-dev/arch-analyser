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

PROMPT = """ROLE: Staff Site Reliability Engineer and Security Architect.

CONTEXT:
System context:
{context_block}

Component inventory:
{component_inventory}

Architectural patterns:
{pattern_analysis}

FOCUS:
1. Infrastructure failure risks: SPOF, network partitions, hardware failure
2. Software failure risks: race conditions, data consistency violations, deadlocks,
   cascading failures, resource exhaustion
3. Security threat risks: STRIDE classification (Spoofing, Tampering, Repudiation,
   Information disclosure, Denial of service, Elevation of privilege)

TASK:
Scrutinize the system for risks using Tree of Thought reasoning.

Step 1 — Generate three branches independently:
  Branch A (Infrastructure): reason through every STATEFUL component for
    single points of failure. For each: what single failure halts the system?
  Branch B (Software): reason through every service interaction for
    consistency violations, race conditions, and cascading failure paths.
  Branch C (Security): apply STRIDE to every external boundary and
    every privileged operation in the component inventory.

  Reason through each branch completely before moving to the next.
  Do not reference other branches while reasoning within one.

Step 2 — Evaluate each branch:
  Score each identified risk 1-3 on:
    - Likelihood: given the stated scale and patterns
    - Blast radius: scope of impact if triggered
  Mark risks scoring 5-6 total as P1 (BLOCKING).
  Mark risks scoring 3-4 as P2 (HIGH).
  Mark risks scoring 1-2 as P3 (MEDIUM).

Step 3 — Synthesize:
  Risks appearing across multiple branches are the highest-confidence findings.
  Flag these as CROSS-BRANCH.
  State the recommended mitigation for each P1 risk in one sentence.

Do not include any introductory or concluding remarks.
Start the response immediately with the first Risk: entry.

OUTPUT:
Return ONLY the Step 2 evaluation and Step 3 synthesis as Risk: entries.
Do not include the Branch A/B/C reasoning narrative in the output.
Return ONLY a risk list in this exact format:
  Risk: [name]
  Branch: [INFRASTRUCTURE | SOFTWARE | SECURITY | CROSS-BRANCH]
  Severity: [P1-BLOCKING | P2-HIGH | P3-MEDIUM]
  Likelihood score: [1-3]
  Blast radius score: [1-3]
  Description: [one sentence — specific component, specific failure mode]
  Mitigation: [one sentence — required for P1 only, omit for P2/P3]"""


def run(
    context_block: str,
    component_inventory: str,
    pattern_analysis: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    from arch_analyser.cache import get as cache_get
    from arch_analyser.cache import set as cache_set

    cached = cache_get("p4_risks", context_block, component_inventory, pattern_analysis)
    if cached:
        return cached

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(
                    context_block=context_block,
                    component_inventory=component_inventory,
                    pattern_analysis=pattern_analysis,
                ),
            }
        ],
    )

    result = {
        "raw": response.content[0].text.strip(),
        "prompt_id": "p4_risks",
    }
    cache_set("p4_risks", result, context_block, component_inventory, pattern_analysis)
    return result


if __name__ == "__main__":
    from arch_analyser.prompts.p1_context import run as p1_run
    from arch_analyser.prompts.p2_decompose import run as p2_run
    from arch_analyser.prompts.p3_patterns import run as p3_run

    test_input = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "departure control system, 500 concurrent check-ins, "
            "PostgreSQL, Redis, Kafka, SITA integration"
        )
    )

    console.print(
        Panel(f"[bold]Input:[/bold] {test_input}", title="P4 — Risk Analysis")
    )

    p1 = p1_run(test_input)
    console.print(Panel(p1["raw"], title="P1 context", border_style="dim"))

    p2 = p2_run(p1["raw"])
    console.print(Panel(p2["raw"], title="P2 components", border_style="dim"))

    p3 = p3_run(p1["raw"], p2["raw"])
    console.print(Panel(p3["raw"], title="P3 patterns", border_style="dim"))

    try:
        result = run(p1["raw"], p2["raw"], p3["raw"])
        console.print(Panel(result["raw"], title="Risk Analysis", border_style="red"))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
