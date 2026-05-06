# Super Ivan Pro

Super Ivan Pro 当前重点是 Windows 微信自动化桌面控制台。Flutter Windows app 负责展示状态、配置监听对象和规则、控制本地 Python 服务；Python 侧负责托管消息源、运行 live bot，并在明确 `armed` 后按规则处理新消息。

## 当前桌面链路

1. Flutter app 首次读取状态时会尝试连接 `http://127.0.0.1:18090/status`。
2. 如果本地 HTTP 服务未启动，Flutter 会通过 `WindowsServiceLauncher` 拉起 `wechat_automation/scripts/desktop_service.py`。
3. 打开 app 只会保证本地 HTTP wrapper 可用，不会自动启动 live bot。
4. 点击“启动服务”后，`desktop_service.py` 会先检查消息源 `wechat-decrypt`，必要时从 `wechat_decrypt_root` 启动它，再启动 `scripts/run_bot.py --live`。
5. 只有 `arm_state.local.json` 中 `enabled=true` 时，bot 才会在匹配新消息后发送回复。

## 本机运行前提

运行时配置位于：

```text
%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json
```

当前机器需要至少包含：

```json
{
  "watcher_url": "http://127.0.0.1:5678",
  "wechat_decrypt_root": "D:\\flutter_app\\_tmp\\wechat-decrypt"
}
```

还需要：

- Windows 上已有可执行的 `python`，或设置 `SUPER_IVAN_DESKTOP_PYTHON`。
- `wechat_decrypt_root` 指向的目录存在，并包含可运行的 `main.py`。
- `wechat-decrypt` 自身依赖已安装。

## 安全边界

- 不要在未确认目标窗口、规则和 `armed` 状态前测试真实发送。
- `启动服务`、`重启服务`、`切换模式`、`保存对象`、`保存规则` 本身不会发送消息；它们只会启动或重启 bot。
- `Arm` 会允许后续匹配到的新消息触发发送，测试时默认保持 `armed=false`。
- 不要提交本地测试配置文件，例如 `arm_state.local.json`、`rules.local.json`、`runtime.local.json`。

## 常用验证

```powershell
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_*.py" -v
flutter analyze
flutter test
flutter build windows
```

打包产物通常位于：

```text
build\windows\x64\runner\Release\super_ivan_pro.exe
```

## 关键代码

- Flutter 本地服务客户端：`lib/features/desktop_console/data/http_desktop_service.dart`
- Flutter 服务启动器：`lib/features/desktop_console/data/windows_service_launcher.dart`
- Flutter 控制器：`lib/features/desktop_console/controller/desktop_console_controller.dart`
- Python HTTP API：`android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/desktop_service/http_api.py`
- Python live bot 入口：`android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/run_bot.py`
- 进度记录：`android/app/src/main/kotlin/com/super_ivan_pro/glacier/discussion_progress/wechat_automation_windows_desktop_progress_2026-04-23.md`
