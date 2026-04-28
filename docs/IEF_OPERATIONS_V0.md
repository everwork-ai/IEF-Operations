# IEF Operations v0

> IEF Operations Layer — the work operating system that governs task state, run state, and the event ledger.

## 1. Operations Positioning

IEF-Operations is the **work operating system** of the IEF ecosystem. It answers the question: *What work is being done now, by whom, and in what state?*

Operations owns the lifecycle of every unit of work in IEF — from creation through execution to completion or failure. It manages how tasks progress through states, how runs record events, and how the system maintains an auditable, append-only record of all work activity.

Operations is the **runtime backbone**: when a task is created, assigned, executed, blocked, approved, or completed, Operations defines the rules for how that happens and what evidence is required.

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

1. Operations defines **state machines, transition rules, and ledger rules only**.
2. Operations does **not** define Protocol object schemas — it references them.
3. Operations does **not** define governance profiles — it is constrained by them.
4. Operations does **not** implement runners, adapters, or knowledge storage.
5. Operations may define how `TaskEnvelope.status` values are used, but **Protocol owns the schema field** and **Operations owns the allowed values and transitions**.
6. Operations may define how `RunEvent.event_type` values are emitted, but **Protocol owns the schema** and **Operations owns the semantic mapping**.
7. Operations does **not** create its own Task object schema — it uses `TaskEnvelope` as the exchange format.

---

## 2. Boundaries with Other Layers

### 2.1 Operations ↔ Program

- **Program** coordinates work across repositories and creates issues that become tasks.
- **Operations** manages the lifecycle of those tasks once they enter the system.
- Program does not define lifecycle rules; Operations does not define program-level coordination.

### 2.2 Operations ↔ Governance

- **Governance** defines profiles (e.g., Contract-Critical) that constrain which transitions require approval, what evidence is required, and who can approve.
- **Operations** implements the gates defined by Governance profiles.
- Operations does not define what the profiles are; it consumes and enforces them.

### 2.3 Operations ↔ Protocol

- **Protocol** defines the schemas for `TaskEnvelope`, `RunEvent`, `ArtifactRef`, and `ContextRef`.
- **Operations** references these objects and defines how they are used in lifecycle and ledger contexts.
- Operations must never redefine or duplicate Protocol schemas.
- If Protocol adds or changes a field, Operations adjusts its usage rules without modifying the schema.

### 2.4 Operations ↔ Runners

- **Runners** execute work and emit events into the Operations run ledger.
- **Operations** defines what events are valid, what transitions they trigger, and what evidence is required.
- Runners do not define lifecycle rules; Operations does not implement runner logic.

### 2.5 Operations ↔ Knowledge

- **Knowledge** produces and manages context content.
- **Operations** attaches `ContextRef` references to tasks during execution.
- Operations does not store knowledge; it references it.

### 2.6 Operations ↔ Adapters

- **Adapters** translate external requests into internal IEF work objects.
- **Operations** receives tasks from adapters and manages their lifecycle.
- Adapters do not define lifecycle rules; Operations does not implement adapter logic.

---

## 3. Operations v0 Minimum Responsibilities

For v0, Operations is responsible for:

1. **Task lifecycle** — Define the 13 task states and all valid transitions with entry/exit conditions and evidence requirements.
2. **Run lifecycle** — Define the 8 run states and valid transitions.
3. **Run ledger** — Define the append-only event log rules, event ordering, immutability, and how events map to state changes.
4. **Protocol object usage** — Define how `TaskEnvelope`, `RunEvent`, `ArtifactRef`, and `ContextRef` are used within lifecycle and ledger contexts without redefining their schemas.
5. **Governance alignment** — Specify which transitions require governance review or approval per the Contract-Critical profile.
6. **Downstream readiness** — Produce definitions complete enough for Runners, Knowledge, and Adapters to begin their v0 implementations.

---

## 4. Task Lifecycle Overview

The task lifecycle defines how a unit of work progresses from creation to a terminal state.

### 4.1 Task States (13)

```text
draft → ready → assigned → running
                                ├── waiting_input
                                ├── waiting_approval
                                ├── blocked
                                ├── review_pending
                                └── failed / cancelled
running → review_pending → completed / failed
blocked → escalated
waiting_input / waiting_approval / blocked → resumed → running
```

### 4.2 Terminal States

- **completed** — Task finished successfully, review passed.
- **failed** — Task cannot proceed; unrecoverable error or review rejection.
- **cancelled** — Task explicitly cancelled by authorized party.
- **escalated** — Task escalated beyond normal resolution (effectively terminal until Program Agent intervenes).

### 4.3 Full Definition

See [TASK_LIFECYCLE.md](./TASK_LIFECYCLE.md) for complete state definitions, transition rules, evidence requirements, and governance review mappings.

---

## 5. Run Lifecycle Overview

A run is a single execution attempt within a task. A task may have multiple runs (e.g., after resume or retry).

### 5.1 Run States (8)

```text
prepared → started → in_progress → checkpointed → resumed → completed / failed / cancelled
```

### 5.2 Terminal States

- **completed** — Run finished successfully.
- **failed** — Run encountered an unrecoverable error.
- **cancelled** — Run explicitly cancelled.

### 5.3 Full Definition

See [RUN_LEDGER.md](./RUN_LEDGER.md) for complete run state definitions, ledger rules, and event type recommendations.

---

## 6. Run Ledger Overview

The run ledger is an **append-only event log** that records all activity during a task's execution.

### 6.1 Core Principles

1. **Append-only** — Events can only be added, never modified or deleted.
2. **Immutable** — Once written, an event cannot be changed.
3. **Ordered** — Events are ordered by monotonically increasing `sequence` number within a run.
4. **Typed** — Each event has an `event_type` that maps to a state transition or activity.
5. **Protocol-aligned** — Every event is an instance of `RunEvent` as defined by IEF-Protocol.

### 6.2 Full Definition

See [RUN_LEDGER.md](./RUN_LEDGER.md) for ledger rules, event type recommendations, and ArtifactRef/ContextRef linkage.

---

## 7. How Operations References Protocol Objects

Operations references Protocol objects **by name and usage**, never by redefining their schemas.

### 7.1 TaskEnvelope

- Operations defines the allowed values for `TaskEnvelope.status` (the 13 task states).
- Operations defines the transition rules that govern when and how `status` changes.
- Operations does **not** redefine the `TaskEnvelope` schema or its fields.

### 7.2 RunEvent

- Operations defines the recommended `RunEvent.event_type` values used in the ledger.
- Operations defines the `payload` structure for each event type it governs.
- Operations does **not** redefine the `RunEvent` schema or its fields.

### 7.3 ArtifactRef

- Operations defines when and how `ArtifactRef` instances are created during a run.
- Operations defines the ledger rules for linking artifacts to runs and tasks.
- Operations does **not** redefine the `ArtifactRef` schema or its fields.

### 7.4 ContextRef

- Operations defines when and how `ContextRef` instances are attached to a task.
- Operations defines the ledger rules for recording context usage.
- Operations does **not** redefine the `ContextRef` schema or its fields.

### 7.5 Extension

If Operations needs fields beyond what Protocol defines, it uses the `x_operations_` prefix convention on `additionalProperties`, as permitted by Protocol schemas.

---

## 8. How Operations Is Constrained by Governance Contract-Critical Profile

Operations#2 operates under the **Contract-Critical** governance profile as defined by IEF-Governance#2 and documented in IEF-Program's Definition of Done.

### 8.1 Contract-Critical Requirements for Operations

| Requirement | How Operations Complies |
|---|---|
| Linked issue exists | IEF-Operations#2 |
| Design document or RFC reference | This document (`IEF_OPERATIONS_V0.md`) plus `TASK_LIFECYCLE.md` and `RUN_LEDGER.md` |
| Explicit input/output contract documented | State machines with defined entry/exit conditions; event types with defined payloads |
| Explicit boundary documented | Section 1.2 (what Operations does not own) and Section 2 (layer boundaries) |
| Schema, example, or validation rule provided | State transition tables; event type definitions; ledger rules |
| Cross-review from at least one other repo perspective | Protocol and Runners perspectives must review |
| Program Controller or human approval before merge | Required before this PR merges |
| Rollback plan documented if replacing existing contract | Included in PR body (new files, simple revert) |

### 8.2 Governance Review in Lifecycle

Certain task transitions require governance review or approval:

- **waiting_approval → resumed**: Requires explicit approval (human or Program Agent) recorded as evidence.
- **review_pending → completed**: Requires review approval.
- **blocked → escalated**: Triggers Program Agent intervention.
- **running → cancelled**: Requires authorized party confirmation.

These gates are defined in `TASK_LIFECYCLE.md` and are consistent with the Contract-Critical profile requirements.

---

## 9. Cross-References

| Reference | Relationship |
|---|---|
| [IEF-Program#6](https://github.com/everwork-ai/IEF-Program/issues/6) | P1-Contracts execution plan — coordinates Operations with Governance and Protocol |
| [IEF-Governance#2](https://github.com/everwork-ai/IEF-Governance/issues/2) | Defines Contract-Critical profile that constrains Operations#2 merge criteria |
| [IEF-Protocol#2](https://github.com/everwork-ai/IEF-Protocol/issues/2) | Defines TaskEnvelope / RunEvent / ArtifactRef / ContextRef schemas that Operations references |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Draft PR containing Protocol object definitions — referenced as draft contract |
| [IEF-Runners#2](https://github.com/everwork-ai/IEF-Runners/issues/2) | Blocked — waiting for Operations draft to begin implementation |
| [IEF-Knowledge#2](https://github.com/everwork-ai/IEF-Knowledge/issues/2) | Blocked — waiting for Operations draft to begin implementation |
| [IEF-Adapters#2](https://github.com/everwork-ai/IEF-Adapters/issues/2) | Blocked — waiting for Operations draft to begin implementation |

---

## 10. Draft Consistency Disclaimer

> This draft references [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) as a draft contract. Final consistency must be checked after Protocol#3 is merged or at minimum after all Protocol review blockers are resolved. Operations does not depend on specific Protocol field definitions to an unadjustable degree — it references object names and usage semantics only.
