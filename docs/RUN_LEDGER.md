# IEF Run Ledger v0

> Defines the run lifecycle, the append-only event ledger, ledger rules, and how Protocol objects are used within the ledger.

## 1. Run Lifecycle

A run is a single execution attempt within a task. A task may have multiple runs — for example, after a resume or retry. Each run has its own lifecycle, distinct from the task lifecycle.

### 1.1 Run States

```text
prepared → started → in_progress → checkpointed → resumed → completed / failed / cancelled
```

### 1.2 State Definitions

#### prepared

| Attribute | Value |
|---|---|
| **Meaning** | Run has been created and configured but execution has not started. Context is attached, runner is selected, and resources are allocated. |
| **Entry condition** | Task transitions to `running` or `resumed`; a run is created or resumed. |
| **Exit condition** | Runner confirms it is ready to begin execution. |
| **Allowed next states** | `started` |
| **Corresponding RunEvent type** | `run_prepared` |

#### started

| Attribute | Value |
|---|---|
| **Meaning** | Runner has confirmed execution has begun. The run is now active. |
| **Entry condition** | Runner accepts the prepared run and signals start. |
| **Exit condition** | Runner begins making progress or encounters an issue. |
| **Allowed next states** | `in_progress`, `failed`, `cancelled` (run-level); when the task enters a suspension gate (`waiting_input`, `waiting_approval`, `blocked`, `review_pending`), the run remains `started` — these are task-level state changes |
| **Corresponding RunEvent type** | `run_started` |

#### in_progress

| Attribute | Value |
|---|---|
| **Meaning** | Run is actively executing. Progress events are being emitted. |
| **Entry condition** | Runner begins making progress after start. |
| **Exit condition** | Runner reaches a checkpoint, completes execution, encounters an error, or the run is cancelled. |
| **Allowed next states** | `checkpointed`, `completed`, `failed`, `cancelled` (run-level); when the task enters a suspension gate (`waiting_input`, `waiting_approval`, `blocked`, `review_pending`), the run remains `in_progress` — these are task-level state changes |
| **Corresponding RunEvent type** | `progress` (ongoing) |

#### checkpointed

| Attribute | Value |
|---|---|
| **Meaning** | Run has reached a checkpoint — a known-good intermediate state that can be resumed from if the run is interrupted. |
| **Entry condition** | Runner explicitly saves a checkpoint with the current state of execution. |
| **Exit condition** | Run continues, is interrupted, or is explicitly resumed later. |
| **Allowed next states** | `in_progress`, `resumed` |
| **Corresponding RunEvent type** | `checkpoint_created` |

#### resumed

| Attribute | Value |
|---|---|
| **Meaning** | Run is resuming from a checkpoint or interruption. This is a transient state — the run immediately transitions to `in_progress`. |
| **Entry condition** | Run is restarted from a checkpoint or after an interruption. |
| **Exit condition** | Runner confirms execution has resumed. |
| **Allowed next states** | `in_progress`, `failed`, `cancelled` (run-level); when the task enters a suspension gate (`waiting_input`, `waiting_approval`, `blocked`, `review_pending`), the run remains in its current state — these are task-level state changes |
| **Corresponding RunEvent type** | `task_resumed` (task-level evidence); `run_started` or `progress` (run-level continuation evidence) |

#### completed

| Attribute | Value |
|---|---|
| **Meaning** | Run finished successfully. All expected output has been produced. |
| **Entry condition** | Runner completes execution and produces final output. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None |
| **Corresponding RunEvent type** | `run_completed` (run-level terminal); `task_completed` used only when completing this run also completes the task |

#### failed

| Attribute | Value |
|---|---|
| **Meaning** | Run encountered an unrecoverable error and cannot complete. |
| **Entry condition** | Runner encounters an error that prevents completion. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None |
| **Corresponding RunEvent type** | `run_failed` with error details in payload (run-level terminal); `task_failed` used only when this run failure also fails the task |

#### cancelled

| Attribute | Value |
|---|---|
| **Meaning** | Run was explicitly cancelled before completion. |
| **Entry condition** | Authorized party cancels the run. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None |
| **Corresponding RunEvent type** | `run_cancelled` (run-level terminal); `task_cancelled` used only when this run cancellation also cancels the task |

### 1.3 Run Transition Table

| From | To | Trigger | Required Evidence |
|---|---|---|---|
| `prepared` | `started` | Runner confirms execution start | `run_started` RunEvent |
| `started` | `in_progress` | Runner begins making progress | `progress` RunEvent |
| `started` | `failed` | Unrecoverable error before progress | `run_failed` RunEvent with error details |
| `started` | `cancelled` | Run cancelled before progress | `run_cancelled` RunEvent |
| `started` | stays `started` | Task enters a suspension gate (`waiting_input`, `waiting_approval`, `blocked`, `review_pending`); run-level state unchanged | Suspension recorded at task level via `task_blocked`, `approval_requested`, or `review_requested` |
| `in_progress` | `checkpointed` | Runner saves checkpoint | `checkpoint_created` RunEvent with checkpoint data |
| `in_progress` | `completed` | Runner finishes execution | `run_completed` RunEvent (mandatory run-level terminal); `artifact_produced` or `review_requested` evidence as appropriate |
| `in_progress` | `failed` | Unrecoverable error | `run_failed` RunEvent with error details |
| `in_progress` | `cancelled` | Run cancelled | `run_cancelled` RunEvent |
| `in_progress` | stays `in_progress` | Task enters a suspension gate (`waiting_input`, `waiting_approval`, `blocked`, `review_pending`); run-level state unchanged | Suspension recorded at task level via `task_blocked`, `approval_requested`, or `review_requested` |
| `checkpointed` | `in_progress` | Runner continues from checkpoint | `progress` RunEvent |
| `checkpointed` | `resumed` | Run restarted from checkpoint | `run_started` RunEvent (new run) or `progress` RunEvent (continuation from checkpoint) |
| `resumed` | `in_progress` | Runner confirms resumed execution | `progress` RunEvent |
| `resumed` | `failed` | Unrecoverable error immediately after resume | `run_failed` RunEvent with error details |
| `resumed` | `cancelled` | Run cancelled immediately after resume | `run_cancelled` RunEvent |

### 1.4 Relationship Between Run and Task

- A task may have multiple runs: initial run, retries, or resumed runs.
- Each run has a unique `run_id` and its own event sequence.
- Task state transitions are driven by run-level evidence and governance decisions.
- When a task resumes, a new run may be created or the existing run may continue from a checkpoint.
- A run can finish execution while the task remains in `review_pending`; task completion requires review/approval evidence when required by governance.

---

## 2. Run Ledger

### 2.1 What Is the Run Ledger?

The run ledger is an **append-only event log** that records activity during task execution. It is the source of evidence for what happened during a run, in what order, and with what artifacts/context.

### 2.2 Core Principles

1. **Append-only** — Events can only be added to the ledger. No event can be removed.
2. **Immutable** — Once an event is written to the ledger, it cannot be modified. If a correction is needed, a new compensating event is appended.
3. **Ordered** — Events are ordered by monotonically increasing `sequence` number within a run. The `sequence` field is required on every `RunEvent`.
4. **Typed** — Each event has an `event_type` that indicates what happened and maps to a state transition or activity.
5. **Protocol-aligned** — Every event in the ledger is an instance of `RunEvent` as defined by merged Protocol v0.1.0. Operations does not redefine the `RunEvent` schema.
6. **Evidence-first** — Claims of progress, blocker, review readiness, or completion must be backed by ledger-compatible evidence.

### 2.3 Ledger Structure

The ledger is organized per run: (execution runs). Pre-run task events are recorded in a task-level stream before any run exists.

```text
Task-level (pre-run) stream:
├── T#0: task_created
├── T#1: task_assigned
└── T#2: context_attached (at assignment)

Run Ledger (per-run, each run has independent sequence numbering):
Run: run-2026-001 (task: task-2026-001, execution run)
├── R1#0: run_prepared
├── R1#1: run_started
├── R1#2: context_attached
├── R1#3: progress
├── R1#4: checkpoint_created
├── R1#5: artifact_produced
├── R1#6: review_requested (task enters review_pending)
└── R1#7: run_completed (run finishes; task still in review_pending)
Task-level stream (continues after run completion):
├── T#3: review_completed (reviewer decision, separate stream)
└── T#4: task_completed (task terminal, after review approval)

Run: run-2026-002 (task: task-2026-001, resumed run after rework)
├── R2#0: run_prepared
├── R2#1: run_started
└── ...
```

Each run has its own run-level sequence numbering (R<N>#0, R<N>#1, ...). Task-level events use independent task-level numbering (T#0, T#1, ...). Cross-run and cross-stream ordering is established by timestamp.

---

## 3. Ledger Rules

### 3.1 Event Ordering

- Events within a run are ordered by `sequence`, a monotonically increasing integer starting from 0.
- The `sequence` number must be unique within a run.
- Events must be appended in chronological order. The timestamp should be consistent with the sequence order.
- Consumers must process events in sequence order to reconstruct run state correctly.

### 3.2 Event Immutability

- Once an event is appended to the ledger, it cannot be modified or deleted.
- If an error is discovered in a previous event, a compensating event is appended.
- The original event remains in the ledger as historical record.
- Event immutability ensures complete auditability.

### 3.3 Recording Checkpoints

When a runner saves a checkpoint:

1. A `checkpoint_created` RunEvent is appended to the ledger.
2. The event payload contains:
   - `checkpoint_id`: unique identifier for the checkpoint
   - `checkpoint_data`: serializable state data or a reference to where the state is stored
   - `description`: what the checkpoint represents
3. The checkpoint can be used to resume the run if it is interrupted.
4. Checkpoint events serve as recovery points; they do not by themselves complete the task.

### 3.4 Recording Artifacts Produced

When a runner produces an artifact during execution:

1. An `artifact_produced` RunEvent is appended to the ledger.
2. The event payload contains or references an `ArtifactRef` instance.
3. The `ArtifactRef` is also linked to the task-level artifact list when the TaskEnvelope representation is updated.
4. Multiple artifacts can be produced in a run; each should be traceable to task, run, producer, and URI.

### 3.5 Recording Context Used

When context is attached to a task during execution:

1. A `context_attached` RunEvent is appended to the ledger.
2. The event payload contains or references a `ContextRef` instance.
3. The `ContextRef` is also linked to the task-level context list when the TaskEnvelope representation is updated.
4. Context attachment can happen at task creation, assignment, or during execution.

### 3.6 Recording Approval / Review / Failure

#### Approval

Approval gates must be recorded with approval-specific events, not generic blocker events:

- Request: `approval_requested` RunEvent with approval type, requested approver, and context.
- Response: `approval_received` RunEvent with decision, approver identity, timestamp, and optional reason.

A task in `waiting_approval` must not be represented only by `task_blocked`; doing so loses the approver/context evidence required to resume safely.

#### Review

- Request: `review_requested` RunEvent with ArtifactRef-style output references.
- Response: `review_completed` RunEvent with decision, reviewer, timestamp, and comments.

#### Failure

- `task_failed` RunEvent with reason and error details if applicable.
- Severity should be `error` or `critical` depending on impact.

### 3.7 Associating ArtifactRef

Artifact references are associated with the ledger through:

1. **Event-level**: `artifact_produced` carries or references an ArtifactRef-style object in payload.
2. **Task-level**: TaskEnvelope accumulates ArtifactRef instances produced across runs.
3. **Cross-reference**: ArtifactRef includes task/run/provenance fields per Protocol schema.

### 3.8 Associating ContextRef

Context references are associated with the ledger through:

1. **Event-level**: `context_attached` carries or references a ContextRef-style object in payload.
2. **Task-level**: TaskEnvelope accumulates ContextRef instances attached to the task.
3. **Cross-reference**: ContextRef enables consumers to resolve context source and provenance per Protocol schema.

---

## 4. Recommended Event Types

Operations recommends the following event types for use in the run ledger. These types are recommended, not mandatory. The `RunEvent.event_type` field is extensible per Protocol. Consumers must handle unknown event types gracefully.

### 4.1 Task-Level Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `task_created` | Task enters `draft` state | `info` | title, description, source, governance_profile |
| `task_assigned` | Task enters `assigned` state | `info` | assignee |
| `task_completed` | Task enters `completed` state | `info` | completion_summary |
| `task_failed` | Task enters `failed` state | `error` | reason, error_details |
| `task_cancelled` | Task enters `cancelled` state | `warning` | cancelled_by, reason |
| `task_escalated` | Task enters `escalated` state | `critical` | escalation_reason, escalated_to |

### 4.2 Run-Level Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `run_prepared` | Run enters `prepared` state | `info` | run_id, runner_type, context_refs_count |
| `run_started` | Run enters `started` state | `info` | message |
| `run_completed` | Run enters `completed` state | `info` | summary, artifact_refs_count |
| `run_failed` | Run enters `failed` state | `error` | reason, error_details |
| `run_cancelled` | Run enters `cancelled` state | `warning` | cancelled_by, reason |

### 4.3 Execution Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `context_attached` | Context reference attached to task | `info` | ContextRef-style reference |
| `checkpoint_created` | Runner saves a checkpoint | `info` | checkpoint_id, checkpoint_data, description |
| `artifact_produced` | Runner produces an artifact | `info` | ArtifactRef-style reference |
| `progress` | Runner reports progress | `info` | message, percent_complete optional |

### 4.4 Governance Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `approval_requested` | Task enters `waiting_approval` | `info` | approval_type, requested_from, context |
| `approval_received` | Approval decision received | `info` | decision, approved_by, approval_timestamp, reason |
| `review_requested` | Task enters `review_pending` | `info` | ArtifactRef-style output references |
| `review_completed` | Review decision made | `info` | decision, reviewer, review_timestamp, comments |

### 4.5 Suspension Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `task_blocked` | Task enters `blocked`, or enters `waiting_input` because required input is missing | `warning` | reason, blocking_condition or requested_input |
| `task_resumed` | Task resumes from suspended state | `info` | from_state, resolution |

`waiting_approval` is intentionally excluded from `task_blocked`. Approval waits must use `approval_requested` and `approval_received` events so governance gates retain approver/context evidence.

### 4.6 Correction Events

Corrections are non-state-changing audit events. They must not be used to move a task out of a terminal state.

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `ledger_correction` | A prior ledger event needs correction without changing task state | `warning` | corrected_event_id, correction_reason, corrected_fields or replacement_reference |

If a task was marked `completed` erroneously, Operations must not append `task_failed` after `task_completed` to compensate. Instead, append `ledger_correction` and create a follow-up task or authorized remediation workflow if additional work is required.

### 4.7 Event Type Extension

If a runner or operation needs to emit events not listed above:

1. Use a descriptive, lowercase, snake_case event type name.
2. Ensure the payload is a valid JSON object with sufficient context for consumers.
3. Document the custom event type in the run metadata or follow-up docs.
4. Consumers must ignore unknown event types gracefully per Protocol extensibility rules.

---

## 5. RunEvent Usage in the Ledger

### 5.1 How Operations Uses RunEvent

Operations uses `RunEvent` from merged Protocol v0.1.0 as the envelope for every ledger event. Operations does not redefine the `RunEvent` schema. It defines:

1. Which event types are recommended.
2. What each event type's payload should contain semantically.
3. How events map to state transitions.
4. Ledger rules for ordering, immutability, and integrity.

### 5.2 RunEvent Fields and Operations Semantics

| RunEvent Field | Operations Usage |
|---|---|
| `event_id` | Unique identifier for each ledger entry. Generated by Operations when the event is appended. |
| `run_id` | Identifies which run this event belongs to. Links to the run lifecycle. |
| `task_id` | Identifies the task this event relates to. Links to `TaskEnvelope.task_id`. |
| `event_type` | Determines semantic meaning and payload structure. Operations recommends types; Protocol defines the field as extensible. |
| `timestamp` | ISO 8601 timestamp when the event occurred. Used for cross-run ordering and audit. |
| `agent_id` | Identifies the runner or agent that emitted the event. Links to `AgentCard.agent_id`. |
| `payload` | Structured content whose semantics depend on `event_type`. Operations defines recommended payload meaning per event type. |
| `severity` | Indicates event impact level. Used for monitoring, alerting, and audit filtering. |
| `sequence` | Monotonically increasing integer for ordering within a run. Enforced by ledger rules. |

### 5.3 Operations Does Not Redefine RunEvent

Operations references the `RunEvent` schema by name and usage. It does not:

- Create its own event schema
- Modify the `RunEvent` field definitions
- Add required fields beyond what Protocol defines
- Restrict `event_type` to only Operations-recommended values

If Operations needs event-level metadata beyond what RunEvent provides, it uses documented extension conventions permitted by Protocol rather than redefining the schema.

---

## 6. Ledger Integrity and Recovery

### 6.1 Sequence Gap Detection

If a gap is detected in sequence numbers within a run, it indicates that an event may have been lost or a write failure occurred.

Consumers should flag sequence gaps as integrity warnings. The ledger should attempt to recover missing events from the source runner.

### 6.2 Duplicate Detection

If two events share the same `event_id` within a run, the duplicate must be discarded. `event_id` is the deduplication key.

### 6.3 Compensating and Correction Events

When a correction is needed, a compensating or correction event is appended. The correction must respect lifecycle terminal-state rules.

Allowed correction patterns:

- Non-terminal correction: append a state-appropriate compensating event if the lifecycle permits the transition.
- Terminal-state correction: append `ledger_correction` only; do not append a new state-changing task event after a terminal state.
- Follow-up work: create a new task if the correction reveals additional required work.

The compensating or correction event must include a reference to the original event being corrected when possible. Both the original and correction events remain in the ledger.

---

## 7. Cross-References

| Reference | Relationship |
|---|---|
| [IEF_OPERATIONS_V0.md](./IEF_OPERATIONS_V0.md) | Operations overview, positioning, and AI coding agent conformance model |
| [TASK_LIFECYCLE.md](./TASK_LIFECYCLE.md) | Task lifecycle state machine and transitions |
| [IEF-Program#6](https://github.com/everwork-ai/IEF-Program/issues/6) | P1-Contracts execution plan |
| [IEF-Program#9](https://github.com/everwork-ai/IEF-Program/issues/9) | Operations-led multi-agent execution solidity plan |
| [IEF-Governance#2](https://github.com/everwork-ai/IEF-Governance/issues/2) | Contract-Critical profile definition |
| [IEF-Protocol#2](https://github.com/everwork-ai/IEF-Protocol/issues/2) | RunEvent, ArtifactRef, ContextRef schema definitions |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Merged Protocol v0.1.0 baseline |
