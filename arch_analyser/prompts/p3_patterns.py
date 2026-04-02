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

PROMPT = """ROLE: Staff Systems Architect, expert in distributed systems patterns.

CONTEXT:
System context:
{context_block}

Component inventory:
{component_inventory}

FOCUS:
1. Data flow patterns: synchronous vs asynchronous, push vs pull, fan-out
2. Consistency patterns: eventual vs strong, write propagation, read models
3. Reliability patterns: retry, circuit breaker, bulkhead, timeout
4. Scalability patterns: horizontal scaling, partitioning, caching strategy
5. Integration patterns: point-to-point vs broker-mediated, choreography vs orchestration

TASK:
For each component in the inventory, identify which architectural patterns it
requires, enables, or constrains. Classify each pattern as:
  - REQUIRED: the component cannot function correctly without it
  - RECOMMENDED: significantly reduces known failure risk
  - OPTIONAL: applicable but not warranted by current context

Do not recommend patterns not warranted by the component inventory.
Explicitly state why each REQUIRED pattern is required — reference the
specific component and the failure mode it prevents.
Do not include any introductory or concluding remarks.
Start the response immediately with the first Pattern: entry.

OUTPUT:
Return ONLY a pattern list in this exact format:
  Pattern: [name]
  Applies to: [component(s)]
  Classification: [REQUIRED | RECOMMENDED | OPTIONAL]
  Rationale: [one sentence referencing the specific component and failure mode]"""


def run(context_block: str, component_inventory: str, model: str = DEFAULT_MODEL) -> dict:
    from arch_analyser.cache import get as cache_get, set as cache_set

    cached = cache_get("p3_patterns", context_block, component_inventory)
    if cached:
        return cached

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": PROMPT.format(
                context_block=context_block,
                component_inventory=component_inventory,
            ),
        }],
    )

    result = {
        "raw": response.content[0].text.strip(),
        "prompt_id": "p3_patterns",
    }
    cache_set("p3_patterns", result, context_block, component_inventory)
    return result


if __name__ == "__main__":
    from arch_analyser.prompts.p1_context import run as p1_run
    from arch_analyser.prompts.p2_decompose import run as p2_run

    test_input = sys.argv[1] if len(sys.argv) > 1 else (
        "departure control system, 500 concurrent check-ins, "
        "PostgreSQL, Redis, Kafka, SITA integration"
    )

    console.print(Panel(f"[bold]Input:[/bold] {test_input}", title="P3 — Pattern Matching"))

    p1_result = p1_run(test_input)
    console.print(Panel(p1_result["raw"], title="P1 context", border_style="dim"))

    p2_result = p2_run(p1_result["raw"])
    console.print(Panel(p2_result["raw"], title="P2 component inventory", border_style="dim"))

    try:
        result = run(p1_result["raw"], p2_result["raw"])
        console.print(Panel(result["raw"], title="Pattern Analysis", border_style="blue"))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")