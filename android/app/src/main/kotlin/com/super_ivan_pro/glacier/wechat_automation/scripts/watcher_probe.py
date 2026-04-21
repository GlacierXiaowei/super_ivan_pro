from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.watcher_adapter import JsonlReplayWatcher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe replay watcher normalization.")
    parser.add_argument("--events", required=True, help="Path to replay JSONL events.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    watcher = JsonlReplayWatcher(args.events)
    for event in watcher.iter_events():
        print(
            json.dumps(
                {
                    "seq": event.seq,
                    "talker": event.display_talker,
                    "sender": event.display_sender,
                    "type": event.message_type.value,
                    "content": event.content,
                },
                ensure_ascii=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
