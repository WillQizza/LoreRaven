import argparse

from . import config, ingest, query


def _print_answer(assistant: query.Assistant, question: str, k: int) -> None:
	text, sources = assistant.answer(question, k=k)
	print(text)
	if sources:
		print("\nSources:")
		for source in sources:
			print(f"  - {source}")


def main(argv: list[str] | None = None) -> None:
	parser = argparse.ArgumentParser(
		prog="loreraven",
		description="Clone a GitHub repo, embed it into Postgres, and ask an AI about it.",
	)
	sub = parser.add_subparsers(dest="command", required=True)

	p_ingest = sub.add_parser("ingest", help="Clone a repo and build the index")
	p_ingest.add_argument("repo", help="GitHub repo URL (or a local git path)")
	p_ingest.add_argument("--branch", default=None, help="Branch to clone")

	p_query = sub.add_parser("query", help="Ask a single question")
	p_query.add_argument("question", help="Your question")
	p_query.add_argument("-k", type=int, default=4, help="Chunks to retrieve (default 4)")

	p_chat = sub.add_parser("chat", help="Interactive question/answer loop")
	p_chat.add_argument("-k", type=int, default=4, help="Chunks to retrieve (default 4)")

	args = parser.parse_args(argv)
	config.require_env()

	if args.command == "ingest":
		ingest.ingest_repo(args.repo, branch=args.branch)
	elif args.command == "query":
		assistant = query.Assistant()
		_print_answer(assistant, args.question, args.k)
	elif args.command == "chat":
		assistant = query.Assistant()
		print("LoreRaven chat. Type a question, or 'exit' to quit.")
		while True:
			try:
				question = input("\n> ").strip()
			except (EOFError, KeyboardInterrupt):
				print()
				break
			if question.lower() in {"exit", "quit"}:
				break
			if question:
				_print_answer(assistant, question, args.k)


if __name__ == "__main__":
	main()
