import pytest

from src.utils import tokenomics
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


def test_log_usage_records_entry_for_summary():
    log_usage("manager", input_tokens=10, output_tokens=5)
    summary = tokenomics.summarize()
    assert summary["calls"] == 1


def test_reset_log_clears_previous_entries():
    log_usage("manager", input_tokens=10, output_tokens=10)
    tokenomics.reset_log()
    summary = tokenomics.summarize()
    assert summary["calls"] == 0
    assert summary["total_cost"] == 0


def test_summarize_aggregates_ten_queries_by_agent():
    for _ in range(6):
        log_usage("manager", input_tokens=50, output_tokens=20)
    for _ in range(3):
        log_usage("qualitative_agent", input_tokens=200, output_tokens=100)
    log_usage("quantitative_agent", input_tokens=300, output_tokens=20)

    summary = tokenomics.summarize()

    assert summary["calls"] == 10
    assert summary["by_agent"]["manager"]["calls"] == 6
    assert summary["by_agent"]["qualitative_agent"]["calls"] == 3
    assert summary["by_agent"]["qualitative_agent"]["input_tokens"] == 600
    assert summary["by_agent"]["quantitative_agent"]["calls"] == 1

    expected_total = (
        6 * ((50 / 1000 * COST_PER_1K_INPUT) + (20 / 1000 * COST_PER_1K_OUTPUT))
        + 3 * ((200 / 1000 * COST_PER_1K_INPUT) + (100 / 1000 * COST_PER_1K_OUTPUT))
        + 1 * ((300 / 1000 * COST_PER_1K_INPUT) + (20 / 1000 * COST_PER_1K_OUTPUT))
    )
    assert summary["total_cost"] == pytest.approx(expected_total)


def test_format_summary_includes_agent_breakdown_and_total():
    log_usage("manager", input_tokens=100, output_tokens=50)
    log_usage("qualitative_agent", input_tokens=200, output_tokens=100)

    text = tokenomics.format_summary(tokenomics.summarize())

    assert "2 LLM calls" in text
    assert "manager" in text
    assert "qualitative_agent" in text
    assert "Total cost" in text
