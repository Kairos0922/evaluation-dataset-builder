# 被测 Skill 能力说明

**对象：** Anthropic `webapp-testing`  
**来源仓库：** https://github.com/anthropics/skills  
**来源路径：** `skills/webapp-testing`  
**固定版本：** `2c5958ecac7cee2b583967a2c4981d0f4a75c579`  
**许可证：** Apache License 2.0  
**来源类型：** 上游公开资产

## 官方能力描述

上游 `SKILL.md` 将该 Skill 描述为：使用 Playwright 与本地 Web 应用交互和测试的工具集。它支持验证前端功能、调试 UI 行为、捕获浏览器截图和查看浏览器日志。

## 可观察能力范围

以下内容用于规划评测能力，不代表任何测试已经执行。

- 理解用户提供的 Web 应用测试目标和验收规则。
- 判断目标应用是静态 HTML，还是需要启动服务的动态应用。
- 按上游指引使用 `scripts/with_server.py` 管理本地服务。
- 使用 Python Playwright sync API 与 Chromium 进行浏览器操作。
- 在页面可用后检查 DOM、识别元素、执行操作和验证页面状态。
- 根据目标采集截图、浏览器日志和其他可观察证据。
- 识别等待条件、selector、浏览器错误和服务生命周期方面的限制。
- 在任务完成后关闭浏览器，并遵守应用权限和副作用边界。

## 证据边界

`SKILL.md`、脚本和示例是能力定义与执行指引的来源。它们不能单独证明 Skill 在某次任务中成功。能力结果必须来自 DSH 调用记录、实际浏览器执行、应用状态和独立证据。

此文件不是正式评测集，也不预先指定评测用例数量。
