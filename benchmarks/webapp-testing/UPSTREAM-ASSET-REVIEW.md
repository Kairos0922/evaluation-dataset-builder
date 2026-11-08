# webapp-testing 上游资产审查记录

**审查对象：** `anthropics/skills/skills/webapp-testing`  
**冻结 Commit：** `2c5958ecac7cee2b583967a2c4981d0f4a75c579`  
**审查状态：** 关键文件已核验；完整目录清单待补  
**实验状态：** DESIGN_ONLY  
**用途：** 为 Builder 的公开输入资产包提供可追溯来源；本文件不是评测用例。

## 1. 已核验文件

以下 Blob SHA 均来自 GitHub 固定 Commit 的文件读取结果：

| 路径 | Blob SHA |
|---|---|
| `skills/webapp-testing/SKILL.md` | `4726215301db64a0cc4d41fc3219c61f37a30f4a` |
| `skills/webapp-testing/LICENSE.txt` | `4f881c52d1f72f4cfb720e339e2d35c3058d01a9` |
| `skills/webapp-testing/scripts/with_server.py` | `431f2eba16b268b7f3e2ae4daae9db41c0289b6d` |
| `skills/webapp-testing/examples/console_logging.py` | `9329b5e232ed53d944bfe95e750070117d31b9ab` |
| `skills/webapp-testing/examples/element_discovery.py` | `917ba72f52421a1b324f93ae8e38af72010a87b9` |
| `skills/webapp-testing/examples/static_html_automation.py` | `90bbedcc08cdb345c74fb938ebad02c0baf56603` |

**完整性限制：** 当前审查只核验了上表 6 个文件。尚未获得该 Skill 目录在固定 commit 下的递归 Git tree 清单，因此不能声称这是完整文件清单，也不能声称已经计算出目录树哈希。进入正式资产冻结前，必须取得完整 tree，并将全部文件纳入 manifest；若目录还有未核验文件，需逐一审查其用途、依赖和许可证状态。

## 2. Skill 能力与执行约束（来自 SKILL.md）

Skill 明确要求：

- 通过 Python Playwright 脚本测试本地 Web 应用。
- 使用前先运行 `scripts/with_server.py --help`。
- 将该 helper 作为黑盒调用；只有确实需要定制时才读取源代码。
- 静态 HTML 优先读取 HTML 识别 selector。
- 动态应用在执行操作前先导航并等待 `networkidle`，再截图或检查 DOM。
- 使用 Playwright sync API、headless Chromium，完成后关闭浏览器。
- Skill 只提供指令、helper 和示例；它没有在该目录内声明固定的 Playwright/Python 依赖锁文件。

因此，正式测试必须把 Skill 指令遵循与底层依赖可用性分开记录。依赖安装成功不代表 Agent 正确使用 Skill。

## 3. 已发现的可验证风险

以下是源代码审查发现的风险，不等于已在 Actions 中复现的运行缺陷。

### R1. 服务就绪检查仅检测 TCP 端口

`with_server.py` 的 `is_server_ready` 通过 `socket.create_connection` 判断端口是否可连接。它不验证 HTTP 响应、健康检查路径或应用初始化完成状态。

**实验影响：** 端口已监听但应用尚未可用时，helper 可能过早开始 Playwright 任务。测试夹具应提供独立健康检查；记录 helper 返回与 HTTP readiness 的时间差。

### R2. 服务 stdout/stderr 使用 PIPE，但未持续消费

服务进程以 `stdout=subprocess.PIPE` 和 `stderr=subprocess.PIPE` 启动；代码没有后台读取这些管道。若服务输出量超过操作系统管道缓冲区，子进程可能阻塞。

**实验影响：** 服务启动或测试挂起可能来自 helper 的日志管道设计，而非被测 Agent 的 Playwright 能力。需设计可控日志压力试验，且将 helper 故障单独归类。

### R3. 清理逻辑未显式管理进程组

脚本对 `Popen` 返回的 shell 进程调用 `terminate`/ `kill`，未显式创建或终止进程组。通过 shell 启动的服务子进程可能残留。

**实验影响：** 端口占用、跨用例状态污染和 runner 资源泄漏可能影响后续样本。需通过 PID/进程树和端口状态验证清理完整性。

### R4. 服务命令使用 shell=True

helper 为支持 `cd &&` 等命令使用 `shell=True`。

**实验影响：** 只能传入仓库内受控、固定的服务启动命令；不得把用例输入、用户文本或不可信资产拼接进服务命令。需要在 Workflow 中限制命令来源。

### R5. 示例使用特定输出目录

`console_logging.py` 和 `static_html_automation.py` 将截图/日志写入 `/mnt/user-data/outputs/`。该路径不是 GitHub Actions runner 的通用路径。

**实验影响：** 示例不能原样假定在 Actions 可写。被测 Agent 应依据当前环境配置选择输出目录，并将产物放入 Actions 可归档目录；不能把路径适配失败直接归因于 Playwright 功能失败。

### R6. networkidle 并非所有动态应用的通用就绪条件

Skill 把 `networkidle` 作为其推荐流程，但持续轮询、WebSocket 或长连接应用可能无法进入该状态。

**实验影响：** 首轮 fixture 应采用可稳定进入 networkidle 的页面，以测试 Skill 原生流程。若以后测试长连接应用，应将替代等待策略作为明确能力挑战，而不是在首轮混入环境不确定性。

## 4. 许可证

已核验 `LICENSE.txt` 内容为 Apache License 2.0。复制/分发该上游 Skill 时，需保留许可证；对修改文件作显著修改声明；保留适用的版权、专利、商标和归属声明。当前固定文件中未发现独立 NOTICE 文件，但完整目录清点时仍须确认。

## 5. 资产冻结前必须补齐的事项

- [ ] 获取固定 commit 下 `skills/webapp-testing/` 的完整递归 tree。
- [ ] 逐一核验 tree 中全部文件的 Blob SHA 和文件内容。
- [ ] 计算并记录规范化文件清单哈希（明确哈希算法、路径排序和换行处理）。
- [ ] 检查隐藏文件、符号链接、脚本引用、示例引用和未声明依赖。
- [ ] 执行 `with_server.py --help`，记录真实输出和退出码；不要预先假定其行为。
- [ ] 由 Actions 运行时验证 Python、Playwright、Chromium 和 DSH Shell 的兼容性。
- [ ] 验证服务进程启动、就绪、日志、退出和子进程清理。
- [ ] 在复制目录时保留 Apache 2.0 许可证及必要归属/修改声明。

## 6. 当前结论

上游 Skill 的核心指令、helper、三个示例和许可证已在固定 commit 下逐文件核验。它适合作为待测对象，但服务生命周期 helper 和示例输出路径带来明确的 CI 适配风险。

**目前不满足完整资产冻结条件。** 在完整 tree、依赖与运行约束得到核验前，不应把这份部分文件清单标记为最终 B0 资产包，也不应开始正式 Builder 生产或 B0 评分。
