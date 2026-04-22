from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.arm_state import ArmStateStore
from core.bot import WeChatAutomationBot
from core.config_loader import load_rules, load_runtime_config
from core.dispatcher import SendDispatcher
from core.logger import configure_logger
from core.sender_adapter import create_sender
from core.watcher_adapter import JsonlReplayWatcher, WechatDecryptHistoryWatcher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the WeChat automation bot in replay mode.")
    parser.add_argument("--runtime", required=True, help="Path to runtime config JSON/YAML.")
    parser.add_argument("--rules", required=True, help="Path to rules config JSON/YAML.")
    parser.add_argument("--events", help="Path to replay JSONL events.")
    parser.add_argument("--live", action="store_true", help="Use the live wechat-decrypt history watcher.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = load_runtime_config(args.runtime)
    rules = load_rules(args.rules)

    log_dir = (ROOT / runtime.log_dir).resolve()
    logger = configure_logger("wechat_automation", log_dir)
    sender = create_sender(runtime, logger)
    dispatcher = SendDispatcher(sender, runtime, logger)
    arm_state_store = ArmStateStore(ROOT / runtime.arm_state_path)
    bot = WeChatAutomationBot(rules, dispatcher, logger, arm_state_store)
    if args.live:
        watcher = WechatDecryptHistoryWatcher(runtime)
    else:
        if not args.events:
            raise ValueError("--events is required unless --live is used.")
        watcher = JsonlReplayWatcher(args.events)

    for event in watcher.iter_events():
        bot.process(event)

    logger.info("run_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
