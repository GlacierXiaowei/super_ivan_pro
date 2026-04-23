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
