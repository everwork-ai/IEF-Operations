# Control Plane Freeze Specification — Stage G (G8-1)

> **Status:** Frozen  
> **Created:** 2026-06-22T12:02+08:00  
> **Authority:** Program Controller DISPATCH_AUTHORIZED (comment [4763724671](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4763724671))  
> **Baseline:** IEF-Operations `main` @ `31bc466`  
> **Governance Profile:** Contract-Critical  

---

## 1. Purpose

This specification **freezes** the control plane boundaries between Program, Operations, and Verification layers for Stage G of the IEF program. Once frozen, no layer may silently expand, contract, or redefine another layer's authority without explicit Program Controller approval.

This document does **not** introduce runtime logic, execution engine changes, or implementation code. It is a specification-level contract lock.

---

## 2. Layer Boundary Definitions (Frozen)

### 2.1 Program Layer — Control Plane Authority

| Responsibility | Scope |
|---|---|
| Cross-repository coordination | Decides which repos are active, blocked, or unblocked |
| Controller gating | All dispatch decisions require explicit Controller approval |
| Directive issuance | Creates actionable directives via GitHub issue/PR comments |
| Stage progression | Decides when a stage is complete and next stage may begin |
| Standing delegation | May delegate bounded authority to Coordinator; may revoke at any time |
| Conflict resolution | Resolves boundary disputes between layers |

**Frozen constraints on Program:**

1. Program **must not** directly modify Operations lifecycle rules or ledger semantics.
2. Program **must not** bypass Operations approval gates or review gates.
3. Program directives **must** be posted as GitHub comments with a stable comment ID.
4. Program **must not** rely on private chat, memory, or model context as the source of a directive.

### 2.2 Operations Layer — Work Operating System

| Responsibility | Scope |
|---|---|
| Task lifecycle | State machine: 13 states, transition rules, evidence requirements |
| Run lifecycle | State machine: 8 states, transition rules |
| Run ledger | Append-only event log; ordering, immutability, integrity |
| Protocol object usage | How `TaskEnvelope`, `RunEvent`, `ArtifactRef`, `ContextRef` are consumed |
| Governance alignment | Maps governance profiles into lifecycle stop points and evidence gates |
| Agent conformance | Normative rules for AI coding agents operating within IEF |

**Frozen constraints on Operations:**

1. Operations **must not** redefine Protocol schemas (owned by IEF-Protocol).
2. Operations **must not** redefine Governance profiles (owned by IEF-Governance).
3. Operations **must not** implement runners, adapters, or knowledge storage.
4. Operations **must not** make cross-repo coordination decisions (owned by Program).
5. Operations **must not** self-approve review gates or unblock downstream repos.

### 2.3 Verification Layer — Review and Approval Gates

| Responsibility | Scope |
|---|---|
| Review gates | Validates artifacts, evidence, and conformance before acceptance |
| Approval gates | Human Owner or Program Controller approval for gated transitions |
| Evidence validation | Checks that required evidence exists and meets governance profile |
| Escalation routing | Routes unresolved failures to Program Controller or Human Owner |

**Frozen constraints on Verification:**

1. Verification **must not** initiate task dispatch or lifecycle transitions.
2. Verification **must not** modify task state without evidence of review outcome.
3. Verification **must not** approve its own work (no self-approval).
4. Verification decisions **must** be recorded as ledger events or GitHub comments.

---

## 3. No Implicit State Source Rule

This is the **primary formalized rule** required by G8-1 done criteria.

### 3.1 Rule Statement

> **No layer, agent, or operator may treat chat history, local memory, model memory, private conversation, or in-memory state as a durable source of truth for task scope, authorization, boundaries, or decisions.**

### 3.2 Allowed Durable Sources (exhaustive)

| Source | Format | Authority |
|---|---|---|
| GitHub issue/PR comments | Comment ID + body text | Directives, decisions, proposals |
| GitHub repo files | Committed file at specific SHA | Specifications, schemas, documentation |
| GitHub PR state | PR metadata (head SHA, base, status) | Branch state, merge readiness |
| Protocol schemas | JSON Schema / Markdown in IEF-Protocol | Object definitions |
| Governance profiles | Documents in IEF-Governance | Conformance and review rules |
| Trigger JSON | File in `IEF-Orchestration/triggers/` | Operator dispatch parameters |

### 3.3 Prohibited Implicit Sources

| Prohibited Source | Why |
|---|---|
| Chat history (any platform) | Ephemeral, mutable, not version-controlled |
| Local agent memory (`MEMORY.md`, `memory/*.md`) | May be stale, unverified, or contradicted by GitHub |
| Model parametric memory | Not auditable, may hallucinate, not version-controlled |
| Private conversations | Not visible to other layers or human oversight |
| Assumed prior decisions | May have been superseded by newer GitHub evidence |

### 3.4 Conflict Resolution

When an implicit source conflicts with a durable source, the durable source **always** wins. The agent or operator **must** report the conflict and proceed based on the durable source.

---

## 4. Dispatch Control Rule (Frozen)

As defined by the Program Controller (comment 4763724671):

> 1. **Requires explicit Controller approval** for each dispatch.  
> 2. **No time-based implicit authorization** allowed.  
> 3. **Coordinator cannot assume execution** after timeout.

### 4.1 Implications

- The Coordinator **must not** auto-dispatch after any timeout or idle period.
- The Operator **must not** execute without a valid `DISPATCH_AUTHORIZED` classification referencing a specific Controller decision.
- Each dispatch cycle is **bounded**: one operator invocation, one commit set, one delivery report, then stop.
- No standing authorization carries across slices. Each G8 sub-slice (G8-1 through G8-4) requires its own Controller approval.

---

## 5. Scope Exclusions (What This Document Does NOT Do)

This specification explicitly **does not**:

1. Introduce runtime logic or execution code.
2. Change any task lifecycle state machine or transition rule.
3. Modify the run ledger schema or event catalog.
4. Unblock any downstream repository (IEF-Runners, IEF-Knowledge, IEF-Adapters).
5. Redefine or fork Protocol or Governance schemas.
6. Authorize any merge, close, or cross-repo implementation.
7. Grant standing authority for future slices.

---

## 6. Freeze Amendment Process

To modify any frozen boundary or rule in this document:

1. A change proposal must be posted as a GitHub comment on IEF-Program#11.
2. The Program Controller must issue a new `DISPATCH_AUTHORIZED` decision referencing the change.
3. The change must be implemented as a new commit on a new branch (no amendments to frozen commits).
4. The `STAGE_G_CONTRACT_LOCK.json` schema must be updated to reflect the change.

No implicit, time-based, or silent amendment is permitted.

---

## 7. References

| Reference | Relationship |
|---|---|
| [IEF-Program#11](https://github.com/everwork-ai/IEF-Program/issues/11) | Stage G execution issue |
| [IEF-Program#11 comment 4763724671](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4763724671) | Controller DISPATCH_AUTHORIZED decision |
| [IEF-Program#11 comment 4763704384](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4763704384) | Coordinator dispatch proposal |
| [IEF-Operations docs/IEF_OPERATIONS_V0.md](../IEF_OPERATIONS_V0.md) | Operations baseline (boundaries in Sections 1.2, 1.3, 3, 8) |
| [AUTHORIZED_MUTATION_MATRIX.md](./AUTHORIZED_MUTATION_MATRIX.md) | Companion: mutation path allow/deny matrix |
| [STAGE_G_CONTRACT_LOCK.json](../../schemas/STAGE_G_CONTRACT_LOCK.json) | Companion: machine-readable contract lock |
| [IEF-Governance#3](https://github.com/everwork-ai/IEF-Governance/pull/3) | Merged Contract-Critical governance baseline |
| [IEF-Protocol#3](https://github.com/everwork-ai/IEF-Protocol/pull/3) | Merged Protocol v0.1.0 baseline |
