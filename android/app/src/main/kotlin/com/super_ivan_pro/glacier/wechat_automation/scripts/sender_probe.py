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
    parser = argparse.ArgumentParser(description="Probe sender backend.")
    parser.add_argument("--runtime", required=True, help="Path to runtime config JSON/YAML.")
    parser.add_argument("--talker", required=True, help="Target talker display name.")
    parser.add_argument("--message", required=True, help="Message to send.")
    parser.add_argument("--group", action="store_true", help="Mark the target as a group chat.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = load_runtime_config(args.runtime)
    log_dir = (ROOT / runtime.log_dir).resolve()
    logger = configure_logger("sender_probe", log_dir)
    sender = create_sender(runtime, logger)
    context = MessageEvent(
        seq="probe",
        timestamp="",
        talker=args.talker,
        talker_name=args.talker,
        is_chat_room=args.group,
        sender="probe_sender",
        sender_name="probe_sender",
        message_type=MessageType.TEXT,
        content="",
        raw={"probe": True},
    )
    sender.send_text(context, args.message)
    logger.info("sender_probe_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
