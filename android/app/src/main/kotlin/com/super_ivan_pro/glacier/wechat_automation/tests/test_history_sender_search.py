from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.history_sender_search import search_history_senders  # noqa: E402


class HistorySenderSearchTest(unittest.TestCase):
    def test_searches_group_history_and_returns_sender_username(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "wechat-decrypt"
            message_dir = source_root / "decrypted" / "_monitor_cache"
            contact_dir = source_root / "decrypted" / "contact"
            message_dir.mkdir(parents=True)
            contact_dir.mkdir(parents=True)

            chat = "123456@chatroom"
            table_name = f"Msg_{hashlib.md5(chat.encode()).hexdigest()}"
            message_db = message_dir / "message_message_0.db"
            conn = sqlite3.connect(message_db)
            try:
                conn.execute("CREATE TABLE Name2Id (user_name TEXT, is_session INTEGER)")
                conn.execute(
                    "CREATE TABLE [%s] ("
                    "local_id INTEGER PRIMARY KEY, "
                    "local_type INTEGER, "
                    "create_time INTEGER, "
                    "real_sender_id INTEGER, "
                    "message_content TEXT, "
                    "WCDB_CT_message_content INTEGER"
                    ")" % table_name
                )
                conn.execute("INSERT INTO Name2Id(rowid, user_name, is_session) VALUES (11, 'wxid_alice', 1)")
                conn.execute("INSERT INTO Name2Id(rowid, user_name, is_session) VALUES (12, 'wxid_bob', 1)")
                conn.execute(
                    "INSERT INTO [%s] VALUES (1, 1, 1778000001, 11, '第一条历史发言', NULL)" % table_name
                )
                conn.execute(
                    "INSERT INTO [%s] VALUES (2, 1, 1778000002, 12, '无关发言', NULL)" % table_name
                )
                conn.execute(
                    "INSERT INTO [%s] VALUES (3, 1, 1778000003, 11, '最近一条历史发言', NULL)" % table_name
                )
                conn.commit()
            finally:
                conn.close()

            contact_db = contact_dir / "contact.db"
            conn = sqlite3.connect(contact_db)
            try:
                conn.execute("CREATE TABLE contact (username TEXT, nick_name TEXT, remark TEXT)")
                conn.execute("INSERT INTO contact VALUES ('wxid_alice', 'Alice Nick', 'Alice Remark')")
                conn.execute("INSERT INTO contact VALUES ('wxid_bob', 'Bob Nick', '')")
                conn.commit()
            finally:
                conn.close()

            results = search_history_senders(source_root, chat=chat, query="Alice", limit=10)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].sender, "wxid_alice")
            self.assertEqual(results[0].sender_name, "Alice Remark")
            self.assertEqual(results[0].last_timestamp, 1778000003)
            self.assertEqual(results[0].last_content, "最近一条历史发言")
            self.assertEqual(results[0].message_count, 2)


if __name__ == "__main__":
    unittest.main()
