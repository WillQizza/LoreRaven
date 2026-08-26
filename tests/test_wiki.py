import pytest

from loreraven.ingest.wiki import normalize_wiki_url, repo_slug


@pytest.mark.parametrize(
	"url, expected",
	[
		("https://github.com/owner/repo", "https://github.com/owner/repo.wiki.git"),
		("https://github.com/owner/repo/", "https://github.com/owner/repo.wiki.git"),
		("https://github.com/owner/repo.git", "https://github.com/owner/repo.wiki.git"),
		("https://github.com/owner/repo.wiki", "https://github.com/owner/repo.wiki.git"),
		("https://github.com/owner/repo.wiki.git", "https://github.com/owner/repo.wiki.git"),
		("git@github.com:owner/repo.git", "git@github.com:owner/repo.wiki.git"),
	],
)
def test_normalize_wiki_url(url: str, expected: str) -> None:
	assert normalize_wiki_url(url) == expected

@pytest.mark.parametrize(
	"url, expected",
	[
		("https://github.com/owner/repo", "owner/repo"),
		("https://github.com/owner/repo/", "owner/repo"),
		("https://github.com/owner/repo.git", "owner/repo"),
		("https://github.com/owner/repo.wiki", "owner/repo"),
		("https://github.com/owner/repo.wiki.git", "owner/repo"),
		("git@github.com:owner/repo.git", "owner/repo"),
	],
)
def test_repo_slug(url: str, expected: str) -> None:
	assert repo_slug(url) == expected

def test_repo_slug_single_segment() -> None:
	assert repo_slug("myrepo.wiki.git") == "myrepo"
