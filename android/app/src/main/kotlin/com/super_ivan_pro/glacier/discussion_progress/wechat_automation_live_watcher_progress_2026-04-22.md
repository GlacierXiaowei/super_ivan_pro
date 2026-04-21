# WeChat Automation Live Watcher Progress

Saved at: 2026-04-22

## What changed

The module now supports a live watcher path for `wechat-decrypt`.

Integration approach:

- source: `wechat-decrypt` Web UI server
- endpoint: `GET /api/history`
- mode: polling with `since` timestamp

## Why this path was chosen

`wechat-decrypt` already maintains an in-memory recent message log and exposes it
through `/api/history`.

Using that endpoint is simpler than consuming raw SSE directly:

- easier to debug
- easier to replay mentally
- easier to recover from short disconnects
- enough for the current text-trigger milestone

## Added behavior

- runtime config now supports:
  - `watcher_backend`
  - `watcher_url`
  - `poll_interval_ms`
  - `history_limit`
- `run_bot.py` now supports `--live`
- `WechatDecryptHistoryWatcher` normalizes `wechat-decrypt` message payloads
- live events are mapped into the internal `MessageEvent` model

## Validation already completed

1. Full module compile passed.
2. Replay mode still works after the watcher changes.
3. A mocked `/api/history` payload was converted successfully into:
   - talker
   - sender
   - type
   - content
   - derived sequence key

## Current limitation

The live path is coded, but not yet exercised against a real local
`wechat-decrypt` process on this machine.

That means the next live validation still needs:

1. `wechat-decrypt` installed and running
2. local server reachable on `http://127.0.0.1:5678`
3. one real incoming test message to `文件传输助手`

## Next step

Run real integration in this order:

1. start `wechat-decrypt` Web UI
2. run the bot with `--live`
3. send `START` to `文件传输助手`
4. verify that the bot emits the two configured replies
