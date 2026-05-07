from __future__ import annotations

import codecs
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
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
        self.assertIn('set "release_root=%~dp0"', content)
        self.assertIn(
            'set "packaged_service_script=%release_root%data\\flutter_assets\\android\\app\\src\\main\\kotlin\\com\\super_ivan_pro\\glacier\\wechat_automation\\scripts\\desktop_service.py"',
            content,
        )
        self.assertIn(
            'set "tool_packaged_service_script=%release_root%..\\..\\data\\flutter_assets\\android\\app\\src\\main\\kotlin\\com\\super_ivan_pro\\glacier\\wechat_automation\\scripts\\desktop_service.py"',
            content,
        )
        self.assertIn('echo   %tool_packaged_service_script%', content)
        self.assertIn('pushd "%~dp0..\\.."', content)
        self.assertIn("searched paths", content)
        self.assertIn("where python", content)
        self.assertIn("where py", content)
        self.assertIn("python was not found", content)
        self.assertIn("http://127.0.0.1:18090/status", content)
        self.assertIn("armed=true", content)
        self.assertIn("/arm-state", content)
        self.assertIn("disarming before restart", content)
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
        self.assertIn("where python", content)
        self.assertIn("where py", content)
        self.assertIn("python was not found", content)
        self.assertIn("main.py", content)
        self.assertIn("decrypt", content)
        self.assertIn("pause", content)
        self.assertIn(":finish", content)
        self.assertNotIn("/arm-state", content)
        self.assertNotIn("/services/start", content)

    def test_init_first_run_script_updates_local_runtime_config(self) -> None:
        script = _repo_root() / "tools" / "windows" / "init_first_run.bat"
        self.assertTrue(script.exists(), "init_first_run.bat should exist")

        content = script.read_text(encoding="utf-8").lower()
        self.assertIn("runtime.local.json", content)
        self.assertIn("wechat-decrypt", content)
        self.assertIn("localappdata", content)
        self.assertIn("convertfrom-json", content)
        self.assertIn("convertto-json", content)
        self.assertIn("press any key to close this window", content)

    def test_init_first_run_script_handles_existing_config_without_watcher_url(self) -> None:
        script = _repo_root() / "tools" / "windows" / "init_first_run.bat"
        self.assertTrue(script.exists(), "init_first_run.bat should exist")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_root = temp_path / "portable"
            tools_dir = package_root / "tools" / "windows"
            runtime_dir = package_root / "runtime" / "wechat-decrypt"
            assets_dir = package_root / "data" / "flutter_assets"
            local_app_data = temp_path / "localappdata"
            config_dir = (
                local_app_data
                / "SuperIvanPro"
                / "wechat_automation"
                / "config"
            )
            config_path = config_dir / "runtime.local.json"

            tools_dir.mkdir(parents=True)
            runtime_dir.mkdir(parents=True)
            assets_dir.mkdir(parents=True)
            config_dir.mkdir(parents=True)

            shutil.copy2(script, tools_dir / "init_first_run.bat")
            (runtime_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")
            config_path.write_text(
                json.dumps(
                    {
                        "wechat_decrypt_root": "D:\\old\\wechat-decrypt",
                        "poll_interval_ms": 20,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            env = dict(os.environ)
            env["LOCALAPPDATA"] = str(local_app_data)
            result = subprocess.run(
                f'"{tools_dir / "init_first_run.bat"}" < nul',
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
                shell=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                result.stdout + "\n" + result.stderr,
            )

            payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
            self.assertFalse(config_path.read_bytes().startswith(codecs.BOM_UTF8))
            self.assertEqual(
                Path(payload["wechat_decrypt_root"]).resolve(),
                runtime_dir.resolve(),
            )
            self.assertEqual(
                payload["watcher_url"],
                "http://127.0.0.1:5678",
            )
            self.assertEqual(payload["sender_backend"], "current_chat")
            self.assertFalse(payload["dry_run"])
            self.assertEqual(payload["poll_interval_ms"], 20)

    def test_package_portable_release_script_collects_bundled_runtime(self) -> None:
        script = _repo_root() / "tools" / "windows" / "package_portable_release.ps1"
        self.assertTrue(script.exists(), "package_portable_release.ps1 should exist")

        content = script.read_text(encoding="utf-8").lower()
        self.assertIn("copy-item -path", content)
        self.assertIn("runtime\\wechat-decrypt", content)
        self.assertIn("compress-archive", content)
        self.assertIn("super_ivan_pro.exe", content)
        self.assertIn("new-unicodename", content)
        self.assertIn("write-wrapperbat", content)
        self.assertIn("windows-portable-user-guide.zh-cn.md", content)
        self.assertIn("bundled_python=false", content)
        self.assertIn("system_python_required=true", content)
        self.assertNotIn("pythonroot", content)


if __name__ == "__main__":
    unittest.main()
