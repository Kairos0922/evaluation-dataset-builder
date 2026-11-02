# 评测数据集构建 Skill

**版本：** 0.0.1  
**发布状态：** 发布候选，尚未正式发布  
**类型：** Agent Skills 开放格式 Skill

## 这个 Skill 是做什么的

本 Skill 帮助 Agent 为 Agent、Skill、API、工作流及其他软件系统构建高质量评测数据集。它提供一套可复用的业务分析、场景规划、用例生成、评分器设计、质量审查和增量维护流程。

核心能力包括：

- 从业务资料中提取目标、能力、角色、规则、流程、状态、风险和可观察证据。
- 建立覆盖范围全集，识别覆盖缺口，并按业务影响和风险优先级生成用例。
- 覆盖正常、边界、业务规则、权限、安全、异常恢复、多轮和工具交互等适用场景。
- 为每条用例设计可判定的预期行为、禁止行为、评分条件和证据要求。
- 区分真实业务案例、基于证据派生的场景和合成补缺用例。
- 对用例和数据集执行独立质量审查，输出缺陷、限制和质量状态。
- 在规则、来源、能力或评分标准变化时分析影响范围，并局部修复受影响资产。

## Skill 在哪里运行

Skill 不是独立运行的程序、服务或 Agent。它是一个包含 `SKILL.md` 和按需参考资料的目录，由支持 Agent Skills 的宿主 Agent 发现和加载：

1. 宿主通常先读取 Skill 的名称和描述，用于判断任务是否适用。
2. 用户请求匹配时，宿主读取 `SKILL.md` 中的执行流程。
3. 执行到具体环节时，宿主再按指引读取对应的 `references/` 文件。
4. 实际分析、文件读写、代码执行、网络访问和外部系统操作，均由宿主 Agent 已提供并获授权的能力完成。

因此，Skill 本身不附带工具、权限、接口或独立运行环境。同一个 Skill 的目录可以跨支持该开放格式的宿主复用，但它不会自动获得相同的工具权限或执行环境。

## 安装

本仓库中的可安装 Skill 目录是：

```text
skills/evaluation-dataset-builder/
├── SKILL.md
└── references/
```

请复制整个 `evaluation-dataset-builder` 目录，保持 `SKILL.md` 与 `references/` 的相对路径不变。不要只复制 `SKILL.md`。

### Codex

用户级安装：

```bash
mkdir -p ~/.agents/skills
cp -R skills/evaluation-dataset-builder ~/.agents/skills/
```

仅在当前项目使用：

```bash
mkdir -p .agents/skills
cp -R skills/evaluation-dataset-builder .agents/skills/
```

### Claude Code

用户级安装：

```bash
mkdir -p ~/.claude/skills
cp -R skills/evaluation-dataset-builder ~/.claude/skills/
```

仅在当前项目使用：

```bash
mkdir -p .claude/skills
cp -R skills/evaluation-dataset-builder .claude/skills/
```

### claude.ai

先确认 Claude 已启用代码执行和文件创建能力。然后将 Skill 目录打包为 ZIP：

```bash
cd skills
zip -r evaluation-dataset-builder.zip evaluation-dataset-builder
```

ZIP 内必须保留最外层的 `evaluation-dataset-builder/` 目录，不能把 `SKILL.md` 直接放在 ZIP 根目录。

在 Claude 中依次进入 `Customize > Skills > + > + Create skill > Upload a skill`，上传生成的 ZIP。上传后在 Skills 列表中启用该 Skill。

### Claude API

API 使用方式与本地目录安装不同：先通过 Skills API 上传 Skill，再在 Messages API 请求中同时启用代码执行工具并传入对应的 Skill ID。Skill 在 API 提供的代码执行容器中访问；该容器的网络和依赖安装能力受 API 运行环境限制。

### 其他宿主

若使用其他支持 Agent Skills 的产品，请遵循该产品的 Skill 安装目录、上传方式和运行环境说明。不要假设不同产品共享相同目录、自动发现规则或工具权限。

## 使用方法

安装后，可以在对话中明确要求使用本 Skill，也可以描述符合其适用范围的任务，让宿主根据 Skill 描述决定是否加载。

例如：

> 请使用评测数据集构建 Skill。根据我提供的产品文档和业务规则，为这个云服务 Agent 设计一套评测数据集。先建立业务场景模型和覆盖矩阵，再按高优先级缺口生成 80 条用例。每条用例都要有可观察的期望行为、评分标准和来源依据。资料不足的地方标记待确认，不要编造业务规则。最终交付 JSONL 用例、数据集清单、覆盖矩阵和质量报告。

建议尽量提供以下材料：评测对象及版本、评测目标、产品/接口文档、业务规则、用户角色与权限、历史缺陷或事故、执行环境限制、期望用例数量、数据集划分和输出格式。资料不齐全时，Skill 会标记缺口，并继续完成不依赖缺失资料的部分。

## 预期交付物

根据任务范围，通常包括：

- 评测用例文件（可使用 JSONL）。
- 数据集清单和覆盖矩阵。
- 评分器说明及通过/失败条件。
- 质量审查报告、来源映射和未解决问题。
- 合成用例、假设、限制和变更记录。

实际交付格式和文件数量以用户要求为准。

## 开发与验证

仓库中的开发、测试和发布设施不属于 Skill 本体。开发者可在 Python 3.10 或更高版本环境中运行：

```bash
python -m pip install pyyaml
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py" -v
```

这些检查验证 Skill 目录结构、元数据、引用、Schema 和离线测试。它们不能替代真实使用场景评测，也不能证明某个宿主环境具备所需工具或执行权限。

## 许可

本项目采用 MIT License，详见仓库根目录的 `LICENSE`。
