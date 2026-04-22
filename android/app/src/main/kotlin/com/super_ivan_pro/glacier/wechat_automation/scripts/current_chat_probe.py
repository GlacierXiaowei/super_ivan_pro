from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config_loader import load_runtime_config
from core.logger import configure_logger
from core.models import MessageEvent, MessageType
from core.sender_adapter import create_sender


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send one message into the current WeChat chat."
    )
    parser.add_argument("--runtime", required=True, help="Path to runtime config JSON/YAML.")
    parser.add_argument("--message", required=True, help="Message to send into the current chat.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = load_runtime_config(args.runtime)
    logger = configure_logger("wechat_automation_probe", (ROOT / runtime.log_dir).resolve())
    sender = create_sender(runtime, logger)
    probe_event = MessageEvent(
        seq="probe",
        timestamp="0",
        talker="current_chat",
        talker_name="当前聊天",
        is_chat_room=False,
        sender="",
        sender_name="",
        message_type=MessageType.TEXT,
        content="",
    )
    sender.send_text(probe_event, args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
