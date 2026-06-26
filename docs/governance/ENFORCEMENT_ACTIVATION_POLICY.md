# Enforcement Activation Policy — Stage D

> **Status:** Declarative Policy — No Runtime Enforcement  
> **Created:** 2026-06-26T19:30+08:00  
> **Authority:** Program Controller ENFORCEMENT_ACTIVATION_POLICY_AUTHORIZED (P0)  
> **Baseline:** IEF-Operations `main` @ `29b05e5`  
> **Governance Profile:** Contract-Critical  
> **Companion specs:** `EXECUTION_ENFORCEMENT_PHASE_MODEL.md` (Operations — spec maturity), IEF-Program `EXECUTION_ENFORCEMENT_PHASE_MODEL.md` (execution gating), `EVOLUTION_GUARDRAIL_SPEC.md`, `CLASSIFICATION_REGISTRY_SPEC_PLAN.md`, `VERIFICATION_HARDENING_SPEC.md`

---

## 1. Purpose

This document defines **how the Execution Enforcement Phase Model becomes active** in real IEF workflows. It bridges the gap between the phase model's declarative definitions and the operational reality of agents, dispatches, and cross-system interactions.

The Execution Enforcement Phase Model defines five phases for work execution:

```
REPORT → VALIDATE → AUTHORIZE → EXECUTE → VERIFY/CLOSE
  (0)      (1)        (2)        (3)        (4)
```

This policy specifies:
- **When** the phase model activates (prerequisites)
- **Who** may advance work through each phase (transition authority)
- **What** constitutes an authorization-bearing event vs evidence-only input
- **How** failures are handled at each phase (rollback/abort)
- **Which** components interact with phase state and how (boundaries)

This is a **declarative policy only**. It does not implement runtime enforcement, CI rules, SDK code, or runner integration. Those are deferred to future implementation phases.

---

## 2. Scope

### 2.1 What This Policy Governs

This policy governs the **activation and operation** of the execution phase model for all execution-bearing work in the IEF program:

- Dispatch cycles (Operator worker cycles)
- Contract creation (new specs, schemas, governance documents)
- Governance actions (classification changes, phase model updates)
- Cross-repo operations (multi-repo coordination)
- Smoke tests and diagnostics

### 2.2 Relationship to Phase Models

Two phase models exist in the IEF program. This policy addresses the **execution workflow** model, not the **spec maturity** model:

| Model | Repo | Phases | What It Governs |
|---|---|---|---|
| Execution Phase Model | IEF-Program | Report → Validate → Authorize → Execute → Verify | How work flows through the system |
| Spec Maturity Model | IEF-Operations | Draft → Active → Guarded → Enforced → Locked | How artifacts progress to frozen state |

This activation policy applies to the **Execution Phase Model**. Spec maturity transitions follow the Operations Phase Model's own transition matrix and are out of scope here.

### 2.3 What This Policy Does NOT Govern

- Spec maturity phase transitions (governed by Operations Phase Model Section 4)
- Runtime code behavior (agent implementations)
- CI pipeline configuration
- Classification registry schema (governed by Classification Registry Spec)
- Dashboard rendering or display logic

---

## 3. Activation Prerequisites

The execution phase model activates when **all** of the following conditions are met for a given work item:

### 3.1 Mandatory Prerequisites

| # | Prerequisite | Validator | Evidence |
|---|---|---|---|
| P1 | A GitHub issue exists for the work item | Coordinator | Issue URL in trigger or directive |
| P2 | The issue is classified with a recognized classification | Coordinator (preflight) | Classification matches registry |
| P3 | The issue is linked to IEF Command Center (Project) | Coordinator | Project board membership |
| P4 | At least one governance artifact exists in the target repo | Coordinator | File listing check |
| P5 | No unresolved `IEF_BLOCKED` classification on the work item | Coordinator | Classification scan |

### 3.2 Conditional Prerequisites

These apply depending on the work category:

| Work Category | Additional Prerequisite |
|---|---|
| Contract creation | Target repo must have a `contracts/` or `docs/governance/` directory |
| Schema modification | Schema meta-schema validation tooling available |
| Cross-repo operation | All target repos must be accessible to the Operator |
| Dispatch execution | Trigger JSON must exist and parse successfully |

### 3.3 Activation Failure

If any mandatory prerequisite fails:
1. The work item is flagged as `ACTIVATION_BLOCKED`.
2. A report is posted to the issue identifying which prerequisite failed.
3. The work item enters Phase 0 (Report) but cannot advance to Phase 1 until all prerequisites are met.
4. No automated retry — the Coordinator must re-evaluate after prerequisites are addressed.

---

## 4. Phase Transition Authority

### 4.1 Transition Authority Matrix

Each phase transition requires a specific authority level. No transition may be performed by an actor below the required level.

| Transition | Required Authority | Actor | Mechanism |
|---|---|---|---|
| Phase 0 → Phase 1 (Report → Validate) | L2 | Coordinator | Validation report comment on issue |
| Phase 1 → Phase 2 (Validate → Authorize) | L1 | Controller or L1-delegate | Validation sign-off comment |
| Phase 2 → Phase 3 (Authorize → Execute) | L1 | Controller | `Label: ACTION REQUIRED` comment + trigger JSON |
| Phase 3 → Phase 4 (Execute → Verify) | L3 → L2 | Executor (reports) → Coordinator (verifies) | Delivery report + ledger update |
| Phase 4 Close | L1 | Controller (Contract-Critical) or L2 (low-risk) | Issue close or PR merge authorization |

### 4.2 Backward Transition Authority

| Transition | Required Authority | Actor | Mechanism |
|---|---|---|---|
| Phase 1 → Phase 0 (Validate → Report) | L2 | Coordinator | Rejection comment with remediation steps |
| Phase 2 → Phase 1 (Authorize → Validate) | L1 | Controller | Scope change directive |
| Phase 3 → Phase 2 (Execute → Authorize) | L1 | Controller | New authorization with updated constraints |
| Phase 4 → Phase 3 (Verify → Execute) | L1 | Controller | Revision directive |
| Phase 4 → Phase 0 (Verify → Report) | L1 or L0 | Controller or Human Owner | Full re-scoping directive |

### 4.3 Separation of Concerns

| Role | May NOT also be |
|---|---|
| Phase 0 reporter | Phase 1 validator of the same work |
| Phase 1 validator | Phase 2 authorizer of the same work |
| Phase 2 authorizer | Phase 3 executor of the same work |
| Phase 3 executor | Phase 4 verifier of the same work |

---

## 5. Event Classification: Authorization-Bearing vs Evidence-Only

This is the most critical section of this policy. It distinguishes events that **carry authority to trigger phase transitions** from events that are **informational only**.

### 5.1 Authorization-Bearing Events

These events carry the authority to advance work to the next phase. They MUST originate from an actor at or above the required authority level and MUST be GitHub-durable (issue/PR comment).

| Event | Authority Source | Phase Transition Triggered |
|---|---|---|
| `PROG_AUTHORIZATION_GRANTED` | Controller (L1) | Phase 2 readiness (work authorized) |
| `OPS_ACTION_REQUIRED` with trigger JSON | Controller (L1) or L1-delegate | Phase 3 readiness (execution authorized) |
| Validation sign-off comment | Coordinator (L2) | Phase 0 → Phase 1 |
| Controller directive with `Label: ACTION REQUIRED` | Controller (L1) | Phase 2 → Phase 3 |
| Delivery report posted by executor | Executor (L3) | Phase 3 → Phase 4 (verification pending) |
| Controller merge approval | Controller (L1) | Phase 4 close |

**Properties of authorization-bearing events:**
- Must be posted as a GitHub issue or PR comment
- Must include explicit scope (target repo, branch, allowed files)
- Must include explicit constraints (forbidden actions, hard constraints)
- Must reference an authority chain (Controller decision, relay comment)
- Must include a timeout value (or default to 1500s for execution)
- Must use a registered classification from the Classification Registry
- Dedupe key must be derived from the triggering context

### 5.2 Evidence-Only Events

These events provide information about work state but do NOT carry authority to trigger phase transitions. They may be consumed by any component but must not cause automated phase advancement.

| Event | Source | Information Provided |
|---|---|---|
| `RUN_EXECUTABLE_IDLE` | Runner | Execution has started (informational) |
| `RUN_ARTIFACT_DELIVERED` | Runner | Execution completed (informational) |
| `KNW_REVIEW_RETURNED` | Knowledge | Review completed (informational) |
| `OPS_WAITING_CODEX` | PM | Awaiting external agent (informational) |
| `OPS_WAITING_AGENT` | PM | Awaiting agent availability (informational) |
| `OPS_WAITING_HUMAN` | PM/Coordinator | Awaiting human decision (informational) |
| `OPS_NO_ACTION_REQUIRED` | PM | Cycle completed, no work found (informational) |
| `OPS_NO_SAFE_ACTION` | Operator | Safety check prevented action (informational) |
| Dashboard render event | Dashboard | Data displayed (informational) |
| Knowledge index update | Knowledge | Content indexed (informational) |
| Git commit/push | Any | Code change recorded (informational) |
| Lint result (Spectral) | CI | Validation outcome (informational) |
| Verification result | Verification Module | Quality assessment (informational) |

**Properties of evidence-only events:**
- May be emitted by any component (runners, adapters, knowledge, dashboard, CI)
- May be consumed by Coordinator for decision-making
- Must NOT trigger automated phase transitions
- Must NOT be treated as authorization for execution
- Must be logged in the dispatch ledger for audit trail

### 5.3 Event Misclassification Prevention

If an evidence-only event is mistakenly treated as authorization-bearing:

1. The Operator MUST reject the execution attempt.
2. Post a `PREFLIGHT_VOCABULARY_MISMATCH` or `ACTIVATION_POLICY_VIOLATION` report.
3. The Coordinator MUST investigate and clarify.
4. The work item remains in its current phase until a genuine authorization-bearing event arrives.

**Known failure mode:** A runner emits `RUN_ARTIFACT_DELIVERED` and an automated system interprets this as Phase 4 readiness, auto-closing the work item. This is prevented by requiring Phase 4 verification to be performed by a Coordinator or Controller, not triggered by runner output.

---

## 6. Component Interaction Rules

### 6.1 Coordinator (PM Agent)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| Phase 0 (Report) | Create issue, classify, link to Project, post initial context | Create branch, modify target files |
| Phase 1 (Validate) | Inspect repos, check dependencies, validate classifications, post validation report, sign off Phase 0→1 | Create working branch, modify target files, dispatch execution |
| Phase 2 (Authorize) | Create trigger JSON (when delegated L1 authority), post authorization comment | Begin execution, create branch, modify target files |
| Phase 3 (Execute) | Monitor execution, post progress comments | Execute work (Operator role), modify allowed files |
| Phase 4 (Verify) | Post delivery report, update dispatch ledger, verify scope compliance | Close issue (Contract-Critical), modify delivered files |

### 6.2 Operator Agent

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| Phase 0 (Report) | N/A — Operator not involved | All actions |
| Phase 1 (Validate) | N/A — Operator not involved | All actions |
| Phase 2 (Authorize) | N/A — Operator not involved | All actions |
| Phase 3 (Execute) | Re-read directive, checkout branch, create branch, modify allowed files, commit, push, draft delivery report | Modify non-allowed files, merge PRs, close issues, expand scope |
| Phase 4 (Verify) | Post delivery report, update dispatch ledger | Modify delivered files (unless revision directive), close issue |

**Critical rule:** The Operator may execute exactly **one bounded worker cycle** per Phase 2 authorization. No retries without new authorization.

### 6.3 Controller (Human or Program Controller Agent)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| Phase 0 (Report) | Create issue, override any constraint | N/A |
| Phase 1 (Validate) | Sign off validation, reject scope | N/A |
| Phase 2 (Authorize) | Issue authorization, define scope/constraints, delegate to Coordinator | Self-execute |
| Phase 3 (Execute) | Monitor, issue emergency halt | Modify files directly |
| Phase 4 (Verify) | Review delivery, authorize close, authorize revision | N/A |

### 6.4 Runner (IEF-Runners)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| Phase 0 (Report) | Read issue context | Create issues, classify work, trigger transitions |
| Phase 1 (Validate) | N/A | All actions |
| Phase 2 (Authorize) | N/A | All actions |
| Phase 3 (Execute) | Execute within allowed-tools whitelist, report status via evidence-only events | Trigger phase transitions, modify phase state, self-authorize |
| Phase 4 (Verify) | N/A | All actions |

**Critical constraint:** Runners emit evidence-only events (`RUN_EXECUTABLE_IDLE`, `RUN_ARTIFACT_DELIVERED`). These events are consumed by the Coordinator for tracking but MUST NOT trigger phase transitions.

### 6.5 Adapter (IEF-Adapters)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| All phases | Translate external requests into Phase 0 reports (issue creation) | Trigger phase transitions, modify phase state, execute work, classify work beyond initial report |

**Critical constraint:** Adapters may create issues (Phase 0 entry) but may not advance work beyond Phase 0. All subsequent transitions require Coordinator/Controller action.

### 6.6 Knowledge System (IEF-Knowledge)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| All phases | Read phase state, index content, provide context packs, emit evidence-only events (`KNW_REVIEW_RETURNED`) | Trigger phase transitions, modify phase state, auto-promote knowledge, infer task lifecycle from phase state |

**Critical constraint:** Knowledge is a read-only consumer of phase state. It may reference phase information in context packs but must not treat phase state as authoritative or trigger any workflow action based on it.

### 6.7 Dashboard (IEF-Operations dashboard.html)

| Phase | Allowed Actions | Forbidden Actions |
|---|---|---|
| All phases | Read phase state from embedded JSON, render visual projection | Trigger phase transitions, compute phase state, infer task lifecycle, schedule execution, emit events |

**Critical constraint:** The Dashboard is a read-only projection of the Operations ledger. It does not compute state, does not trigger actions, and does not constitute a secondary state authority. The visible footer declares this: "Read-only projection — Data source: Operations ledger."

---

## 7. Failure, Rollback, and Abort Behavior

### 7.1 Failure Mode Definitions

| Failure Mode | Phase | Description | Severity |
|---|---|---|---|
| **Activation Blocked** | Phase 0 | Prerequisites not met | Low — informational |
| **Validation Failed** | Phase 1 | Scope unclear, dependencies unresolved, classification invalid | Medium — requires remediation |
| **Authorization Declined** | Phase 2 | Controller rejects scope or constraints | Medium — requires re-scoping |
| **Authorization Lapsed** | Phase 2 | Timeout expired before execution began | Medium — requires re-authorization |
| **Execution Failed** | Phase 3 | Worker error, tool failure, dependency failure | High — requires investigation |
| **Execution Blocked** | Phase 3 | Safety check prevented action (`OPS_NO_SAFE_ACTION`) | High — requires Controller decision |
| **Scope Violation** | Phase 3 | Changed files outside allowed list | Critical — guardrail violation |
| **Forbidden Action** | Phase 3 | Allowed-tools denial or forbidden operation attempted | Critical — guardrail violation |
| **Verification Failed** | Phase 4 | Delivery does not meet done criteria | Medium — requires revision |
| **Evidence Chain Broken** | Any | Required evidence artifact missing | High — phase transition invalid |

### 7.2 Rollback Procedures by Phase

#### Phase 1 → Phase 0 Rollback (Validation Failure)

**Trigger:** Validation report identifies unresolvable issues.

**Procedure:**
1. Coordinator posts rejection comment identifying failures.
2. Issue remains open; classification updated to reflect blocked state.
3. No branch created; no files modified.
4. Reporter addresses issues and requests re-validation.
5. Coordinator re-evaluates prerequisites before re-entering Phase 1.

**Abort condition:** If validation fails 3+ times on the same work item, escalate to Controller.

#### Phase 2 → Phase 1 Rollback (Authorization Declined)

**Trigger:** Controller declines authorization or scope changes significantly.

**Procedure:**
1. Controller posts directive explaining why authorization was declined.
2. Work returns to Phase 1 for re-validation with updated scope.
3. Trigger JSON (if created) is invalidated.
4. New validation report required before re-authorization attempt.

**Abort condition:** If authorization is declined twice, the Controller must explicitly decide whether to continue or cancel the work item.

#### Phase 3 → Phase 2 Rollback (Execution Failure)

**Trigger:** Worker exits with failure code, tool failure, or safety check block.

**Procedure:**
1. Operator posts failure report to issue with exit code and error details.
2. Operator stops — no retry without new authorization.
3. Controller evaluates failure and decides:
   - **Retryable:** Issue new Phase 2 authorization with updated constraints.
   - **Non-retryable:** Escalate to Phase 2 → Phase 1 rollback for re-scoping.
4. If retryable, new trigger JSON created with updated parameters.
5. Operator executes new cycle under new authorization.

**Abort condition:** If execution fails 3+ times on the same work item with different approaches, escalate to Controller for fundamental re-evaluation.

#### Phase 4 → Phase 3 Rollback (Verification Failure)

**Trigger:** Coordinator verification identifies gaps against done criteria.

**Procedure:**
1. Coordinator posts verification failure report with specific gaps.
2. Controller issues revision directive (new Phase 2 authorization scoped to gaps).
3. Operator executes revision under new authorization.
4. New delivery report and verification cycle required.

**Abort condition:** If verification fails twice, Controller must decide whether to accept partial delivery or cancel.

### 7.3 Emergency Halt

The Controller may issue an emergency halt at any phase:

1. Controller posts `EMERGENCY_HALT` directive comment.
2. All active work on the item stops immediately.
3. Operator (if in Phase 3) stops execution, does not commit or push.
4. Work item flagged as `HALTED` in dispatch ledger.
5. No resumption until Controller issues explicit `HALT_LIFTED` directive.

### 7.4 Abort (Permanent Cancellation)

Work items may be permanently aborted:

| Authority | Condition |
|---|---|
| Human Owner (L0) | Any time, any reason |
| Controller (L1) | Work item no longer aligned with program goals, or infeasible |

**Abort procedure:**
1. Abort directive posted to issue with rationale.
2. Issue closed with `wontfix` label.
3. Dispatch ledger updated with `status: ABORTED`.
4. Any open PRs closed.
5. No branch cleanup required (branches remain for historical record).

---

## 8. Phase State Map: Inputs, Outputs, Authority

### 8.1 Phase 0 — Report

| Aspect | Definition |
|---|---|
| **Allowed inputs** | GitHub issue creation, classification assignment, context comments, IEF Command Center linkage |
| **Produced outputs** | Issue with complete description, classification label, context comment, dependency list |
| **Transition authority** | Coordinator (L2) — validates readiness for Phase 1 |
| **Allowed actors** | Any (L0–L4) may create issues and post context |
| **Forbidden actors** | None at this phase |
| **Evidence produced** | Issue URL, classification, context comment |
| **State on exit** | Work item validated and ready for authorization |

### 8.2 Phase 1 — Validate

| Aspect | Definition |
|---|---|
| **Allowed inputs** | Repo inspection, dependency checks, classification validation, scope analysis |
| **Produced outputs** | Validation report (comment), trigger JSON (if dispatch-based), allowed files list, forbidden actions list |
| **Transition authority** | Controller (L1) or L1-delegate — signs off validation |
| **Allowed actors** | Coordinator (L2) performs validation; Controller (L1) signs off |
| **Forbidden actors** | Runners, Adapters, Knowledge, Dashboard |
| **Evidence produced** | Validation report comment, trigger JSON file |
| **State on exit** | Work item authorized and ready for execution |

### 8.3 Phase 2 — Authorize

| Aspect | Definition |
|---|---|
| **Allowed inputs** | Authorization comment, trigger JSON, priority/timeout metadata |
| **Produced outputs** | `Label: ACTION REQUIRED` comment, trigger JSON (if not already created), scope definition |
| **Transition authority** | Controller (L1) — issues authorization |
| **Allowed actors** | Controller (L1) authorizes; Coordinator (L2) may create trigger JSON when delegated |
| **Forbidden actors** | Runners, Adapters, Knowledge, Dashboard |
| **Evidence produced** | Authorization comment with `Label: ACTION REQUIRED`, trigger JSON |
| **State on exit** | Executor has received authorization and is ready to execute |

### 8.4 Phase 3 — Execute

| Aspect | Definition |
|---|---|
| **Allowed inputs** | Authorization comment, trigger JSON, target repo checkout, allowed files |
| **Produced outputs** | Git branch, commits, push to remote, delivery report draft |
| **Transition authority** | Executor (L3) reports completion; Coordinator (L2) verifies |
| **Allowed actors** | Operator (L3) or Runner (L3) executes within scope |
| **Forbidden actors** | Adapters, Knowledge, Dashboard (may observe but not participate) |
| **Evidence produced** | Commits, branch push, worker output, delivery report |
| **State on exit** | Execution artifacts delivered, awaiting verification |

### 8.5 Phase 4 — Verify/Close

| Aspect | Definition |
|---|---|
| **Allowed inputs** | Delivery report, dispatch ledger, done criteria, verification checklist |
| **Produced outputs** | Delivery report (posted), ledger update, PR (if applicable), issue close (if authorized) |
| **Transition authority** | Controller (L1) for Contract-Critical close; Coordinator (L2) for low-risk close |
| **Allowed actors** | Coordinator (L2) verifies; Controller (L1) or Human Owner (L0) closes |
| **Forbidden actors** | Runners, Adapters, Knowledge, Dashboard |
| **Evidence produced** | Delivery report comment, ledger entry, PR/issue close record |
| **State on exit** | Work item complete (SUCCESS, FAILED, BLOCKED, or NEEDS_REVISION) |

---

## 9. Critical Constraints (Reaffirmed)

The following constraints are absolute and non-negotiable. They are reaffirmed here to ensure no component interaction violates the phase model's integrity.

### 9.1 No Self-Execution

- No component may execute work on itself. The Operator executes work authorized by the Controller, validated by the Coordinator.
- The Coordinator may not execute work it validated.
- The Controller may not execute work it authorized.

### 9.2 No Self-Approval

- No component may approve its own work. The executor's delivery is verified by an independent Coordinator.
- The Coordinator's validation is signed off by an independent Controller.
- Self-approval attempts constitute guardrail violations.

### 9.3 No Auto-Merge

- No component may automatically merge PRs. All merges require human authorization (Controller or Human Owner).
- Auto-merge would bypass the Phase 4 verification gate.

### 9.4 No Auto-Unblock

- No component may unblock itself from a `blocked` state. Unblock requires an explicit `IEF_UNBLOCKED` event from an equal or higher authority than the original blocker.
- Self-unblock attempts constitute guardrail violations.

### 9.5 No Phase Transition by Downstream Components

- **No runner, adapter, Knowledge component, Dashboard, or local state file may trigger a phase transition.**
- These components are read-only consumers of phase state.
- Events from these components are evidence-only, not authorization-bearing.
- The Coordinator must independently validate and relay any apparent phase change request through the normal transition matrix.

### 9.6 No Phase State Computation by Dashboard or Knowledge

- The Dashboard may render phase state visually but must not compute, infer, or derive new phase state.
- Knowledge may index phase information but must not treat it as authoritative or trigger workflow actions.
- Neither Dashboard nor Knowledge may infer task lifecycle state from visual or indexed phase information.

### 9.7 Execution Cannot Occur Before AUTHORIZE

- Phase 3 (Execute) requires a valid Phase 2 authorization with `Label: ACTION REQUIRED`.
- No execution may begin based on Phase 0 or Phase 1 state alone.
- An Operator that begins execution without Phase 2 authorization is in violation.

### 9.8 VERIFY/CLOSE Cannot Be Inferred

- Phase 4 (Verify/Close) requires explicit Coordinator verification and Controller close authorization.
- Dashboard display of "complete" status does not constitute verification.
- Knowledge indexing of delivery report does not constitute close.
- Runner reporting `RUN_ARTIFACT_DELIVERED` does not constitute verification.

---

## 10. Authorization Chain Validation

Every phase transition must include a verifiable authorization chain. The Coordinator validates this chain before accepting any transition.

### 10.1 Chain Structure

```
Controller Decision (GitHub comment)
    ↓
Coordinator Relay (GitHub comment with relay reference)
    ↓
Trigger JSON (file with authorization metadata)
    ↓
Operator Execution (bounded worker cycle)
    ↓
Delivery Report (GitHub comment with evidence chain)
    ↓
Ledger Update (dispatch ledger entry)
```

### 10.2 Chain Validation Rules

| Rule | Description |
|---|---|
| **CV-1** | Every link in the chain must be GitHub-durable (comments, files in repo). |
| **CV-2** | The Controller decision must reference a specific scope (repo, issue, files). |
| **CV-3** | The Coordinator relay must reference the Controller decision comment ID. |
| **CV-4** | The trigger JSON must reference the Coordinator relay comment ID. |
| **CV-5** | The Operator execution must reference the trigger JSON trigger ID. |
| **CV-6** | The delivery report must reference the Operator's execution evidence. |
| **CV-7** | The ledger update must reference the delivery report comment ID. |
| **CV-8** | Any broken link invalidates the chain; the transition is rejected. |

### 10.3 Chain Failure Response

If the authorization chain is broken at any point:
1. The Coordinator flags the transition as `AUTHORIZATION_CHAIN_BROKEN`.
2. The work item is returned to the phase where the chain was last intact.
3. A new authorization chain must be established from that phase.
4. The failure is recorded in the dispatch ledger.

---

## 11. Anti-Circumvention Rules

### 11.1 Policy Bypass Prevention

- No component may bypass this policy by operating outside the phase model.
- Work performed outside the phase model is unofficial and does not count as IEF progress.
- The Coordinator must reject any delivery that does not follow the phase model.

### 11.2 Implicit Authorization Prevention

- No event, regardless of source, may be treated as implicit authorization.
- All authorizations must be explicit, GitHub-durable, and use registered classifications.
- Chat messages, memory, local state files, and dashboard renders are not authorization sources.

### 11.3 Cascade Prevention

- A phase transition in one work item must not automatically cascade to related work items.
- Each work item's phase transitions are independent.
- Cross-work-item dependencies are managed by the Coordinator through explicit dependency tracking, not automated cascading.

### 11.4 Replay Prevention

- An authorization-bearing event may only be consumed once per work item.
- Dedupe keys (per Classification Registry) prevent replay of authorizations.
- After consumption, the authorization is marked as consumed in the dispatch ledger.
- Re-execution requires a new authorization cycle.

---

## 12. Compliance Checklist

For any work item subject to this activation policy, verify:

- [ ] All activation prerequisites met (Section 3)
- [ ] Phase transition authority respected (Section 4)
- [ ] Authorization-bearing events correctly identified (Section 5)
- [ ] Evidence-only events not treated as authorization (Section 5)
- [ ] Component interaction rules followed (Section 6)
- [ ] Failure/rollback procedures available and documented (Section 7)
- [ ] Phase state map inputs/outputs/authority respected (Section 8)
- [ ] Critical constraints not violated (Section 9)
- [ ] Authorization chain complete and validated (Section 10)
- [ ] Anti-circumvention rules respected (Section 11)

---

## 13. Future Work

1. **Runtime Enforcement**: Automated validation of authorization chains in CI.
2. **SDK Implementation**: Programmatic API for phase state queries (read-only).
3. **Runner Integration**: Runner lifecycle events mapped to evidence-only phase signals.
4. **Dashboard Phase Visualization**: Phase state rendered in dashboard (read-only projection).
5. **Metrics**: Time-in-phase, transition frequency, failure rates, chain validation success rate.

---

*End of policy.*
