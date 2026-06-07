# IEF Operations v0

> IEF Operations Layer — the work operating system that governs task state, run state, evidence, and the event ledger.

## 1. Operations Positioning

IEF-Operations is the **work operating system** of the IEF ecosystem. It answers: *What work is being done now, by whom, under which governance profile, in what state, and with what evidence?*

Operations owns the lifecycle of every unit of work in IEF — from creation through execution to completion or failure. It defines how tasks progress through states, how runs record events, and how the system maintains an auditable, append-only record of work activity.

For v0, Operations is especially responsible for making AI coding agents **obey** task scope, lifecycle stop points, approval gates, evidence requirements, and ledger expectations. This is the current solidity bottleneck for supporting large, complex, multi-agent development work.

### 1.1 What Operations Owns

| Domain | Description |
|---|---|
| Task lifecycle | State machine defining how tasks progress from draft to terminal state |
| Task transition rules | Conditions and evidence required for each state change |
| Run lifecycle | State machine for execution runs within a task |
| Run ledger | Append-only event log that records all run activity |
| Ledger rules | Immutability, ordering, and integrity constraints for the event log |
| Event type semantics | How events are emitted, what they mean, and how they map to state changes |
| Approval gates | Which transitions require human or Program Agent approval |
| Blocked / escalation logic | How blocked tasks are flagged, escalated, and unblocked |
| Artifact linkage rules | How produced artifacts are associated with runs and tasks |
| Context attachment rules | How context references are attached to tasks during execution |
| Agent conformance requirements | How AI coding tools must obey lifecycle, evidence, approval, and ledger rules |

### 1.2 What Operations Does NOT Own

| Domain | Owner |
|---|---|
| TaskEnvelope schema | IEF-Protocol |
| RunEvent schema | IEF-Protocol |
| ArtifactRef schema | IEF-Protocol |
| ContextRef schema | IEF-Protocol |
| Governance profiles and rules | IEF-Governance |
| Runner implementations | IEF-Runners |
| Adapter implementations | IEF-Adapters |
| Knowledge storage | IEF-Knowledge |
| Program coordination | IEF-Program |

### 1.3 Boundary Rules

1. Operations defines **state machines, transition rules, evidence rules, agent conformance rules, and ledger rules**.
2. Operations does **not** define Protocol object schemas — it references them.
3. Operations does **not** define governance profiles — it is constrained by them.
4. Operations does **not** implement runners, adapters, or knowledge storage.
5. Operations may define how `TaskEnvelope.status` values are used, but **Protocol owns the schema field** and **Operations owns the allowed values and transitions**.
6. Operations may define how `RunEvent.event_type` values are emitted, but **Protocol owns the schema** and **Operations owns the semantic mapping**.
7. Operations does **not** create its own Task object schema — it uses `TaskEnvelope` as the exchange format.
8. Operations conformance rules are normative for AI coding agents, but tool-specific implementation belongs to Runners and Adapters.

---

## 2. Baseline Dependencies

Operations v0 is aligned to the merged P1 contract baselines:

| Upstream | Status | Operations dependency |
|---|---|---|
| `IEF-Governance#3` | Merged | Contract-Critical / Implementation-Controlled review and evidence rules |
| `IEF-Protocol#3` | Merged | Protocol v0.1.0 shared object model |
| Protocol merge commit | `7989f09fec6b3ef25e988312b3e7106a37e4cee4` | Stable baseline for object names and schema ownership |

Operations references Protocol v0.1.0 objects by **name and usage only**. It does not copy, redefine, or fork Protocol schemas.

---

## 3. Boundaries with Other Layers

### 3.1 Operations ↔ Program

- **Program** coordinates work across repositories and creates issues that become tasks.
- **Operations** manages the lifecycle of those tasks once they enter the system.
- Program does not define lifecycle rules; Operations does not define program-level coordination.
- Program Controller may create actionable directives; Operations defines how assigned work must move through task/run state and evidence gates.

### 3.2 Operations ↔ Governance

- **Governance** defines profiles that constrain which transitions require approval, what evidence is required, and who can approve.
- **Operations** maps those governance constraints into lifecycle stop points, evidence requirements, and ledger events.
- Operations does not define governance profiles; it consumes and enforces them.

### 3.3 Operations ↔ Protocol

- **Protocol** defines schemas for `TaskEnvelope`, `RunEvent`, `ArtifactRef`, and `ContextRef`.
- **Operations** defines how those objects are used in lifecycle and ledger contexts.
- Operations must never redefine or duplicate Protocol schemas.
- If Protocol changes a field in a future version, Operations must update usage rules through a Contract-Critical follow-up.

### 3.4 Operations ↔ Runners

- **Runners** execute work and emit/report events into the Operations run ledger.
- **Operations** defines what transitions, events, and evidence are required.
- Runners do not define lifecycle rules; Operations does not implement runner logic.

### 3.5 Operations ↔ Knowledge

- **Knowledge** produces and manages context content.
- **Operations** attaches `ContextRef` references to tasks during execution.
- Operations does not store knowledge; it references it and records its usage.

### 3.6 Operations ↔ Adapters

- **Adapters** translate external requests into internal IEF work objects.
- **Operations** receives tasks from adapters and manages their lifecycle.
- Adapters do not define lifecycle rules; Operations does not implement adapter logic.

---

## 4. Operations v0 Minimum Responsibilities

For v0, Operations is responsible for:

1. **Task lifecycle** — Define the 13 task states and valid transitions with entry/exit conditions and evidence requirements.
2. **Run lifecycle** — Define the 8 run states and valid transitions.
3. **Run ledger** — Define append-only event log rules, ordering, immutability, and how events map to state changes.
4. **Protocol object usage** — Define how `TaskEnvelope`, `RunEvent`, `ArtifactRef`, and `ContextRef` are used without redefining schemas.
5. **Governance alignment** — Specify which transitions require review or approval according to Governance profiles.
6. **Agent conformance** — Define how AI coding agents must obey lifecycle, gates, evidence, and ledger expectations.
7. **Downstream readiness gate** — Produce definitions complete enough for Runners, Knowledge, and Adapters to begin contract planning only after this Operations PR is reviewed and approved for that purpose by Program Controller / Human Owner.

---

## 5. Task Lifecycle Overview

The task lifecycle defines how a unit of work progresses from creation to a terminal state.

### 5.1 Task States

```text
draft → ready → assigned → running
                                ├── waiting_input
                                ├── waiting_approval
                                ├── blocked
                                ├── review_pending
                                ├── completed
                                └── failed / cancelled
running → completed / review_pending / failed / cancelled
blocked → escalated
waiting_input / waiting_approval / blocked → resumed → running
```

### 5.2 Stop Points

Operations defines stop points where AI agents must pause instead of continuing autonomously:

| Stop point | Meaning | Required behavior |
|---|---|---|
| `waiting_input` | Missing information or external input | Stop and request input. Do not guess durable facts. |
| `waiting_approval` | Explicit approval required | Stop and request approval. Do not self-approve. |
| `blocked` | Dependency/resource blocker | Stop, record blocker, and wait for unblock/escalation. |
| `review_pending` | Output awaits review | Stop, attach artifacts/evidence, and request review. |
| `escalated` | Normal resolution exceeded | Stop and wait for Program Agent / Human Owner intervention. |

Full state definitions are in [TASK_LIFECYCLE.md](./TASK_LIFECYCLE.md).

---

## 6. Run Lifecycle and Ledger Overview

A run is a single execution attempt within a task. A task may have multiple runs after resume or retry.

```text
prepared → started → in_progress → checkpointed → resumed → completed / failed / cancelled
```

The run ledger is an append-only record of what happened during execution. It is used to reconstruct task state, verify evidence, and support review.

Core ledger principles:

1. **Append-only** — Events are appended, not rewritten.
2. **Immutable** — Corrections use compensating or correction events.
3. **Ordered** — Events are ordered by `sequence` within a run.
4. **Typed** — `event_type` maps to transition or activity semantics.
5. **Protocol-aligned** — Every event is a `RunEvent` as defined by IEF-Protocol.
6. **Terminal-state safe** — Correction events must not move a task out of a terminal state.

Full ledger rules are in [RUN_LEDGER.md](./RUN_LEDGER.md).

---

## 7. How Operations References Protocol Objects

Operations references Protocol objects **by name and usage**, never by redefining their schemas.

### 7.1 TaskEnvelope

- Protocol owns the `TaskEnvelope` schema.
- Operations defines allowed `TaskEnvelope.status` values and transition rules.
- Agents must consume assigned task scope, governance profile, priority, context refs, and artifact refs from the task envelope or linked durable evidence.

### 7.2 RunEvent

- Protocol owns the `RunEvent` schema.
- Operations defines recommended event types, event semantics, and state transition mapping.
- Agents must emit or report equivalent event evidence for major transitions.

### 7.3 ArtifactRef

- Protocol owns the `ArtifactRef` schema.
- Operations defines when artifacts must be produced, linked, and reviewed.
- Agents must use ArtifactRef-style traceability for durable outputs such as PRs, commits, docs, schemas, plans, or reports.

### 7.4 ContextRef

- Protocol owns the `ContextRef` schema.
- Operations defines when context must be attached and how context usage is recorded.
- Agents must not treat private chat or local memory as durable truth unless it is represented through GitHub evidence or a ContextRef-compatible reference.

---

## 8. Operations Conformance Model for AI Coding Agents

This section defines what Operations requires from any AI coding agent or tool. It is normative for IEF work execution, but it does not implement tool-specific runners or adapters.

### 8.1 TaskEnvelope Obedience

An AI coding agent must:

1. Consume the assigned task scope, acceptance criteria, governance profile, and current state before modifying files.
2. Treat GitHub issue/PR comments and approved Program directives as operational evidence.
3. Avoid silently expanding scope beyond the task envelope or latest authorized directive.
4. Avoid treating chat history, local notes, or model memory as durable truth unless linked through ContextRef-style evidence.
5. Report a blocker if scope, authority, target branch, or target files are unclear.

### 8.2 Lifecycle Obedience

An AI coding agent must:

1. Move work only through allowed task states.
2. Stop at `waiting_input`, `waiting_approval`, `blocked`, `review_pending`, or `escalated`.
3. Not continue autonomously across approval or review gates.
4. Not self-approve human/Program gates.
5. Not mark a task complete without required artifacts, evidence, and review outcome.
6. Use direct `running → completed` only when the governance profile does not require review and acceptance evidence is complete.

### 8.3 Evidence Obedience

An AI coding agent must attach evidence before claiming progress or completion:

| Claim | Required evidence |
|---|---|
| Started work | branch/commit/run reference or `run_started`-equivalent report |
| Changed files | commit hash and changed file list |
| Produced output | ArtifactRef-style reference to PR, doc, schema, report, or generated artifact |
| Used context | ContextRef-style reference to issue, PR, doc, file, or approved source |
| Needs input | `waiting_input` reason and requested input |
| Needs approval | `approval_requested` evidence with approver target |
| Blocked | `task_blocked` evidence with blocker reason and unblock condition |
| Ready for review | `review_requested` evidence and ArtifactRef-style output references |
| Completed | `review_completed` / approval evidence where required, or no-review completion evidence and final artifact list |

Implementation-Controlled work must provide test evidence according to Governance profile. Dry-run evidence is supplemental and must not substitute for required L1/L2/L3 evidence where Governance requires it.

### 8.4 Ledger Obedience

An AI coding agent must emit, produce, or report ledger-equivalent evidence for major transitions.

Minimum expected event mappings:

| Operational moment | Recommended RunEvent event_type |
|---|---|
| Task assigned | `task_assigned` |
| Run starts | `run_started` |
| Context attached | `context_attached` |
| Checkpoint saved | `checkpoint_created` |
| Artifact produced | `artifact_produced` |
| Progress reported | `progress` |
| Input/blocker encountered | `task_blocked` |
| Approval requested | `approval_requested` |
| Approval received | `approval_received` |
| Review requested | `review_requested` |
| Review completed | `review_completed` |
| Task completed | `task_completed` |
| Task failed | `task_failed` |
| Task cancelled | `task_cancelled` |
| Task escalated | `task_escalated` |
| Ledger correction | `ledger_correction` |

If a tool cannot emit structured `RunEvent` objects yet, it must report equivalent evidence in GitHub issue/PR comments so a future runner/adapter can map it into the ledger.

### 8.5 Boundary Obedience

An AI coding agent must not:

1. Redefine Protocol schemas.
2. Redefine Governance profiles.
3. Start downstream repos unless Program Controller explicitly unblocks them.
4. Merge PRs or close core issues without explicit authorization.
5. Modify sibling repositories unless operating under a Program Controller directive with explicit standing delegation authority.
6. Treat generated output as durable artifact unless it is linked through an ArtifactRef-style reference.

### 8.6 Tool-Surface Mapping

| Tool / Surface | Likely control surface | Operations conformance approach |
|---|---|---|
| Codex App / IDE | GitHub issue, PR body, repo instructions, PR comments | Consume GitHub directives; obey no-scope-expansion and no-self-merge gates; report evidence in PR comments. |
| Claude Code | `CLAUDE.md`, `AGENTS.md`, local instructions, GitHub issue | Inject lifecycle and stop-point rules into project instructions; stop at approval/review gates. |
| Qoder IDE | Workspace prompt plus GitHub sync prompt | Use `SYNC_FROM_GITHUB`; act only on `ACTION REQUIRED`; return Operations Sync/Alignment Reports. |
| Gemini CLI | CLI instruction file, command prompt, GitHub issue | Load task envelope and lifecycle checklist before file changes; report blockers instead of guessing. |
| Antigravity | Workspace/project instructions plus GitHub PR loop | Treat GitHub as control plane; require evidence and gate compliance before completion. |
| OpenClaw / Hermes-style agents | `agents.md`, `memory.md`, channel routing, GitHub API | Consume GitHub task state; emit ledger/status comments; do not rely on private chat memory as source of truth. |

### 8.7 Parallel Multi-Agent Execution Rules

For large projects with multiple agents working in parallel:

1. Each agent must have one assigned task envelope or clearly scoped issue/PR directive.
2. Agents must not share implicit state through chat memory; shared state must be in GitHub, Protocol objects, or ContextRef-compatible evidence.
3. Cross-agent dependency must be represented as `blocked`, `waiting_input`, or `waiting_approval`, not informal prose only.
4. Program Controller decides when downstream repos are unblocked.
5. Runners, Knowledge, and Adapters must remain blocked from contract planning and implementation until this Operations PR is reviewed and Program Controller / Human Owner explicitly unblocks the next stage.
6. Stage reviews must convert non-blocking findings into follow-up issues rather than expanding the active PR indefinitely.

---

## 9. How Operations Is Constrained by Governance Contract-Critical Profile

Operations#2 operates under the **Contract-Critical** governance profile as defined by IEF-Governance#2 and the merged Governance baseline.

### 9.1 Contract-Critical Requirements for Operations

| Requirement | How Operations Complies |
|---|---|
| Linked issue exists | IEF-Operations#2 |
| Design document or RFC reference | This document plus `TASK_LIFECYCLE.md` and `RUN_LEDGER.md` |
| Explicit input/output contract documented | State machines, conformance rules, event mappings, evidence requirements |
| Explicit boundary documented | Sections 1.2, 1.3, 3, and 8.5 |
| Schema/example/validation rule provided | State transition tables, event type mappings, evidence tables, ledger rules |
| Cross-review from another repo perspective | Program, Protocol, Governance, and downstream planning perspectives |
| Program Controller or human approval before merge | Required before this PR merges |
| Rollback plan documented | PR body rollback plan |

### 9.2 Governance Review in Lifecycle

Certain task transitions require governance review or approval:

- `waiting_approval → resumed`: explicit approval required.
- `review_pending → completed`: review approval required.
- `blocked → escalated`: Program Agent intervention required.
- `running → cancelled`: authorized party confirmation required.

These gates are defined in `TASK_LIFECYCLE.md` and are consistent with the Contract-Critical profile requirements.

---

## 10. Cross-References

| Reference | Relationship |
|---|---|
| [IEF-Program#6](https://github.com/everwork-ai/IEF-Program/issues/6) | P1-Contracts execution plan |
| [IEF-Program#9](https://github.com/everwork-ai/IEF-Program/issues/9) | Operations-led multi-agent execution solidity plan |
| [IEF-Governance#2](https://github.com/everwork-ai/IEF-Governance/issues/2) | Contract-Critical profile governing this PR |
| [IEF-Protocol#2](https://github.com/everwork-ai/IEF-Protocol/issues/2) | Shared object model issue |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Merged Protocol v0.1.0 baseline |
| [IEF-Runners#2](https://github.com/everwork-ai/IEF-Runners/issues/2) | Blocked until Operations PR is reviewed and next-stage planning is explicitly unblocked |
| [IEF-Knowledge#2](https://github.com/everwork-ai/IEF-Knowledge/issues/2) | Blocked until Operations PR is reviewed and next-stage planning is explicitly unblocked |
| [IEF-Adapters#2](https://github.com/everwork-ai/IEF-Adapters/issues/2) | Blocked until Operations PR is reviewed and next-stage planning is explicitly unblocked |

---

## 11. Review Status

This document is aligned to merged Protocol v0.1.0 and is under formal review. `TASK_LIFECYCLE.md` and `RUN_LEDGER.md` remain the detailed lifecycle and ledger references. Downstream contract planning must remain blocked until this Operations PR is reviewed and Program Controller / Human Owner explicitly opens the next stage.

---

## 12. Stage D P0: Minimum Lifecycle/Ledger Path (GitHub-First Closed Loop)

> Source of truth: [everwork-ai/IEF-Operations#4 comment 4618600457](https://github.com/everwork-ai/IEF-Operations/issues/4#issuecomment-4618600457)
> Boundary: Contract spec only. No implementation code. No multi-runner orchestration. No chat/AI ingestion.

This section defines the **minimum closed loop** through which a GitHub directive flows end-to-end:

```text
GitHub directive/comment
  -> TaskEnvelope intake (from Adapters layer)
  -> lifecycle states (pending -> dispatched -> running -> completed/failed/blocked)
  -> RunEvent names (run_started, run_completed, run_failed, run_stopped, run_blocked, run_cancelled, run_timed_out)
  -> append-only ledger
  -> evidence / ArtifactRef
  -> review gate
  -> accepted / escalated
```

### 12.1 TaskEnvelope Intake (GitHub-First Only)

Operations receives `TaskEnvelope` objects from the Adapters layer (GitHub-first ingestion only). The minimum intake contract:

```text
TaskEnvelope {
  envelope_id: <UUID>
  dedupe_key: <string>                    // SHA-256 from adapter
  source_event_id: <string>               // GitHub event_id
  source_type: "github_issue_comment" | "github_issue" | "github_pr_comment"
  intent: "directive"
  target_repo: <string>                   // owner/repo
  target_pr: <number | null>
  target_issue: <number | null>
  actor: <string>                         // GitHub login
  directive_text: <string>
  branch: <string | null>
  allowed_files: <string[] | null>
  forbidden_actions: <string[] | null>
  done_criteria: <string | null>
  created_at: <ISO-8601 UTC>
}
```

**Intake rules:**

- Validate envelope against Protocol schema -> reject with `schema_validation_failed` if invalid.
- Check `dedupe_key` against ledger -> if already processed, acknowledge but do not re-dispatch.
- Envelope `actor` must match a known GitHub identity -> reject with `identity_unknown` if not.
- `intent` must be `"directive"` -> other intents are logged but not dispatched in this P0 scope.

### 12.2 Minimum Lifecycle States

For the GitHub-first closed loop, the minimum lifecycle state machine:

| State | Trigger | Next State(s) | Evidence Required |
|---|---|---|---|
| `pending` | TaskEnvelope intake | `dispatched` | -- |
| `dispatched` | Ops dispatch to runner | `running` | `dispatched` ledger entry with runner_id |
| `running` | Runner emits `started` | `completed`, `blocked`, `waiting_approval`, `failed`, `stopped`, `cancelled` | `run_started` ledger entry |
| `completed` | Runner emits `completed` + review gate passes | `accepted` | `run_completed` + `review_accepted` |
| `failed` | Runner emits `failed` | `retried` or `escalated` | `run_failed` with error_code |
| `blocked` | Runner emits `blocked`/`stopped` | `dispatched` (retry) or `escalated` | `run_blocked` with reason |
| `waiting_approval` | Review gate requires approval | `dispatched` (after approval) or `failed` (denied) | `approval_requested` |
| `accepted` | Review gate accepts | _(terminal)_ | `review_accepted` ledger entry |
| `escalated` | Failure needs human/Program intervention | _(terminal until Program resolves)_ | `escalation` ledger entry |

**Critical rules:**

- A task **cannot** transition to `accepted` without an external review gate decision. No self-approval.
- A task **cannot** transition from `running` to `completed` without the runner emitting `completed` with `exit_code = 0`.
- The `stopped`, `cancelled`, and `blocked` states are reversible via retry (back to `dispatched`) or escalation (to `escalated`).

Full state definitions and transition rules are in [TASK_LIFECYCLE.md](./TASK_LIFECYCLE.md) Section 8.

### 12.3 RunEvent Name Catalog (Minimum)

Runners emit `RunEvent` objects. The minimum set for the closed loop:

| RunEvent Name | When Emitted | Key Fields |
|---|---|---|
| `run_started` | Runner begins execution | `envelope_id`, `runner_id`, `tool_runner_type`, `started_at` |
| `run_completed` | Runner finishes with exit 0 | `envelope_id`, `runner_id`, `exit_code`, `finished_at`, `artifact_refs[]` |
| `run_failed` | Runner exits non-zero or errors | `envelope_id`, `runner_id`, `error_code`, `error_message`, `finished_at` |
| `run_stopped` | Runner stops on operator signal | `envelope_id`, `runner_id`, `reason`, `stopped_at`, `partial_artifacts[]` |
| `run_blocked` | Runner blocked by missing input/gate | `envelope_id`, `runner_id`, `reason_code`, `blocked_at` |
| `run_cancelled` | Runner cancelled by operator | `envelope_id`, `runner_id`, `reason`, `cancelled_at` |
| `run_timed_out` | Runner exceeds timeout | `envelope_id`, `runner_id`, `elapsed_ms`, `timeout_ms` |

Full ledger schema and rules are in [RUN_LEDGER.md](./RUN_LEDGER.md) Section 8.

### 12.4 Scope Exclusions

**Excluded from the P0 minimum loop:**

- Full P2 backlog (21 items)
- Multi-runner orchestration
- External tool integrations
- Chat/AI ingestion
- Runner self-approval
- Downstream repo implementation

These are deferred to later stages. The P0 loop is the narrowest possible path that demonstrates end-to-end GitHub-first task lifecycle with evidence and review gates.
