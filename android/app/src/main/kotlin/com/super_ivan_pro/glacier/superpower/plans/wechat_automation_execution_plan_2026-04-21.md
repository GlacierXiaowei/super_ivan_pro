# WeChat Automation Execution Plan

Saved under `glacier/superpower/plans` to keep the working plan close to the
implementation.

## Locked first milestone

- one target chat
- text trigger only
- exact match only
- one rule file
- one runtime file
- sequential fixed replies
- dedupe by message sequence
- cooldown by rule and sender context
- default dry-run mode

## Implementation order

1. Build standalone Python module under `glacier/wechat_automation`.
2. Validate replay watcher normalization with sample JSONL events.
3. Validate sender probe in dry-run mode.
4. Wire bot pipeline: load config -> match -> dedupe -> dispatch.
5. Replace replay watcher with live `wechat-decrypt` adapter.
6. Replace dry-run sender with `wx4py` sender on a test chat.

## Exit criteria for milestone 1

- running the bot with sample events triggers the expected reply batch
- duplicate sample events do not trigger duplicate sends
- cooldown suppresses rapid retriggers
- sender probe can switch from dry-run to a real backend without code changes

## Deferred work

- sender filter hardening
- live `wechat-decrypt` adapter
- emoji-specific matching
- multi-rule orchestration
- GUI or Flutter integration
