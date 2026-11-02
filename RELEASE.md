# 0.0.1 发布候选说明

**状态：** 尚未正式发布

## 范围

通用 Agent Skill，用于评测数据集规划、生成、质量审查、修复和维护。

## 安装

可安装的 Skill 本体位于 `skills/evaluation-dataset-builder/`。将该目录整体复制或上传到目标宿主支持的 Skills 目录，保持 `SKILL.md` 与 `references/` 的相对路径不变。不同宿主的安装方式见仓库根目录 `README.md`。

本仓库中的 `README.md` 是面向用户的安装和使用指南；`scripts/`、`tests/`、`.github/` 和发布文档属于开发维护设施，不属于 Skill 本体。

## 验证

在开发环境运行：

    python -m pip install pyyaml
    python scripts/validate_skill.py
    python -m unittest discover -s tests -p "test_*.py" -v

## 使用

安装后，向宿主 Agent 提供评测对象、目标能力、业务资料、规则、历史案例、环境约束、数据集数量与划分，以及输出格式。Skill 将指导宿主完成数据集规划、用例和评分器设计、质量审查及问题报告。

缺失的权威依据必须明确标记，不得编造。真实执行结论必须有实际执行证据。

## 发布门禁

- [ ] Skill 目录符合 Agent Skills 元数据、命名和结构要求。
- [ ] 入口文件的按需资源引用完整，目录中无无关文件。
- [ ] Schema、质量标准、引用路径和离线测试通过。
- [ ] 行为测试达到预设阈值，并提供可审查报告。
- [ ] 独立审查通过。
- [ ] 目标运行环境验证通过，并提供可核验执行证据。
- [ ] 所有门禁均绑定到同一候选提交。

只有全部门禁通过后，才可以创建 `v0.0.1` 标签并发布 GitHub Release。结构验证通过不等于正式发布批准。
