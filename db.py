"""Thin query helpers on top of mssql_conn (pymssql uses %s placeholders)."""

from __future__ import annotations

from typing import Iterable

from mssql_conn import production_cursor


def fetchall(query: str, params: Iterable | None = None) -> list[tuple]:
    with production_cursor() as cursor:
        cursor.execute(query, tuple(params or ()))
        rows = cursor.fetchall()
        return list(rows or [])
