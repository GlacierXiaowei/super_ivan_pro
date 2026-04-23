from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from desktop_service.http_api import create_app  # noqa: E402


class DesktopServiceApiTest(unittest.TestCase):
    def test_status_and_target_update_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(runtime_root=Path(tmp))

            status_code, status = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(status["mode"], "normal")
            self.assertEqual(status["service_state"], "running")

            status_code, updated = app.handle_json(
                "POST",
                "/targets/active",
                {
                    "talker": "filehelper",
                    "display_name": "文件传输助手",
                    "is_group": False,
                },
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(updated["active_target"]["display_name"], "文件传输助手")

            status_code, latest = app.handle_json("GET", "/status")
            self.assertEqual(status_code, 200)
            self.assertEqual(latest["active_target"]["talker"], "filehelper")

    def test_mode_update_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(runtime_root=Path(tmp))

            status_code, updated = app.handle_json(
                "POST",
                "/mode",
                {"mode": "rapid"},
            )

            self.assertEqual(status_code, 200)
            self.assertEqual(updated["mode"], "rapid")

    def test_rejects_incomplete_target_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(runtime_root=Path(tmp))
            status_code, payload = app.handle_json("POST", "/targets/active", {"talker": "a"})
            self.assertEqual(status_code, 400)
            self.assertEqual(payload["ok"], False)


if __name__ == "__main__":
    unittest.main()
