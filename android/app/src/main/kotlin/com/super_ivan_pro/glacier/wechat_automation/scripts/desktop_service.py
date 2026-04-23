from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop_service.http_api import create_app, create_http_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the WeChat automation desktop service.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the desktop service.")
    parser.add_argument("--port", type=int, default=18090, help="Port for the desktop service.")
    parser.add_argument(
        "--runtime-root",
        default="",
        help="Optional runtime root directory override.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_root = Path(args.runtime_root) if args.runtime_root else None
    app = create_app(runtime_root=runtime_root)
    server = create_http_server(app=app, host=args.host, port=args.port)
    print(f"desktop service listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

