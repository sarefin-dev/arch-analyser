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

PROMPT = """ROLE: Staff Distributed Systems Architect.

CONTEXT:
{context_block}

FOCUS:
1. Data layer: storage engines, caches, message brokers
2. Service layer: core services, background workers, scheduled jobs
3. Edge layer: API gateways, load balancers, CDN, auth boundaries
4. Cross-cutting: observability, configuration management, secret management

TASK:
Enumerate every component implied by the context, working from the data layer upward.
For each component:
  - Name it precisely (use the technology named in context where specified)
  - State its primary responsibility in one sentence
  - Classify it as: STATEFUL / STATELESS / HYBRID
  - Flag it as: SPECIFIED (named in input) or INFERRED (architectural necessity)

Do not enumerate implementation details. Enumerate structural components only.
Do not include any introductory or concluding remarks.
Start the response immediately with the first Component: entry."""


def run(context_block: str, model: str = DEFAULT_MODEL) -> dict:
    from arch_analyser.cache import get as cache_get, set as cache_set

    cached = cache_get("p2_decompose", context_block)
    if cached:
        return cached

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": PROMPT.format(context_block=context_block),
        }],
    )

    result = {
        "raw": response.content[0].text.strip(),
        "prompt_id": "p2_decompose",
    }
    cache_set("p2_decompose", result, context_block)
    return result


if __name__ == "__main__":
    from arch_analyser.prompts.p1_context import run as p1_run

    test_input = sys.argv[1] if len(sys.argv) > 1 else (
        "departure control system, 500 concurrent check-ins, "
        "PostgreSQL, Redis, Kafka, SITA integration"
    )

    console.print(Panel(f"[bold]Input:[/bold] {test_input}", title="P2 — Component Decomposition"))

    p1_result = p1_run(test_input)
    console.print(Panel(p1_result["raw"], title="P1 context (input to P2)", border_style="dim"))

    try:
        result = run(p1_result["raw"])
        console.print(Panel(result["raw"], title="Component Inventory", border_style="blue"))
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")