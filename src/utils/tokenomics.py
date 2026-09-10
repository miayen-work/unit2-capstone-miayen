COST_PER_1K_INPUT = 0.00001875  # check current Gemini pricing — free tier may not report usage the same way
COST_PER_1K_OUTPUT = 0.000075


def log_usage(agent_name: str, input_tokens: int, output_tokens: int) -> dict:
    cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (output_tokens / 1000 * COST_PER_1K_OUTPUT)
    print(f"[{agent_name}] tokens: in={input_tokens} out={output_tokens} cost=${cost:.6f}")
    return {
        "agent": agent_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
