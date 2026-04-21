# WeChat Automation

This directory contains the standalone experiment module for the WeChat 4.1.7
automation workflow discussed in `glacier/discussion_progress`.

## Current scope

The first implementation intentionally keeps the live integrations thin:

- rule loading
- message normalization
- rule matching
- dedupe and cooldown control
- serial reply dispatching
- dry-run and `wx4py` sender backends
- replay-based watcher probe for local validation
- `wechat-decrypt` `/api/history` polling watcher

Live watcher integration with `wechat-decrypt` is the next step after the local
pipeline is validated end to end.

## Layout

```text
wechat_automation/
  config/
    runtime.example.json
    rules.example.json
    events.sample.jsonl
  core/
    bot.py
    config_loader.py
    dedupe.py
    dispatcher.py
    logger.py
    matcher.py
    models.py
    sender_adapter.py
    watcher_adapter.py
  scripts/
    run_bot.py
    sender_probe.py
    watcher_probe.py
  logs/
```

## Supported message flow

1. A watcher yields a normalized `MessageEvent`.
2. The bot evaluates all enabled rules.
3. Matching rules are filtered through dedupe and cooldown gates.
4. Replies are sent serially by the dispatcher.

## Quick start

Dry-run the sample event stream:

```powershell
python scripts/run_bot.py `
  --runtime config/runtime.example.json `
  --rules config/rules.example.json `
  --events config/events.sample.jsonl
```

Probe watcher normalization only:

```powershell
python scripts/watcher_probe.py --events config/events.sample.jsonl
```

Run against a live `wechat-decrypt` Web UI instance:

```powershell
python scripts/run_bot.py `
  --runtime config/runtime.local.json `
  --rules config/rules.local.json `
  --live
```

Probe sender backend:

```powershell
python scripts/sender_probe.py `
  --runtime config/runtime.example.json `
  --talker "Test Group" `
  --message "hello from sender probe" `
  --group
```

## Notes

- Default mode is dry-run. It will not send real messages.
- The `wx4py` backend is optional and requires `wx4py` to be installed locally.
- The current watcher is replay-based on purpose. It makes the core logic
  testable before wiring in a live event source.
- The live watcher expects `wechat-decrypt` to be running locally and serving
  `/api/history` on `http://127.0.0.1:5678`.
