from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.history_sender_search import _ensure_decrypted_contact_db


@dataclass(slots=True)
class HistoryChatCandidate:
    talker: str
    display_name: str
    last_timestamp: int
    summary: str
    source: str
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "talker": self.talker,
            "display_name": self.display_name,
            "last_timestamp": self.last_timestamp,
            "summary": self.summary,
            "source": self.source,
        }


def search_history_chats(
    source_root: str | Path,
    query: str = "",
    limit: int = 20,
) -> list[HistoryChatCandidate]:
    source_path = Path(source_root)
    normalized_query = query.strip().lower()
    contact_chats = _load_contact_chats(source_path)
    candidates: dict[str, HistoryChatCandidate] = {}

    for db_path in _session_db_paths(source_path):
        for row in _read_session_rows(db_path):
            talker = row["talker"]
            if not _is_group_talker(talker):
                continue

            contact_name = contact_chats.get(talker, "")
            display_name = (
                row["session_title"]
                or contact_name
                or talker
            )
            candidate = HistoryChatCandidate(
                talker=talker,
                display_name=display_name,
                last_timestamp=row["last_timestamp"],
                summary=row["summary"],
                source="session",
                aliases=_unique_names(row["session_title"], contact_name),
            )
            candidates[talker] = candidate

    for talker, display_name in contact_chats.items():
        if talker in candidates:
            continue
        candidates[talker] = HistoryChatCandidate(
            talker=talker,
            display_name=display_name or talker,
            last_timestamp=0,
            summary="",
            source="contact",
        )

    filtered = [
        candidate
        for candidate in candidates.values()
        if not normalized_query or _matches_query(normalized_query, candidate)
    ]
    ordered = sorted(
        filtered,
        key=lambda candidate: (
            candidate.last_timestamp <= 0,
            -candidate.last_timestamp,
            candidate.display_name.lower(),
        ),
    )
    return ordered[: max(limit, 1)]


def _session_db_paths(source_root: Path) -> list[Path]:
    candidates = [
        source_root / "decrypted" / "session" / "session.db",
        source_root / "decrypted" / "_monitor_cache" / "session_session.db",
    ]
    return [path for path in candidates if path.exists()]


def _read_session_rows(db_path: Path) -> list[dict[str, Any]]:
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        if not _table_exists(conn, "SessionTable"):
            return []

        session_titles = _load_session_titles(conn)
        rows = conn.execute(
            """
            SELECT username, summary, last_timestamp
            FROM SessionTable
            WHERE username LIKE '%@chatroom'
            ORDER BY last_timestamp DESC
            """
        ).fetchall()
        return [
            {
                "talker": str(username or "").strip(),
                "summary": _normalize_summary(summary),
                "last_timestamp": int(last_timestamp or 0),
                "session_title": session_titles.get(str(username or "").strip(), ""),
            }
            for username, summary, last_timestamp in rows
        ]
    except sqlite3.Error:
        return []
    finally:
        if conn is not None:
            conn.close()


def _load_session_titles(conn: sqlite3.Connection) -> dict[str, str]:
    if not _table_exists(conn, "SessionNoContactInfoTable"):
        return {}
    try:
        rows = conn.execute(
            "SELECT username, session_title FROM SessionNoContactInfoTable"
        ).fetchall()
    except sqlite3.Error:
        return {}
    return {
        str(username or "").strip(): str(title or "").strip()
        for username, title in rows
        if str(username or "").strip()
    }


def _load_contact_chats(source_root: Path) -> dict[str, str]:
    candidates = [
        source_root / "decrypted" / "contact" / "contact.db",
        source_root / "decrypted" / "_monitor_cache" / "contact_contact.db",
    ]
    decrypted_contact = _ensure_decrypted_contact_db(source_root)
    if decrypted_contact is not None:
        candidates.append(decrypted_contact)

    chats: dict[str, str] = {}
    for path in candidates:
        if not path.exists():
            continue
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(path)
            if not _table_exists(conn, "contact"):
                continue
            rows = conn.execute("SELECT username, nick_name, remark FROM contact").fetchall()
        except sqlite3.Error:
            continue
        finally:
            if conn is not None:
                conn.close()

        for username, nick_name, remark in rows:
            talker = str(username or "").strip()
            if not _is_group_talker(talker):
                continue
            display = str(remark or nick_name or talker).strip()
            chats[talker] = display or talker
    return chats


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _is_group_talker(value: str) -> bool:
    return value.endswith("@chatroom")


def _normalize_summary(summary: Any) -> str:
    if summary is None:
        return ""
    if isinstance(summary, bytes):
        try:
            import zstandard as zstd

            summary = zstd.ZstdDecompressor().decompress(summary).decode("utf-8", errors="replace")
        except Exception:
            summary = summary.decode("utf-8", errors="replace")
    text = str(summary)
    if ":\n" in text:
        text = text.split(":\n", 1)[1]
    return _collapse_text(text)


def _collapse_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _unique_names(*values: str) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        names.append(normalized)
    return tuple(names)


def _matches_query(query: str, candidate: HistoryChatCandidate) -> bool:
    haystacks = [
        candidate.talker,
        candidate.display_name,
        candidate.summary,
        candidate.source,
        *candidate.aliases,
    ]
    return any(query in item.lower() for item in haystacks if item)
