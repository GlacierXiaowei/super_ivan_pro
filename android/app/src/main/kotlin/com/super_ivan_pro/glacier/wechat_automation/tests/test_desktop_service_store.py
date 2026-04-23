from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from desktop_service.config_paths import resolve_runtime_root  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
