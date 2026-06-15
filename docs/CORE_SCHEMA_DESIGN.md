# IEF Operations — Core Schema Design

> Machine-readable JSON Schema definitions for the IEF Operations layer.  
> Governed by G-Lite profile.  
> JSON Schema draft 2020-12.

**Produced by:** ief-operator  
**Trigger:** `ief_closedloop_validation_20260615_081202`  
**Authorization:** IEF-Program#11 comment 4705865465  
**Timestamp:** 2026-06-15T16:15:00+08:00

---

## 1. Overview

This document defines the four core JSON Schemas for IEF-Operations:

| Schema | File | Purpose |
|--------|------|---------|
| Task | `schemas/task.schema.json` | Task lifecycle and state management |
| Run | `schemas/run.schema.json` | Execution attempts within a task |
| Workflow | `schemas/workflow.schema.json` | Multi-step task graphs with approval checkpoints |
| Ledger Entry | `schemas/ledger_entry.schema.json` | Append-only event log entries |

### 1.1 Design Principles

1. **JSON Schema draft 2020-12** — Uses `$schema: https://json-schema.org/draft/2020-12/schema` for all schemas.
2. **Protocol alignment** — Schemas reference Protocol v0.1.0 object names (TaskEnvelope, RunEvent, ArtifactRef, ContextRef) by name only. They do not redefine Protocol schemas.
3. **Operations semantics** — Schemas encode Operations-specific rules: lifecycle states, transition constraints, evidence requirements, and ledger immutability.
4. **G-Lite governance** — Schemas enforce minimal structural validation. Governance-specific rules (review requirements, approval gates) are encoded as conditional constraints, not hard-coded policy.
5. **Extensibility** — `metadata` fields allow arbitrary extension. `event_type` enum is recommended but Protocol permits extension.

### 1.2 Boundary with Protocol

These schemas are **Operations-internal**. They define how Operations represents tasks, runs, workflows, and ledger entries. They do not define:

- `TaskEnvelope` schema (owned by IEF-Protocol)
- `RunEvent` schema (owned by IEF-Protocol)
- `ArtifactRef` schema (owned by IEF-Protocol)
- `ContextRef` schema (owned by IEF-Protocol)

Operations schemas **consume** Protocol objects by reference. For example:
- `task.schema.json` has `artifact_refs` and `context_refs` arrays that hold Protocol ArtifactRef and ContextRef URIs.
- `ledger_entry.schema.json` has `evidence_refs` that hold Protocol ArtifactRef URIs.
- `ledger_entry.schema.json` `event_type` values map to Protocol RunEvent types.

---

## 2. Task Schema

### 2.1 Purpose

Represents a bounded unit of work managed through the Operations lifecycle. Encodes the 13-state task state machine defined in `TASK_LIFECYCLE.md`.

### 2.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `status` as required enum | Enforces valid lifecycle states at schema level |
| `status_category` as derived field | Enables filtering/grouping by state category without re-deriving |
| `transition_history` as array | Records the full lifecycle path for audit and replay |
| Conditional `required` via `if/then` | Enforces evidence fields for specific terminal/blocked states |
| `governance_profile` as string | References Governance layer without hardcoding profiles |

### 2.3 State Machine Encoding

The `status` field accepts exactly the 13 states from `TASK_LIFECYCLE.md`:

```
draft → ready → assigned → running → [waiting_input | waiting_approval | blocked | resumed | review_pending] → completed | failed | cancelled | escalated
```

Conditional constraints enforce:
- `blocked` / `waiting_input` / `waiting_approval` / `escalated` require `blocked_reason` or `escalation_reason`
- `failed` requires `failure_reason`
- `completed` requires `completion_summary`

### 2.4 Relationship to TaskEnvelope

The Task schema is the **Operations-internal representation** of a task. The `TaskEnvelope` (Protocol) is the **exchange format** used when tasks cross layer boundaries (e.g., Adapters → Operations, Operations → Runners).

Mapping:
| Task field | TaskEnvelope field | Notes |
|------------|-------------------|-------|
| `task_id` | `task_id` | Direct |
| `title` | `title` | Direct |
| `status` | `status` | Operations defines allowed values |
| `governance_profile` | `governance_profile` | Direct |
| `artifact_refs` | `artifact_refs` | Protocol ArtifactRef URIs |
| `context_refs` | `context_refs` | Protocol ContextRef URIs |

---

## 3. Run Schema

### 3.1 Purpose

Represents a single execution attempt within a task. A task may have multiple runs (initial, retry, resume). Each run has its own lifecycle and event sequence.

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 8-state run lifecycle | Matches `RUN_LEDGER.md` Section 1.2 |
| `sequence_counter` as integer | Tracks the current ledger position for next event |
| `ledger_event_ids` as ordered array | Enables replay and audit of the run's event history |
| `parent_run_id` for resumed runs | Links retry/resume runs to their predecessor |
| Conditional `error_details` / `cancellation_reason` / `summary` | Enforces evidence for terminal states |

### 3.3 Run Lifecycle Encoding

```
prepared → started → in_progress → checkpointed → resumed → completed | failed | cancelled
```

The run schema allows direct exits from `started` to `failed`/`cancelled` without requiring `in_progress` first (P2-7: started runs must be able to stop before progress).

### 3.4 Relationship to RunEvent

The Run schema is the **Operations-internal representation** of a run. The `RunEvent` (Protocol) is the **event envelope** written to the ledger. Each run accumulates RunEvents in its `ledger_event_ids` array.

---

## 4. Workflow Schema

### 4.1 Purpose

Defines multi-step task graphs with dependencies, approval checkpoints, and completion conditions. Workflows orchestrate sequences of tasks that may run in parallel or require gate approvals.

### 4.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `task_nodes` as DAG | Supports both sequential and parallel task execution |
| `depends_on` per node | Encodes dependency graph without separate edge list |
| `parallel_group` | Enables explicit parallel execution groups |
| `approval_checkpoints` | Separates approval gates from task definitions |
| `completion_conditions` | Explicit definition of "done" for the workflow |
| `retry_policy` | Per-workflow retry configuration |

### 4.3 Workflow Lifecycle

```
draft → active → [paused] → completed | failed | cancelled
```

Workflows are in `draft` until all task nodes are created and dependencies are validated. They transition to `active` when execution begins.

### 4.4 Relationship to IEF Design Pack

The Workflow schema implements the `Workflow` object defined in IEF Design Pack v0.5 Section 8.4:

> A multi-step graph or sequence of tasks and approvals.  
> Key fields: workflow_id, entry_conditions, tasks, transitions, approval_checkpoints, completion_conditions

---

## 5. Ledger Entry Schema

### 5.1 Purpose

Represents a single immutable entry in the append-only Operations run ledger. Every state transition, artifact production, approval, review, and correction is recorded as a ledger entry.

### 5.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `entry_id` as UUID | Unique dedup key per entry |
| `sequence` as integer | Monotonically increasing within a run, enforced by ledger rules |
| `event_type` as recommended enum | Standard types enforced; Protocol allows extension |
| `corrected_entry_id` for corrections | Links correction events to originals without mutation |
| `dedupe_key` for idempotency | Optional external dedup for adapter ingested events |
| Conditional payload validation via `if/then` | Enforces type-specific payload fields |

### 5.3 Event Type Taxonomy

The schema defines 22 recommended event types across 6 categories:

| Category | Event Types |
|----------|-------------|
| Task-level | `task_created`, `task_assigned`, `task_completed`, `task_failed`, `task_cancelled`, `task_escalated` |
| Suspension | `task_blocked`, `task_resumed` |
| Run-level | `run_prepared`, `run_started`, `run_completed`, `run_failed`, `run_cancelled` |
| Execution | `progress`, `checkpoint_created`, `context_attached`, `artifact_produced` |
| Governance | `approval_requested`, `approval_received`, `review_requested`, `review_completed` |
| Correction | `ledger_correction` |

### 5.4 Conditional Constraints

| When event_type is... | Then required in payload |
|----------------------|--------------------------|
| `ledger_correction` | `corrected_entry_id` (top-level), `correction_reason` |
| `task_failed` | `reason`, severity must be `error` or `critical` |
| `task_escalated` | `escalation_reason`, severity must be `critical` |
| `approval_requested` | `approval_type`, `requested_from` |
| `approval_received` | `decision` (approved/denied), `approved_by` |
| `review_completed` | `decision` (approved/rejected/rework), `reviewer` |
| `task_resumed` | `from_state` |

### 5.5 Ledger Rules Encoded

| Ledger Rule (from RUN_LEDGER.md) | Schema Enforcement |
|----------------------------------|--------------------|
| Append-only | `entry_id` is immutable; no update/delete mechanism in schema |
| Immutable | Corrections use `corrected_entry_id` + new entry; original preserved |
| Ordered | `sequence` is monotonically increasing integer within a run |
| Typed | `event_type` enum constrains valid types |
| Terminal-state safe | `ledger_correction` is the only correction type; cannot change task state |
| Dedupe | `entry_id` and optional `dedupe_key` prevent duplicates |

### 5.6 Relationship to RunEvent

The Ledger Entry schema is the **Operations-internal representation** of a ledger event. The `RunEvent` (Protocol) is the **canonical event schema**. Ledger entries are a superset that adds:

- `sequence` (ordering)
- `corrected_entry_id` (correction linking)
- `dedupe_key` (idempotency)
- `evidence_refs` (evidence linking)

A ledger entry's `payload` + `event_type` + `agent_id` + `timestamp` + `severity` maps directly to a Protocol `RunEvent` instance.

---

## 6. Cross-Schema Relationships

```
┌─────────────┐     1:N     ┌──────────┐
│   Workflow  │────────────▶│   Task   │
└─────────────┘             └────┬─────┘
                                 │ 1:N
                                 ▼
                            ┌──────────┐
                            │   Run    │
                            └────┬─────┘
                                 │ 1:N
                                 ▼
                         ┌───────────────┐
                         │  Ledger Entry │
                         └───────────────┘
```

- A **Workflow** contains multiple **Tasks** (via `task_nodes[].task_id`)
- A **Task** has multiple **Runs** (initial, retry, resume)
- A **Run** has multiple **Ledger Entries** (events in sequence)
- All schemas reference Protocol objects (ArtifactRef, ContextRef) by URI

---

## 7. Governance Profile Integration

Schemas are governed by the G-Lite profile, which requires:

| G-Lite Requirement | Schema Compliance |
|--------------------|-------------------|
| Linked issue exists | IEF-Operations#4 |
| Design document | This document (CORE_SCHEMA_DESIGN.md) |
| Explicit schema | 4 JSON Schema files in `schemas/` |
| Boundary documented | Section 1.2 (Protocol boundary) |
| Example/validation rule | Conditional constraints in `if/then` blocks |

Operations-specific governance (review gates, approval requirements) is encoded as conditional schema constraints rather than hard-coded rules, allowing Governance profiles to layer additional requirements at runtime.

---

## 8. Validation Examples

### 8.1 Valid Task (running state)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement schema validation",
  "status": "running",
  "governance_profile": "Implementation-Controlled",
  "priority": "high",
  "assignee": "claude-code-runner",
  "current_run_id": "550e8400-e29b-41d4-a716-446655440001",
  "run_count": 1,
  "artifact_refs": [],
  "context_refs": ["https://github.com/everwork-ai/IEF-Protocol/blob/main/schemas/run_event.schema.json"],
  "transition_history": [
    { "from": "draft", "to": "ready", "timestamp": "2026-06-15T10:00:00Z", "event_id": "a1b2c3d4" },
    { "from": "ready", "to": "assigned", "timestamp": "2026-06-15T10:01:00Z", "event_id": "e5f6a7b8" },
    { "from": "assigned", "to": "running", "timestamp": "2026-06-15T10:02:00Z", "event_id": "c9d0e1f2" }
  ],
  "created_at": "2026-06-15T10:00:00Z",
  "updated_at": "2026-06-15T10:02:00Z",
  "started_at": "2026-06-15T10:02:00Z"
}
```

### 8.2 Valid Task (failed state — requires failure_reason)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440010",
  "title": "Deploy to production",
  "status": "failed",
  "failure_reason": "Environment credential expired",
  "governance_profile": "Contract-Critical",
  "priority": "critical",
  "run_count": 2,
  "transition_history": [],
  "created_at": "2026-06-15T09:00:00Z",
  "updated_at": "2026-06-15T11:00:00Z"
}
```

### 8.3 Valid Ledger Entry (approval_received)

```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440100",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "550e8400-e29b-41d4-a716-446655440001",
  "event_type": "approval_received",
  "sequence": 7,
  "timestamp": "2026-06-15T10:30:00Z",
  "agent_id": "program-controller",
  "severity": "info",
  "payload": {
    "decision": "approved",
    "approved_by": "human-owner",
    "approval_timestamp": "2026-06-15T10:29:00Z",
    "reason": "Schema validation passed review"
  }
}
```

### 8.4 Invalid Task (missing failure_reason when failed)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440020",
  "title": "Bad task",
  "status": "failed",
  "created_at": "2026-06-15T09:00:00Z",
  "updated_at": "2026-06-15T11:00:00Z"
}
// Schema validation FAILS: missing required "failure_reason" per if/then constraint
```

---

## 9. Future Extensions

| Extension | Schema Impact | Priority |
|-----------|---------------|----------|
| Multi-runner orchestration | `run.schema.json`: add `orchestration_id`, fan-out fields | P2 |
| Workflow versioning | `workflow.schema.json`: add `version`, `supersedes` | P2 |
| Ledger compaction | `ledger_entry.schema.json`: add `compacted_from` | P2 |
| Cross-workflow dependencies | `workflow.schema.json`: add `depends_on_workflows` | P2 |
| Artifact provenance chain | `task.schema.json`: extend `artifact_refs` with provenance | P2 |

---

## 10. Non-Goals

- This document does **not** redefine Protocol schemas (TaskEnvelope, RunEvent, ArtifactRef, ContextRef).
- This document does **not** define governance profiles (owned by IEF-Governance).
- This document does **not** implement runners, adapters, or knowledge storage.
- This document does **not** authorize runtime deployment or production use.

---

*Produced by ief-operator. One bounded cycle. G-Lite governance. JSON Schema draft 2020-12.*
