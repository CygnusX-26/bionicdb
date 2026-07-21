"""Read-only MCP tools for querying BionicDB."""

from __future__ import annotations

from contextlib import contextmanager
import sqlite3

from mcp.server.fastmcp import FastMCP
from collections.abc import Generator

from app.db import (
    connect_database,
    get_all_libs,
    get_build_id_from_symbol_offset,
    get_lib_path_from_build_id,
    get_offset_from_symbol_build_id,
)


mcp = FastMCP(
    "BionicDB",
    instructions=(
        "Query indexed Android Bionic libc builds, symbols, offsets, releases, "
        "and local library object files. All operations are read-only."
    ),
    json_response=True,
)


@contextmanager
def database_connection() -> Generator[sqlite3.Connection]:
    database = connect_database()
    try:
        yield database
    finally:
        database.close()


@mcp.tool()
def list_builds() -> dict[str, object]:
    """List every indexed libc build with Android, API, patch, firmware, and device data."""
    with database_connection() as database:
        builds = [dict(row) for row in get_all_libs(database)]
    return {"builds": builds, "count": len(builds)}


@mcp.tool()
def find_libraries(offset: str, symbol: str | None = None) -> dict[str, object]:
    """Find libc builds containing a hexadecimal symbol offset, optionally by symbol name."""
    try:
        numeric_offset = int(offset, 16)
    except ValueError as error:
        raise ValueError(f"Invalid hexadecimal offset: {offset}") from error
    if numeric_offset < 0:
        raise ValueError("Offset must not be negative")

    with database_connection() as database:
        libraries = [
            dict(row)
            for row in get_build_id_from_symbol_offset(database, numeric_offset, symbol)
        ]
    return {"libraries": libraries, "count": len(libraries)}


@mcp.tool()
def find_symbol_offset(build_id: str, symbol: str) -> dict[str, str]:
    """Get a symbol's hexadecimal offset from a libc ELF build ID."""
    with database_connection() as database:
        offset = get_offset_from_symbol_build_id(database, symbol, build_id)
    if offset is None:
        raise ValueError(f"No matching symbol {symbol} for build ID {build_id}")
    return {"build_id": build_id, "symbol": symbol, "offset": hex(offset)}


@mcp.tool()
def get_library_file(build_id: str) -> dict[str, object]:
    """Locate the local libc.so object associated with an ELF build ID."""
    with database_connection() as database:
        path = get_lib_path_from_build_id(database, build_id)
    if path is None or not path.is_file():
        raise ValueError(f"No library found for build ID {build_id}")
    return {
        "build_id": build_id,
        "path": str(path),
        "file_uri": path.as_uri(),
        "size": path.stat().st_size,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
