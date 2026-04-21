# WeChat Automation Current Status

Saved at: 2026-04-21
Updated at: 2026-04-22

This file is the single handoff entry for the current experiment. Future work
should update this file first, then add narrower supporting notes only when
needed.

## Locked stage 1 goal

- target chat: `文件传输助手`
- trigger text: `START`
- replies:
  1. `TEST`
  2. `第二条`
- speed target: trigger as soon as the watcher sees the incoming message
- current safety mode: dry-run sender first, real sender later

## Architecture locked for the experiment

- listener: `wechat-decrypt` Web UI history API
- current live ingestion path: `GET /api/history`
- sending path for current validation: dry-run sender
- planned real sender path: `wx4py`
- implementation location:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation`

This is intentionally not integrated into Flutter yet.

## Completed work

1. Built the standalone Python module and config structure.
2. Verified replay-mode end-to-end rule matching and serial reply dispatch.
3. Added a live watcher adapter for `wechat-decrypt` history polling.
4. Verified live dry-run against a real local `wechat-decrypt` process and a
   real `START` message in `文件传输助手`.
5. Fixed live talker normalization for `filehelper -> 文件传输助手`.
6. Built a local web console for recent-event inspection and rule editing.
7. Installed `wx4py==0.2.1` into the active Python 3.10 environment.
8. Verified that the real sender backend can be imported and created safely
   without sending a WeChat message.
9. Saved plan and progress notes under `glacier/discussion_progress` and
   `glacier/superpower/plans`.

## Existing commits

- `e9d9bb4` `feat(glacier): scaffold wechat automation experiment`
- `3c1e25b` `feat(glacier): add wechat-decrypt live watcher adapter`

## Current local rule/config state

Rules file:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/rules.local.json`
- talker: `文件传输助手`
- sender filter: empty
- type: `text`
- match mode: `exact`
- pattern: `START`
- cooldown: `800ms`
- replies: `TEST`, `第二条`

Runtime file:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/runtime.local.json`
- sender backend: `dry_run`
- `dry_run: true`
- `watcher_url: http://127.0.0.1:5678`
- `poll_interval_ms: 300`
- `history_limit: 200`

Important note:

- `scripts/run_bot.py --live` directly selects the live watcher adapter.
- The current `watcher_backend` field in `runtime.local.json` does not control
  that switch by itself.
- `runtime.local.json` is intentionally still in `dry_run` mode even though
  `wx4py` is now installed locally.

## Machine status verified on 2026-04-22

- Windows WeChat process is running locally as `Weixin`
- one process has main window title `微信`
- temp clone exists at `D:\flutter_app\_tmp\wechat-decrypt`
- `wechat-decrypt` was started successfully from the temp clone
- `http://127.0.0.1:5678/api/history` returned live local history data
- a real `START` message sent to `文件传输助手` was captured as:
  - `chat=filehelper`
  - `is_group=false`
  - `type=文本`
- the bot matched the rule and emitted the configured two-message dry-run batch

## Root cause resolved in live validation

The first real live run reached the bot, but did not match because
`wechat-decrypt` reports `文件传输助手` as `filehelper`.

That meant:

- live ingestion worked
- message classification worked
- rule matching failed only on talker alias mismatch

The watcher now normalizes `filehelper` into display talker
`文件传输助手`, so the existing local rule file can stay unchanged.

## Verification evidence from 2026-04-22

Real live event observed:

- `timestamp=1776787441`
- raw chat id: `filehelper`
- normalized talker: `文件传输助手`
- content: `START`

Bot log result:

- `rule_match rule=filehelper_start_sequence`
- `dry_run_send payload=TEST`
- `dry_run_send payload=第二条`

Web console verification:

- local server started on `http://127.0.0.1:8090`
- `GET /`, `GET /api/rules`, and `GET /api/events` all returned `200`
- browser page rendered both:
  - recent live events
  - current local rule
- clicking an event in the browser correctly filled:
  - talker
  - sender
  - chat scope
  - type
  - trigger pattern

Wx4py install verification:

- `python -m pip index versions wx4py` showed `0.2.1` as the latest available
  version on this machine
- `python -m pip install wx4py==0.2.1` completed successfully
- `python -m pip show wx4py` confirmed install location under Python 3.10
- `from wx4py import WeChatClient` import probe passed
- local sender creation probe passed:
  - `create_sender(RuntimeConfig(sender_backend='wx4py', dry_run=False), ...)`
  - result: `Wx4pySender`
- no real WeChat send was executed in this verification stage

## Operator boundary

- do not control or type into WeChat while the user is actively using the mouse
- before any future WeChat send attempt, explicitly ask the user first
- terminal-side work, log inspection, config edits, tests, and commits can
  continue without asking
- the local web console is allowed because it does not manipulate the WeChat
  desktop window

## Next execution order

1. Use the web console to save the exact listener target that should be used for
   the first real-send test.
2. Keep the real sender stage separate from the install-prep stage.
3. Before the first real-send test, ask the user explicitly because that step
   will interact with WeChat.
4. Prepare a temporary non-dry-run runtime config for the first real-send test.
5. Run one controlled sender probe to a user-approved target.
6. Only after that result is confirmed, decide whether to switch the main local
   runtime from `dry_run` to `wx4py`.

## Commit boundary rule

- commit after each completed stage
- do not bundle live watcher validation and real sender integration into one
  commit
- the next commit after this one should target the real sender stage only

## Related files

- build progress:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_build_progress_2026-04-21.md`
- live watcher progress:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_live_watcher_progress_2026-04-22.md`
- stage 1 config note:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_stage1_config_2026-04-22.md`
- execution plan:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/superpower/plans/wechat_automation_execution_plan_2026-04-21.md`
