# Webapp-testing 实验公开资产目录

本目录是 Evaluation Dataset Builder 的公开输入。目录内容不包含正式评测用例、隐藏 Gold Oracle、独立验证器答案或预先指定的用例数量。

| 文件 | 资产类型 | 用途 |
|---|---|---|
| `capability-description.md` | Skill 能力描述 | 定义被测 Skill 的来源和可观察能力范围 |
| `application-overview.md` | 应用说明 | 描述 Workboard Lite 的页面、数据和交互 |
| `business-rules.md` | 合成业务规则 | 定义应用期望行为 |
| `runtime-and-tool-contracts.md` | 工具与环境信息 | 定义可用工具、运行入口、版本和限制 |
| `../../fixtures/workboard/server.py` | 应用源代码 | 解释服务实现与接口结构 |
| `../../fixtures/workboard/static/index.html` | 应用页面 | 说明页面结构和可访问控件 |
| `../../fixtures/workboard/static/app.js` | 应用前端逻辑 | 说明页面交互和请求流程 |
| `../../fixtures/workboard/static/style.css` | 页面样式 | 定义页面展示 |

## 来源和限制

- 上游 Skill 文件来自固定 commit 的公开 GitHub 仓库，完整来源见 `../../UPSTREAM-ASSET-REVIEW.md`。
- Workboard Lite 是本实验自行创建的合成应用。
- 业务规则是该应用的规范来源。应用代码是被测系统实现，不自动构成正确行为依据。
- 本目录资产用于生成评测套件，不是评测套件本身。
