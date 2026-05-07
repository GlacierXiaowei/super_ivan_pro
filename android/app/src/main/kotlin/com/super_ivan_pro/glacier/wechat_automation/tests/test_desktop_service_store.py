from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from desktop_service.config_paths import resolve_runtime_root  # noqa: E402
from desktop_service.http_api import create_app  # noqa: E402
from desktop_service.state_store import DesktopStateStore  # noqa: E402


class RuntimeRootResolverTest(unittest.TestCase):
    def test_uses_override_runtime_root_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "runtime"
            resolved = resolve_runtime_root(override=override)
            self.assertEqual(resolved, override)

    def test_builds_runtime_root_from_localappdata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": tmp}, clear=False):
                resolved = resolve_runtime_root()
            self.assertEqual(resolved, Path(tmp) / "SuperIvanPro" / "wechat_automation")


class DesktopStateStoreTest(unittest.TestCase):
    def test_persists_active_target_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = DesktopStateStore(Path(tmp))
            state = store.load()

            state["active_target"] = {
                "talker": "filehelper",
                "display_name": "文件传输助手",
                "is_group": False,
            }
            state["mode"] = "rapid"
            store.save(state)

            reloaded = store.load()
            self.assertEqual(reloaded["active_target"]["display_name"], "文件传输助手")
            self.assertEqual(reloaded["mode"], "rapid")


class DesktopServiceRuntimeFilesTest(unittest.TestCase):
    def _build_repo_fixture(self, root: Path) -> None:
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "run_bot.py").write_text(
            "print('bot placeholder')\n",
            encoding="utf-8",
        )
        (root / "config" / "runtime.local.json").write_text(
            json.dumps(
                {
                    "watcher_url": "http://127.0.0.1:5678",
                    "sender_backend": "dry_run",
                    "dry_run": True,
                    "arm_state_path": "config/arm_state.local.json",
                    "log_dir": "logs",
                }
            ),
            encoding="utf-8",
        )
        (root / "config" / "rules.local.json").write_text("[]", encoding="utf-8")
        (root / "config" / "arm_state.local.json").write_text(
            json.dumps(
                {
                    "enabled": False,
                    "mode": "armed_current_chat",
                    "max_triggers": 1,
                    "triggers_sent": 0,
                    "remaining_triggers": 1,
                    "reason": "not_armed",
                }
            ),
            encoding="utf-8",
        )

    def test_seeds_desktop_runtime_files_without_modifying_repo_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)
            source_runtime_text = (repo_root / "config" / "runtime.local.json").read_text(encoding="utf-8")

            create_app(runtime_root=runtime_root, repo_root=repo_root)

            desktop_runtime_path = runtime_root / "config" / "runtime.local.json"
            desktop_rules_path = runtime_root / "config" / "rules.local.json"
            desktop_arm_path = runtime_root / "config" / "arm_state.local.json"
            self.assertTrue(desktop_runtime_path.exists())
            self.assertTrue(desktop_rules_path.exists())
            self.assertTrue(desktop_arm_path.exists())

            runtime_payload = json.loads(desktop_runtime_path.read_text(encoding="utf-8"))
            self.assertEqual(runtime_payload["arm_state_path"], str(desktop_arm_path))
            self.assertEqual(runtime_payload["log_dir"], str((runtime_root / "logs")))

            source_runtime_after = (repo_root / "config" / "runtime.local.json").read_text(encoding="utf-8")
            self.assertEqual(source_runtime_after, source_runtime_text)

    def test_seeds_packaged_wechat_decrypt_root_when_bundled_runtime_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package_root = tmp_path / "Release"
            repo_root = (
                package_root
                / "data"
                / "flutter_assets"
                / "android"
                / "app"
                / "src"
                / "main"
                / "kotlin"
                / "com"
                / "super_ivan_pro"
                / "glacier"
                / "wechat_automation"
            )
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)

            bundled_wechat_decrypt = package_root / "runtime" / "wechat-decrypt"
            bundled_wechat_decrypt.mkdir(parents=True, exist_ok=True)
            (bundled_wechat_decrypt / "main.py").write_text(
                "print('wechat decrypt placeholder')\n",
                encoding="utf-8",
            )
            (package_root / "super_ivan_pro.exe").write_text("", encoding="utf-8")

            create_app(runtime_root=runtime_root, repo_root=repo_root)

            desktop_runtime_path = runtime_root / "config" / "runtime.local.json"
            runtime_payload = json.loads(desktop_runtime_path.read_text(encoding="utf-8"))
            self.assertEqual(
                runtime_payload["wechat_decrypt_root"],
                str(bundled_wechat_decrypt),
            )

    def test_packaged_runtime_backfills_real_send_defaults_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package_root = tmp_path / "Release"
            repo_root = (
                package_root
                / "data"
                / "flutter_assets"
                / "android"
                / "app"
                / "src"
                / "main"
                / "kotlin"
                / "com"
                / "super_ivan_pro"
                / "glacier"
                / "wechat_automation"
            )
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)

            bundled_wechat_decrypt = package_root / "runtime" / "wechat-decrypt"
            bundled_wechat_decrypt.mkdir(parents=True, exist_ok=True)
            (bundled_wechat_decrypt / "main.py").write_text(
                "print('wechat decrypt placeholder')\n",
                encoding="utf-8",
            )
            (package_root / "super_ivan_pro.exe").write_text("", encoding="utf-8")
            sparse_runtime_path = runtime_root / "config" / "runtime.local.json"
            sparse_runtime_path.parent.mkdir(parents=True, exist_ok=True)
            sparse_runtime_path.write_text(
                json.dumps(
                    {
                        "watcher_url": "http://127.0.0.1:5678",
                        "poll_interval_ms": 20,
                    }
                ),
                encoding="utf-8",
            )

            create_app(runtime_root=runtime_root, repo_root=repo_root)

            runtime_payload = json.loads(sparse_runtime_path.read_text(encoding="utf-8"))
            self.assertEqual(runtime_payload["sender_backend"], "current_chat")
            self.assertFalse(runtime_payload["dry_run"])

    def test_packaged_runtime_preserves_explicit_send_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package_root = tmp_path / "Release"
            repo_root = (
                package_root
                / "data"
                / "flutter_assets"
                / "android"
                / "app"
                / "src"
                / "main"
                / "kotlin"
                / "com"
                / "super_ivan_pro"
                / "glacier"
                / "wechat_automation"
            )
            runtime_root = tmp_path / "desktop-runtime"
            self._build_repo_fixture(repo_root)

            bundled_wechat_decrypt = package_root / "runtime" / "wechat-decrypt"
            bundled_wechat_decrypt.mkdir(parents=True, exist_ok=True)
            (bundled_wechat_decrypt / "main.py").write_text(
                "print('wechat decrypt placeholder')\n",
                encoding="utf-8",
            )
            (package_root / "super_ivan_pro.exe").write_text("", encoding="utf-8")
            explicit_runtime_path = runtime_root / "config" / "runtime.local.json"
            explicit_runtime_path.parent.mkdir(parents=True, exist_ok=True)
            explicit_runtime_path.write_text(
                json.dumps(
                    {
                        "watcher_url": "http://127.0.0.1:5678",
                        "sender_backend": "dry_run",
                        "dry_run": True,
                    }
                ),
                encoding="utf-8",
            )

            create_app(runtime_root=runtime_root, repo_root=repo_root)

            runtime_payload = json.loads(explicit_runtime_path.read_text(encoding="utf-8"))
            self.assertEqual(runtime_payload["sender_backend"], "dry_run")
            self.assertTrue(runtime_payload["dry_run"])


if __name__ == "__main__":
    unittest.main()
