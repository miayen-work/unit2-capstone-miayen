COST_PER_1K_INPUT = 0.00001875  # check current Gemini pricing — free tier may not report usage the same way
COST_PER_1K_OUTPUT = 0.000075

_usage_log: list[dict] = []


def log_usage(agent_name: str, input_tokens: int, output_tokens: int) -> dict:
    cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (output_tokens / 1000 * COST_PER_1K_OUTPUT)
    print(f"[{agent_name}] tokens: in={input_tokens} out={output_tokens} cost=${cost:.6f}")
    record = {
        "agent": agent_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
    _usage_log.append(record)
    return record


def reset_log() -> None:
    _usage_log.clear()


def summarize() -> dict:
    by_agent: dict[str, dict] = {}
    for record in _usage_log:
        totals = by_agent.setdefault(
            record["agent"], {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        )
        totals["calls"] += 1
        totals["input_tokens"] += record["input_tokens"]
        totals["output_tokens"] += record["output_tokens"]
        totals["cost"] += record["cost"]

    return {
        "calls": len(_usage_log),
        "total_cost": sum(record["cost"] for record in _usage_log),
        "by_agent": by_agent,
    }


def format_summary(summary: dict) -> str:
    lines = [f"Tokenomics summary ({summary['calls']} LLM calls):"]
    for agent_name in sorted(summary["by_agent"]):
        totals = summary["by_agent"][agent_name]
        lines.append(
            f"  {agent_name}: {totals['calls']} calls, "
            f"in={totals['input_tokens']} out={totals['output_tokens']} "
            f"cost=${totals['cost']:.6f}"
        )
    lines.append(f"Total cost: ${summary['total_cost']:.6f}")
    return "\n".join(lines)
