from arch_analyser.prompts.p2_decompose import run


def test_p2_decompose():
    context = {"source": "x"}
    output = run(context)
    assert "components" in output
    assert isinstance(output["components"], list)
