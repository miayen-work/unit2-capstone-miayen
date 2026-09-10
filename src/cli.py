from src import config  # noqa: F401 - loads GEMINI_API_KEY from .env before anything calls Gemini
from src.agents import manager
from src.utils import tokenomics

EXIT_COMMANDS = {"exit", "quit"}
SUMMARY_INTERVAL = 10


def format_result(result: dict) -> str:
    query_type = result["type"]

    if query_type == "qualitative":
        sources = ", ".join(result["sources"]) if result["sources"] else "no sources found"
        return f"{result['answer']}\n\nSources: {sources}"

    if query_type == "quantitative":
        if result["error"]:
            if result["sql"] is None:
                return result["error"]
            return f"Could not run that query: {result['error']}"
        return f"{result['answer']}\n\n(query used: {result['sql']})"

    qualitative_text = format_result({"type": "qualitative", **result["qualitative"]})
    quantitative_text = format_result({"type": "quantitative", **result["quantitative"]})
    return f"{qualitative_text}\n\n{quantitative_text}"


def run(input_fn=input, print_fn=print) -> None:
    print_fn("Cloudly Enterprise Assistant - type 'exit' or 'quit' to stop.")
    query_count = 0
    while True:
        query = input_fn("> ").strip()
        if not query:
            continue
        if query.lower() in EXIT_COMMANDS:
            break
        result = manager.handle_query(query)
        print_fn(format_result(result))
        query_count += 1
        if query_count % SUMMARY_INTERVAL == 0:
            print_fn(tokenomics.format_summary(tokenomics.summarize()))

    if query_count > 0 and query_count % SUMMARY_INTERVAL != 0:
        print_fn(tokenomics.format_summary(tokenomics.summarize()))


def main():
    run()


if __name__ == "__main__":
    main()
