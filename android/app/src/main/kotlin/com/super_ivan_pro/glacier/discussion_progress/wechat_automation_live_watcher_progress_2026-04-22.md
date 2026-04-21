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

## Real live validation completed on 2026-04-22

The live path has now been exercised against a real local
`wechat-decrypt` process on this machine.

What was verified:

1. `python main.py` started the local Web UI successfully.
2. `http://127.0.0.1:5678/api/history` returned live message data.
3. a real `START` message sent to `文件传输助手` appeared in history as:
   - `chat=filehelper`
   - `is_group=false`
   - `type=文本`
4. the bot initially skipped that event because the configured rule used the
   display name `文件传输助手` while the raw live chat id was `filehelper`.
5. after adding talker normalization for `filehelper -> 文件传输助手`, the same
   live path matched successfully and emitted:
   - `TEST`
   - `第二条`
   in dry-run mode.

## Next step

Move to the real sender stage in this order:

1. keep live watcher code unchanged unless a new talker alias issue appears
2. install and validate `wx4py`
3. switch from dry-run to a real sender only with explicit user approval before
   any WeChat send action
