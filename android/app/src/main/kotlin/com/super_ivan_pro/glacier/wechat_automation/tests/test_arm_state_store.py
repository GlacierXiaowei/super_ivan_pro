from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.arm_state import ArmStateStore  # noqa: E402
from core.models import RuntimeConfig  # noqa: E402


class ArmStateStoreTest(unittest.TestCase):
    def test_default_state_is_disarmed_with_one_remaining_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)

            state = store.read()
            self.assertFalse(state.enabled)
            self.assertEqual(state.mode, "armed_current_chat")
            self.assertEqual(state.remaining_triggers, 1)

    def test_arm_resets_triggers_sent_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            path.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "mode": "armed_current_chat",
                        "max_triggers": 3,
                        "triggers_sent": 2,
                        "reason": "prior_state",
                    }
                ),
                encoding="utf-8",
            )
            store = ArmStateStore(path)

            store.arm(max_triggers=3)
            state = store.read()
            self.assertTrue(state.enabled)
            self.assertEqual(state.max_triggers, 3)
            self.assertEqual(state.triggers_sent, 0)
            self.assertEqual(state.remaining_triggers, 3)

    def test_record_success_auto_disarms_when_budget_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)

            store.arm(max_triggers=2)
            state = store.record_success()
            self.assertTrue(state.enabled)
            self.assertEqual(state.triggers_sent, 1)
            self.assertEqual(state.remaining_triggers, 1)

            state = store.record_success()
            self.assertFalse(state.enabled)
            self.assertEqual(state.triggers_sent, 2)
            self.assertEqual(state.remaining_triggers, 0)
            self.assertEqual(state.reason, "budget_exhausted")

    def test_unlimited_mode_stays_armed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arm_state.json"
            store = ArmStateStore(path)

            store.arm(max_triggers=0)
            for _ in range(5):
                state = store.record_success()
            self.assertTrue(state.enabled)
            self.assertEqual(state.max_triggers, 0)
            self.assertEqual(state.triggers_sent, 5)
            self.assertIsNone(state.remaining_triggers)


class RuntimeConfigArmStatePathTest(unittest.TestCase):
    def test_runtime_config_arm_state_path_defaults_and_overrides(self) -> None:
        default_cfg = RuntimeConfig.from_dict({})
        self.assertEqual(default_cfg.arm_state_path, "config/arm_state.local.json")

        overridden = RuntimeConfig.from_dict({"arm_state_path": "config/custom_arm.json"})
        self.assertEqual(overridden.arm_state_path, "config/custom_arm.json")


if __name__ == "__main__":
    unittest.main()
