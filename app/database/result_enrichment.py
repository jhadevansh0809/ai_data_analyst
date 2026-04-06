"""Attach human-readable names to query rows that only have foreign-key IDs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.database.connection import DatabaseManager


def _column_key_map(first_row: dict[str, Any]) -> dict[str, str]:
    """Map lowercase column name -> actual key used in rows (preserve casing)."""
    return {k.lower(): k for k in first_row.keys()}


def enrich_rows_with_entity_names(db_manager: DatabaseManager, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add ``cafe_name`` / ``vendor_name`` when rows contain ``cafe_id`` / ``vendor_id`` without names.

    Skips lookup if the query already returned name columns (e.g. from a JOIN).
    """
    if not rows:
        return rows

    key_map = _column_key_map(rows[0])

    def has(name: str) -> bool:
        return name.lower() in key_map

    need_cafe = has("cafe_id") and not has("cafe_name")
    need_vendor = has("vendor_id") and not has("vendor_name")

    if not need_cafe and not need_vendor:
        return rows

    cafe_id_key = key_map.get("cafe_id") if need_cafe else None
    vendor_id_key = key_map.get("vendor_id") if need_vendor else None

    cafe_ids: set[Any] = set()
    vendor_ids: set[Any] = set()

    for row in rows:
        if cafe_id_key is not None and row.get(cafe_id_key) is not None:
            cafe_ids.add(row[cafe_id_key])
        if vendor_id_key is not None and row.get(vendor_id_key) is not None:
            vendor_ids.add(row[vendor_id_key])

    cafe_map: dict[Any, str] = {}
    vendor_map: dict[Any, str] = {}

    with db_manager.get_session() as session:
        if need_cafe and cafe_ids:
            cafe_map = _fetch_id_name_map(session, "cafes", cafe_ids)
        if need_vendor and vendor_ids:
            vendor_map = _fetch_id_name_map(session, "vendors", vendor_ids)

    out: list[dict[str, Any]] = []
    for row in rows:
        new_row = dict(row)
        if need_cafe and cafe_id_key is not None:
            cid = new_row.get(cafe_id_key)
            if cid is not None and cid in cafe_map:
                new_row["cafe_name"] = cafe_map[cid]
        if need_vendor and vendor_id_key is not None:
            vid = new_row.get(vendor_id_key)
            if vid is not None and vid in vendor_map:
                new_row["vendor_name"] = vendor_map[vid]
        out.append(new_row)

    return out


def _fetch_id_name_map(session: Session, table: str, ids: set[Any]) -> dict[Any, str]:
    """Load id -> name for the given table (cafes or vendors)."""
    if table == "cafes":
        sql = "SELECT id, name FROM cafes WHERE id IN :ids"
    elif table == "vendors":
        sql = "SELECT id, name FROM vendors WHERE id IN :ids"
    else:
        raise ValueError(f"Unsupported lookup table: {table!r}")

    id_list = list(ids)
    stmt = text(sql).bindparams(bindparam("ids", expanding=True))
    result = session.execute(stmt, {"ids": id_list})
    return {row[0]: row[1] for row in result.fetchall()}
