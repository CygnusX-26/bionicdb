from fastapi import FastAPI

from app.db import Database, get_lib_from_symbol_offset

app = FastAPI(
    title="BionicDB API",
    version="0.1.0",
    description="Query metadata for indexed Android Bionic libc builds.",
)


@app.get("/v1/symbol/matches")
def symbol_matches(
    database: Database,
    offset: str,
    symbol: str | None = None,
) -> dict[str, object]:
    try:
        base_10_offset = int(offset, 16)
    except ValueError:
        return {
            "status": "error",
            "reason": "Offset must be a valid hexadecimal number.",
        }

    return {
        "status": "ok",
        "libs": [
            dict(row)
            for row in get_lib_from_symbol_offset(database, base_10_offset, symbol)
        ],
    }
