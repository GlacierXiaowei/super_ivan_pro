# WeChat Automation Windows Desktop Progress

Saved at: 2026-04-23
Status: phase 1 implementation completed, Windows packaging blocked by local toolchain

## 今天已经完成的内容

### 1. 实施计划已落地

已写入本地计划文档：

- `android/app/src/main/kotlin/com/super_ivan_pro/glacier/superpower/plans/wechat_automation_windows_desktop_phase1_plan_2026-04-23.md`

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
