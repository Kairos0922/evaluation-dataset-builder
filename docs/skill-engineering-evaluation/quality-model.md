# Skill Quality Evaluation Model

**Version:** 0.1.0  
**Status:** Proposed measurement model; metrics are not empirically validated.  
**Target baseline:** Evaluation Dataset Builder Skill v0.0.2.

## 1. Measurement principles

This model evaluates a Skill as an intervention in an Agent workflow. It separates package conformance, use behavior, and outcome quality.

Every reported metric must identify:
- evaluation batch and protocol version;
- Skill package version, commit SHA, and Skill-tree SHA;
- task-suite ID/version and task/item IDs;
- host, model identity/revision, harness, tools, and relevant configuration;
- numerator, denominator, unit, and exclusion rules;
- evidence references and evidence type;
- uncertainty and missingness status;
- applicable task/host/model scope.

Do not average heterogeneous metrics into a composite score. Do not interpret an unavailable denominator as zero. Use NOT_APPLICABLE for a genuine zero denominator, NOT_RUN when the procedure was not executed, NOT_ASSESSED when evidence was not evaluated, and UNKNOWN when the available evidence cannot support a decision.

## 2. Layer 0 — Package conformance (gate, not score)

Reuse `scripts/validate_skill.py` and offline tests.

Checks include:
- Agent Skills metadata and naming constraints;
- package contents and direct reference links;
- reference existence and prohibited second-level reference chains;
- schema validity and internal consistency;
- static test-suite shape and positive/negative trigger sample counts.

Report validator version, command, exit status, commit SHA, and complete log. A passing static check proves only the encoded constraints. It does not prove discoverability, semantic quality, or runtime compatibility.

## 3. Dimension D1 — Discovery

**Question:** Does the Skill activate for requests that need it and remain inactive for requests that do not?

Use the existing `tests/trigger-evals.json` as the initial labelled set. Preserve the 20 positive / 20 negative split unless a documented relabelling review changes the suite.

Let TP = relevant requests correctly activated; FP = irrelevant requests incorrectly activated; FN = relevant requests missed; TN = irrelevant requests correctly not activated.

- Trigger Precision = TP / (TP + FP)
- Trigger Recall = TP / (TP + FN)
- Trigger F1 = 2 × Precision × Recall / (Precision + Recall), when the denominator is non-zero.
- False Activation Rate = FP / (FP + TN)
- Missed Activation Rate = FN / (TP + FN)

Always report the confusion matrix and raw counts. Precision and recall are not interchangeable. A high recall with frequent irrelevant activation is not sufficient.

**Evidence:** frozen labelled prompts, actual host activation evidence or an explicitly identified trigger-classification proxy, raw predictions, and independent label review.

**Important limitation:** the current `run_eval.py` classifies trigger examples through a model-based Judge. This is a proxy evaluation, not direct evidence that a particular host actually discovered and activated the Skill. Host-specific discovery requires the target-runtime procedure.

No universal pass threshold is assigned by this model. Any release gate threshold must be separately justified for its decision context.

## 4. Dimension D2 — Progressive disclosure / reference navigation

**Question:** Does the Agent read the right reference material for the task, at the right time, with neither critical omissions nor unnecessary loading?

For each task, create an independently reviewed reference-dependency annotation:
- required references;
- critical references;
- conditionally relevant references;
- references that are not relevant to the task.

Record actual file-open/read events. Merely having a reference in the package, mentioning its path, or receiving its contents as an implicit system prompt does not count as an observed read.

Metrics:
- Required Reference Recall = required references actually read / required references.
- Relevant Read Precision = relevant references actually read / all references actually read.
- Critical Reference Omission Rate = tasks with at least one omitted critical reference / tasks requiring one or more critical references.
- Unnecessary Read Rate = irrelevant reference reads / all reference reads.
- Task Navigation Success = tasks that read all critical references and no disqualifying irrelevant resources / tasks with a complete and observable navigation trace.

Report both reference-level and task-level counts. A task can fail navigation despite a high aggregate reference recall if it omits one critical reference.

**Evidence:** host or harness file-access events with timestamps, task ID, path, and outcome; dependency annotations frozen before evaluation.

**Current limitation:** the existing `tests/run_eval.py` loads only `SKILL.md` through `load_skill()`. It does not execute a host's on-demand reference loading and does not record reference-read telemetry. Therefore D2 is currently NOT_ASSESSED by that runner.

Do not optimize for the fewest reads. Optimize for sufficient task-relevant context with no critical omissions.

## 5. Dimension D3 — Instruction following

**Question:** Does the Agent apply the Skill's rules correctly, including under ambiguity, conflicting evidence, and multi-rule interactions?

Use the existing SE01–SE12 expected assertions as the initial task rubric. Before scoring, map each assertion to a rule class and severity:

- **Ordinary:** presentation and completeness requirements that do not invalidate the core conclusion.
- **Important:** evidence mapping, coverage accounting, deduplication, grading-contract quality, and change traceability.
- **Critical:** fabricated sources or execution evidence; incorrect evaluation-subject attribution; unsafe authorization or side effects; false PASS when evidence is missing; misuse of UNKNOWN / NOT_RUN / NOT_ASSESSED; bypass of non-compensatory gates.

Metrics:
- Critical Rule Compliance = passed, assessable critical opportunities / all assessable critical opportunities.
- Critical Violation Count = number of independently confirmed critical violations. Always report the count and cases; never average it away.
- Important Rule Compliance = passed, assessable important opportunities / all assessable important opportunities.
- Status Semantics Accuracy = correctly assigned status decisions / assessable status decisions.
- Evaluation Subject Accuracy = correctly attributed subject decisions / assessable multi-subject decisions.
- Unsupported Claim Rate = unsupported factual claims / factual claims independently sampled and reviewed.
- Evaluability Rate = PASS + FAIL decisions / all expected checks; report UNKNOWN separately.

A critical rule opportunity must be defined before seeing the output. Do not count a rule as an opportunity when the task does not invoke it.

**Evidence:** exact output excerpts, source/trace references, deterministic checks where possible, and independent blind adjudication for semantic claims.

The Judge's own UNKNOWN must not silently become FAIL or be removed from the denominator. Report evaluability alongside accuracy/compliance.

## 6. Dimension D4 — Outcome effectiveness

**Question:** Does access to the Skill improve the quality of completed work compared with a matched no-Skill baseline?

Use paired task conditions:
- Condition A: no Evaluation Dataset Builder Skill; a neutral baseline instruction.
- Condition B: the frozen Skill package available to the Agent through the declared host/runtime mechanism.

Keep task input, model identity/revision, sampling parameters, tools, permissions, and environment constant where possible. Randomize condition order where the execution setup permits. If a host or model configuration differs, treat it as a separate stratum rather than attributing the difference to the Skill.

Use a blinded independent rubric covering:
- target and construct alignment;
- source identity and claim support;
- handling of missing/conflicting evidence;
- coverage universe and critical-gap identification;
- semantic redundancy and meaningful variants;
- grading-contract observability and subject consistency;
- execution readiness, permission boundaries, and cleanup;
- output/schema completeness where applicable.

Metrics:
- Baseline and Skill condition task-level pass/fail/unknown counts.
- Paired Outcome Difference = mean (or predeclared ordinal difference) of Skill-condition outcome minus baseline outcome, with the task as the pairing unit.
- Critical Defect Difference = paired difference in independently confirmed critical violations per task.
- Output Evaluability Rate for each condition.
- Per-dimension reviewer distributions and disagreement.

Report raw paired transitions (baseline pass → Skill pass, baseline fail → Skill pass, and the reverse), not only an aggregate difference. Use confidence intervals appropriate to the paired and clustered design when the sample supports them.

**Independence requirement:** a Judge that uses the same model identity as the generator may provide useful automated screening, but it is not an independent evaluator in the strong sense. Preserve that limitation and use blind human review or a genuinely distinct independent evaluation source for claims about semantic outcome quality. Separate API keys alone do not establish evaluator independence.

The existing 12 cases are a small Pilot set. They are not sufficient by themselves to establish broad effectiveness, statistical generalization, or universal superiority.

## 7. Dimension D5 — Cross-runtime compatibility

**Question:** Does a specific host correctly discover, load, and use the package, and respect its file/tool/safety boundaries?

Assess each host separately. Reuse `tests/target-runtime-matrix.md` and `tests/target-runtime-report.schema.json`, after confirming the schema captures every check required by the intended certification.

Minimum stages:
1. package discovery;
2. positive trigger;
3. negative trigger;
4. reference loading;
5. end-to-end task execution;
6. side-effect and authorization checks;
7. cleanup and reset.

For every check, report PASS, FAIL, BLOCKED, or NOT_RUN with evidence references. A host-level PASS requires every required check to pass with auditable evidence. Missing evidence is not PASS.

Do not infer that one host's result applies to another. Do not infer compatibility from installation instructions or package-format conformance.

## 8. Reporting and decision rules

The report must include:
- package-conformance gate;
- each of D1–D5 as a separate profile;
- raw numerators/denominators and confusion matrices where applicable;
- unknown/not-run/not-assessed/not-applicable counts;
- critical violations and affected task IDs;
- host/model/configuration scope;
- evidence references and limitations;
- paired Skill-vs-baseline results;
- unresolved reviewer disagreements.

Do not define a Skill-quality composite score, fixed universal weights, or global pass threshold at this stage. Any future scalar decision rule requires construct definition, independent review, pre-registered decision costs, external validation, and a frozen validation set. Reuse the repository's existing formula-validation governance rather than inventing a parallel validation regime.
