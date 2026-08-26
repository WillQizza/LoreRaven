def normalize_wiki_url(repo_url: str) -> str:
	"""Ensures repo urls always end with .wiki.git"""

	url = repo_url.rstrip("/")
	if url.endswith(".wiki.git"):
		return url

	if url.endswith(".git"):
		url = url[: -len(".git")]

	if url.endswith(".wiki"):
		return url + ".git"

	return url + ".wiki.git"


def repo_slug(repo_url: str) -> str:
	"""Converts the repository URL into a slug"""

	url = repo_url.rstrip("/")
	for suffix in (".wiki.git", ".wiki", ".git"):
		if url.endswith(suffix):
			url = url[: -len(suffix)]
			break

	# Drop the scheme and any `user@host:` / `host/` prefix, keeping the path.
	url = url.split("://", 1)[-1].replace(":", "/")
	parts = [p for p in url.split("/") if p]
	if len(parts) >= 2:
		return "/".join(parts[-2:])
	return parts[-1] if parts else repo_url
