from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run(raw_input: str, model: str = "claude-sonnet-4-5") -> dict:
    """
    Orchestrates the 5-prompt Plan-and-Execute pipeline.
    Returns the final structured breakdown from P5.
    """
    from arch_analyser.prompts.p1_context import run as p1
    from arch_analyser.prompts.p2_decompose import run as p2
    from arch_analyser.prompts.p3_patterns import run as p3
    from arch_analyser.prompts.p4_risks import run as p4
    from arch_analyser.prompts.p5_synthesis import run as p5

    steps = [
        ("P1  Context assembly", lambda: p1(raw_input, model=model)),
        ("P2  Component decomposition", lambda ctx: p2(ctx["raw"], model=model)),
        (
            "P3  Pattern matching",
            lambda ctx, inv: p3(ctx["raw"], inv["raw"], model=model),
        ),
        (
            "P4  Risk analysis",
            lambda ctx, inv, pat: p4(ctx["raw"], inv["raw"], pat["raw"], model=model),
        ),
        (
            "P5  Structured synthesis",
            lambda ctx, inv, pat, risk: p5(
                ctx["raw"], inv["raw"], pat["raw"], risk["raw"], model=model
            ),
        ),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running pipeline...", total=len(steps))

        progress.update(task, description=steps[0][0])
        p1_result = steps[0][1]()
        progress.advance(task)

        progress.update(task, description=steps[1][0])
        p2_result = steps[1][1](p1_result)
        progress.advance(task)

        progress.update(task, description=steps[2][0])
        p3_result = steps[2][1](p1_result, p2_result)
        progress.advance(task)

        progress.update(task, description=steps[3][0])
        p4_result = steps[3][1](p1_result, p2_result, p3_result)
        progress.advance(task)

        progress.update(task, description=steps[4][0])
        p5_result = steps[4][1](p1_result, p2_result, p3_result, p4_result)
        progress.advance(task)

    return p5_result
