from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.history_chat_search import search_history_chats  # noqa: E402


class HistoryChatSearchTest(unittest.TestCase):
    def test_searches_session_and_contact_group_chats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "wechat-decrypt"
            session_dir = source_root / "decrypted" / "session"
            contact_dir = source_root / "decrypted" / "_monitor_cache"
            session_dir.mkdir(parents=True)
            contact_dir.mkdir(parents=True)

            session_db = session_dir / "session.db"
            conn = sqlite3.connect(session_db)
            try:
                conn.execute(
                    "CREATE TABLE SessionTable ("
                    "username TEXT, summary TEXT, last_timestamp INTEGER"
                    ")"
                )
                conn.execute(
                    "CREATE TABLE SessionNoContactInfoTable ("
                    "username TEXT, session_title TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO SessionTable VALUES (?, ?, ?)",
                    ("111@chatroom", "Alice:\n今天开会", 1778000002),
                )
                conn.execute(
                    "INSERT INTO SessionNoContactInfoTable VALUES (?, ?)",
                    ("111@chatroom", "项目讨论群"),
                )
                conn.execute(
                    "INSERT INTO SessionTable VALUES (?, ?, ?)",
                    ("wxid_alice", "私聊不应出现在群聊搜索", 1778000003),
                )
                conn.commit()
            finally:
                conn.close()

            contact_db = contact_dir / "contact_contact.db"
            conn = sqlite3.connect(contact_db)
            try:
                conn.execute(
                    "CREATE TABLE contact ("
                    "username TEXT, nick_name TEXT, remark TEXT"
                    ")"
                )
                conn.execute(
                    "INSERT INTO contact VALUES (?, ?, ?)",
                    ("111@chatroom", "旧群名", ""),
                )
                conn.execute(
                    "INSERT INTO contact VALUES (?, ?, ?)",
                    ("222@chatroom", "历史测试群", ""),
                )
                conn.execute(
                    "INSERT INTO contact VALUES (?, ?, ?)",
                    ("wxid_bob", "Bob", ""),
                )
                conn.commit()
            finally:
                conn.close()

            session_results = search_history_chats(source_root, query="项目", limit=10)
            self.assertEqual(len(session_results), 1)
            self.assertEqual(session_results[0].talker, "111@chatroom")
            self.assertEqual(session_results[0].display_name, "项目讨论群")
            self.assertEqual(session_results[0].last_timestamp, 1778000002)
            self.assertEqual(session_results[0].summary, "今天开会")
            self.assertEqual(session_results[0].source, "session")

            contact_results = search_history_chats(source_root, query="历史", limit=10)
            self.assertEqual(len(contact_results), 1)
            self.assertEqual(contact_results[0].talker, "222@chatroom")
            self.assertEqual(contact_results[0].display_name, "历史测试群")
            self.assertEqual(contact_results[0].last_timestamp, 0)
            self.assertEqual(contact_results[0].source, "contact")

            all_results = search_history_chats(source_root, query="", limit=10)
            self.assertEqual([item.talker for item in all_results], ["111@chatroom", "222@chatroom"])


if __name__ == "__main__":
    unittest.main()
