from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette import status

from app.db import (
    REPOSITORY_ROOT,
    Database,
    get_build_id_from_symbol_offset,
    get_lib_path_from_build_id,
    get_offset_from_symbol_build_id,
)

app = FastAPI(
    title="BionicDB API",
    version="0.1.0",
    description="Query metadata for indexed Android Bionic libc builds.",
)


@app.get("/v1/libs/{build_id}/offset")
def libs_build_id_offset(
    database: Database, symbol: str, build_id: str
) -> dict[str, object]:
    offset = get_offset_from_symbol_build_id(database, symbol, build_id)
    if offset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matching symbol: {symbol} for build_id: {build_id}",
        )
    return {"status": "ok", "offset": hex(offset)}


@app.get("/v1/libs/{build_id}")
def libs_build_id(database: Database, build_id: str) -> FileResponse:
    path = get_lib_path_from_build_id(database, build_id)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No library found for build ID {build_id}.",
        )
    return FileResponse(
        path=path,
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


app.mount(
    "/",
    StaticFiles(directory=REPOSITORY_ROOT / "api" / "static", html=True),
    name="frontend",
)
