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
