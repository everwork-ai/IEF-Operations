# IEF Task Lifecycle v0

> Defines the task state machine, transitions, evidence requirements, and governance gates for IEF v0.

## 1. Task Lifecycle Overview

A task is a bounded unit of work managed by IEF-Operations. Its lifecycle is defined as a state machine with 13 states and explicit transition rules.

```text
draft → ready → assigned → running
  │       │         │           ├── waiting_input
  │       │         │           ├── waiting_approval
  │       │         │           ├── blocked
  │       │         │           ├── review_pending
  │       │         │           ├── completed
  │       │         │           └── failed / cancelled
  ↓       ↓         ↓         ───────────────────────────────
cancelled cancelled cancelled    waiting_input → resumed | cancelled
                                waiting_approval → resumed | failed | cancelled
                                blocked → resumed | escalated | cancelled
                                escalated → blocked | cancelled
                                resumed → running
                                review_pending → completed | failed | resumed | cancelled
                                running → completed | failed | cancelled
```

### 1.1 State Categories

| Category | States |
|---|---|
| Initial | `draft` |
| Pre-execution | `ready`, `assigned` |
| Active execution | `running`, `resumed` |
| Suspended (waiting) | `waiting_input`, `waiting_approval`, `blocked` |
| Review | `review_pending` |
| Terminal | `completed`, `failed`, `cancelled` |
| Quasi-terminal | `escalated` |

**Note on `escalated`:** Escalated is classified as **quasi-terminal**, distinct from true terminal states. It indicates the task has exceeded normal resolution capacity and requires Program Agent intervention. A task in `escalated` can transition back to `blocked` (and then potentially `resumed`) after Program Agent action. Unlike true terminal states (`completed`, `failed`, `cancelled`), `escalated` has a defined recovery path governed by Program-level coordination.

### 1.2 Agent Stop-Point Rule

AI coding agents must stop at the suspended, review, or escalation states rather than continuing autonomously:

| State | Agent requirement |
|---|---|
| `waiting_input` | Request missing input and stop. Do not guess durable facts. |
| `waiting_approval` | Request approval and stop. Do not self-approve. |
| `blocked` | Record blocker and stop until unblocked or escalated. |
| `review_pending` | Attach output evidence and request review. Do not self-complete. |
| `escalated` | Stop and wait for Program Agent / Human Owner intervention. |

These stop-point rules support the Operations conformance model in `IEF_OPERATIONS_V0.md`.

---

## 2. Task State Definitions

### 2.1 draft

| Attribute | Value |
|---|---|
| **Meaning** | Task has been created but is not yet ready for assignment. Details may be incomplete. |
| **Entry condition** | Task created via Program, adapter, or human request. |
| **Exit condition** | All required fields are populated; governance profile is assigned; acceptance criteria are defined. |
| **Allowed next states** | `ready`, `cancelled` |
| **Required evidence** | TaskEnvelope with `task_id`, `title`, `description`, `governance_profile`, `source`, `priority` |
| **Governance review required?** | No |
| **Human / Program Agent approval?** | No |
| **Corresponding RunEvent type** | `task_created` |

### 2.2 ready

| Attribute | Value |
|---|---|
| **Meaning** | Task is fully specified and eligible for assignment. |
| **Entry condition** | Task exits `draft` with all required fields populated. |
| **Exit condition** | An assignee (runner or agent) is selected and available. |
| **Allowed next states** | `assigned`, `cancelled` |
| **Required evidence** | TaskEnvelope with all required fields; acceptance criteria documented |
| **Governance review required?** | No |
| **Human / Program Agent approval?** | No (Program Agent may auto-assign, but assignment itself is a separate state) |
| **Corresponding RunEvent type** | (no event — readiness is implicit upon `draft → ready` transition) |

### 2.3 assigned

| Attribute | Value |
|---|---|
| **Meaning** | Task has been assigned to a specific runner or agent but execution has not started. |
| **Entry condition** | Assignee is determined; runner availability is confirmed. |
| **Exit condition** | Runner accepts the task and begins execution. |
| **Allowed next states** | `running`, `cancelled` |
| **Required evidence** | TaskEnvelope with `assignee` set; `task_assigned` RunEvent emitted |
| **Governance review required?** | No |
| **Human / Program Agent approval?** | No |
| **Corresponding RunEvent type** | `task_assigned` |

### 2.4 running

| Attribute | Value |
|---|---|
| **Meaning** | Task is actively being executed by the assigned runner. |
| **Entry condition** | Runner accepts assignment and starts execution; run is prepared and started. |
| **Exit condition** | Runner reaches a point requiring input, approval, review, direct completion, or encounters a blocking condition, error, or cancellation. |
| **Allowed next states** | `waiting_input`, `waiting_approval`, `blocked`, `review_pending`, `completed`, `failed`, `cancelled` |
| **Required evidence** | `run_started` RunEvent emitted. A subsequent `progress` or `checkpoint_created` event is recommended when progress occurs, but not required before an immediate blocker, approval gate, failure, cancellation, or direct completion is recorded. |
| **Governance review required?** | No (governance gates apply at specific transitions out of `running`) |
| **Human / Program Agent approval?** | No (unless task's governance profile mandates approval for certain transitions) |
| **Corresponding RunEvent type** | `run_started` (entry), optional `progress` events during execution |

### 2.5 waiting_input

| Attribute | Value |
|---|---|
| **Meaning** | Task execution is suspended because additional input is required from a human, another agent, or an external system. |
| **Entry condition** | Runner determines it cannot proceed without external input (e.g., clarification, data, configuration). |
| **Exit condition** | Required input is provided. |
| **Allowed next states** | `resumed`, `cancelled` |
| **Required evidence** | RunEvent with `event_type: task_blocked` and `payload.reason: waiting_input`; description of what input is needed |
| **Governance review required?** | No |
| **Human / Program Agent approval?** | Human input is required to proceed, but no formal approval gate |
| **Corresponding RunEvent type** | `task_blocked` (with reason `waiting_input`) |

### 2.6 waiting_approval

| Attribute | Value |
|---|---|
| **Meaning** | Task execution is suspended pending explicit approval from a human or Program Agent. |
| **Entry condition** | Runner encounters a point where the task's governance profile requires approval before proceeding. |
| **Exit condition** | Approval is granted (or denied, which may lead to `failed` or `cancelled`). |
| **Allowed next states** | `resumed` (if approved), `failed` (if denied and unrecoverable), `cancelled` (if denied and task is cancelled) |
| **Required evidence** | `approval_requested` RunEvent emitted; `approval_received` RunEvent with approver identity and decision; `task_resumed` RunEvent required when approval leads to resumed work |
| **Governance review required?** | Yes — this is a governance gate |
| **Human / Program Agent approval?** | **Yes** — either human or Program Agent must explicitly approve. See Section 4 for distinction. |
| **Corresponding RunEvent type** | `approval_requested` (entry), `approval_received` and `task_resumed` (exit if approved) |

### 2.7 blocked

| Attribute | Value |
|---|---|
| **Meaning** | Task execution is suspended due to an external dependency, resource constraint, or unresolvable condition that is not an approval gate. |
| **Entry condition** | Runner determines it cannot proceed due to a blocking condition (e.g., dependency not met, resource unavailable, environment failure). |
| **Exit condition** | Blocking condition is resolved, or task is escalated. |
| **Allowed next states** | `resumed`, `escalated`, `cancelled` |
| **Required evidence** | RunEvent with `event_type: task_blocked` and `payload.reason`; description of the blocking condition |
| **Governance review required?** | No (unless escalation is triggered) |
| **Human / Program Agent approval?** | No (for unblock), Yes (for escalation — Program Agent must intervene) |
| **Corresponding RunEvent type** | `task_blocked` (entry), `task_resumed` (exit via unblock), `task_escalated` (exit via escalation) |

### 2.8 resumed

| Attribute | Value |
|---|---|
| **Meaning** | Task is resuming execution after being in a suspended or rework state (`waiting_input`, `waiting_approval`, `blocked`, or `review_pending`). This is a transient state — the task immediately transitions to `running`. |
| **Entry condition** | The condition that caused suspension or rework is resolved (input provided, approval granted, blocker removed, or review rework instructions accepted). |
| **Exit condition** | Runner confirms execution has resumed. |
| **Allowed next states** | `running` |
| **Required evidence** | `task_resumed` RunEvent emitted with `payload.from_state` indicating which state the task is resuming from |
| **Governance review required?** | Only if resuming from `waiting_approval` or `review_pending` after a review decision |
| **Human / Program Agent approval?** | Only if resuming from a state that requires approval or review evidence |
| **Corresponding RunEvent type** | `task_resumed` |

### 2.9 review_pending

| Attribute | Value |
|---|---|
| **Meaning** | Task execution is complete and output is awaiting review before final completion. |
| **Entry condition** | Runner has produced output artifacts and requests review. |
| **Exit condition** | Review is completed (approved, rejected, or returned for rework). |
| **Allowed next states** | `completed` (review approved), `failed` (review rejected, unrecoverable), `resumed` (review rejected with instructions to rework), `cancelled` |
| **Required evidence** | `review_requested` RunEvent; ArtifactRef pointing to reviewable output; `review_completed` RunEvent with decision and reviewer identity; `task_completed` required when review approval leads to completion; `task_failed` required when review rejection leads to failure; `task_resumed` required when review leads to rework |
| **Governance review required?** | Yes — this is a governance gate |
| **Human / Program Agent approval?** | **Yes** — review must be performed by human or Program Agent |
| **Corresponding RunEvent type** | `review_requested` (entry), `review_completed` plus `task_completed` or `task_resumed` depending on exit path |

### 2.10 completed

| Attribute | Value |
|---|---|
| **Meaning** | Task has finished successfully. All acceptance criteria are met and required review, if any, has passed. |
| **Entry condition** | Review approved from `review_pending`, or direct completion from `running` when the governance profile does not require review and acceptance criteria are satisfied. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Required evidence** | `task_completed` RunEvent; ArtifactRef(s) for all produced outputs; review approval evidence if the governance profile requires review |
| **Governance review required?** | Profile-dependent — required when the governance profile mandates review; not required for no-review profiles. |
| **Human / Program Agent approval?** | Profile-dependent — required when review or approval gates apply. |
| **Corresponding RunEvent type** | `task_completed` |

### 2.11 failed

| Attribute | Value |
|---|---|
| **Meaning** | Task cannot proceed to completion. The failure may be due to an unrecoverable error, review rejection, or approval denial. |
| **Entry condition** | Runner encounters an unrecoverable error, review is rejected as unrecoverable, or approval is denied and task cannot proceed. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Required evidence** | `task_failed` RunEvent; `payload.reason` documenting the failure; error details or review rejection evidence |
| **Governance review required?** | No (failure is the end state, but governance may require failure notification) |
| **Human / Program Agent approval?** | No (but human or Program Agent may create a follow-up task) |
| **Corresponding RunEvent type** | `task_failed` |

### 2.12 cancelled

| Attribute | Value |
|---|---|
| **Meaning** | Task has been explicitly cancelled by an authorized party before completion. |
| **Entry condition** | Authorized party (human, Program Agent, or governance rule) cancels the task. |
| **Exit condition** | Terminal state — no further transitions. |
| **Allowed next states** | None (terminal) |
| **Required evidence** | `task_cancelled` RunEvent; `payload.cancelled_by` and `payload.reason` |
| **Governance review required?** | Depends on governance profile — Contract-Critical tasks require authorized cancellation |
| **Human / Program Agent approval?** | Yes — cancellation must be performed by an authorized party |
| **Corresponding RunEvent type** | `task_cancelled` |

### 2.13 escalated

| Attribute | Value |
|---|---|
| **Meaning** | Task has exceeded normal resolution capacity and requires Program Agent intervention. This is a quasi-terminal state. |
| **Entry condition** | Task is `blocked` and the blocker cannot be resolved through normal operations within a defined timeout or after escalation criteria are met. |
| **Exit condition** | Program Agent intervenes and reclassifies the task (typically back to `blocked` with new resolution path, then `resumed`). |
| **Allowed next states** | `blocked` (after Program Agent intervention and reclassification), `cancelled` |
| **Required evidence** | `task_escalated` RunEvent; `payload.escalation_reason`; `payload.escalated_to` |
| **Governance review required?** | Yes — escalation triggers Program Agent review |
| **Human / Program Agent approval?** | **Yes** — Program Agent must acknowledge and act on escalation |
| **Corresponding RunEvent type** | `task_escalated` |

---

## 3. Transition Rules

### 3.1 Transition Table

| From | To | Trigger | Required Evidence | Governance Gate? | Approval Required? |
|---|---|---|---|---|---|
| `draft` | `ready` | All required fields populated; governance profile assigned | Complete TaskEnvelope | No | No |
| `draft` | `cancelled` | Authorized party cancels before task is ready | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `ready` | `assigned` | Assignee selected and available | TaskEnvelope with `assignee`; `task_assigned` event | No | No |
| `ready` | `cancelled` | Authorized party cancels before assignment | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `assigned` | `running` | Runner accepts and starts execution | `run_started` event | No | No |
| `assigned` | `cancelled` | Authorized party cancels before execution starts | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `running` | `waiting_input` | Runner needs external input | `task_blocked` event with `reason: waiting_input` | No | No |
| `running` | `waiting_approval` | Governance profile requires approval at this point | `approval_requested` event | **Yes** | **Yes** (human or Program Agent) |
| `running` | `blocked` | External dependency or resource constraint | `task_blocked` event with reason | No | No |
| `running` | `review_pending` | Runner produces output that requires review | `review_requested` event; ArtifactRef(s) | **Yes** | **Yes** (reviewer) |
| `running` | `completed` | Runner completes output and governance profile does not require review | `task_completed` event; ArtifactRef(s); acceptance evidence | Profile-dependent | Profile-dependent |
| `running` | `failed` | Unrecoverable error | `task_failed` event with reason | No | No |
| `running` | `cancelled` | Authorized party cancels | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `waiting_input` | `resumed` | Required input provided | `task_resumed` event with `from_state: waiting_input` | No | No |
| `waiting_input` | `cancelled` | Authorized party cancels while awaiting input | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `waiting_approval` | `resumed` | Approval granted | `approval_received` event with approver and decision; `task_resumed` event with `from_state: waiting_approval` | **Yes** | **Yes** (human or Program Agent) |
| `waiting_approval` | `failed` | Approval denied and unrecoverable | `approval_received` event with denial decision and approver identity; `task_failed` event with denial reason | **Yes** | Decision already made |
| `waiting_approval` | `cancelled` | Approval denied and task cancelled | `approval_received` event with denial decision and approver identity; `task_cancelled` event with reason | **Yes** | **Yes** (authorized party) |
| `blocked` | `resumed` | Blocking condition resolved | `task_resumed` event with `from_state: blocked` | No | No |
| `blocked` | `escalated` | Blocker cannot be resolved within normal operations | `task_escalated` event with reason | **Yes** | **Yes** (Program Agent) |
| `blocked` | `cancelled` | Authorized party cancels while blocked | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `resumed` | `running` | Runner confirms execution resumed | `progress` RunEvent (run continuation) or `run_started` RunEvent (new run) | No | No |
| `review_pending` | `completed` | Review approved | `review_completed` event with approval; `task_completed` event; ArtifactRef(s) | **Yes** | **Yes** (reviewer) |
| `review_pending` | `failed` | Review rejected, unrecoverable | `review_completed` event with rejection; `task_failed` event; reason | **Yes** | Decision already made |
| `review_pending` | `resumed` | Review rejected with rework instructions | `review_completed` event with rework instructions; `task_resumed` event with `from_state: review_pending` | **Yes** | **Yes** (reviewer) |
| `review_pending` | `cancelled` | Authorized party cancels during review | `task_cancelled` event with `cancelled_by` and reason | Profile-dependent | **Yes** (authorized party) |
| `escalated` | `blocked` | Program Agent intervenes and reclassifies | Program Agent action evidence; new `task_blocked` event | **Yes** | **Yes** (Program Agent) |
| `escalated` | `cancelled` | Authorized party cancels escalated task | `task_cancelled` event with `cancelled_by` and reason | **Yes** | **Yes** (authorized party) |

### 3.2 Invalid Transitions

The following transitions are **not allowed**:

- Any transition from a terminal state (`completed`, `failed`, `cancelled`)
- `draft` → any state other than `ready` or `cancelled`
- `ready` → any state other than `assigned` or `cancelled`
- `assigned` → any state other than `running` or `cancelled`
- `running` → `ready` or `draft` (no backward transitions)
- `waiting_input` → `running` directly (must go through `resumed`)
- `waiting_approval` → `running` directly (must go through `resumed`)
- `blocked` → `running` directly (must go through `resumed`)
- `review_pending` → `running` directly (must go through `resumed` when rework is required)
- `escalated` → any state other than `blocked` or `cancelled` (escalation must be resolved through Program Agent or cancelled)

---

## 4. Detailed State Definitions: blocked / waiting_approval / review_pending

### 4.1 blocked

#### What constitutes blocked?

A task is `blocked` when execution cannot proceed due to a condition that is **not an approval gate** and **not a request for input**. Examples:

- An upstream dependency has not completed
- A required resource is unavailable (environment, credential, tool)
- An external system is down or unresponsive
- A conflict with another task prevents progress

#### Who can mark a task as blocked?

- The **assigned runner** can mark a task as blocked when it encounters a blocking condition during execution.
- A **Program Agent** can mark a task as blocked when it detects a systemic blocker (e.g., cross-task dependency).

#### Unblock conditions

1. The blocking condition is resolved (dependency completes, resource becomes available, external system recovers).
2. An alternative path is found that bypasses the blocker.
3. The task is escalated if the blocker cannot be resolved within a defined timeframe.

#### Does unblock require Program Agent intervention?

- **No** — if the blocker is resolved through normal operations (dependency completes, resource recovers).
- **Yes** — if the task is escalated (`blocked → escalated`), Program Agent must intervene.

#### Blocked lifecycle

```text
running → blocked (runner detects blocker)
blocked → resumed (blocker resolved)
blocked → escalated (blocker unresolvable within timeout)
escalated → blocked (Program Agent reclassifies after intervention)
```

### 4.2 waiting_approval

#### What approval is being waited for?

A task enters `waiting_approval` when the task's governance profile requires an explicit **approval gate** before the runner can proceed. This is distinct from `waiting_input` (which is about missing information) and `blocked` (which is about external constraints).

Approval gates are triggered by:

- The task's `governance_profile` field (e.g., Contract-Critical tasks require approval at specific checkpoints)
- Governance rules that mandate human sign-off for certain task types or priorities
- Runners that encounter a decision point requiring authorization

#### Human approval vs. Program Agent approval

| Aspect | Human Approval | Program Agent Approval |
|---|---|---|
| **When used** | High-risk decisions, policy-sensitive tasks, tasks with external impact | Routine checks, governance compliance verification, known-pattern approvals |
| **Who approves** | A designated human reviewer | The Program Agent acting under governance delegation |
| **Evidence** | Human identity, timestamp, explicit decision | Program Agent identity, governance rule applied, decision |
| **Auditability** | Full human audit trail | Machine audit trail with governance rule reference |
| **Override** | Human can override Program Agent decisions | Program Agent cannot override human decisions |

#### How is approval evidence recorded?

Approval evidence is recorded as `RunEvent` instances in the run ledger:

1. **Entry**: `approval_requested` RunEvent emitted with:
   - `payload.approval_type`: the type of approval required
   - `payload.requested_from`: who the approval is requested from (human identity or Program Agent)
   - `payload.context`: what the approval covers

2. **Exit**: `approval_received` RunEvent emitted with:
   - `payload.decision`: `approved` or `denied`
   - `payload.approved_by`: identity of the approver
   - `payload.approval_timestamp`: when the approval was granted/denied
   - `payload.reason`: optional reason for the decision

3. **Resume**: `task_resumed` RunEvent emitted with:
   - `payload.from_state`: `waiting_approval`
   - `payload.resolution`: approval decision reference

### 4.3 review_pending

#### What enters review?

A task enters `review_pending` when the runner has completed execution and produced output artifacts that require review before the task can be marked as `completed`.

Review is required when:

- The task's governance profile mandates review (e.g., Contract-Critical)
- The task produces artifacts that affect shared contracts, schemas, or interfaces
- The task modifies code, configuration, or documentation that impacts other layers

#### What is review evidence?

Review evidence consists of:

1. **Input artifacts**: The ArtifactRef(s) pointing to the output being reviewed (PRs, commits, documents)
2. **Review decision**: `review_completed` RunEvent with:
   - `payload.decision`: `approved`, `rejected`, or `rework`
   - `payload.reviewer`: identity of the reviewer
   - `payload.review_timestamp`: when the review was completed
   - `payload.comments`: review feedback or instructions
3. **Completion or resume evidence**:
   - `task_completed` when review approval moves the task to `completed`
   - `task_resumed` with `from_state: review_pending` when review returns rework

#### How does review lead to completion?

```text
review_pending → completed (review approved)
  Evidence: review_completed event with decision: approved; task_completed event; all ArtifactRef(s) verified
```

#### How does review lead to failure?

```text
review_pending → failed (review rejected, unrecoverable)
  Evidence: review_completed event with decision: rejected; task_failed event; reason documented
```

This path is taken when the review identifies fundamental issues that cannot be resolved through rework within the scope of the current task.

#### How does review lead to rework?

```text
review_pending → resumed (review rejected with rework instructions)
  Evidence: review_completed event with decision: rework; task_resumed event with from_state: review_pending; rework instructions documented
```

The task returns to `resumed` (and then `running`) with specific rework instructions. The runner is expected to address the review feedback and re-enter `review_pending` when rework is complete.

---

## 5. TaskEnvelope Status Mapping

Operations defines the allowed values for `TaskEnvelope.status`. The mapping is:

| TaskEnvelope.status value | Operations State |
|---|---|
| `draft` | draft |
| `ready` | ready |
| `assigned` | assigned |
| `running` | running |
| `waiting_input` | waiting_input |
| `waiting_approval` | waiting_approval |
| `blocked` | blocked |
| `resumed` | resumed |
| `review_pending` | review_pending |
| `completed` | completed |
| `failed` | failed |
| `cancelled` | cancelled |
| `escalated` | escalated |

These values are **constrained by Operations**. The `TaskEnvelope` schema is defined in the merged Protocol v0.1.0 baseline; Operations defines which values are valid and how they transition.

---

## 6. Event Type Mapping

Each task state transition corresponds to one or more `RunEvent` types:

| Transition | RunEvent.event_type | Severity |
|---|---|---|
| Task created | `task_created` | `info` |
| Task assigned | `task_assigned` | `info` |
| Run started | `run_started` | `info` |
| Task blocked | `task_blocked` | `warning` |
| Input requested | `task_blocked` (reason: `waiting_input`) | `info` |
| Approval requested | `approval_requested` | `info` |
| Approval received | `approval_received` | `info` |
| Task resumed | `task_resumed` | `info` |
| Review requested | `review_requested` | `info` |
| Review completed | `review_completed` | `info` |
| Task completed | `task_completed` | `info` |
| Task failed | `task_failed` | `error` |
| Task cancelled | `task_cancelled` | `warning` |
| Task escalated | `task_escalated` | `critical` |

---

## 7. Cross-References

| Reference | Relationship |
|---|---|
| [IEF_OPERATIONS_V0.md](./IEF_OPERATIONS_V0.md) | Operations overview, positioning, and AI coding agent conformance model |
| [RUN_LEDGER.md](./RUN_LEDGER.md) | Run lifecycle and ledger rules |
| [IEF-Program#6](https://github.com/everwork-ai/IEF-Program/issues/6) | P1-Contracts execution plan |
| [IEF-Program#9](https://github.com/everwork-ai/IEF-Program/issues/9) | Operations-led multi-agent execution solidity plan |
| [IEF-Governance#2](https://github.com/everwork-ai/IEF-Governance/issues/2) | Contract-Critical profile definition |
| [IEF-Protocol#2](https://github.com/everwork-ai/IEF-Protocol/issues/2) | TaskEnvelope and RunEvent schema definitions |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Merged Protocol v0.1.0 baseline |


---

## 8. Stage D P0: Minimum Lifecycle State Machine (GitHub-First Closed Loop)

> Source of truth: [everwork-ai/IEF-Operations#4 comment 4618600457](https://github.com/everwork-ai/IEF-Operations/issues/4#issuecomment-4618600457)
> Boundary: Contract spec only. This section defines the minimum state machine for the GitHub-first closed loop. It does not replace Sections 1-7 above; it complements them with a narrower P0 scope.

### 8.1 Minimum States

For the GitHub-first closed loop, the minimum lifecycle state machine has 9 states:

```text
pending -> dispatched -> running -> completed -> accepted
                          |           |
                          |           +-> failed -> retried -> dispatched
                          |           |                    \
                          |           |                     +-> escalated
                          |           +-> blocked -> dispatched (retry)
                          |           |            \
                          |           |             +-> escalated
                          |           +-> waiting_approval -> dispatched (approved)
                          |           |                   \
                          |           |                    +-> failed (denied)
                          |           +-> stopped -> dispatched (retry)
                          |           |            \
                          |           |             +-> escalated
                          |           +-> cancelled
                          |
                          +-> escalated (dispatch failure)
```

### 8.2 State Definitions (P0 Minimum)

| State | Meaning | Entry | Exit | Terminal? |
|---|---|---|---|---|
| `pending` | TaskEnvelope received, not yet dispatched | TaskEnvelope intake validated | `dispatched` | No |
| `dispatched` | Operations has assigned a runner and dispatched work | Dispatch decision made | `running` | No |
| `running` | Runner is actively executing | Runner emits `run_started` | `completed`, `failed`, `blocked`, `waiting_approval`, `stopped`, `cancelled` | No |
| `completed` | Runner finished with exit 0; awaiting review gate | Runner emits `run_completed` + evidence | `accepted` | No (review gate pending) |
| `failed` | Runner failed or review rejected | Runner emits `run_failed` or review rejects | `retried` (back to `dispatched`) or `escalated` | No |
| `blocked` | Runner cannot proceed (missing input, dependency, gate) | Runner emits `run_blocked`/`run_stopped` | `dispatched` (retry after unblock) or `escalated` | No |
| `waiting_approval` | Review gate requires external approval | Review gate triggered on `completed` | `dispatched` (approved) or `failed` (denied) | No |
| `accepted` | Review gate accepted; task is done | Review gate approves | _(none)_ | **Yes** |
| `escalated` | Failure needs human/Program intervention | Escalation triggered | _(none until Program resolves)_ | **Quasi-terminal** |

### 8.3 Transition Rules (P0 Minimum)

| From | To | Trigger | Required Evidence |
|---|---|---|---|
| `pending` | `dispatched` | Operations dispatches to runner | Ledger entry: `dispatched` with `runner_id`, `dispatched_at` |
| `pending` | `escalated` | Envelope invalid or unprocessable | Ledger entry: `escalated` with reason |
| `dispatched` | `running` | Runner emits `run_started` | Ledger entry: `run_started` with `runner_id`, `started_at` |
| `dispatched` | `escalated` | Runner unresponsive or dispatch fails | Ledger entry: `escalated` with reason |
| `running` | `completed` | Runner emits `run_completed` with exit_code=0 | Ledger entry: `run_completed` with `exit_code`, `finished_at`, `artifact_refs[]` |
| `running` | `failed` | Runner emits `run_failed` | Ledger entry: `run_failed` with `error_code`, `error_message` |
| `running` | `blocked` | Runner emits `run_blocked` or `run_stopped` | Ledger entry: `run_blocked` with `reason_code` |
| `running` | `waiting_approval` | Governance profile requires approval mid-run | Ledger entry: `approval_requested` |
| `running` | `stopped` | Operator signals stop | Ledger entry: `run_stopped` with `reason` |
| `running` | `cancelled` | Operator cancels | Ledger entry: `run_cancelled` with `reason` |
| `completed` | `accepted` | Review gate approves | Ledger entry: `review_accepted` with reviewer identity |
| `completed` | `waiting_approval` | Review gate requires approval | Ledger entry: `approval_requested` |
| `failed` | `dispatched` | Retry authorized | Ledger entry: `retried` with retry count |
| `failed` | `escalated` | Failure unresolvable | Ledger entry: `escalated` with reason |
| `blocked` | `dispatched` | Blocker resolved, retry authorized | Ledger entry: `retried` with resolution |
| `blocked` | `escalated` | Blocker unresolvable | Ledger entry: `escalated` with reason |
| `waiting_approval` | `dispatched` | Approval granted | Ledger entry: `approved` with approver identity |
| `waiting_approval` | `failed` | Approval denied | Ledger entry: `denied` with reason |
| `stopped` | `dispatched` | Operator authorizes retry | Ledger entry: `retried` |
| `stopped` | `escalated` | Stop requires intervention | Ledger entry: `escalated` |

### 8.4 Critical Rules

1. **No self-approval**: A task **cannot** transition to `accepted` without an external review gate decision. A runner cannot review its own output.
2. **No phantom completion**: A task **cannot** transition from `running` to `completed` without the runner emitting `run_completed` with `exit_code = 0` and at least one `artifact_refs[]`.
3. **Reversibility**: The `stopped`, `cancelled`, and `blocked` states are reversible via retry (back to `dispatched`) or escalation (to `escalated`).
4. **Terminal authority**: Only `accepted` is a true terminal state in the P0 minimum loop. `escalated` is quasi-terminal and requires Program Agent intervention to resolve.
5. **Ledger is truth**: The ledger is the single source of truth for task state. No other system (Redis, WorkContext, status reports) defines task state.

### 8.5 Relationship to Full Lifecycle (Sections 1-7)

The P0 minimum state machine is a **subset** of the full 13-state lifecycle defined in Sections 1-7:

| P0 Minimum State | Full Lifecycle Equivalent |
|---|---|
| `pending` | `draft` + `ready` |
| `dispatched` | `assigned` |
| `running` | `running` |
| `completed` | `review_pending` (pre-review) |
| `failed` | `failed` |
| `blocked` | `blocked` + `waiting_input` |
| `waiting_approval` | `waiting_approval` |
| `accepted` | `completed` (post-review) |
| `escalated` | `escalated` |

The P0 minimum is used for the GitHub-first closed loop demonstration. The full lifecycle (Sections 1-7) remains the normative definition for production use.
