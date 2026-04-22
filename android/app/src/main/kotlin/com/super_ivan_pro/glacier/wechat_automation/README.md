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
- local web console for rule editing and recent event inspection

The live watcher is now validated. The current operator-facing next step is a
local web console for testing different listener targets without hand-editing
the JSON files.

## Armed current-chat mode

This mode is optimized for fastest local response:

- the operator manually opens the target chat first
- the operator manually arms the experiment from the local web console
- the bot keeps listening through `wechat-decrypt`
- when the trigger matches, replies are sent into the current WeChat chat only
- the run auto-disarms after the configured trigger budget is exhausted

Important safety boundary:

- this mode must not send unless the foreground window is WeChat
- this mode must not send unless the focused control is editable
- any real send still requires explicit user approval before the manual probe step

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
    web_console.py
  logs/
  web/
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

Install the optional real sender dependency:

```powershell
python -m pip install wx4py==0.2.1
```

Safe import probe without sending:

```powershell
python -c "from wx4py import WeChatClient; print(WeChatClient.__name__)"
```

Run the local web console:

```powershell
python scripts/web_console.py `
  --runtime config/runtime.local.json `
  --rules config/rules.local.json `
  --host 127.0.0.1 `
  --port 8090
```

Then open:

```text
http://127.0.0.1:8090
```

What the console does:

- shows recent normalized live events
- lets the operator click one event to prefill a rule
- lets the operator save the rule back to `config/rules.local.json`
- lets the operator arm or disarm the current experiment
- does not send real messages by itself

## Notes

- Default mode is dry-run. It will not send real messages.
- The `wx4py` backend is optional and requires `wx4py` to be installed locally.
- Installing `wx4py` only prepares the real sender path. It does not send any
  WeChat message by itself.
- The `current_chat` backend is the preferred fast path for this experiment.
  It validates the frontmost window and focused input before sending.
- The current watcher is replay-based on purpose. It makes the core logic
  testable before wiring in a live event source.
- The live watcher expects `wechat-decrypt` to be running locally and serving
  `/api/history` on `http://127.0.0.1:5678`.
- The web console is safe to use while the user works normally because it does
  not control the WeChat desktop window.
