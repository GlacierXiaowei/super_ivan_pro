from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PAGE_SIZE = 4096
SALT_SIZE = 16
RESERVE_SIZE = 80
SQLITE_HEADER = b"SQLite format 3\x00"


@dataclass(slots=True)
class HistorySenderCandidate:
    sender: str
    sender_name: str
    last_timestamp: int
    last_content: str
    message_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "sender": self.sender,
            "sender_name": self.sender_name,
            "last_timestamp": self.last_timestamp,
            "last_content": self.last_content,
            "message_count": self.message_count,
        }


def search_history_senders(
    source_root: str | Path,
    chat: str,
    query: str = "",
    limit: int = 20,
) -> list[HistorySenderCandidate]:
    source_path = Path(source_root)
    chat_username = chat.strip()
    if not chat_username:
        return []

    table_name = f"Msg_{hashlib.md5(chat_username.encode()).hexdigest()}"
    contact_names = _load_contact_names(source_path)
    normalized_query = query.strip().lower()
    candidates: dict[str, HistorySenderCandidate] = {}

    for db_path in _message_db_paths(source_path):
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(db_path)
            if not _table_exists(conn, table_name):
                continue
            id_to_username = _load_name2id(conn)
            rows = conn.execute(
                f"""
                SELECT real_sender_id, create_time, message_content, WCDB_CT_message_content
                FROM [{table_name}]
                WHERE real_sender_id > 0
                ORDER BY create_time DESC
                LIMIT 5000
                """
            ).fetchall()
        except sqlite3.Error:
            continue
        finally:
            if conn is not None:
                conn.close()

        for real_sender_id, create_time, raw_content, content_type in rows:
            sender = id_to_username.get(int(real_sender_id or 0), "")
            content = _normalize_content(raw_content, content_type)
            sender_from_content, message_text = _split_group_content(content)
            if not sender and sender_from_content:
                sender = sender_from_content
            if not sender:
                continue

            sender_name = contact_names.get(sender, sender)
            if normalized_query and not _matches_query(
                normalized_query,
                sender=sender,
                sender_name=sender_name,
                sender_from_content=sender_from_content,
                content=message_text,
            ):
                continue

            timestamp = int(create_time or 0)
            existing = candidates.get(sender)
            if existing is None:
                candidates[sender] = HistorySenderCandidate(
                    sender=sender,
                    sender_name=sender_name,
                    last_timestamp=timestamp,
                    last_content=message_text,
                    message_count=1,
                )
                continue

            existing.message_count += 1
            if timestamp > existing.last_timestamp:
                existing.last_timestamp = timestamp
                existing.last_content = message_text

    ordered = sorted(
        candidates.values(),
        key=lambda candidate: candidate.last_timestamp,
        reverse=True,
    )
    return ordered[: max(limit, 1)]


def _message_db_paths(source_root: Path) -> list[Path]:
    roots = [
        source_root / "decrypted" / "_monitor_cache",
        source_root / "decrypted" / "message",
    ]
    paths: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("message*.db")):
            if path in seen:
                continue
            seen.add(path)
            paths.append(path)
    return paths


def _load_contact_names(source_root: Path) -> dict[str, str]:
    candidates = [
        source_root / "decrypted" / "contact" / "contact.db",
        source_root / "decrypted" / "_monitor_cache" / "contact_contact.db",
    ]
    decrypted_contact = _ensure_decrypted_contact_db(source_root)
    if decrypted_contact is not None:
        candidates.append(decrypted_contact)

    names: dict[str, str] = {}
    for path in candidates:
        if not path.exists():
            continue
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(path)
            rows = conn.execute("SELECT username, nick_name, remark FROM contact").fetchall()
        except sqlite3.Error:
            continue
        finally:
            if conn is not None:
                conn.close()
        for username, nick_name, remark in rows:
            sender = str(username or "").strip()
            if not sender:
                continue
            display = str(remark or nick_name or sender).strip()
            names[sender] = display or sender
    return names


def _ensure_decrypted_contact_db(source_root: Path) -> Path | None:
    cache_path = source_root / "decrypted" / "_monitor_cache" / "contact_contact.db"
    if cache_path.exists():
        return cache_path

    config_path = source_root / "config.json"
    if not config_path.exists():
        return None

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        db_dir = Path(str(config["db_dir"]))
        keys_path = Path(str(config.get("keys_file", "all_keys.json")))
        if not keys_path.is_absolute():
            keys_path = source_root / keys_path
        keys_payload = json.loads(keys_path.read_text(encoding="utf-8"))
        key_info = _find_key_info(keys_payload, "contact/contact.db")
        if not key_info:
            return None
        enc_key = bytes.fromhex(str(key_info["enc_key"]))
        encrypted_path = db_dir / "contact" / "contact.db"
        if not encrypted_path.exists():
            return None
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        _decrypt_sqlcipher_db(encrypted_path, cache_path, enc_key)
        return cache_path
    except Exception:
        return None


def _find_key_info(keys_payload: dict[str, Any], relative_path: str) -> dict[str, Any] | None:
    normalized = relative_path.replace("/", "\\").lower()
    for key, value in keys_payload.items():
        if str(key).replace("/", "\\").lower() == normalized and isinstance(value, dict):
            return value
    return None


def _decrypt_sqlcipher_db(encrypted_path: Path, output_path: Path, enc_key: bytes) -> None:
    from Crypto.Cipher import AES

    with encrypted_path.open("rb") as source, output_path.open("wb") as output:
        page_no = 1
        while True:
            page = source.read(PAGE_SIZE)
            if not page:
                break
            if len(page) < PAGE_SIZE:
                output.write(page)
                break

            iv = page[PAGE_SIZE - RESERVE_SIZE : PAGE_SIZE - RESERVE_SIZE + 16]
            if page_no == 1:
                encrypted = page[SALT_SIZE : PAGE_SIZE - RESERVE_SIZE]
                decrypted = AES.new(enc_key, AES.MODE_CBC, iv).decrypt(encrypted)
                output.write(SQLITE_HEADER + decrypted + b"\x00" * RESERVE_SIZE)
            else:
                encrypted = page[: PAGE_SIZE - RESERVE_SIZE]
                decrypted = AES.new(enc_key, AES.MODE_CBC, iv).decrypt(encrypted)
                output.write(decrypted + b"\x00" * RESERVE_SIZE)
            page_no += 1


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _load_name2id(conn: sqlite3.Connection) -> dict[int, str]:
    try:
        rows = conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()
    except sqlite3.Error:
        return {}
    return {
        int(rowid): str(username)
        for rowid, username in rows
        if rowid is not None and username
    }


def _normalize_content(content: Any, content_type: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, bytes):
        if int(content_type or 0) == 4:
            try:
                import zstandard as zstd

                return zstd.ZstdDecompressor().decompress(content).decode("utf-8", errors="replace")
            except Exception:
                pass
        return content.decode("utf-8", errors="replace")
    return str(content)


def _split_group_content(content: str) -> tuple[str, str]:
    if ":\n" not in content:
        return "", _collapse_text(content)
    sender, text = content.split(":\n", 1)
    return sender.strip(), _collapse_text(text)


def _collapse_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _matches_query(
    query: str,
    *,
    sender: str,
    sender_name: str,
    sender_from_content: str,
    content: str,
) -> bool:
    haystacks = [sender, sender_name, sender_from_content, content]
    return any(query in item.lower() for item in haystacks if item)
