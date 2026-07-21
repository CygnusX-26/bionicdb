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

## MCP server

Run the read-only MCP server over stdio:

```bash
uv run python -m app.mcp_server
```

It provides these tools:

- `list_builds`
- `find_libraries`
- `find_symbol_offset`
- `get_library_file`

Example MCP client configuration:

```json
{
  "mcpServers": {
    "bionicdb": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/bionicdb/api",
        "python",
        "-m",
        "app.mcp_server"
      ],
      "env": {
        "BIONIC_DB_PATH": "/absolute/path/to/bionicdb/bionic.db"
      }
    }
  }
}
```

Run tests with:

```bash
uv run pytest
```
