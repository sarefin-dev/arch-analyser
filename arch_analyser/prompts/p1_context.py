import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from arch_analyser.cache import get as cache_get
from arch_analyser.cache import set as cache_set

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("CRITICAL: ANTHROPIC_API_KEY not found in environment.")
    sys.exit(1)

client = Anthropic()
console = Console()

DEFAULT_MODEL = "claude-sonnet-4-5"

PROMPT = """ROLE: Staff Systems Architect.

CONTEXT:
User input: {raw_input}

FOCUS:
1. Identify: system name, primary function, scale targets (throughput, latency, users)
2. Identify: technology stack (databases, brokers, compute, languages)
3. Identify: stated constraints (compliance, cost, team size, timeline)
4. Identify: what is NOT specified — mark these as [UNSPECIFIED]

TASK:
Extract and structure all technical specifics. Do not infer beyond what is stated.
For every dimension that is unspecified, record it as [UNSPECIFIED].

OUTPUT:
Return ONLY a structured context block in this exact format (no conversational text):
  System: [name]
  Function: [one sentence]
  Scale: throughput=[x], latency_target=[x], user_count=[x]
  Stack: [component: technology] for each named component
  Constraints: [list]
  Unspecified: [list of missing dimensions]"""


def run(raw_input: str, model: str = DEFAULT_MODEL) -> dict:
    cached = cache_get("p1_context", raw_input)
    if cached:
        return cached

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(raw_input=raw_input),
            }
        ],
    )

    result = {
        "raw": response.content[0].text.strip(),
        "source": raw_input,
        "prompt_id": "p1_context",
    }
    cache_set("p1_context", result, raw_input)
    return result


if __name__ == "__main__":
    test_input = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "departure control system, 500 concurrent check-ins, "
            "PostgreSQL, Redis, Kafka, SITA integration"
        )
    )

    console.print(
        Panel(f"[bold]Input:[/bold] {test_input}", title="P1 — Context Assembly")
    )

    try:
        result = run(test_input)
        console.print(
            Panel(result["raw"], title="Structured Context Block", border_style="blue")
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
