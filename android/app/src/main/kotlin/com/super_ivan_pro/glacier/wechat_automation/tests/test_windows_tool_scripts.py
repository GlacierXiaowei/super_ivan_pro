from __future__ import annotations

from pathlib import Path
import unittest


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pubspec.yaml").exists():
            return parent
    raise AssertionError("repo root with pubspec.yaml not found")


class WindowsToolScriptsTest(unittest.TestCase):
    def test_restart_python_service_script_has_safety_checks(self) -> None:
        script = _repo_root() / "tools" / "windows" / "restart_python_service.bat"
        self.assertTrue(script.exists(), "restart_python_service.bat should exist")

        content = script.read_text(encoding="utf-8").lower()
        self.assertIn("http://127.0.0.1:18090/status", content)
        self.assertIn("armed=true", content)
        self.assertIn("/services/stop", content)
        self.assertIn("get-nettcpconnection", content)
        self.assertIn("stop-process", content)
        self.assertIn("desktop_service.py", content)
        self.assertIn("pause", content)
        self.assertIn(":finish", content)

    def test_build_wechat_cache_script_runs_full_decrypt_only(self) -> None:
        script = _repo_root() / "tools" / "windows" / "build_wechat_cache.bat"
        self.assertTrue(script.exists(), "build_wechat_cache.bat should exist")

        content = script.read_text(encoding="utf-8").lower()
        self.assertIn("runtime.local.json", content)
        self.assertIn("wechat_decrypt_root", content)
        self.assertIn("main.py", content)
        self.assertIn("decrypt", content)
        self.assertIn("pause", content)
        self.assertIn(":finish", content)
        self.assertNotIn("/arm-state", content)
        self.assertNotIn("/services/start", content)


if __name__ == "__main__":
    unittest.main()
