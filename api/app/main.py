from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from starlette import status

from app.db import (
    REPOSITORY_ROOT,
    Database,
    get_build_id_from_symbol_offset,
    get_lib_path_from_build_id,
)

app = FastAPI(
    title="BionicDB API",
    version="0.1.0",
    description="Query metadata for indexed Android Bionic libc builds.",
)


@app.get("/v1/libs/{build_id}")
def libs(database: Database, build_id: str) -> FileResponse:
    path = get_lib_path_from_build_id(database, build_id)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No library found for build ID {build_id}.",
        )
    return FileResponse(
        path=REPOSITORY_ROOT / path,
        filename=f"{build_id}.so",
        media_type="application/octet-stream",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hexadecimal number {offset}",
        )

    return {
        "status": "ok",
        "libs": [
            dict(row)
            for row in get_build_id_from_symbol_offset(database, base_10_offset, symbol)
        ],
    }
