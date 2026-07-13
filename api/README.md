# BionicDB

Install the environment and run the API with `uv`:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>, with interactive documentation
at <http://127.0.0.1:8000/docs>.

By default the API opens `bionic.db` in the project root as read-only. Override
the location when needed:

```bash
BIONIC_DB_PATH=/path/to/bionic.db uv run uvicorn app.main:app
```

Run tests with:

```bash
uv run pytest
```
