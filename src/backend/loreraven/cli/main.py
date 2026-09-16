import argparse

import uvicorn

from .. import config, ingest
from . import query


def _print_answer(assistant: query.Assistant, question: str, k: int | None) -> None:
	text, sources = assistant.answer(question, k=k)
	print(text)
	if sources:
		print("\nSources:")
		for source in sources:
			print(f"  - {source}")


def _serve(host: str, port: int, reload: bool) -> None:
	uvicorn.run(
		"loreraven.api.app:create_app",
		factory=True,
		host=host,
		port=port,
		reload=reload,
	)


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
	p_query.add_argument("-k", type=int, default=None, help=f"Chunks to retrieve (default {config.TOP_K}, from LORERAVEN_TOP_K)")

	p_chat = sub.add_parser("chat", help="Interactive question/answer loop")
	p_chat.add_argument("-k", type=int, default=None, help=f"Chunks to retrieve (default {config.TOP_K}, from LORERAVEN_TOP_K)")

	p_serve = sub.add_parser("serve", help="Run the web API")
	p_serve.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
	p_serve.add_argument("--port", type=int, default=8000, help="Port (default 8000)")
	p_serve.add_argument("--reload", action="store_true", help="Restart on source changes")

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
	elif args.command == "serve":
		_serve(args.host, args.port, args.reload)


if __name__ == "__main__":
	main()
