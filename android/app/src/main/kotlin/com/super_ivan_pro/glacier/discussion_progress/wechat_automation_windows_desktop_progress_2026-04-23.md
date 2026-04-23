# WeChat Automation Windows Desktop Progress

Saved at: 2026-04-23
Status: phase 1 in progress

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
3. 新增测试已覆盖：
   - launcher 命令生成
   - HTTP status / mode 请求
   - controller 启停 busy 状态

### Python

已执行：

```bash
python -m unittest discover android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/tests -p "test_desktop_service_*.py" -v
```

结果：

1. `6/6` 通过

### 本地服务烟雾验证

已执行：

```bash
python android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py --host 127.0.0.1 --port 18091 --runtime-root <temp>
GET http://127.0.0.1:18091/status
```

结果：

1. 脚本可正常启动本地 HTTP server
2. `/status` 返回了有效 JSON

## 当前仍未完成

这一轮还没有完成的关键点：

1. Flutter 还没有把“监听对象输入”和“规则配置”真正保存到 live service
2. Python service 还没有扩展 arm/disarm、rules、recent events 等 API
3. 还没有把 `wechat-decrypt` 和现有 bot 纳入统一托管
4. 还没有做桌面安装包或 bundled python 分发

## 建议的下一执行顺序

下一步建议按这个顺序推进：

1. 让监听对象区真正调用 `saveTarget`
2. 扩展 Python service：
   - `GET /events/recent`
   - `POST /arm`
   - `POST /disarm`
   - `GET /rules`
   - `POST /rules`
3. 让规则区和 armed 状态区切到 live service
4. 再把 `wechat-decrypt` 和 bot 进程纳入统一托管

## 重要边界

本轮实现没有动这些用户本地实验文件：

1. `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/arm_state.local.json`
2. `android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/config/rules.local.json`

本轮也没有覆盖用户手改过的设计文档内容。
