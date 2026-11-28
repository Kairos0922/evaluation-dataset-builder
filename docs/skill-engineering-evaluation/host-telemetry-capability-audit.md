# Host Telemetry Capability Audit

**Audit date:** 2026-11-28  
**Research branch:** `research/skill-engineering-evaluation`  
**Scope:** Observable reference-file access for RN01–RN08. This is a documentation-based capability assessment, not a live host certification.

## 1. Decision

**Recommended first adapter: Claude Code Hooks, restricted to explicit `Read` tool calls.**

Claude Code currently has the strongest documented evidence path for a reference-navigation pilot:

- `PreToolUse` identifies the `Read` tool, its `tool_input.file_path`, `tool_use_id`, and session context.
- `PostToolBatch` provides the resolved tool calls and, for `Read`, the exact serialized `tool_response` content delivered in the corresponding model-visible `tool_result` block.
- `PostToolUseFailure` provides a separate failure path.
- The event contract includes `session_id`, `tool_use_id`, path, result, and error information needed to correlate a read attempt with its delivery outcome.

This is sufficient to implement a narrow, evidence-backed adapter for explicit `Read` calls. It is **not** proof that all file access performed by Claude Code is observable.

Official references:
- Claude Code Hooks reference: https://code.claude.com/docs/en/hooks
- Claude Agent Skills architecture: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

## 2. Capability matrix

Status meanings:
- **DOCUMENTED:** official documentation describes the relevant mechanism.
- **PARTIAL:** useful telemetry exists, but known paths or required fields are not covered by the documented event contract.
- **NOT_DOCUMENTED:** the reviewed official documentation does not establish the capability. This is not proof that the product has no internal telemetry.
- **NOT_TESTED:** no live adapter or host run has verified the behavior.

| Host | Read/tool lifecycle | Model-visible content evidence | Correlation | Important gaps | Assessment |
|---|---|---|---|---|---|
| Claude Code | `PreToolUse`, `PostToolBatch`, `PostToolUseFailure`; explicit `Read` tool | `PostToolBatch.tool_calls[].tool_response` is documented as the same content the model receives in the `tool_result` block | `session_id`, `tool_use_id`; task ID must be supplied by the harness | Skill-injected shell commands are handled by `PreSkillShellCommand`, which exposes the command before execution, not its returned file content. Prompt `@file` mentions can inject content without a Read tool call. | **DOCUMENTED / best first candidate; NOT_TESTED** |
| Codex CLI | `PreToolUse` and `PostToolUse` hooks cover Bash, MCP tools, and other local function tools | `PostToolUse.tool_response` is the tool-specific output; MCP and local function tools expose model-facing output | `turn_id`, `tool_use_id`, session context | The reviewed docs do not establish a universal stable built-in file-read tool contract across all internal file-access paths. Bash output can be logged, but command text alone is not proof that a file's content reached the model. | **DOCUMENTED / PARTIAL; NOT_TESTED** |
| Claude API — Messages API | Tool use is explicit in the Messages API protocol; application code executes client-side tools and returns tool results | A harness-controlled file-read tool can preserve the exact result sent back as `tool_result` | Application can assign task/session/tool IDs | Native Skill-internal file reads through hosted code execution are not established as per-file audit events by the reviewed Skills documentation. A custom harness would need to own the read tool or instrument the execution boundary. | **PARTIAL; NOT_TESTED** |
| Claude Managed Agents | Skills run in a managed execution environment; session/event APIs are documented | Reviewed docs do not establish per-file read result events for Skill reference files | Session correlation exists at the managed-agent layer | Per-file path + delivered bytes + failure semantics need confirmation in a live API/harness experiment. | **NOT_DOCUMENTED for per-file reads; NOT_TESTED** |
| claude.ai | Skills can be uploaded and enabled | Reviewed public docs describe Skill use and progressive disclosure, but not a user-accessible per-file read event stream | Not established | No documented hook/export contract for per-file reads in the reviewed sources. | **NOT_DOCUMENTED; NOT_TESTED** |

Official references:
- Codex Hooks: https://learn.chatgpt.com/docs/hooks
- OpenAI Agents API tracing: https://developers.openai.com/api/docs/guides/agents-api/tracing
- Claude Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Claude API tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

## 3. Claude Code evidence semantics

The adapter must preserve the distinction between an attempted read and content delivery.

| Hook observation | Normalized event | Counts as a delivered reference read? |
|---|---|---:|
| `PreToolUse` with `tool_name == "Read"` | `FILE_READ_REQUESTED` | No |
| `PostToolBatch` entry with `tool_name == "Read"` and a returned `tool_response` | `CONTENT_DELIVERED` | Yes, when path and response can be validated |
| `PostToolUseFailure` for `Read` | `FILE_READ_FAILED` | No |
| File injected by prompt mention or another preloaded mechanism | `PRELOADED_CONTEXT` only when independently evidenced by the harness | No selective read |
| Skill-injected shell command | Request/command metadata only unless a separate reliable result event is captured | No, not from the pre-hook alone |

The official Hooks documentation explicitly notes two coverage caveats:
1. `PreToolUse` does not fire for injected shell commands used while a Skill loads; `PreSkillShellCommand` runs before those commands and exposes the command input.
2. Files referenced with `@` can be inserted into the prompt without a tool call, so a Read hook will not observe them by default.

For the first Pilot, avoid these unobservable paths rather than pretending they are captured:
- Disable file-mention prompt injection using `CLAUDE_CODE_DISABLE_FILE_MENTIONS=1` in the controlled test environment (supported in documented recent Claude Code versions).
- Do not use `!` injected shell commands in the test Skill package or test prompt.
- Restrict navigation measurement to explicit `Read` calls. If a run reads reference files through Bash/PowerShell or another path, mark that access as unclassified / NOT_ASSESSED; do not infer a successful selective read from the command string.
- Preserve all hook payloads as raw evidence. Never use the Agent's own statement that it read a file as evidence.

These restrictions narrow the claim: the Pilot measures explicit Read-tool navigation under a controlled Claude Code setup, not every possible way Claude Code can obtain file contents.

## 4. First adapter contract

### 4.1 Hook subscriptions

Register project-local command hooks for:

1. `PreToolUse`, matcher `Read`: record the read request.
2. `PostToolBatch`: inspect every entry in `tool_calls`; emit delivery events only for `tool_name == "Read"`.
3. `PostToolUseFailure`, matcher `Read`: record failed reads.

Use `PostToolBatch` for delivery evidence rather than `PostToolUse`: the Hooks reference documents the former's `tool_response` as the exact model-visible `tool_result` content. `PostToolUse` has a different structured output shape.

### 4.2 Required correlation metadata

The hook payload supplies `session_id` and `tool_use_id`. The harness must supply and freeze:
- `EDB_TASK_ID`
- `EDB_SKILL_COMMIT_SHA`
- `EDB_SKILL_TREE_SHA`
- `EDB_SKILL_ROOT`
- an output location for raw hook evidence and normalized JSONL events

Capture host version and model identity from the actual launch/session configuration, not from the Agent's answer. If unavailable, preserve null/unknown rather than guessing.

### 4.3 Delivery proof

For each successful Read result:
- Resolve the absolute path against the frozen Skill root.
- Reject paths outside the Skill package and paths that do not map to a declared reference.
- Hash the exact serialized `tool_response` payload that the model received (UTF-8 SHA-256).
- Record byte count, relative path, session ID, tool-use ID, timestamp, and raw evidence reference.
- Keep the raw hook payload; normalized JSONL is an index, not a substitute for source evidence.

A path mention, a successful pre-hook, or a file-system existence check is not delivery proof.

### 4.4 Schema delta to consider before implementation

The current `tests/reference-read-event.schema.json` does not yet contain a `tool_use_id` field. Add an optional `tool_use_id` (and, if useful, `host_event_name`) before implementing the adapter so request and delivery events can be joined without relying on timestamps or path equality alone.

The current event schema can represent the main event types. Do not add host-specific claims to the shared schema; keep Claude Code payload parsing in a host adapter and normalize into the shared event contract.

## 5. Pilot execution scope

Start with the smallest set that exercises distinct evidence paths:

- **RN01:** required human-readable references; verify two explicit Read deliveries and no irrelevant schema reads.
- **RN05:** required machine-readable dataset and manifest schemas; verify both content payloads were delivered before final serialization.
- **RN08:** negative task; verify no Skill reference Read calls. Any preloaded content must be separately recorded, not counted as selective navigation.

Do not start with all eight navigation cases. RN01/RN05/RN08 cover required reads, schema reads, and a negative control with minimal execution cost.

For each case, run a controlled, read-only task with a frozen Skill tree and unique task ID. Keep the model, host version, prompt, permissions, and context-loading configuration fixed across replications. The first adapter-validation run should use synthetic fixture content and should not modify the production Skill package.

## 6. Exit criteria for calling the adapter operational

The adapter is **IMPLEMENTED** only after:
1. Hook payloads from a real Claude Code session are captured.
2. Read request and delivered-content events correlate by `tool_use_id`.
3. The recorded content hash matches the actual model-visible Read response.
4. Failed reads are represented distinctly.
5. A deliberately preloaded or `@`-injected reference is not misclassified as a selective Read.
6. RN01, RN05, and RN08 complete with raw hook evidence and independently checked event records.

Until then, status remains **DESIGN_ONLY / NOT_TESTED**. Offline fixtures can validate the parser but cannot certify the host adapter.

## 7. Sources and limitations

This audit is based on public official documentation available on 2026-11-28. Product documentation establishes the published event contracts; it does not prove that a specific installed version, configuration, or runtime emits complete events in practice. The first real host session is still required.

- Claude Code Hooks reference: https://code.claude.com/docs/en/hooks
- Claude Agent Skills architecture: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Codex Hooks: https://learn.chatgpt.com/docs/hooks
- OpenAI Agents API tracing: https://developers.openai.com/api/docs/guides/agents-api/tracing
- Claude API tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
