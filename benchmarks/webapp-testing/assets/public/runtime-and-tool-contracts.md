# 运行环境与工具契约

**环境类型：** GitHub Actions Linux runner  
**来源类型：** SYNTHETIC / CONTROLLED TEST ENVIRONMENT

## 1. 固定运行版本

| 组件 | 固定版本 |
|---|---|
| DSH CLI | 0.2.2-rc.1 |
| Node.js | 24.9.0 |
| Python | 3.12.16 |
| Playwright Python | 1.64.1 |
| Chromium | 156.0.8078.4 |

版本信息来自已通过的 GitHub Actions 运行时预检。正式执行时必须将实际版本记录到每次运行报告。

## 2. 应用入口

- URL：`http://127.0.0.1:4173`
- 健康检查：`GET /api/health`
- 初始数据：应用启动时自动加载。
- 重置接口：`POST /api/reset`。
- 应用服务使用 Python 标准库，无需安装额外 Python 包。

## 3. 可用工具

- DSH Headless 用于加载 Skill 和执行 Agent 任务。
- Python Playwright sync API 用于浏览器自动化。
- Chromium headless 用于页面交互和截图。
- 上游 `webapp-testing` Skill 目录内的 `scripts/with_server.py` 可管理本地服务。

使用 `with_server.py` 前，先执行其 `--help`。按 Skill 约定使用 helper 时，应将服务启动命令限定为受控固定命令。当前 runner 验证过的单进程命令使用 `exec` 替换 shell，避免 shell 与服务进程分离造成残留。

## 4. 权限和网络边界

- 只允许访问本地 Workboard Lite 地址。
- 不需要登录、API Key、外部网站或云服务。
- 不允许访问真实用户数据或生产系统。
- 不允许执行线上写操作。
- 不得把用户输入或不可信资产拼接进 `shell=True` 的服务启动命令。
- 不得读取隐藏 Oracle、运行标签或独立验证器内部数据。
- 不得修改测试应用代码来掩盖缺陷。

## 5. 运行状态重置

每条正式用例执行前，实验运行器负责恢复测试应用初始状态。被测 Skill 不得依赖前一条用例的状态。重置后由独立验证步骤确认初始数据和摘要一致。

## 6. 证据要求

可采集的证据包括页面截图、Playwright 执行日志、浏览器页面错误、HTTP 响应、服务端请求审计和用例执行前后的应用状态。Agent 自述不能替代这些证据。

本文件定义执行环境，不包含正式评测用例或其评分答案。
