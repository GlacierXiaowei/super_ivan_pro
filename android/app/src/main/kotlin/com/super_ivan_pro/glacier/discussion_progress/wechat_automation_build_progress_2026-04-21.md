# WeChat Automation Build Progress

Saved at: 2026-04-21

## What was implemented

A standalone Python experiment module was created at:

`glacier/wechat_automation`

The module currently includes:

- config samples
- normalized message model
- runtime config loader
- rule matcher
- sequence dedupe
- cooldown gate
- serial dispatcher
- dry-run sender backend
- `wx4py` sender backend stub
- replay watcher adapter based on JSONL
- watcher probe script
- sender probe script
- replay-mode bot runner

## What is already working

The local replay loop is working end to end.

Validated behaviors:

- a text event matching the configured rule triggers replies
- multiple replies are sent serially
- a non-matching event is skipped correctly
- the dry-run sender backend logs without sending real messages
- the full module compiles under Python 3.10

## Verification commands already run

Syntax check:

```powershell
python -m compileall glacier/wechat_automation
```

Watcher probe:

```powershell
python glacier/wechat_automation/scripts/watcher_probe.py --events glacier/wechat_automation/config/events.sample.jsonl
```

Replay bot:

```powershell
python glacier/wechat_automation/scripts/run_bot.py `
  --runtime glacier/wechat_automation/config/runtime.example.json `
  --rules glacier/wechat_automation/config/rules.example.json `
  --events glacier/wechat_automation/config/events.sample.jsonl
```

Sender probe:

```powershell
python glacier/wechat_automation/scripts/sender_probe.py `
  --runtime glacier/wechat_automation/config/runtime.example.json `
  --talker "Test Group" `
  --message "sender probe hello" `
  --group
```

## Current limitation

The watcher is still replay-based.

That means:

- there is no live `wechat-decrypt` adapter yet
- there is no real event ingestion from WeChat yet
- `wx4py` is present as a backend path, but not validated on a real chat yet

## Immediate next step

The next implementation step should be:

1. wire a live watcher adapter to `wechat-decrypt`
2. confirm which fields are stable on this machine for:
   - talker
   - sender
   - type
   - content
3. switch sender validation from dry-run to a real `wx4py` test message on a safe test chat

## Result

The project now has a working core pipeline and is ready for live integration work.
