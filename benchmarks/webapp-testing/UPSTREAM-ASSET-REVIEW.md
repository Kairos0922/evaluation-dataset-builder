# webapp-testing 上游资产审查记录

**审查对象：** `anthropics/skills/skills/webapp-testing`  
**冻结 Commit：** `2c5958ecac7cee2b583967a2c4981d0f4a75c579`  
**资产清单状态：** COMPLETE，完整目录清单已冻结  
**运行状态：** RUNTIME_PREFLIGHT_PASS；尚未通过 DSH 调用被测 Skill  
**用途：** 为 Evaluation Dataset Builder 的公开输入资产包提供可追溯来源。本文件不是评测用例。

## 1. 完整性核验结果

通过 GitHub 固定提交的递归 Git tree 接口读取 `skills/webapp-testing/`。返回结果为 `truncated: false`。目录树对象 SHA-1：

`5ffb7dc66b9fd4c25c3e400a4c00da99a349b714`

目录下只有两个子目录（`examples/`、`scripts/`）和六个文件。没有发现符号链接、Git submodule 或其他隐藏文件。

| 路径 | Git 模式 | 字节数 | Blob SHA | 用途 |
|---|---:|---:|---|---|
| `LICENSE.txt` | 100644 | 11,345 | `4f881c52d1f72f4cfb720e339e2d35c3058d01a9` | 许可证 |
| `SKILL.md` | 100644 | 3,913 | `4726215301db64a0cc4d41fc3219c61f37a30f4a` | Skill 指令 |
| `examples/console_logging.py` | 100644 | 1,027 | `9329b5e232ed53d944bfe95e750070117d31b9ab` | 控制台日志示例 |
| `examples/element_discovery.py` | 100644 | 1,463 | `917ba72f52421a1b324f93ae8e38af72010a87b9` | 页面元素发现示例 |
| `examples/static_html_automation.py` | 100644 | 953 | `90bbedcc08cdb345c74fb938ebad02c0baf56603` | 静态 HTML 自动化示例 |
| `scripts/with_server.py` | 100755 | 3,693 | `431f2eba16b268b7f3e2ae4daae9db41c0289b6d` | 服务生命周期辅助脚本 |

文件总数为 6，合计 22,394 字节。目录清单 SHA-256：

`ca5f067e6fc69cd9b6286df33517fd7e0b45fb6fa9d643b23309865b7e47ab88`

该 SHA-256 的输入为按路径排序的文件记录，字段为 `path`、`mode`、`type`、`blob_sha`、`size`。先将记录序列化为 UTF-8 JSON，使用 `sort_keys=true`、`ensure_ascii=false` 和紧凑分隔符 `(',', ':')`，再计算 SHA-256。Git tree SHA-1 用于核验上游 Git 目录对象；清单 SHA-256 用于核验规范化文件记录。两者用途不同。

机器可读清单：`upstream-asset-manifest.json`。  
复现脚本：`scripts/audit_upstream_assets.py`。  
自动审计：`.github/workflows/validate.yml` 中的 `audit-upstream-assets` job。

## 2. Skill 能力与执行约束

已逐项读取并审查六个文件。Skill 的主要约束如下：

- 通过 Python Playwright 脚本测试本地 Web 应用。
- 使用服务管理 helper 前必须先运行 `scripts/with_server.py --help`。
- 将 helper 作为黑盒调用；只有确需定制时才读取其源码。
- 静态 HTML 优先读取 HTML 文件并识别 selector。
- 动态应用在执行操作前先导航并等待 `networkidle`，再截图或检查 DOM。
- 使用 Playwright sync API 和 headless Chromium，完成后关闭浏览器。
- `SKILL.md` 明确引用了服务 helper 和三个示例文件。目录中没有其他相对引用目标。
- 该目录没有声明 Python 或 Playwright 版本锁定文件。运行时依赖需由实验环境单独固定并记录。

## 3. 源码审查风险

以下是静态源码审查发现，不代表已经在 GitHub Actions 中复现为运行故障。

### R1. 服务就绪检查仅检测 TCP 端口

`with_server.py` 的 `is_server_ready` 通过 `socket.create_connection` 判断端口是否可连接。它不验证 HTTP 响应、健康检查路径或应用初始化完成状态。

**实验影响：** 端口已监听但应用尚未可用时，helper 可能过早启动 Playwright 任务。测试夹具应提供独立健康检查，并记录 helper 返回与 HTTP readiness 的时间差。

### R2. 服务 stdout/stderr 使用 PIPE，但未持续消费

服务进程以 `stdout=subprocess.PIPE` 和 `stderr=subprocess.PIPE` 启动；代码没有后台读取这些管道。若服务输出量超过操作系统管道缓冲区，子进程可能阻塞。

**实验影响：** 服务启动或测试挂起可能来自 helper 的日志管道设计，而非被测 Agent 的 Playwright 能力。应设计可控日志压力试验，并把 helper 故障单独归类。

### R3. 清理逻辑未显式管理进程组

脚本对 `Popen` 返回的 shell 进程调用 `terminate` 和 `kill`，未显式创建或终止进程组。通过 shell 启动的服务子进程可能残留。

**Actions 运行复现：** 在首次运行预检中，helper 使用普通命令 `python -m http.server 4173 ...` 启动服务。Playwright 测试成功，helper 随后输出 `Server 1 stopped` 和 `All servers stopped`，但 helper 进程退出后，TCP 4173 仍接受连接。端口清理断言因此失败。该结果证明普通 shell 子进程在该运行路径中确实残留，不再只是静态推测。

**受控命令规避方式：** 对单进程、可信的固定服务命令，使用 `exec python -m http.server ...` 让 shell 替换为服务进程。这样 helper 持有的 `Popen` 进程就是实际监听进程，终止目标一致。CI 预检已改用该形式复测。

**未解决边界：** 这不是对上游 helper 的修复。helper 仍未显式管理进程组；复合命令、包装脚本或会派生长期存活子进程的服务仍可能留下后代进程。正式实验必须使用受控固定启动命令，并在每次用例后检查端口和进程；不能将本次单进程规避结果推广为多进程清理保证。

### R4. 服务命令使用 shell=True

helper 为支持 `cd &&` 等命令使用 `shell=True`。

**实验影响：** 只能传入仓库内受控、固定的服务启动命令。不得把用例输入、用户文本或不可信资产拼接进服务命令。

### R5. 两个示例使用固定输出路径

`console_logging.py` 和 `static_html_automation.py` 将截图或日志写入 `/mnt/user-data/outputs/`。该路径不是 GitHub Actions runner 的通用路径。

**实验影响：** 示例不能原样假定在 Actions 中可写。被测 Agent 应依据当前环境配置选择输出目录，并将产物放入 Actions 可归档目录。

### R6. networkidle 不是所有动态应用的通用就绪条件

Skill 将 `networkidle` 作为推荐流程，但持续轮询、WebSocket 或长连接应用可能无法进入该状态。

**实验影响：** 首轮 fixture 应采用可稳定进入 `networkidle` 的页面。长连接场景应作为后续独立能力挑战，不应在首轮引入环境不确定性。

## 4. 许可证

已核验 `LICENSE.txt` 内容为 Apache License 2.0。复制或分发该上游 Skill 时，应保留许可证；对修改文件作显著修改声明；保留适用的版权、专利、商标和归属声明。完整目录清单中未发现独立 NOTICE 文件。

## 5. GitHub Actions 运行时预检

**运行：** [42481994066](https://github.com/Kairos0922/evaluation-dataset-builder/actions/runs/42481994066)  
**结果：** `runtime-preflight` job 通过。  
**证据包：** artifact `13617733280`，保留至 2026-11-22。

固定环境：
- DSH CLI：`0.2.2-rc.1`
- Node.js：`24.9.0`
- Python：`3.12`
- Playwright：`1.64.1`
- Chromium headless shell：`156.0.8078.4`

验证结果：
- DSH 组合配置确认 `session-log-deepseek` 已禁用；同时设置 `DSH_TELEMETRY_MODE=DISABLED` 和 `DSH_TELEMETRY_DISABLED=1`。
- 固定 commit 的六个上游文件被复制到临时项目级 Skill 路径，并通过目录比较确认一致。
- 按要求先执行 `with_server.py --help`，退出成功。
- helper 启动自有 HTTP fixture 后，Playwright 成功导航并等待 `networkidle`。
- HTTP 状态为 200，页面标题正确，按钮点击使页面状态从 `Value: 0` 变为 `Value: 1`。
- 浏览器页面异常数为 0，截图已归档。
- 使用 `exec python -m http.server ...` 启动单一受控服务进程后，helper 返回时 TCP 4173 端口保持关闭。

**重要限制：** 第一次使用普通 `python -m http.server ...` 命令的运行中，浏览器检查成功，但 helper 退出后端口仍在监听。随后改用 `exec` 让 shell 进程替换为服务器进程，端口清理检查通过。该规避只适用于受控的单进程命令，不证明 helper 能可靠清理复合命令或多进程服务。上文 R3 已记录首次失败的实测证据。

**本次没有做的事情：**
- 没有向 DSH 发起 Agent 对话或调用 `webapp-testing` Skill。
- 没有调用 Evaluation Dataset Builder 生成正式用例。
- 没有运行被测 Skill 的业务能力测试。
- 没有读取隐藏 Gold Oracle，也没有计算任何 Skill 质量分数。

本次验证的是 CI 运行时、依赖、浏览器和服务 helper 的受控单进程执行路径，不是 Skill 能力评测。

## 6. 资产冻结与实验边界

**已完成：**
- 固定上游 commit 和 Skill 根目录 Git tree SHA。
- 完整递归文件清单核验，确认 GitHub API 未截断结果。
- 六个文件的路径、模式、大小和 Blob SHA 核验。
- 两个子目录 tree SHA 和规范化清单 SHA-256 核验。
- 许可证、指令、示例和 helper 的静态内容审查。
- GitHub Actions 重复生成并逐字节比对完整资产 manifest。
- 固定 DSH、Node.js、Python、Playwright 和 Chromium 版本。
- 验证 DSH Session Log 与 OTel 上传关闭配置。
- 执行 `with_server.py --help` 和本地浏览器操作。
- 在受控单进程 `exec` 命令下确认 helper 结束后端口释放。
- 记录普通 shell 子进程残留的实测失败边界。

**尚未完成：**
- 使用 DSH Headless 实际调用 `webapp-testing` Skill。
- 由 Evaluation Dataset Builder 根据上游公开资产自动生成正式评测套件。
- 构建并冻结独立 Gold Oracle 和本地业务应用测试场景。
- 运行被测 Skill 的正式评测与独立判定。
- 评估复合命令、多进程服务和高日志量下的 helper 生命周期问题。

## 7. 当前结论

上游资产已完成静态完整冻结，且固定依赖、DSH 隔离配置、Playwright/Chromium 浏览器运行、受控单进程服务启停均已在 GitHub Actions 中通过预检。相关审计和浏览器证据已归档。

这只表示**实验环境具备进入下一阶段的基础条件**。被测 `webapp-testing` Skill 尚未通过 DSH 实际调用，Evaluation Dataset Builder 也尚未生产该 Skill 的正式评测套件，因此整体实验状态仍为 `DESIGN_ONLY`。下一阶段必须先由 Builder 自动生成正式评测套件，再由 DSH 调用被测 Skill 消费这些用例，并由独立 Oracle 判定。
