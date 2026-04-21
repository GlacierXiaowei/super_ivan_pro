# WeChat Automation Stage 1 Config

Saved at: 2026-04-22

## Locked first-stage test target

- target chat: `文件传输助手`
- trigger text: `START`
- reply sequence:
  - `TEST`
  - `第二条`

## Current assumptions

- sender filter remains empty for now
- first-stage backend remains `dry_run`
- first-stage validation target is still local replay plus later real chat validation

## Files added for this stage

- `glacier/wechat_automation/config/runtime.local.json`
- `glacier/wechat_automation/config/rules.local.json`
- `glacier/wechat_automation/config/events.local.sample.jsonl`
