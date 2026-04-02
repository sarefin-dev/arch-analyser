from arch_analyser.prompts.p1_context import run
from tests.fixtures import sample_input


def test_p1_context():
    s = sample_input()
    output = run(s)
    assert isinstance(output, dict)
    assert output["source"] == s
