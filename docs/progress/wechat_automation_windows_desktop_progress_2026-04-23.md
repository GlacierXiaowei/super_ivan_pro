# WeChat Automation Windows Desktop Progress

Saved at: 2026-04-23
Status: phase 1 implementation completed, Windows packaging blocked by local toolchain

## 今天已经完成的内容

### 1. 实施计划已落地

已写入本地计划文档：

- `docs/plans/wechat_automation_windows_desktop_phase1_plan_2026-04-23.md`

已提交：

- `6d118e0` `docs(glacier): add windows desktop phase1 plan`

### 2. Flutter Windows 桌面壳基础已建立

当前已经完成：

1. 修复并替换了默认损坏的 `lib/main.dart`
2. 建立了新的桌面应用入口 `SuperIvanDesktopApp`
3. 建立了单页控制台基础主题和 Windows runner 骨架
4. 建立了桌面控制台第一版 UI 分区：
   - 服务状态
   - 监听对象
   - 规则配置
   - 模式配置
   - 日志与事件
5. 建立了最小桌面模型、假服务、控制器和 widget 测试

已提交：

- `51b36ba` `feat(glacier): scaffold windows desktop shell`
- `cc17c65` `feat(glacier): add desktop console ui shell`

### 3. Python 桌面服务骨架已建立

当前已经完成：

1. 新增 `desktop_service` 包
2. 新增 runtime root 解析逻辑
3. 支持 `%LOCALAPPDATA%\\SuperIvanPro\\wechat_automation`
4. 支持环境变量或参数 override
5. 新增本地 JSON 状态文件 `config/desktop_state.json`
6. 新增最小 API：
   - `GET /status`
   - `POST /targets/active`
7. 新增本地服务启动脚本：
   - `scripts/desktop_service.py`

已提交：

- `7abc8ec` `feat(glacier): add desktop service api skeleton`

### 4. Flutter 已接入 live local service

当前已经完成：

1. 新增 `HttpDesktopService`
2. 新增 `WindowsServiceLauncher`
3. Flutter 默认启动路径已切到本地 HTTP service
4. 服务状态区已增加：
   - `启动服务`
   - `停止服务`
5. 控制器已支持：
   - `startServices()`
   - `stopServices()`
   - busy 状态切换
6. Python desktop service 已扩展：
   - `POST /mode`
   - `GET /status` 返回 `service_state = running`

已提交：

- `f8df5a5` `feat(glacier): wire desktop console to local service`

### 5. 桌面控制台已接入可编辑 live 配置

当前这一轮新增完成：

1. 监听对象区现在可以直接编辑并保存：
   - 最近会话快捷选择
   - 手动输入监听对象
   - 群聊开关
2. 规则配置区现在可以直接编辑并保存：
   - 触发文本
   - 多条回复
   - 冷却毫秒
   - 最大触发次数
3. 状态区现在可以直接控制：
   - 启动服务
   - 停止服务
   - Arm
   - Disarm
4. Flutter controller 已支持：
   - `saveTarget(...)`
   - `saveRule(...)`
   - `setArmed(...)`
   - `setMode(...)`
   - `startServices()`
   - `stopServices()`
5. Python desktop service 已支持：
   - `/services/start`
   - `/services/stop`
   - `/targets/active`
   - `/rules`
   - `/arm-state`
   - `/mode`
   - `/events/recent`
6. Desktop runtime 现在会在独立目录下自动播种：
   - `runtime.local.json`
   - `rules.local.json`
   - `arm_state.local.json`
7. `/status` 现在会返回桌面端真正需要的完整状态：
   - 当前 service state
   - armed / max_triggers / remaining_triggers
   - active target
   - recent chats / recent events
   - 当前规则 pattern / replies / cooldown / match_mode

## 已验证结果

### Flutter

已执行：

```bash
flutter test
flutter analyze
```

结果：

1. `flutter test` 通过
2. `flutter analyze` 无报错
3. 本轮新增测试已覆盖：
   - launcher 命令生成
   - HTTP status / mode 请求
   - controller 启停 busy 状态
   - HTTP rule / arm-state 请求
   - `talker_name -> chatName` 最近事件解析
   - `/status` 完整规则字段解析

### Python

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_desktop_service_*.py" -v
```

结果：

1. `7/7` 通过

### 本地服务烟雾验证

已执行：

```bash
python android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py --host 127.0.0.1 --port 18091 --runtime-root <temp>
GET http://127.0.0.1:18091/status
```

结果：

1. 脚本可正常启动本地 HTTP server
2. `/status` 返回了有效 JSON
3. `POST /mode` 可切换到 `rapid`
4. `POST /arm-state` 可更新 `armed` 和 `max_triggers`
5. `/status` 现已回传完整规则字段：
   - `replies`
   - `cooldown_ms`
   - `match_mode`

### Windows 打包验证

已执行：

```bash
flutter build windows
flutter doctor -v
```

结果：

1. Flutter 代码侧没有新的 analyze / test 问题
2. 当前机器的 Windows 打包被本机 Visual Studio 组件缺失阻塞
3. `2026-04-23` 本机 `flutter doctor -v` 明确提示缺少：
   - `Desktop development with C++`
   - `MSVC v142 - VS 2019 C++ x64/x86 build tools`
   - `C++ CMake tools for Windows`
   - `Windows SDK`
4. 因为当前 Codex 进程不是管理员权限，未在本轮直接改动系统级 Visual Studio 安装

## 当前仍未完成

当前仍未完成的关键点：

1. 还没有把 `wechat-decrypt` 和现有 bot 进程做完整托管与打包分发
2. 还没有做 bundled python / bundled runtime 资源
3. 当前机器还不能直接 `flutter build windows`，需要先补齐 Visual Studio Windows C++ 工具链

## 建议的下一执行顺序

下一步建议按这个顺序推进：

1. 在本机 Visual Studio Installer 中补齐 Windows C++ workload
2. 重新执行 `flutter build windows`
3. 用打包出的桌面端做真实联调
4. 下一阶段再推进 bundled runtime 与完整 bot 进程托管

## 重要边界

本轮实现没有动这些用户本地实验文件：

1. `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/arm_state.local.json`
2. `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/rules.local.json`

本轮也没有覆盖用户手改过的设计文档内容。

---

## 2026-04-30 追加进展

### 本轮定位到的真实现象

1. “监听指定窗口后发送关键词没成功”在这一轮不是 matcher 再次失效。
2. 当时桌面 HTTP 服务是活着的，但它内部托管的 `run_bot.py` 已经不在运行。
3. 在这种状态下，页面仍然能显示历史消息和当前配置，但不会继续消费新消息，因此发出 `START` 不会触发回复。

### 本轮新增修复

1. 已补 watcher 冷启动保护：
   - `WechatDecryptHistoryWatcher` 首次进入 live 轮询时，先把 `since_timestamp` 预热到“当前最新消息”。
   - 这样重新启动 bot 时不会把启动前已经存在的旧消息重新当作新消息处理。
2. 已新增回归测试覆盖这个场景：
   - 冷启动时跳过旧历史
   - 只处理启动之后到达的新消息

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_live_watcher_cold_start.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
```

结果：

1. 新增冷启动回归测试先红后绿。
2. 当前 Python 测试总计 `28/28` 通过。

### 当前测试注意事项

1. 现在如果页面上 `服务状态` 显示 `stopped`，说明 live bot 没在运行；这时仅仅保存监听对象和规则还不够，仍需要显式启动 bot。
2. 因为冷启动回放旧消息的问题已经修掉，后续重新启动 live bot 时，误扫旧 `START` 的风险已显著下降。

---

## 2026-04-30 极速模式修正

### 本轮定位到的真实现象

1. 真实发送已经成功，但从 `rule_match` 到第一条 `current_chat_send` 大约有 3-4 秒。
2. 当时页面状态显示 `mode = rapid`，但 runtime 仍是：
   - `poll_interval_ms = 300`
   - `inter_message_delay_ms = 180`
3. 这说明之前的“极速模式”只保存到了桌面状态，没有真正写入 live bot 使用的 runtime。
4. 当前 `current_chat` 发送还走 wx4py 默认 `send_text_via_input`，里面包含多段点击、清空、粘贴和发送等待。

### 本轮新增修复

1. `/mode` 现在会写入 runtime profile：
   - 普通模式：`poll_interval_ms = 300`、`history_limit = 200`、`inter_message_delay_ms = 180`、`retry_count = 1`
   - 极速模式：`poll_interval_ms = 20`、`history_limit = 50`、`inter_message_delay_ms = 0`、`retry_count = 0`
2. `/mode` 在 bot 正在运行时会自动重启 bot，让新 runtime 立即生效。
3. `run_bot.py` 启动前会按当前桌面模式重新套用 runtime profile。
4. 极速模式下 `current_chat` 发送会启用快速剪贴板驱动：
   - 要求当前焦点必须已经在微信聊天输入框内
   - 直接执行 `Ctrl+A`、`Delete`、写剪贴板、`Ctrl+V`、`Enter`
   - 不再走 wx4py 默认慢速输入路径

### 本轮验证

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter test test/desktop_console_controller_test.dart test/http_desktop_service_test.dart test/desktop_console_page_test.dart
```

结果：

1. Python 测试总计 `31/31` 通过。
2. Flutter 目标测试通过。

### 后续测试注意事项

1. 这次改的是 Python desktop service 和 bot runtime；如果桌面服务已经在运行，需要重启桌面服务或重新点一次模式切换，才能加载新代码。
2. 极速模式要求微信当前焦点已经在目标聊天输入框，否则会快速失败为 `chat_input_not_focused`，不会再花时间搜索输入框。

---

## 2026-05-06 桌面端测试闭环简化

### 本轮目标

这次主要解决桌面端真实测试太分散的问题：

1. 尽量让桌面 app 自己拉起本地 Python 服务，不再要求手动开命令行启动 `desktop_service.py`。
2. 在 Flutter UI 中直接展示运行日志，方便判断是否触发、是否匹配、是否发送失败。
3. 在 UI 中提供显式“重启服务”按钮，用于切换模式或配置后手动重启 bot。

### 本轮新增实现

1. Flutter app 启动器现在优先解析 `wechat_automation` 服务根目录：
   - 开发环境：从仓库内 `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation` 启动。
   - 打包环境：从 Flutter assets 中的同一套 Python 服务文件启动。
   - 仍可通过 `SUPER_IVAN_WECHAT_AUTOMATION_ROOT` 指定自定义服务目录。
2. `pubspec.yaml` 已加入 Python 服务所需 assets：
   - `config/*.example.json`
   - `core/*.py`
   - `desktop_service/*.py`
   - `scripts/desktop_service.py`
   - `scripts/run_bot.py`
3. Python desktop service 新增：
   - `POST /services/restart`
   - `GET /logs/recent?limit=...`
   - `GET /status` 返回 `recent_logs`
4. Flutter UI 新增：
   - “重启服务”按钮。
   - “运行日志”面板，显示 `wechat_automation.log`、`live_bot/stdout.log`、`live_bot/stderr.log` 的最近日志。
   - 页面每 1 秒自动刷新一次状态和日志，减少手动刷新。

### 当前边界

1. 本轮已经内嵌并托管的是我们自己的 `desktop_service.py` 和 `run_bot.py`。
2. `wechat-decrypt` 这一层目前不在本仓库内，当前 app 还不能自动启动它。
3. 如果 `wechat-decrypt` 没运行，日志面板会更容易看到连接失败或无新事件，但监听源仍需要下一步单独托管。
4. 当前仍依赖本机已有 Python 和相关 Python 依赖；还没有做 bundled Python runtime。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
flutter test test/desktop_console_controller_test.dart test/http_desktop_service_test.dart test/desktop_console_page_test.dart test/windows_service_launcher_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. Python desktop service API 目标测试 `8/8` 通过。
2. Flutter 桌面控制台目标测试 `10/10` 通过。
3. Python 全量测试 `33/33` 通过。
4. Flutter analyze 无问题。
5. Flutter 全量测试通过。
6. Windows 打包成功生成 `build/windows/x64/runner/Release/super_ivan_pro.exe`。
7. 打包产物中已确认存在 Python 服务 assets：
   - `scripts/desktop_service.py`
   - `core/bot.py`
   - `config/runtime.example.json`

### 下一步建议

1. 重新打包 Windows 桌面 app。
2. 打开打包后的 app，点击“启动服务”。
3. 如果模式或配置切换后状态异常，点击“重启服务”。
4. 在“运行日志”区域查看是否出现 `event_received`、`rule_match`、`dispatch_success` 或 `chat_input_not_focused`。
5. 如果下一步要真正做到单 app 全托管，还需要把 `wechat-decrypt` 的源码路径、启动命令和依赖一起纳入 launcher。

---

## 2026-05-06 打包 app 启动服务但消息不更新修复

### 本轮定位到的真实原因

1. 打包后的 Flutter app 已经可以启动 `desktop_service.py`。
2. 但是点击“启动服务”后，`run_bot.py` 依赖的消息源 `http://127.0.0.1:5678/api/history` 没有运行。
3. 结果是 live bot 在启动初期因为 `ConnectionRefusedError` 退出，页面只能看到 `stopped` 或无法更新消息列表。
4. 根因不是 Flutter UI 没发出启动请求，而是 `wechat-decrypt` 这一层之前没有被桌面 app 托管。

### 本轮新增修复

1. `RuntimeConfig` 新增 `wechat_decrypt_root`，用于配置本机 `wechat-decrypt` 源码目录。
2. Python desktop service 新增 `WechatDecryptProcessManager`：
   - 如果 runtime 中配置了 `wechat_decrypt_root`，启动 bot 前先检查 `watcher_url`。
   - 如果消息源不可用，先在 `wechat_decrypt_root` 下执行 `python main.py`。
   - 等待消息源健康后再启动 `run_bot.py`。
3. `POST /services/stop` 会同时停止由 desktop service 拉起的 live bot 和 `wechat-decrypt`。
4. `GET /status` 新增：
   - `watcher_state`
   - `watcher_error`
5. Flutter 控制台新增“消息源”状态展示，并在消息源异常时显示具体错误。
6. 日志面板现在会读取：
   - `logs/live_bot/stdout.log`
   - `logs/live_bot/stderr.log`
   - `logs/wechat_decrypt/stdout.log`
   - `logs/wechat_decrypt/stderr.log`

### 本机配置要求

打包 app 的运行时配置位于：

```text
%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json
```

本机当前需要写入：

```json
"wechat_decrypt_root": "D:\\flutter_app\\_tmp\\wechat-decrypt"
```

如果这个路径不存在、缺少 `main.py`，或者 `wechat-decrypt` 自身依赖缺失，desktop service 仍然无法托管消息源。

### 本轮运行时验证

已确认：

1. `desktop_service.py` 从打包产物 assets 启动，监听 `127.0.0.1:18090`。
2. `wechat-decrypt` 已由 desktop service 拉起，`http://127.0.0.1:5678/api/history?limit=1` 可返回消息。
3. `run_bot.py` 已启动。
4. `/status` 返回：
   - `service_state = running`
   - `watcher_state = running`
   - `watcher_error = ""`
   - `armed = false`
   - `mode = rapid`
5. `recent_events` 已能显示真实消息记录。

### 本轮代码验证

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. Python 测试总计 `35/35` 通过。
2. Flutter analyze 无问题。
3. Flutter 全量测试通过。
4. Windows 打包成功生成 `build/windows/x64/runner/Release/super_ivan_pro.exe`。

### 当前边界

1. 这次解决的是“app 只启动 bot，但没有启动消息源”的问题。
2. 仍然依赖本机 Python、`wechat-decrypt` 源码目录和其 Python 依赖，不是完全独立的单 exe。
3. 自动发送仍受 armed 状态控制；测试期间默认应先保持 `armed=false`，避免误触发。
4. 表情包识别仍取决于 `wechat-decrypt` 能否正确解析 type=47 / emoji 资源，目前日志里仍可能出现 emoji 查询失败，这不是本轮修复范围。

---

## 2026-05-06 桌面端启动链路复查与按钮等待优化

### 本轮复查结论

1. “只打开 app”当前能懒启动的是本地 HTTP wrapper：
   - Flutter 访问 `127.0.0.1:18090/status` 失败时，会拉起 `scripts/desktop_service.py`。
   - 这一步只保证 desktop service HTTP API 可用。
2. `wechat-decrypt` 和 `run_bot.py` 不会在 app 打开时自动启动：
   - 它们仍由 `POST /services/start` 或 `POST /services/restart` 触发。
   - 如果 runtime 配置了 `wechat_decrypt_root` 且 watcher 不健康，desktop service 会先启动 `wechat-decrypt`，再启动 `run_bot.py`。
3. 安全边界仍成立：
   - `启动服务`、`重启服务`、`切换模式`、`保存对象`、`保存规则` 本身不会直接发送消息。
   - 真正发送仍要求后续新消息匹配规则，并且 `arm_state.enabled = true`。
   - 本轮运行态检查时 `/status` 显示 `armed=false`。

### 本轮修复

1. Flutter `DesktopService` 写操作现在返回 `DesktopSnapshot`：
   - `saveTarget`
   - `saveRule`
   - `saveArmState`
   - `saveMode`
   - `startServices`
   - `restartServices`
   - `stopServices`
2. Flutter controller 不再在每次按钮操作后额外调用一次 `GET /status`。
3. `HttpDesktopService` 不再在每个 POST 前预先 `GET /status`：
   - 现在直接 POST。
   - 只有连接失败时才启动本地 desktop service 并重试。
4. Python POST 状态接口返回完整状态快照，但不强制刷新 watcher 历史：
   - 避免按钮动作被同步 watcher 拉取拖慢。
   - 消息和日志仍由页面 1 秒轮询刷新。
5. `POST /rules` 现在也返回完整状态，并保留 `rules` 字段，避免半截 payload 造成前端解析陷阱。
6. 模式切换控件在 busy 状态下会禁用，避免与其他按钮操作交错。
7. 最近会话现在回传真实结构：
   - `label`
   - `talker`
   - `is_group`
   点击最近会话保存监听对象时，不再从显示文本猜 `talker` 和群聊状态。

### 文档新增

1. 新增/重写 `README.md`：
   - 当前桌面链路
   - 本机运行前提
   - 安全边界
   - 常用验证命令
   - 关键代码位置
2. 新增 `AGENTS.md`：
   - 后续 agent 工作边界
   - 微信发送安全规则
   - runtime 模型
   - 验证命令

### 本轮验证

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. Python 测试总计 `36/36` 通过。
2. Flutter analyze 无问题。
3. Flutter 全量测试通过。
4. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`

### 本轮实际冷启动验证

已执行：

1. 停止当前监听 `127.0.0.1:18090` 的 Python desktop service 进程。
2. 确认端口不再监听。
3. 启动打包产物 `build/windows/x64/runner/Release/super_ivan_pro.exe`。
4. 再次请求 `GET http://127.0.0.1:18090/status`。

结果：

1. app 成功从 Flutter assets 拉起 `desktop_service.py`。
2. 新 desktop service 监听进程命令行为：
   - `python .../data/flutter_assets/.../wechat_automation/scripts/desktop_service.py --host 127.0.0.1 --port 18090`
3. `/status` 返回：
   - `service_state = stopped`
   - `watcher_state = running`
   - `watcher_error = ""`
   - `armed = false`
   - `mode = rapid`
4. 结论：只打开 app 能自动恢复本地 HTTP wrapper；不会自动启动 `run_bot.py`，也不会 armed 或发送消息。

### 当前边界

1. 本轮没有改成“打开 app 自动启动 bot”，因为这会扩大运行时副作用；当前仍需要点击“启动服务”才会启动完整托管链路。
2. 本轮没有操作微信窗口，也没有 armed 或触发真实发送。
3. 本轮没有修改本地测试配置文件作为交付内容：
   - `arm_state.local.json`
   - `rules.local.json`
   - `runtime.local.json`
4. `wechat-decrypt` 仍依赖本机源码目录和 Python 依赖，不是 bundled Python/runtime。

---

## 2026-05-06 极速链路速度复查

### 本轮只读复查边界

1. 当前本地仓库位于 `main`，且与 `origin/main` 同步。
2. 复查时 `GET http://127.0.0.1:18090/status` 返回：
   - `service_state = running`
   - `watcher_state = running`
   - `watcher_error = ""`
   - `armed = true`
   - `mode = rapid`
3. 因为 `armed = true`，本轮没有做会触发真实发送的主动联调，只做源码、配置和日志层面的速度分析。

### 当前极速链路结论

1. 当前 rapid runtime 已经生效：
   - `poll_interval_ms = 20`
   - `history_limit = 50`
   - `inter_message_delay_ms = 0`
   - `retry_count = 0`
   - `current_chat_fast_send = true`
2. `wechat-decrypt` 的核心消息发现链路是：
   - 每 `30ms` 轮询 WAL/DB 的 `mtime`
   - 发现变化后执行 session DB 全量解密和 WAL patch
   - 查询会话状态后追加到 `messages_log`
   - 通过 `/api/history` 和 `/stream` 暴露给外部
3. 当前日志中常见 `wechat-decrypt` 处理耗时约为 `30-60ms`，其中解密和查询是主要成本。
4. 当前 bot 侧每 `20ms` 请求一次 `/api/history?since=...&limit=50`，拿到事件后再做 normalize、match、dispatch。
5. `current_chat_fast_send = true` 时，发送路径已经是剪贴板快速发送：
   - 要求微信输入框已经获得焦点
   - 直接 `Ctrl+A` / `Delete` / `Ctrl+V` / `Enter`
   - 不再走 wx4py 的慢速输入框查找路径

### 关于“只收某个人消息是否更快”

1. `wechat-decrypt` 的 `/api/history?chat=...` 只是在已经生成的 `messages_log` 上做内存过滤。
2. 这不能减少 `wechat-decrypt` 的 WAL/DB 检测、解密和查询成本，因此不会显著缩短消息源发现延迟。
3. 但它可以减少 bot 侧拿到的无关事件，降低 normalize/match/log 噪音，也能降低高消息量时 backlog 风险。

### 建议的第二步优化方向

优先做小改动、安全收益：

1. 让 bot 的 live poll 支持 active target chat 过滤：
   - watcher 请求 `/api/history` 时带 `chat=<active_talker>`
   - bot 侧更早跳过非目标事件
   - 预期收益主要是减少干扰和积压，不是突破消息源解密延迟
2. 在日志里加入毫秒级耗时标记：
   - 记录 `event_received_ms`
   - 记录 `rule_match_ms`
   - 记录 `dispatch_success_ms`
   - 后续真实测试可以明确区分“消息源慢”“bot 轮询慢”“发送慢”

更大改动、后续再评估：

1. 改为消费 `wechat-decrypt` 已有 `/stream` SSE，而不是 bot 继续 HTTP 轮询。
2. 预期可以省掉最多约 `20ms` 的 bot 轮询等待和 HTTP 轮询开销。
3. 但 SSE 需要处理断线重连、冷启动跳旧消息、去重和测试覆盖，改动风险高于目标 chat 过滤。

### 本轮已实施的小优化

已先实现低风险的 active target chat 过滤：

1. `WechatDecryptHistoryWatcher` 新增可选 `chat_filter`。
2. 冷启动预热请求和 live 轮询请求都会在配置了过滤对象时带上：
   - `/api/history?limit=1&chat=<talker>`
   - `/api/history?since=<timestamp>&limit=<limit>&chat=<talker>`
3. `run_bot.py` 会从 enabled rules 中推导 live chat filter：
   - 如果所有 enabled rules 都指向同一个非空 `talker`，启用过滤。
   - 如果没有 enabled rule、存在空 talker、或多个 enabled rules 指向不同 talker，则不启用过滤，避免误丢消息。
4. 这不会改变 matcher 的最终安全判断；即使消息源返回了额外消息，原有 `talker/sender/type/pattern` 规则仍然继续生效。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_live_watcher_cold_start.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_run_bot_live_filter.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. 新增 watcher chat filter 回归测试先红后绿。
2. 新增 `run_bot.py` live filter 推导测试先红后绿。
3. Python 全量测试总计 `40/40` 通过。
4. `flutter analyze` 无问题。
5. `flutter test` 通过。
6. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`
7. 已确认打包产物中的 Python assets 包含本次 `chat_filter` 代码。

---

## 2026-05-06 任意消息触发机制

### 本轮目标

本轮先解决“指定对象发任意消息就立刻回复指定消息”的核心能力，并顺带支持可选回复延迟。

### 本轮新增实现

1. Python 规则新增 `match_mode = any`：
   - 仍然先检查 `enabled`
   - 仍然先检查 `talker`
   - 仍然先检查 `sender`
   - 仍然先检查 `chat_scope`
   - 仍然先检查 `type`
   - 通过这些边界后，不再检查 `pattern`
2. Flutter 规则配置区新增“任意消息触发”开关：
   - 开启后保存 `match_mode = any`
   - 开启后保存 `type = unknown`
   - `unknown` 继续沿用现有语义：允许任意消息类型
   - 因此文本、图片、表情、视频等消息都可以触发
3. Flutter 规则配置区新增“回复延迟毫秒”：
   - 默认 `0`
   - 匹配成功后、真实发送前等待
   - 如果延迟期间用户手动 Disarm，bot 会在延迟后重新检查 armed 状态并跳过发送
4. 现有安全边界不变：
   - 仍受 `armed` 控制
   - 仍受最大触发次数控制
   - 仍受监听对象控制
   - 仍受冷却时间控制

### 表情包相关影响

这不是表情包解析修复，但能绕过“表情包中文名不稳定 / 内容为空”的匹配问题：

1. 如果规则是 `match_mode = any` 且 `type = unknown`，表情包不需要依赖 `content`。
2. 只要消息源能把这条消息作为事件吐出来，并且 talker/scope 匹配，就能触发。
3. 具体表情包资源识别、预览、中文名准确性仍然属于后续单独问题。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_matcher_chat_scope.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_bot_armed_current_chat.py -v
flutter test test/desktop_console_controller_test.dart test/http_desktop_service_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. Python 新增任意触发测试先红后绿。
2. Python 新增回复延迟测试先红后绿。
3. Flutter 新增规则保存 payload 测试先红后绿。
4. Python 全量测试总计 `43/43` 通过。
5. `flutter analyze` 无问题。
6. `flutter test` 通过。
7. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`

---

## 2026-05-06 任意触发回环与 UI 勾选修复

### 本轮定位

本轮根据真实测试反馈定位到两个问题：

1. 任意触发偶发发送两条消息：
   - 根因是 `match_mode = any` 不看消息内容。
   - bot 发出的回复会被 `wechat-decrypt` 再读回同一会话。
   - 读回的自发消息也满足 `talker/chat_scope/type`，于是再次触发。
2. “任意消息触发”勾选状态很难保存：
   - 桌面页面每 1 秒刷新一次 snapshot。
   - HTTP status 每次都会构造新的 `replies` list。
   - Flutter 之前用 list 引用比较判断是否要同步表单，等价内容的新 list 也被认为变化。
   - 因此本地刚点的 checkbox 会被服务端旧状态覆盖。

### 本轮修复

1. bot 新增 sent echo 抑制：
   - 每次成功发送后，短时间记录 `(talker, reply content, source sender)`。
   - 如果随后读到同一会话、同一内容、且不是原始发送人的消息，则视为 bot 自己发出的 echo。
   - echo 事件会记录 `event_skip reason=sent_echo`，不会再次触发回复。
2. `RulePanel` 的刷新同步改为内容比较：
   - `replies` 使用 `listEquals`。
   - 等价刷新不再重置本地 checkbox 状态。
   - 用户可以正常勾选/取消“任意消息触发”，不需要抢在 1 秒刷新前点击保存。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_bot_armed_current_chat.py -v
flutter test test/rule_panel_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. 新增自发 echo 不再触发的回归测试先红后绿。
2. 新增任意触发 checkbox 等价刷新不重置的 widget 测试先红后绿。
3. Python 全量测试总计 `44/44` 通过。
4. `flutter analyze` 无问题。
5. `flutter test` 通过。
6. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`

---

## 2026-05-06 表情中文描述触发修复

### 本轮定位

1. 当前真实事件中，表情包会以 `type = emoji` 进入，且部分表情会带有中文 `content`，例如 `额3`、`嗯嗯2`。
2. 桌面端普通关键词规则保存为 `type = text`、`match_mode = regex`。
3. 旧 matcher 会在内容匹配前先做消息类型检查，因此这类事件被 `type_mismatch` 跳过。
4. 这不是中文正则本身失效，而是 `text` 规则没有允许带中文描述的 `emoji` 事件参与关键词匹配。

### 本轮修复

1. `matcher.py` 现在允许 `type = text` 的关键词规则匹配带有非空中文描述的 `emoji` 事件。
2. 原有 talker、sender、chat_scope、pattern、cooldown、armed、最大触发次数等边界不变。
3. 空内容表情包仍不会因为 `type = text` 规则直接通过类型检查。
4. 规则配置面板 helper 文案已更新，提示普通模式也会匹配表情包解析出的中文描述。

### 当前边界

1. 这次修的是“表情包事件已经提供中文 content 时，中文关键词可以触发”。
2. 这不是完整表情包资源识别；`wechat-decrypt` 日志里的 `emoji 查询失败` / `rich type=47 失败` 仍属于后续独立问题。
3. 已保存的 `type = text` 规则可以沿用，不需要为了这个修复改成本地 `rules.local.json`。
4. 需要重启 live bot 或重新启动打包 app 中的服务，让新的 Python matcher 代码生效。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_matcher_chat_scope.py -v
flutter test test/rule_panel_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. 新增 `type=text` 中文关键词匹配 `type=emoji` 表情中文描述的回归测试先红后绿。
2. Python 全量测试总计 `45/45` 通过。
3. `flutter analyze` 无问题。
4. `flutter test` 通过。
5. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`

---

## 2026-05-07 历史群成员 ID 查询

### 本轮目标

解决“目标成员在监听期间没有新发言，但历史群聊里发过言，能否拿到稳定 sender ID”的问题。

### 本轮新增实现

1. 新增 `core/history_sender_search.py`：
   - 从 `wechat-decrypt` 的历史 message DB cache 中读取指定群聊表。
   - 通过 `real_sender_id -> Name2Id.user_name` 解析群成员真实 sender ID。
   - 聚合候选成员的最近发言时间、最近消息片段和历史发言条数。
   - 如果缺少 contact cache，会尝试用 `all_keys.json` 临时解密 `contact/contact.db`，提高按昵称/备注搜索的成功率。
2. Python desktop service 新增：
   - `GET /history/senders?chat=<chatroom>&query=<keyword>&limit=<n>`
   - 返回候选字段：
     - `sender`
     - `sender_name`
     - `last_timestamp`
     - `last_content`
     - `message_count`
3. Flutter 模型和服务层新增：
   - `HistorySenderCandidate`
   - `DesktopService.searchHistorySenders(...)`
   - `HttpDesktopService` 调用 `/history/senders`
4. Flutter UI 新增：
   - “历史群成员搜索”
   - 输入昵称/备注/ID 关键字后从当前群聊历史发言中查找候选人。
   - 点击“使用”后保存为当前规则的 `sender` 过滤。
   - 支持“清除成员过滤”。
5. 规则配置区新增“群成员 ID（可选）”字段，允许手动填写或查看当前 sender 过滤。
6. `pubspec.yaml` 已把 `history_sender_search.py` 加入 Windows 打包 assets。

### 当前边界

1. 只有目标成员在该群历史消息里发过言，才能通过历史消息拿到 sender ID。
2. `sender` 过滤是群内成员过滤；群聊本身仍由 `talker = xxx@chatroom` 控制。
3. 昵称/备注可能因不同微信账号而不同；最终保存和匹配用的是 `sender` 原始 ID。
4. 如果 message cache 尚未由 `wechat-decrypt` 生成，历史查询可能返回空；启动消息源并等待 warmup 后再查更可靠。
5. 本轮没有操作微信窗口，也没有 armed 或触发真实发送。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_history_sender_search.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
flutter test test/http_desktop_service_test.dart test/desktop_console_controller_test.dart test/desktop_console_page_test.dart test/rule_panel_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. 新增历史 sender 查询测试通过。
2. Python 全量测试总计 `47/47` 通过。
3. `flutter analyze` 无问题。
4. `flutter test` 通过。
5. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`
6. 已确认打包产物包含：
   - `data/flutter_assets/.../core/history_sender_search.py`

---

## 2026-05-07 历史群聊搜索

### 本轮目标

解决“目标群不在最近会话里，用户只知道群名但不知道 `@chatroom` ID，无法先定位群再查成员”的问题。

### 本轮新增实现

1. 新增 `core/history_chat_search.py`：
   - 从 `wechat-decrypt` 的已解密缓存中读取历史群聊候选。
   - 优先读取 `decrypted/session/session.db` 的 `SessionTable` 和 `SessionNoContactInfoTable`。
   - 同时读取 `decrypted/contact/contact.db` 或 `decrypted/_monitor_cache/contact_contact.db` 的群聊联系人。
   - 只返回 `talker` 以 `@chatroom` 结尾的群聊。
   - 返回字段：
     - `talker`
     - `display_name`
     - `last_timestamp`
     - `summary`
     - `source`
2. Python desktop service 新增：
   - `GET /history/chats?query=<keyword>&limit=<n>`
3. Flutter 模型和服务层新增：
   - `HistoryChatCandidate`
   - `DesktopService.searchHistoryChats(...)`
   - `HttpDesktopService` 调用 `/history/chats`
4. Flutter “监听对象”区域新增“历史群聊搜索”：
   - 输入群名或群聊 ID 关键字搜索。
   - 空关键词可以列出缓存中可识别的历史群聊。
   - 点击“使用”会把该群保存为当前对象，并自动按群聊处理。
   - 之后可以继续用已有“历史群成员搜索”查询该群成员 sender ID。
5. `pubspec.yaml` 已把 `history_chat_search.py` 加入 Windows 打包 assets。

### 当前边界

1. 该功能只读取本机 `wechat-decrypt` 已解密缓存，不联网查询微信服务器。
2. 如果某个群既不在 `session.db`，也不在 contact cache 中，历史群聊搜索仍可能查不到。
3. 如果缓存过旧，需要先启动消息源或运行完整解密刷新缓存。
4. 本轮没有操作微信窗口，也没有 armed 或触发真实发送。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_history_chat_search.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
flutter test test/http_desktop_service_test.dart
flutter test test/desktop_console_controller_test.dart
flutter test test/target_panel_test.dart
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

结果：

1. 新增历史群聊搜索核心测试先红后绿。
2. 新增 `/history/chats` API 测试先红后绿。
3. 新增 TargetPanel 搜索并保存群聊对象 widget 测试先红后绿。
4. Python 全量测试总计 `49/49` 通过。
5. `flutter analyze` 无问题。
6. `flutter test` 通过。
7. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`
8. 已确认打包产物包含：
   - `data/flutter_assets/.../core/history_chat_search.py`

---

## 2026-05-07 Windows 辅助脚本

### 本轮目标

为本机测试和后续分发前排障补两个显式脚本：

1. 一键重启 `127.0.0.1:18090` Python desktop service wrapper。
2. 一键运行 `wechat-decrypt` 完整解密，刷新历史群聊和历史群成员查询依赖的缓存。

### 本轮新增文件

1. `tools/windows/restart_python_service.bat`
   - 优先使用 Windows Release assets 中的 `desktop_service.py`。
   - 如果 Release assets 不存在，回退到仓库源码里的 `scripts/desktop_service.py`。
   - 先请求 `/status`，如果发现 `armed=true`，直接拒绝继续。
   - 如果 wrapper 正在运行，先调用 `/services/stop` 停掉托管的 bot/source。
   - 只停止监听 `127.0.0.1:18090` 且命令行包含 `desktop_service.py` 的进程。
   - 重启 wrapper 后，如果重启前 `service_state=running`，且重启后仍 `armed=false`，再恢复 `/services/start`。
2. `tools/windows/build_wechat_cache.bat`
   - 从 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json` 读取 `wechat_decrypt_root`。
   - 进入 `wechat_decrypt_root` 后执行 `python main.py decrypt`。
   - 不调用 `/arm-state`，不调用 `/services/start`，不触发发送链路。

### 当前边界

1. 本轮只创建脚本和测试，没有实际运行这两个脚本。
2. `restart_python_service.bat` 会操作本机 18090 Python wrapper，使用前应确认 App 中已 Disarm。
3. `build_wechat_cache.bat` 会读本机微信数据库并生成解密缓存，可能耗时较长。
4. 两个脚本仍依赖本机已有 Python 和 `wechat-decrypt` 依赖。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
git diff --check
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
```

结果：

1. 新增脚本校验测试先红后绿。
2. `git diff --check` 无空白错误。
3. Python 全量测试总计 `51/51` 通过。

### 2026-05-07 追加修正

1. `restart_python_service.bat` 和 `build_wechat_cache.bat` 现在都会在结束前停留。
2. 无论成功还是失败，脚本都会显示：
   - `Press any key to close this window...`
3. 用户可以看到 PowerShell 或 Python 报错内容，再按任意键关闭窗口。
4. 脚本仍会保留原始退出码，便于以后被其他自动化脚本调用。

### 2026-05-07 重启脚本路径修正

1. 修复 `restart_python_service.bat` 在部分运行方式下推导仓库根目录不稳定的问题。
2. 仓库根目录现在通过 `pushd "%~dp0..\.."` 后读取 `%CD%` 得到。
3. 脚本会在进入 PowerShell 前先确认 `desktop_service.py` 存在。
4. 如果找不到文件，会打印实际搜索的两个路径：
   - Release assets 里的 `desktop_service.py`
   - 仓库源码里的 `desktop_service.py`
5. 本轮没有实际运行重启脚本，没有操作微信窗口，也没有触发发送。

### 2026-05-07 重启脚本 Release 目录兼容修正

1. 修复用户从 Windows Release 目录直接双击 `restart_python_service.bat` 或 `重启后台.bat` 时找不到 `desktop_service.py` 的问题。
2. 根因是旧脚本总是假设自身位于仓库 `tools/windows` 目录下；当脚本位于 `build/windows/x64/runner/Release` 时，会错误拼出重复的 `build/windows/x64/runner/Release/build/windows/x64/runner/Release/...`。
3. 新脚本查找顺序：
   - 当前脚本目录下的 `data/flutter_assets/.../desktop_service.py`，用于 Release 根目录直接运行。
   - 当前脚本目录上一级的 `data/flutter_assets/.../desktop_service.py`，用于以后放在包内 `tools` 子目录。
   - 仓库 `build/windows/x64/runner/Release/data/flutter_assets/.../desktop_service.py`，用于开发者从 `tools/windows` 运行。
   - 仓库源码 `android/app/src/main/kotlin/.../scripts/desktop_service.py`，用于未打包时开发调试。
4. 已将当前本机 Release 目录中的以下脚本同步为新版，便于立即手动测试：
   - `build/windows/x64/runner/Release/restart_python_service.bat`
   - `build/windows/x64/runner/Release/重启后台.bat`
5. 本轮未实际执行重启脚本，没有操作微信窗口，也没有 armed 或触发发送。
6. Android/Linux 未追踪平台文件未纳入本轮修改；项目仍按多平台 Flutter 工程处理。

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
git diff --check
```

结果：

1. `test_windows_tool_scripts.py` 先红后绿，覆盖 Release 目录直接运行场景。
2. Python 全量测试总计 `51/51` 通过。
3. `git diff --check` 无空白错误。

---

## 2026-05-07 Windows 便携分发准备

### 本轮目标

让 Windows Release 产物从“开发者本机可运行”推进到“可组装成测试用户便携文件夹”：

1. Release 目录稳定带上用户可见脚本，而不是依赖手工复制或残留产物。
2. Flutter app、desktop service、辅助 BAT 都优先识别包内 `runtime/python` 与 `runtime/wechat-decrypt`。
3. 提供一键初始化脚本，修正 `%LOCALAPPDATA%` 下旧的 `runtime.local.json`。
4. 提供开发者侧便携目录组装脚本和分发文档。

### 本轮新增/修改

1. Flutter Windows 启动器新增包内 Python 自动发现：
   - `lib/features/desktop_console/data/windows_service_launcher.dart`
   - 新增 `resolvePythonExecutable(...)`
   - 优先查找 `runtime/python/python.exe`
2. Flutter HTTP desktop service 启动 wrapper 时改为使用自动发现的 Python：
   - `lib/features/desktop_console/data/http_desktop_service.dart`
3. Python desktop service 初始化 runtime 配置时，如果检测到打包目录中的：
   - `runtime/wechat-decrypt/main.py`
   - 会自动把 `wechat_decrypt_root` 写入 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json`
4. `restart_python_service.bat` 现支持：
   - Release 根目录运行
   - `Release/tools` 运行
   - `Release/tools/windows` 运行
   - 包内 `runtime/python/python.exe`
5. `build_wechat_cache.bat` 现支持包内 `runtime/python/python.exe`。
6. 新增 `init_first_run.bat`
   - 自动把本机 `runtime.local.json` 指向包内 `runtime/wechat-decrypt`
   - 默认写入 `watcher_url=http://127.0.0.1:5678`
7. `windows/CMakeLists.txt` 已正式安装这些 Windows 用户脚本到 Release：
   - 根目录：
     - `restart_python_service.bat`
     - `build_wechat_cache.bat`
     - `init_first_run.bat`
     - `重启后台.bat`
     - `获取微信历史数据.bat`
     - `首次初始化.bat`
   - `tools/windows/` 子目录中的真实脚本
8. 新增开发者侧组装脚本：
   - `tools/windows/package_portable_release.ps1`
9. 新增分发文档：
   - `docs/windows-portable-distribution.md`

### 当前便携分发形态

当前已经能生成一个测试用户可解压的便携目录，顶层至少包含：

```text
SuperIvanPro-Windows-Portable-*/
  super_ivan_pro.exe
  flutter_windows.dll
  data/
  tools/
  runtime/
  restart_python_service.bat
  build_wechat_cache.bat
  init_first_run.bat
  README_WINDOWS_PORTABLE.md
```

其中 `runtime/` 可包含：

```text
runtime/
  python/
    python.exe
  wechat-decrypt/
    main.py
```

### 当前边界

1. 本轮仍未操作微信窗口，也未 armed 或触发真实发送。
2. 便携目录可生成成功。
3. `Compress-Archive` 在大 Python 运行时目录上偶发文件锁；当前开发者脚本已优先尝试 `tar.exe`，但本轮交付以“文件夹分发可用”为主。
4. 如果测试机器上已经存在旧的 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json`，建议先运行：
   - `init_first_run.bat`

### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_store.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter test test/windows_service_launcher_test.dart
flutter analyze
flutter test
flutter build windows
powershell -ExecutionPolicy Bypass -File .\tools\windows\package_portable_release.ps1 -PythonRoot "<local python root>" -WechatDecryptRoot "<local wechat-decrypt root>"
```

结果：

1. 新增 Flutter 启动器测试先红后绿，覆盖包内 Python 自动发现。
2. 新增 Python runtime 配置测试先红后绿，覆盖包内 `wechat-decrypt` 自动回填。
3. Windows 脚本测试先红后绿，覆盖：
   - 多层 Release 目录定位
   - 包内 Python
   - 初始化脚本
   - 便携组装脚本
4. Python 全量测试现为 `52/52` 通过。
5. `flutter analyze` 通过。
6. `flutter test` 通过。
7. `flutter build windows` 重新通过，生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`
8. 已确认新的 Release 根目录实际包含：
   - `restart_python_service.bat`
   - `build_wechat_cache.bat`
   - `重启后台.bat`
   - `获取微信历史数据.bat`
9. 已从真正的便携分发目录实际执行：
   - `dist/.../restart_python_service.bat`
10. 实际输出确认：
   - `desktop_service.py` 从便携目录 `data/flutter_assets/...` 解析成功
   - `python executable` 使用的是便携目录 `runtime/python/python.exe`
   - 重启后状态仍为：
     - `service_state=running`
     - `watcher_state=running`
     - `watcher_error=""`
     - `armed=false`
     - `mode=rapid`

### 2026-05-07 便携包用户入口收口与实测补记

1. 便携包根目录现在只保留 3 个用户脚本入口：
   - `首次初始化.bat`
   - `重启后台.bat`
   - `重建聊天缓存.bat`
2. 便携包根目录现在同时提供两份同内容中文说明：
   - `使用说明.md`
   - `README.md`
3. 已从真正的便携包根目录实际执行：
   - `dist/SuperIvanPro-Windows-Portable/首次初始化.bat`
   - `dist/SuperIvanPro-Windows-Portable/重启后台.bat`
4. 实际结果：
   - `首次初始化.bat` 成功把 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json` 指向包内 `runtime\wechat-decrypt`
   - `重启后台.bat` 成功从包内 `runtime\python\python.exe` 与 `data/flutter_assets/.../desktop_service.py` 拉起服务
   - 重启后 `GET /status` 仍返回：
     - `service_state=running`
     - `watcher_state=running`
     - `watcher_error=""`
     - `armed=false`
     - `mode=rapid`
5. 这说明当前便携包已经满足“整包解压后运行脚本，不依赖仓库源码路径”的分发目标。

### 2026-05-07 便携包初始化脚本 BOM 修复与最终验收

#### 本轮定位到的真实问题

1. 便携包 `首次初始化.bat` 之前使用 PowerShell `Set-Content -Encoding UTF8` 写 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json`。
2. 在当前 Windows PowerShell 环境下，这会写出带 UTF-8 BOM 的 JSON。
3. 运行中的 Python desktop service 读取 runtime 配置时，多个路径默认按 `utf-8` 解析 JSON。
4. 结果是初始化后 `GET /status` 会出现：
   - `watcher_state = unavailable`
   - `watcher_error = Unexpected UTF-8 BOM (decode using utf-8-sig)`

#### 本轮修复

1. `tools/windows/init_first_run.bat` 改为使用无 BOM 的 UTF-8 写入 `runtime.local.json`。
2. Python runtime 配置读取现在兼容带 BOM 的 JSON：
   - `core/config_loader.py`
   - `desktop_service/config_paths.py`
   - `desktop_service/http_api.py`
3. 新增回归测试覆盖：
   - 初始化脚本写出的 `runtime.local.json` 不带 BOM
   - desktop service 状态接口可读取带 BOM 的 runtime 配置

#### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter build windows
powershell -ExecutionPolicy Bypass -File .\tools\windows\package_portable_release.ps1 -OutputDir .\dist\SuperIvanPro-Windows-Portable-20260507-final -PythonRoot "<local python root>" -WechatDecryptRoot "<local wechat-decrypt root>"
```

结果：

1. 目标回归测试先红后绿。
2. Python 全量测试现为 `56/56` 通过。
3. `flutter build windows` 重新通过。
4. 新的最终便携包目录为：
   - `dist/SuperIvanPro-Windows-Portable-20260507-final`

#### 最终便携包实际验收

已从最终便携包根目录实际执行：

1. `首次初始化.bat`
   - 成功写入 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json`
   - 已确认文件 `bom=false`
   - 已确认包含：
     - `wechat_decrypt_root`
     - `watcher_url = http://127.0.0.1:5678`
2. `重启后台.bat`
   - 成功使用包内：
     - `runtime/python/python.exe`
     - `data/flutter_assets/.../desktop_service.py`
   - 重启后 `GET /status` 返回：
     - `service_state=running`
     - `watcher_state=running`
     - `watcher_error=""`
     - `armed=false`
     - `mode=rapid`
3. `重建聊天缓存.bat`
   - 成功调用包内 `wechat-decrypt` 进行完整解密缓存构建
   - 实际结果：
     - `16` 个数据库成功
     - `1` 个数据库失败
     - 脚本整体正常结束并输出 `WeChat cache build finished.`
4. `super_ivan_pro.exe`
   - 已从最终便携包根目录实际拉起进程
   - 启动后进程存活检查为 `alive=True`

#### 当前建议交付物

当前建议直接分发整个目录：

- `dist/SuperIvanPro-Windows-Portable-20260507-final`

分发时不要只发 `super_ivan_pro.exe`，应发送整个文件夹或其压缩包。

### 2026-05-07 dry-run 发送通道修复与无 Python 便携包

#### 本轮定位到的真实问题

1. 用户侧现象是“规则触发了，但没有真正发送消息”。
2. 实际日志确认 matcher 与 dispatch 都已经执行：
   - `rule_match ...`
   - `dispatch_success ...`
3. 失败点在发送器选择，日志实际为：
   - `dry_run_send ... payload=test`
4. 当前 `%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json` 缺少：
   - `sender_backend`
   - `dry_run`
5. Python `RuntimeConfig` 对缺失字段的安全默认值是：
   - `sender_backend = dry_run`
   - `dry_run = true`
6. 因此根因不是 arm 失效，也不是规则没命中，而是便携初始化/运行时归一化没有补齐实发配置。

#### 本轮修复

1. `tools/windows/init_first_run.bat` 现在会在字段缺失时补齐：
   - `sender_backend = current_chat`
   - `dry_run = false`
2. `desktop_service/config_paths.py` 现在会在打包态 runtime 缺字段时补齐同样的实发默认值，但保留用户显式配置。
3. Flutter Windows service launcher 不再优先查找包内 `runtime/python/python.exe`：
   - 优先使用 `SUPER_IVAN_DESKTOP_PYTHON`
   - 再尝试系统 `python`
   - 再尝试 `py -3`
4. `tools/windows/package_portable_release.ps1` 已移除 `PythonRoot` 参数和 Python 打包分支。
5. `重启后台.bat` 与 `重建聊天缓存.bat` 现在要求系统 Python，并在找不到 Python 时停住显示错误。
6. `重启后台.bat` 的 18090 端口释放等待从 5 秒增强为 15 秒，并会重复确认/停止同一个 `desktop_service.py` 进程。
7. 中文 README 已更新：当前分发包不内置 Python，测试机需要安装 Python 3。

#### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter test test/windows_service_launcher_test.dart
flutter build windows
powershell -ExecutionPolicy Bypass -File .\tools\windows\package_portable_release.ps1 -OutputDir .\dist\SuperIvanPro-Windows-Portable-20260507-nopython -WechatDecryptRoot "D:\flutter_app\_tmp\wechat-decrypt"
```

结果：

1. Python 全量测试为 `58/58` 通过。
2. Flutter launcher 目标测试通过。
3. `flutter build windows` 通过。
4. 新的无 Python 便携包目录为：
   - `dist/SuperIvanPro-Windows-Portable-20260507-nopython`
5. 已确认新包内：
   - `runtime\python\python.exe` 不存在
   - `runtime\wechat-decrypt\main.py` 存在
6. 已从新包实际执行：
   - `首次初始化.bat`
   - `重启后台.bat`
7. 初始化后已确认 runtime 配置：
   - `bom=false`
   - `sender_backend=current_chat`
   - `dry_run=false`
   - `watcher_url=http://127.0.0.1:5678`
8. 本机当前运行状态已恢复为：
   - `service_state=running`
   - `watcher_state=running`
   - `watcher_error=""`
   - `armed=false`
   - `mode=rapid`

#### 当前建议交付物

当前建议分发整个目录：

- `dist/SuperIvanPro-Windows-Portable-20260507-nopython`

注意：该目录不内置 Python。测试电脑必须先安装 Python 3，并保证命令行可运行 `python` 或 `py`。

### 2026-05-07 重启脚本 armed=true 处理与速度边界补记

#### 本轮定位到的问题

1. 用户执行 `重启后台.bat` 时如果当前 `armed=true`，脚本会直接报错：
   - `Refusing to restart because armed=true. Disarm in the app first.`
2. 这是之前为了避免“重启时保留真实发送状态”的安全闸，但对分发用户来说体验不好。
3. 当前极速配置已确认：
   - `poll_interval_ms=20`
   - `inter_message_delay_ms=0`
   - `current_chat_fast_send=true`
   - `sender_backend=current_chat`
   - `dry_run=false`

#### 本轮修复

1. `重启后台.bat` 在检测到 `armed=true` 时不再失败。
2. 新行为是先调用 `/arm-state` 自动 disarm，再继续重启后台。
3. 脚本会明确输出：
   - `armed=true detected. Disarming before restart to avoid accidental sending.`
4. 重启后状态会保持 `armed=False`，用户需要在 app 内重新 arm 才会继续真实发送。

#### 本轮速度判断

1. 最近日志显示触发链路已经是：
   - `event_received`
   - `rule_match`
   - `current_chat_send`
   - `dispatch_success`
2. bot 收到事件后通常同秒或下一秒发送。
3. `wechat-decrypt` 日志显示消息采集延迟近期多在约 `0.4s-1.9s`。
4. 目前 app 侧轮询已是 20ms，下探只能节省十几毫秒；主要瓶颈更可能在 `wechat-decrypt` 采集/解密侧。
5. 后续真正有价值的速度优化应先加毫秒级耗时日志，再决定是否改 `wechat-decrypt` 的 live 查询策略。

#### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_windows_tool_scripts.py -v
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
powershell -ExecutionPolicy Bypass -File .\tools\windows\package_portable_release.ps1 -OutputDir .\dist\SuperIvanPro-Windows-Portable-20260507-nopython -WechatDecryptRoot "D:\flutter_app\_tmp\wechat-decrypt"
```

结果：

1. 目标 Python 测试通过。
2. 新便携包根目录为：
   - `dist/SuperIvanPro-Windows-Portable-20260507-nopython-20260507-140247`
3. 已从新包实际执行：
   - `首次初始化.bat`
   - `重启后台.bat`
4. 新 `重启后台.bat` 已在 `armed=true` 状态下实测通过：
   - 自动 disarm
   - 成功重启
   - `service_state=running`
   - `watcher_state=running`
   - `watcher_error=""`
   - `armed=False`
   - `mode=rapid`

### 2026-05-08 disarm 状态触发次数保存修复

#### 本轮定位到的问题

1. 当前本机 `GET http://127.0.0.1:18090/status` 不可用，未启动真实桌面服务，也未操作 WeChat 窗口。
2. 延迟功能代码链路复查结果：
   - Flutter 规则面板会提交 `reply_delay_ms`。
   - Python service 会把 `reply_delay_ms` 写入规则并在 `/status` 回传。
   - `WeChatAutomationBot` 在 `rule_match` 后先执行 `reply_delay_ms` sleep，再进入 dispatch。
   - rapid 模式仍会写入 `poll_interval_ms=20`、`inter_message_delay_ms=0`、`current_chat_fast_send=true`。
3. “disarm 时无法更新触发次数”的根因在 `/arm-state`：
   - `enabled=false` 分支只调用 `store.disarm(reason="manual_disarm")`。
   - 请求体中的 `max_triggers` 被忽略。
   - 因此 UI 在 disarm 状态保存规则时，后端仍保留旧的最大触发次数。

#### 本轮修复

1. `ArmStateStore.disarm(...)` 新增可选 `max_triggers` 参数。
2. `/arm-state` 的 `enabled=false` 分支现在会读取请求体中的 `max_triggers` 并传给 `disarm(...)`。
3. 当 disarm 状态下的最大触发次数被改动时，会重置 `triggers_sent=0`，让 `remaining_triggers` 立即按新预算显示。
4. 新增回归测试：
   - `test_disarmed_arm_state_update_applies_max_triggers`

#### 本轮验证

已执行：

```bash
python -m unittest android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests/test_desktop_service_api.py -v
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
git diff --check
```

结果：

1. 新增回归测试先红后绿，红灯确认为 `max_triggers` 返回旧值 `1` 而不是请求中的 `4`。
2. Python 全量测试总计 `59/59` 通过。
3. `flutter analyze` 无问题。
4. Flutter 全量测试通过。
5. Windows 打包成功生成：
   - `build/windows/x64/runner/Release/super_ivan_pro.exe`
6. 本轮没有启动真实 bot/source，没有 arm，也没有触发真实发送。

### 2026-05-16 群成员过滤、发送失败兜底与错误提示修复

#### 本轮定位到的问题

1. 延迟单位确认仍是毫秒：
   - Flutter 提交字段为 `reply_delay_ms`。
   - Python bot 使用 `rule.reply_delay_ms / 1000.0` 转为秒后 sleep。
   - 因此 UI 中 `500` 表示 0.5 秒。
2. 群成员过滤存在无效状态：
   - 规则可以出现 `sender_name` 有值但 `sender` 为空。
   - matcher 实际只使用 `sender` 匹配事件发送者，因此这种状态会让“看起来选中了成员”，但实际不限制成员。
3. 发送失败会导致 live bot 退出：
   - `CurrentChatSender` 在前台不是微信、输入框找不到等情况下抛出 `foreground_not_wechat` / `chat_input_not_found`。
   - dispatcher 记录 `dispatch_failure` 后继续抛出。
   - `WeChatAutomationBot.process(...)` 原先没有兜底，会让 `run_bot.py` 退出。
   - 这解释了“ARM 看似打开但不生效，反复保存/重启后又恢复”的现象：保存/重启会重新拉起 bot。
4. 历史群聊搜索只用最终展示名参与匹配：
   - 一个群同时存在 session 标题和 contact 旧名时，旧名不会参与搜索。
   - 改名前/改名后的群名因此可能只命中其中一个。
5. 发送失败目前主要藏在日志里，桌面 UI 没有醒目的错误区。

#### 本轮修复

1. bot 现在会兜住最终发送失败：
   - 保留 dispatcher 的 `dispatch_failure` 详细日志。
   - 额外记录 `dispatch_aborted rule=... seq=... error=...`。
   - 不再让单次发送失败杀死 live bot。
2. Flutter 保存规则时会清理孤儿成员名：
   - `sender` 为空时强制清空 `senderName`。
   - 手动改成另一个 sender ID 时也不会沿用旧成员显示名。
3. Python service 写入/读取规则时会归一化成员字段：
   - `sender` 为空则 `sender_name` 也为空。
4. 历史群聊搜索增加别名匹配：
   - session 标题和 contact 名都会进入查询命中范围。
   - 返回展示名仍优先使用当前 session 标题。
5. `/status` 新增：
   - `arm_reason`
   - `last_error`
6. Flutter 状态面板新增明确提示：
   - `监听状态原因: ...`
   - `最近发送错误: ...`

#### 本轮验证

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
```

结果：

1. Python 全量测试 `62/62` 通过。
2. `flutter analyze` 无问题。
3. Flutter 全量测试 `33/33` 通过。
4. `GET http://127.0.0.1:18090/status` 当前连接被拒绝，说明本地 desktop service 未启动；本轮没有启动真实 bot/source，没有 arm，也没有触发真实发送。
