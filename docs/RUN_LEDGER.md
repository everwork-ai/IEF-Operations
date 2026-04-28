# IEF Run Ledger v0

> Defines the run lifecycle, the append-only event ledger, ledger rules, and how Protocol objects are used within the ledger.

## 1. Run Lifecycle

A run is a single execution attempt within a task. A task may have multiple runs — for example, after a resume or retry. Each run has its own lifecycle, distinct from the task lifecycle.

### 1.1 Run States (8)

```text
prepared → started → in_progress → checkpointed → resumed → completed / failed / cancelled
```

### 1.2 State Definitions

#### prepared

| Attribute | Value |
|---|---|
| **Meaning** | Run has been created and configured but execution has not started. Context is attached, runner is selected, and resources are allocated. |
| **Entry condition** | Task transitions to `running` (or `resumed`); a new run is created. |
| **Exit condition** | Runner confirms it is ready to begin execution. |
| **Allowed next states** | `started` |
| **Corresponding RunEvent type** | `run_prepared` |

#### started

| Attribute | Value |
|---|---|
| **Meaning** | Runner has confirmed execution has begun. The run is now active. |
| **Entry condition** | Runner accepts the prepared run and signals start. |
| **Exit condition** | Runner begins making progress or encounters an issue. |
| **Allowed next states** | `in_progress` |
| **Corresponding RunEvent type** | `run_started` |

#### in_progress

| Attribute | Value |
|---|---|
| **Meaning** | Run is actively executing. Progress events are being emitted. |
| **Entry condition** | Runner begins making progress after start. |
| **Exit condition** | Runner reaches a checkpoint, completes execution, encounters an error, or the run is cancelled. |
| **Allowed next states** | `checkpointed`, `completed`, `failed`, `cancelled` |
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
| **Allowed next states** | `in_progress` |
| **Corresponding RunEvent type** | `task_resumed` (at task level); `run_started` (at run level for continuation) |

#### completed

| Attribute | Value |
|---|---|
| **Meaning** | Run finished successfully. All expected output has been produced. |
| **Entry condition** | Runner completes execution and produces final output. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Corresponding RunEvent type** | `task_completed` (if task-level completion) |

#### failed

| Attribute | Value |
|---|---|
| **Meaning** | Run encountered an unrecoverable error and cannot complete. |
| **Entry condition** | Runner encounters an error that prevents completion. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Corresponding RunEvent type** | `task_failed` (with error details in payload) |

#### cancelled

| Attribute | Value |
|---|---|
| **Meaning** | Run was explicitly cancelled before completion. |
| **Entry condition** | Authorized party cancels the run. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Corresponding RunEvent type** | `task_cancelled` |

### 1.3 Run Transition Table

| From | To | Trigger | Required Evidence |
|---|---|---|---|
| `prepared` | `started` | Runner confirms execution start | `run_started` RunEvent |
| `started` | `in_progress` | Runner begins making progress | `progress` RunEvent |
| `in_progress` | `checkpointed` | Runner saves checkpoint | `checkpoint_created` RunEvent with checkpoint data |
| `in_progress` | `completed` | Runner finishes execution | `task_completed` RunEvent; ArtifactRef(s) |
| `in_progress` | `failed` | Unrecoverable error | `task_failed` RunEvent with error details |
| `in_progress` | `cancelled` | Run cancelled | `task_cancelled` RunEvent |
| `checkpointed` | `in_progress` | Runner continues from checkpoint | `progress` RunEvent |
| `checkpointed` | `resumed` | Run restarted from checkpoint | `task_resumed` RunEvent |
| `resumed` | `in_progress` | Runner confirms resumed execution | `progress` RunEvent |

### 1.4 Relationship Between Run and Task

- A task may have **multiple runs** (initial run + retries or resume runs).
- Each run has a unique `run_id` and its own event sequence.
- Task state transitions (e.g., `running → waiting_approval`) are driven by run-level events.
- When a task resumes (`resumed → running`), a new run may be created or the existing run may continue from a checkpoint.

---

## 2. Run Ledger

### 2.1 What Is the Run Ledger?

The run ledger is an **append-only event log** that records all activity during task execution. It is the single source of truth for what happened during a run, in what order, and with what evidence.

### 2.2 Core Principles

1. **Append-only** — Events can only be added to the ledger. No event can be removed.
2. **Immutable** — Once an event is written to the ledger, it cannot be modified. If a correction is needed, a new compensating event is appended.
3. **Ordered** — Events are ordered by monotonically increasing `sequence` number within a run. The `sequence` field is required on every `RunEvent`.
4. **Typed** — Each event has an `event_type` that indicates what happened and maps to a state transition or activity.
5. **Protocol-aligned** — Every event in the ledger is an instance of `RunEvent` as defined by IEF-Protocol. Operations does not redefine the `RunEvent` schema.

### 2.3 Ledger Structure

The ledger is organized per run:

```text
Run Ledger
├── Run: run-2026-001 (task: task-2026-001)
│   ├── event #0: run_prepared
│   ├── event #1: run_started
│   ├── event #2: context_attached
│   ├── event #3: progress
│   ├── event #4: checkpoint_created
│   ├── event #5: artifact_produced
│   ├── event #6: review_requested
│   ├── event #7: review_completed
│   └── event #8: task_completed
└── Run: run-2026-002 (task: task-2026-001, resumed run)
    ├── event #0: run_prepared
    ├── event #1: run_started
    └── ...
```

Each run has its own `sequence` numbering starting from 0. Cross-run ordering is established by `timestamp`.

---

## 3. Ledger Rules

### 3.1 Event Ordering

- Events within a run are ordered by `sequence` (monotonically increasing integer, starting from 0).
- The `sequence` number must be unique within a run — no two events in the same run can share a `sequence`.
- Events must be appended in chronological order. The `timestamp` should be consistent with the `sequence` order.
- Consumers must process events in `sequence` order to reconstruct the run state correctly.

### 3.2 Event Immutability

- Once an event is appended to the ledger, it **cannot be modified or deleted**.
- If an error is discovered in a previous event, a **compensating event** is appended (e.g., a `task_failed` event followed by a `task_resumed` event if the failure is recovered).
- The original event remains in the ledger as the historical record.
- Event immutability ensures complete auditability.

### 3.3 Recording Checkpoints

When a runner saves a checkpoint:

1. A `checkpoint_created` RunEvent is appended to the ledger.
2. The event `payload` contains:
   - `checkpoint_id`: unique identifier for the checkpoint
   - `checkpoint_data`: serializable state data (or a reference to where the state is stored)
   - `description`: what the checkpoint represents
3. The checkpoint can be used to resume the run if it is interrupted.
4. Checkpoint events serve as recovery points — they do not change the task state.

### 3.4 Recording Artifacts Produced

When a runner produces an artifact during execution:

1. An `artifact_produced` RunEvent is appended to the ledger.
2. The event `payload` contains an `ArtifactRef` instance with:
   - `artifact_id`, `task_id`, `run_id`, `type`, `uri`, `created_at`, `produced_by`
3. The `ArtifactRef` is also added to the `TaskEnvelope.artifact_refs` array.
4. Multiple artifacts can be produced in a single run — each gets its own event.

### 3.5 Recording Context Used

When context is attached to a task during execution:

1. A `context_attached` RunEvent is appended to the ledger.
2. The event `payload` contains a `ContextRef` instance with:
   - `context_id`, `source_type`, `source_id`, `uri`, `relevance_score`, `retrieved_at`
3. The `ContextRef` is also added to the `TaskEnvelope.context_refs` array.
4. Context attachment can happen at task creation, assignment, or during execution.

### 3.6 Recording Approval / Review / Failure

#### Approval

- **Request**: `approval_requested` RunEvent with `payload.approval_type`, `payload.requested_from`, `payload.context`
- **Response**: `approval_received` RunEvent with `payload.decision`, `payload.approved_by`, `payload.approval_timestamp`, `payload.reason`

#### Review

- **Request**: `review_requested` RunEvent with ArtifactRef(s) pointing to reviewable output
- **Response**: `review_completed` RunEvent with `payload.decision`, `payload.reviewer`, `payload.review_timestamp`, `payload.comments`

#### Failure

- `task_failed` RunEvent with `payload.reason`, `payload.error_details` (if applicable)
- Severity: `error` or `critical` depending on impact

### 3.7 Associating ArtifactRef

Artifact references are associated with the ledger through:

1. **Event-level**: The `artifact_produced` RunEvent carries an `ArtifactRef` in its `payload`.
2. **Task-level**: The `TaskEnvelope.artifact_refs` array accumulates all `ArtifactRef` instances produced across all runs of the task.
3. **Cross-referencing**: Each `ArtifactRef` contains `task_id` and `run_id`, enabling consumers to trace any artifact back to the specific run and task that produced it.

### 3.8 Associating ContextRef

Context references are associated with the ledger through:

1. **Event-level**: The `context_attached` RunEvent carries a `ContextRef` in its `payload`.
2. **Task-level**: The `TaskEnvelope.context_refs` array accumulates all `ContextRef` instances attached to the task.
3. **Cross-referencing**: Each `ContextRef` contains `context_id` and `source_type`, enabling consumers to resolve the context source.

---

## 4. Recommended Event Types

Operations recommends the following event types for use in the run ledger. These types are **recommended, not mandatory** — the `RunEvent.event_type` field is extensible per Protocol. Consumers must handle unknown event types gracefully.

### 4.1 Task-Level Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `task_created` | Task enters `draft` state | `info` | `title`, `description`, `source`, `governance_profile` |
| `task_assigned` | Task enters `assigned` state | `info` | `assignee` |
| `task_completed` | Task enters `completed` state | `info` | `completion_summary` |
| `task_failed` | Task enters `failed` state | `error` | `reason`, `error_details` |
| `task_cancelled` | Task enters `cancelled` state | `warning` | `cancelled_by`, `reason` |
| `task_escalated` | Task enters `escalated` state | `critical` | `escalation_reason`, `escalated_to` |

### 4.2 Run-Level Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `run_prepared` | Run enters `prepared` state | `info` | `run_id`, `runner_type`, `context_refs_count` |
| `run_started` | Run enters `started` state | `info` | `message` |

### 4.3 Execution Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `context_attached` | Context reference attached to task | `info` | `ContextRef` instance |
| `checkpoint_created` | Runner saves a checkpoint | `info` | `checkpoint_id`, `checkpoint_data`, `description` |
| `artifact_produced` | Runner produces an artifact | `info` | `ArtifactRef` instance |
| `progress` | Runner reports progress | `info` | `message`, `percent_complete` (optional) |

### 4.4 Governance Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `approval_requested` | Task enters `waiting_approval` | `info` | `approval_type`, `requested_from`, `context` |
| `approval_received` | Approval decision received | `info` | `decision`, `approved_by`, `approval_timestamp`, `reason` |
| `review_requested` | Task enters `review_pending` | `info` | `ArtifactRef`(s) being reviewed |
| `review_completed` | Review decision made | `info` | `decision`, `reviewer`, `review_timestamp`, `comments` |

### 4.5 Suspension Events

| Event Type | When Emitted | Severity | Key Payload Fields |
|---|---|---|---|
| `task_blocked` | Task enters `blocked`, `waiting_input`, or `waiting_approval` | `warning` | `reason`, `blocking_condition` |
| `task_resumed` | Task resumes from suspended state | `info` | `from_state`, `resolution` |

### 4.6 Event Type Extension

If a runner or operation needs to emit events not listed above:

1. Use a descriptive, lowercase, snake_case event type name.
2. Ensure the `payload` is a valid JSON object with sufficient context for consumers.
3. Document the custom event type in the run's metadata.
4. Consumers **must** ignore unknown event types gracefully (per Protocol extensibility rules).

---

## 5. RunEvent Usage in the Ledger

### 5.1 How Operations Uses RunEvent

Operations uses `RunEvent` (defined in IEF-Protocol) as the **envelope** for every event in the ledger. Operations does not redefine the `RunEvent` schema — it defines:

1. **Which event types are recommended** (Section 4).
2. **What each event type's payload should contain** (Section 4).
3. **How events map to state transitions** (TASK_LIFECYCLE.md Section 6).
4. **Ledger rules** for ordering, immutability, and integrity (Section 3).

### 5.2 RunEvent Fields and Operations Semantics

| RunEvent Field | Operations Usage |
|---|---|
| `event_id` | Unique identifier for each ledger entry. Generated by Operations when the event is appended. |
| `run_id` | Identifies which run this event belongs to. Links to the run's lifecycle. |
| `task_id` | Identifies the task this event relates to. Links to `TaskEnvelope.task_id`. |
| `event_type` | Determines the semantic meaning and payload structure. Operations recommends types (Section 4) but Protocol defines the field as extensible. |
| `timestamp` | ISO 8601 timestamp when the event occurred. Used for cross-run ordering and audit. |
| `agent_id` | Identifies the runner or agent that emitted the event. Links to `AgentCard.agent_id`. |
| `payload` | Structured content whose schema depends on `event_type`. Operations defines recommended payload structures per event type. |
| `severity` | Indicates event impact level. Used for monitoring, alerting, and audit filtering. |
| `sequence` | Monotonically increasing integer for ordering within a run. Enforced by ledger rules. |

### 5.3 Operations Does Not Redefine RunEvent

Operations references the `RunEvent` schema by name and usage. It does not:

- Create its own event schema
- Modify the `RunEvent` field definitions
- Add required fields beyond what Protocol defines
- Restrict the `event_type` to only Operations-recommended values

If Operations needs event-level metadata beyond what `RunEvent` provides, it uses the `x_operations_` prefix convention on `payload` or on `RunEvent.additionalProperties`.

---

## 6. Ledger Integrity and Recovery

### 6.1 Sequence Gap Detection

If a gap is detected in `sequence` numbers within a run (e.g., event #3 is followed by event #5), it indicates:

- An event was lost during transmission or storage
- A write failure occurred

Consumers should flag sequence gaps as integrity warnings. The ledger should attempt to recover missing events from the source runner.

### 6.2 Duplicate Detection

If two events share the same `event_id` within a run, the duplicate must be discarded. `event_id` is the deduplication key.

### 6.3 Compensating Events

When a correction is needed (e.g., a task was marked `completed` prematurely), a compensating event is appended:

- `task_completed` followed by `task_failed` (if completion was erroneous)
- The compensating event must include `payload.compensates`: the `event_id` of the original event being corrected
- Both the original and compensating events remain in the ledger

---

## 7. Cross-References

| Reference | Relationship |
|---|---|
| [IEF_OPERATIONS_V0.md](./IEF_OPERATIONS_V0.md) | Operations overview and positioning |
| [TASK_LIFECYCLE.md](./TASK_LIFECYCLE.md) | Task lifecycle state machine and transitions |
| [IEF-Program#6](https://github.com/everwork-ai/IEF-Program/issues/6) | P1-Contracts execution plan |
| [IEF-Governance#2](https://github.com/everwork-ai/IEF-Governance/issues/2) | Contract-Critical profile definition |
| [IEF-Protocol#2](https://github.com/everwork-ai/IEF-Protocol/issues/2) | RunEvent, ArtifactRef, ContextRef schema definitions |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Draft Protocol PR — referenced as draft contract |
