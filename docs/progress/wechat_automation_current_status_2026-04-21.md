# WeChat Automation Current Status

Saved at: 2026-04-21
Updated at: 2026-04-22

This file is the single handoff entry for the current experiment. Future work
should update this file first, then add narrower supporting notes only when
needed.

## Design pivot locked on 2026-04-22

The experiment direction has been narrowed again after the first real-send
attempt review.

New priority:

- first build an `armed_current_chat` mode
- when armed and the trigger matches, send immediately into the current chat
  input instead of searching for a named target first
- require manual start / stop
- support `max_triggers = N` or unlimited
- auto-disarm after the configured trigger count is exhausted

Why this changed:

- the current `wx4py` target-search send path is heavier than needed for the
  "detect then send immediately" goal
- `wx4py` may reconnect or restart WeChat while preparing accessibility state
- searching by target name adds latency and more failure points
- the user explicitly wants the next stage to optimize for fastest response in
  the already-open current chat

Focused design note:

- `docs/progress/wechat_automation_armed_current_chat_design_2026-04-22.md`

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
9. Saved plan and progress notes under `docs/progress` and
   `docs/plans`.
10. Added file-backed arm/disarm state under
    `config/arm_state.local.json`.
11. Gated the bot on armed state and trigger-budget exhaustion.
12. Added the `current_chat` sender backend for lightweight foreground-WeChat
    sending.
13. Added web-console arm/disarm controls and remaining-budget display.
14. Verified the current Python test suite at `15/15` passing after the armed
    current-chat stage.
15. Switched the local operator runtime to real `current_chat` sending.
16. Added an internal short retry loop so consecutive replies can re-acquire
    the chat input inside one send call instead of failing on the first
    transient miss.
17. Verified the current Python test suite at `18/18` passing after the
    consecutive-send retry fix.

## Existing commits

- `e9d9bb4` `feat(glacier): scaffold wechat automation experiment`
- `3c1e25b` `feat(glacier): add wechat-decrypt live watcher adapter`
- `6b7b8af` `feat(glacier): add armed current-chat state store`
- `ee23779` `feat(glacier): gate bot with armed trigger budget`
- `b44313e` `feat(glacier): add current chat sender`
- `a293c15` `feat(glacier): add arm controls to web console`
- `d954a95` `feat(glacier): switch local runtime to real current-chat sending`

## Current local rule/config state

Rules file:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/rules.local.json`
- talker: `filehelper`
- sender filter: empty
- type: `text`
- chat scope: `private`
- match mode: `regex`
- pattern: `START`
- cooldown: `800ms`
- replies: `TEST`, `第二条`

Runtime file:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/runtime.local.json`
- sender backend: `current_chat`
- `dry_run: false`
- `watcher_url: http://127.0.0.1:5678`
- `poll_interval_ms: 300`
- `history_limit: 200`
- `inter_message_delay_ms: 180`
- `retry_count: 1`
- `arm_state_path: config/arm_state.local.json`

Arm state file:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/arm_state.local.json`
- current mode: `armed_current_chat`
- current enabled: `true`
- current trigger budget: `1`
- current `triggers_sent: 0`
- current `remaining_triggers: 1`
- unlimited mode representation: `max_triggers = 0`

Important note:

- `scripts/run_bot.py --live` directly selects the live watcher adapter.
- The current `watcher_backend` field in `runtime.local.json` does not control
  that switch by itself.
- `runtime.local.json` is now a real-send runtime and must be treated as such.

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

## First real-send attempt result on 2026-04-22

User-approved target used for the probe:

- talker: `多姆斯利普🌙`
- message: `test`

Observed result:

- `wx4py` connected with `auto_connect=True`
- the local `wx4py` connection path can repair accessibility settings before
  sending
- that path may restart or relaunch WeChat if the underlying environment needs
  it
- the actual send failed before delivery because the group target could not be
  resolved reliably by name

Implication:

- named-target sending via `wx4py` remains useful as a later capability
- it is no longer the recommended next milestone
- the next milestone should optimize for current-chat sending instead

## Armed current-chat stage result on 2026-04-22

- added file-backed arm/disarm state under `config/arm_state.local.json`
- added `current_chat` sender backend for foreground-WeChat sending
- added trigger budget exhaustion and auto-disarm
- added web-console arm/disarm controls and remaining-budget display
- kept named-target `wx4py` sending as a separate later-stage capability

Verification completed in this stage:

- `python -m unittest discover tests -v`
- result: `15/15` passing
- verified focused sender guard:
  - non-WeChat foreground window -> blocked
  - WeChat foreground window with editable focus -> allowed in unit tests

## Manual current-chat probe result on 2026-04-22

User-approved real send probe was executed with a temporary runtime only:

- `sender_backend = current_chat`
- `dry_run = false`
- `runtime.local.json` remained unchanged

Observed probe sequence:

1. first send attempt was blocked with `foreground_not_wechat`
2. after focusing the WeChat main window, second attempt was blocked with
   `focused_control_not_editable`
3. after explicitly focusing the chat input control, the probe succeeded and
   sent payload `test`

Important current limitation:

- the current `current_chat` sender implementation requires the chat input to
  already be focused
- for the successful probe, a one-off helper step was used to focus the input
  before running `scripts/current_chat_probe.py`
- this means the current fast path is proven workable, but not yet fully
  zero-touch inside the WeChat window

## Auto-focus current-chat probe result on 2026-04-22

After commit `b1667bd` (`feat(glacier): auto-focus current chat input`), a new
user-approved real send probe was executed.

Probe conditions:

- temporary runtime only
- `sender_backend = current_chat`
- `dry_run = false`
- WeChat main window was brought to the foreground
- no manual click into the chat input was needed before sending

Observed result:

- `scripts/current_chat_probe.py --message test` completed successfully
- probe log: `current_chat_send ... payload=test`
- the current-chat path can now:
  - validate WeChat is foreground
  - auto-find the chat input when focus is not already editable
  - send the message without a separate helper focus step

## Operator boundary

- do not control or type into WeChat while the user is actively using the mouse
- before any future WeChat send attempt, explicitly ask the user first
- terminal-side work, log inspection, config edits, tests, and commits can
  continue without asking
- the local web console is allowed because it does not manipulate the WeChat
  desktop window

## Next execution order

1. Ask the user before any real `current_chat` probe.
2. If approved, re-run one controlled live trigger test in the already-open
   chat with no desktop interference.
3. Check whether both configured replies are sent in one batch without relying
   on outer retry.
4. If live sending still fails, inspect the new log output before changing more
   code.
5. Keep named-target sending and emoji matching as separate later stages.

## Commit boundary rule

- commit after each completed stage
- do not bundle live watcher validation and real sender integration into one
  commit
- the next commit after this note should capture the current-chat stability fix
  only

## Local runtime switch on 2026-04-22

After the dry-run chain was verified end to end against `filehelper`, the local
operator runtime was intentionally switched from safe simulation to real current
chat sending:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/runtime.local.json`
- `sender_backend = current_chat`
- `dry_run = false`

Operational implication:

- restarting `scripts/run_bot.py` with `config/runtime.local.json` now enables
  real message sending into the already-open current WeChat chat
- the bot still requires:
  - WeChat in the foreground
  - a matching rule
  - armed state enabled
- after this switch, any new live probe must be treated as a real send step

## Consecutive-send retry fix on 2026-04-22

Fresh failure evidence before the fix:

- live bot log showed `rule_match` for `文件传输助手 -> START`
- first real reply `TEST` only succeeded on outer retry attempt 2
- second reply `第二条` failed with `chat_input_not_found` on both outer retry
  attempts

Root-cause hypothesis used for the fix:

- the live watcher and matcher were already working
- the unstable point was inside `CurrentChatSender.send_text(...)`
- after the first message, WeChat could briefly expose a non-editable focused
  control or temporarily hide the editable chat input from a single lookup
- the sender only attempted one immediate input lookup per send, so a transient
  miss aborted the whole reply

Implemented fix:

- file:
  `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/core/current_chat_sender.py`
- added an internal `_resolve_chat_input(...)` path
- each send now performs up to `3` short lookup attempts with a `0.12s` delay
  before raising `chat_input_not_found`
- this retry stays inside one send call, so it is much cheaper than waiting for
  the outer dispatcher retry

Verification after the fix:

- targeted sender test:
  `python -m unittest android.app.src.main.kotlin.com.super_ivan_pro.glacier.wechat_automation.tests.test_current_chat_sender -v`
- result: `5/5` passing
- full suite:
  `python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -v`
- result: `18/18` passing

Current confidence boundary:

- unit-level reproduction for the consecutive-send miss is now covered
- a fresh live WeChat re-test is still pending and must be user-approved first,
  because it will type into the real foreground chat window

## Controlled live re-test result on 2026-04-22

User approval was obtained before touching the WeChat desktop window.

Observed runtime state before the re-test:

- `wechat-decrypt` live API was reachable on `http://127.0.0.1:5678`
- web console was running on `http://127.0.0.1:8090`
- `scripts/run_bot.py --runtime config/runtime.local.json --rules config/rules.local.json --live`
  was restarted and confirmed running
- `runtime.local.json` was still:
  - `sender_backend = current_chat`
  - `dry_run = false`
- `arm_state.local.json` was armed with:
  - `enabled = true`
  - `max_triggers = 1`
  - `remaining_triggers = 1`

Important probe note:

- a direct `scripts/current_chat_probe.py --message START` call returned a
  sender success log, but did not produce a visible new WeChat message in the
  current chat
- in this environment, that probe path is not yet a trustworthy live-verification
  tool by itself

Controlled trigger method used for the successful re-test:

- WeChat accessibility snapshot confirmed that the current selected chat was
  `文件传输助手`
- the trigger text `START` was then entered into the already-focused WeChat
  input box using native keyboard input and submitted with `Enter`

Observed successful chain:

- `wechat-decrypt` history returned a fresh `filehelper` event:
  - `14:48:38 START`
- bot log showed:
  - `14:48:37 rule_match rule=filehelper_start_sequence`
  - `14:48:41 current_chat_send ... payload=TEST`
  - `14:48:41 dispatch_success ... attempt=1 reply_index=1`
  - `14:48:45 current_chat_send ... payload=第二条`
  - `14:48:45 dispatch_success ... attempt=1 reply_index=2`
  - `14:48:45 armed_state_update enabled=False sent=1 remaining=0 reason=budget_exhausted`
- `wechat-decrypt` history then also showed the bot replies:
  - `14:48:41 TEST`
  - `14:48:45 第二条`

Result:

- the full live trigger -> current-chat send chain is now verified working for
  the `文件传输助手 / START / TEST + 第二条` experiment
- after the consecutive-send retry fix, both replies were sent on attempt `1`
  without relying on the outer dispatcher retry
- auto-disarm after one successful trigger also worked as designed

## Stability re-test result on 2026-04-22

After the first controlled live re-test succeeded, the user manually re-armed
the bot for one more stability pass.

Observed preconditions:

- `arm_state.local.json` was reset back to:
  - `enabled = true`
  - `triggers_sent = 0`
  - `remaining_triggers = 1`
- `scripts/run_bot.py --live` was still running
- the selected current chat was still `文件传输助手`

Controlled trigger method:

- native keyboard input was used again to send one more `START` into the
  already-open `文件传输助手` chat

Observed successful chain:

- bot log showed:
  - `15:01:35 event_received ... talker=文件传输助手 ... content=START`
  - `15:01:35 rule_match rule=filehelper_start_sequence`
  - `15:01:39 current_chat_send ... payload=TEST`
  - `15:01:39 dispatch_success ... attempt=1 reply_index=1`
  - `15:01:43 current_chat_send ... payload=第二条`
  - `15:01:43 dispatch_success ... attempt=1 reply_index=2`
  - `15:01:43 armed_state_update enabled=False sent=1 remaining=0 reason=budget_exhausted`
- `wechat-decrypt` history also showed:
  - `15:01:35 START`
  - `15:01:38 TEST`
  - `15:01:42 第二条`
- WeChat UI accessibility snapshot showed the same final visible message chain:
  - `START`
  - `TEST`
  - `第二条`

Result:

- the same trigger-reply chain succeeded again on a second controlled live run
- this reduces the chance that the earlier success was a one-off timing fluke
- for the current `文件传输助手 / START / TEST + 第二条 / max_triggers=1`
  setup, the workflow is now validated across two consecutive controlled live
  runs

## Related files

- build progress:
  `docs/progress/wechat_automation_build_progress_2026-04-21.md`
- live watcher progress:
  `docs/progress/wechat_automation_live_watcher_progress_2026-04-22.md`
- stage 1 config note:
  `docs/progress/wechat_automation_stage1_config_2026-04-22.md`
- execution plan:
  `docs/plans/wechat_automation_execution_plan_2026-04-21.md`
- armed current-chat design:
  `docs/progress/wechat_automation_armed_current_chat_design_2026-04-22.md`
