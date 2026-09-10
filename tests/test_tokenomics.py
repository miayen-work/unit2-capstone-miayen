from src.utils.tokenomics import log_usage, COST_PER_1K_INPUT, COST_PER_1K_OUTPUT


def test_returns_agent_name_and_token_counts():
    result = log_usage("manager", input_tokens=100, output_tokens=50)
    assert result["agent"] == "manager"
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 50


def test_computes_cost_for_input_and_output():
    result = log_usage("qualitative", input_tokens=1000, output_tokens=1000)
    expected = COST_PER_1K_INPUT + COST_PER_1K_OUTPUT
    assert result["cost"] == expected


def test_zero_tokens_yields_zero_cost():
    result = log_usage("quantitative", input_tokens=0, output_tokens=0)
    assert result["cost"] == 0


def test_input_only_cost():
    result = log_usage("manager", input_tokens=2000, output_tokens=0)
    assert result["cost"] == 2 * COST_PER_1K_INPUT


def test_output_only_cost():
    result = log_usage("manager", input_tokens=0, output_tokens=2000)
    assert result["cost"] == 2 * COST_PER_1K_OUTPUT
