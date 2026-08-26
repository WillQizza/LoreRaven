# LoreRaven

Clone GitHub repositories, embed it into PostgreSQL (`pgvector`), and ask an AI about it.
Built on LangChain + OpenAI, with future browser support to be able interactively ask questions on the web.

## Setup

1. **Install dependencies**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

   This installs the dependencies and puts a `loreraven` command on your PATH.

2. **Configure**

   ```bash
   copy .env.example .env
   ```

   Then edit `.env` and set `OPENAI_API_KEY` and `LORERAVEN_DATABASE_URL`.

3. **PostgreSQL with pgvector**

   You need a Postgres database with the `pgvector` extension available. The
   quickest way is Docker:

   ```bash
   docker run -d --name loreraven-pg -p 5432:5432 \
     -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=loreraven \
     pgvector/pgvector:pg16
   ```

   LoreRaven creates the extension and its table automatically on first ingest.

## Usage

```bash
loreraven ingest https://github.com/pallets/flask
loreraven chat
```