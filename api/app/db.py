import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, cast

from fastapi.param_functions import Depends

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = Path(os.environ.get("BIONIC_DB_PATH", REPOSITORY_ROOT / "bionic.db"))


def get_db() -> Iterator[sqlite3.Connection]:
    """Provide one read-only SQLite connection per request."""
    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro", uri=True, check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    _ = connection.execute("PRAGMA query_only = ON")
    try:
        yield connection
    finally:
        connection.close()


Database = Annotated[sqlite3.Connection, Depends(get_db)]


def get_all_libs(database: Database) -> list[sqlite3.Row]:
    return database.execute(
        """SELECT
            libs.build_id,
            libs.sha256,
            releases.android_version,
            MAX(releases.android_api) AS android_api,
            REPLACE(
                GROUP_CONCAT(DISTINCT releases.security_patch),
                ',',
                ', '
            ) AS security_patch,
            REPLACE(
                GROUP_CONCAT(DISTINCT releases.firmware_build_id),
                ',',
                ', '
            ) AS firmware_build_id,
            REPLACE(
                GROUP_CONCAT(DISTINCT releases.device),
                ',',
                ', '
            ) AS device
        FROM libs
        LEFT JOIN releases ON releases.lib_id = libs.id
        GROUP BY
            libs.build_id,
            libs.sha256,
            releases.android_version
        ORDER BY CAST(releases.android_version AS INTEGER) DESC, libs.build_id;"""
    ).fetchall()


def get_offset_from_symbol_build_id(
    database: Database, symbol: str, build_id: str
) -> int | None:
    offset = cast(
        tuple[int] | None,
        database.execute(
            """
            SELECT offset
            FROM symbols_with_build_id
            WHERE build_id = ?
            AND name = ?;
            """,
            (build_id, symbol),
        ).fetchone(),
    )
    if offset is None:
        return None
    return offset[0]


# get the file path from a build id for a lib
def get_lib_path_from_build_id(
    database: Database,
    build_id: str,
) -> Path | None:
    row = cast(
        tuple[str] | None,
        database.execute(
            """
            SELECT file_path
            FROM libs
            WHERE build_id = ?
            """,
            (build_id,),
        ).fetchone(),
    )

    if row is None:
        return None

    return REPOSITORY_ROOT / Path(row[0])


# Get a lib buildid from a symbol or offset, symbol name is optional.
def get_build_id_from_symbol_offset(
    database: Database, offset: int, symbol: str | None
) -> list[sqlite3.Row]:
    rows: list[sqlite3.Row] = database.execute(
        """SELECT
            symbols.name,
            symbols.offset,
            libs.build_id,
            libs.sha256,
            REPLACE(
                GROUP_CONCAT(DISTINCT releases.device),
                ',',
                ', '
            ) AS device,
            releases.android_version,
            MAX(releases.android_api) AS android_api
        FROM symbols
        JOIN libs ON libs.id = symbols.lib_id
        LEFT JOIN releases ON releases.lib_id = libs.id
        WHERE symbols.offset = ?
        AND (? IS NULL OR symbols.name = ?)
        GROUP BY
            symbols.name,
            symbols.offset,
            libs.build_id,
            libs.sha256,
            releases.android_version
        ORDER BY CAST(releases.android_version AS INTEGER), libs.build_id;""",
        (offset, symbol, symbol),
    ).fetchall()
    return rows
