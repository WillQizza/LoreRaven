from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
	question: str = Field(min_length=1)


class AddRepositoryRequest(BaseModel):
	url: str = Field(min_length=1)

	@field_validator("url")
	@classmethod
	def _github_url(cls, value: str) -> str:
		value = value.strip()
		if any(char.isspace() for char in value):
			raise ValueError("url must not contain whitespace")

		parsed = urlparse(value)
		if (
			parsed.scheme not in ("http", "https")
			or parsed.hostname not in ("github.com", "www.github.com")
		):
			raise ValueError("url must be a GitHub repository URL like https://github.com/owner/repo")

		return value


class RepositoryResponse(BaseModel):
	id: int
	url: str
	status: str
	error: str | None = None
