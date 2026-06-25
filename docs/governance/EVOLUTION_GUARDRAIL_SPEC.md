# Evolution Guardrail Specification — Stage G (G8-4)

> **Status:** Frozen Specification  
> **Created:** 2026-06-25T17:45+08:00  
> **Authority:** Program Controller EXECUTION_AUTHORIZATION (G8-4, P0)  
> **Baseline:** IEF-Operations `main` @ `7888002`  
> **Prior slices:** G8-1 Control Plane Freeze, G8-2 Verification Hardening, G8-3 (reserved)  
> **Governance Profile:** Contract-Critical  
> **Schema Reference:** JSON Schema Draft 2020-12  
> **Companion specs:** `VERIFICATION_HARDENING_SPEC.md`, `FAILURE_REPLAY_MODEL.md`, `IKE_CONSUMER_STABILITY_SPEC.md`

---

## 1. Purpose

This specification defines the **self-evolution boundaries** for the IEF program. It declares what may evolve, what is frozen, who may authorize changes, and how unauthorized mutations are detected and reverted.

The IEF system comprises autonomous agents (Coordinator, PM, Operator, Workers) that operate on shared repositories, schemas, governance documents, and classification vocabularies. Without explicit evolution guardrails, these agents could independently modify foundational contracts, schemas, or governance policies — creating undetectable drift, silent contract violations, or authority escalation.

This document establishes that **all self-evolution is PR-gated and review-gated**. No agent may modify frozen artifacts outside the pull-request workflow. No agent may self-approve changes to its own authority boundaries. No mutation of classification vocabulary is permitted without explicit Controller authorization.

This is a declarative governance specification. It does not implement runtime enforcement, CI hooks, or automated mutation detection. Those are out of scope for G8-4.

---

## 2. Allowed Evolution Paths

The following change categories are permitted within the IEF program, subject to the gating requirements in Section 6.

### 2.1 Schema Additions (Non-Breaking)

| Evolution Type | Scope | Approval Required |
|---|---|---|
| New optional fields in existing schemas | Schemas directory | Coordinator + Reviewer |
| New schema files (non-conflicting with existing) | Schemas directory | Coordinator + Reviewer |
| Schema documentation updates | Schemas directory | Coordinator |
| Schema example/fixture additions | Tests/fixtures directory | Auto (no review) |

**Constraint:** No removal, renaming, or type-change of existing required fields without Controller authorization (see Section 3 Forbidden Paths).

### 2.2 New Contract and Governance Files

| Evolution Type | Scope | Approval Required |
|---|---|---|
| New governance spec (companion to existing) | docs/governance/ | Controller authorization |
| New contract file (OAS, data contract) | docs/governance/ | Controller authorization |
| Updates to existing governance specs | docs/governance/ | Controller authorization |
| New operational runbooks | docs/operations/ | Coordinator + Reviewer |

### 2.3 Documentation and Operational Artifacts

| Evolution Type | Scope | Approval Required |
|---|---|---|
| README updates | Any repo root | Auto (no review) |
| Operational logs, delivery reports | reports/, logs/ | Auto (no review) |
| Trigger and state files | triggers/, state/ | Coordinator |
| Verification fixture additions | tests/fixtures/ | Auto (no review) |

### 2.4 Worker and Tool Configuration

| Evolution Type | Scope | Approval Required |
|---|---|---|
| Worker prompt templates | Internal (not in repo) | Coordinator |
| Allowed-tools whitelist adjustments | Trigger JSON | Coordinator + Reviewer |
| Timeout and retry parameters | Trigger JSON | Coordinator |
| Model selection per worker type | Worker configuration | Coordinator |

---

## 3. Forbidden Evolution Paths

The following mutations are **unconditionally forbidden** regardless of who attempts them or through what mechanism. Attempting any of these constitutes a guardrail violation requiring immediate rollback (Section 7).

### 3.1 Runtime Self-Modification

| Forbidden Action | Rationale |
|---|---|
| Agent modifies its own system prompt or SOUL.md during execution | Prevents authority escalation and identity drift |
| Agent modifies its own allowed-tools whitelist at runtime | Prevents scope expansion beyond authorization |
| Agent writes to its own trigger JSON or dispatch ledger during execution | Prevents retroactive authorization fabrication |
| Agent modifies AGENTS.md or governance specs that define its own boundaries | Prevents self-granted authority expansion |
| Agent creates new agent definitions or spawns unauthorized sub-agents | Prevents uncontrolled replication |

### 3.2 Autonomous Merge and Deployment

| Forbidden Action | Rationale |
|---|---|
| Auto-merge of any PR without human review | All evolution must be review-gated |
| Auto-patching of production branches | Prevents unaudited changes to frozen artifacts |
| Direct push to `main` or `stage-*` branches | Bypasses PR workflow entirely |
| Force-push to any branch | Destroys history and audit trail |
| Auto-close of issues or PRs | Prevents premature termination of governance workflows |

### 3.3 Self-Approval and Self-Unblock

| Forbidden Action | Rationale |
|---|---|
| Agent approves its own PR | Violates separation of authority |
| Agent dismisses its own review comments | Circumvents review gating |
| Agent marks its own verification as passed | Circumvents verification module |
| Agent unblocks itself from a `blocked` verification result | Circumvents failure classification |
| Agent overrides its own `forbidden_actions` list | Self-granted scope expansion |

### 3.4 Classification Vocabulary Mutation

| Forbidden Action | Rationale |
|---|---|
| Any agent adds classification terms without Controller authorization | Vocabulary is Controller-owned |
| Coordinator/PM/Operator modifies `task_type` vocabulary | Only Controller defines task taxonomy |
| Agent reclassifies existing triggers to bypass approval matrix | Circumvents gating requirements |
| Agent creates new `classification` values (e.g., new authorization types) | Prevents unauthorized authority categories |

---

## 4. Mutation Approval Matrix

This matrix defines who may authorize which categories of change. Authorization is cumulative: higher authority includes lower authority permissions.

### 4.1 Authority Levels

| Level | Actor | Scope |
|---|---|---|
| **L0 — Auto** | System/CI | Documentation, fixtures, logs, reports |
| **L1 — Coordinator** | Coordinator agent | Triggers, state files, worker configuration, schema additions |
| **L2 — Reviewer** | Human reviewer (PR review) | Non-breaking schema changes, new governance companions |
| **L3 — Controller** | Program Controller (human) | Vocabulary mutation, frozen spec updates, branch policy, authority boundary changes |

### 4.2 Approval Requirements by Change Category

| Change Category | Minimum Authority | Additional Requirements |
|---|---|---|
| README / documentation (non-governance) | L0 | None |
| Test fixture additions | L0 | None |
| Delivery reports / operational logs | L0 | None |
| Trigger JSON creation | L1 | Must reference valid directive comment |
| State file updates (dispatch ledger) | L1 | Must correspond to completed cycle |
| Worker prompt template changes | L1 | Must not expand allowed-tools scope |
| Schema optional field addition | L1 + L2 | PR review required |
| New governance companion spec | L3 | Controller authorization comment required |
| Update to existing frozen spec | L3 | Controller authorization + PR review |
| Classification vocabulary addition | L3 | Controller decision record required |
| Agent authority boundary change | L3 | Controller decision + new PR + review |
| Branch protection rule change | L3 | Controller decision + GitHub admin action |

### 4.3 Delegation Rules

- Controller may delegate L3 authorization to Coordinator for a specific bounded task via explicit directive comment.
- Delegation is task-scoped: the delegate may exercise L3 authority only for the files and scope defined in the trigger JSON.
- Delegation is non-transferable: the delegate may not further delegate.
- Delegation expires after one operator cycle or the trigger timeout, whichever comes first.

---

## 5. Classification Vocabulary Rules

### 5.1 Controlled Vocabulary

The IEF program uses a controlled classification vocabulary for triggers, task types, and authorization categories. This vocabulary is **owned exclusively by the Program Controller**.

#### Current Vocabulary (as of G8-4)

**Trigger Classifications:**
- `EXECUTION_AUTHORIZATION` — Controller-authorized bounded execution
- `REVIEW_REQUEST` — Code review directive
- `VERIFICATION_REQUEST` — Verification module evaluation
- `SMOKE_TEST` — End-to-end loop validation
- `DIAGNOSTIC` — Infrastructure or system diagnosis

**Task Types:**
- `WORKER_FIX` — Code fix via worker agent
- `HEAVY_DOC_REPAIR` — Governance document creation/repair
- `REVIEW_ONLY` — Code review without modification
- `CROSS_REPO_REVIEW` — Multi-repository review
- `LOCAL_INFRA_DIAG` — Local infrastructure diagnosis
- `EVOLUTION_GUARDRAIL_SPEC` — (reserved, this spec)
- `SMOKE_TEST` — End-to-end validation

**Governance Profiles:**
- `G-Lite` — Minimal governance (auto-verification, no review)
- `G-Std` — Standard governance (review + verification)
- `G-Full` — Full governance (all gates G1–G7)

**Authorization Levels:**
- `L0` — Auto (no human approval)
- `L1` — Coordinator
- `L2` — Reviewer
- `L3` — Controller

### 5.2 Mutation Rules

| Rule | Description |
|---|---|
| **VR-1** | Only the Controller (L3) may add, modify, or deprecate vocabulary terms. |
| **VR-2** | Vocabulary changes must be announced via a directive comment on a tracked issue. |
| **VR-3** | Vocabulary changes must be reflected in this spec (Section 5.1) before they take effect. |
| **VR-4** | No agent may use a vocabulary term that is not defined in this spec. |
| **VR-5** | Deprecated terms remain in the vocabulary list with a `DEPRECATED` marker and deprecation date. |
| **VR-6** | Classification vocabulary changes are themselves L3 changes (require Controller authorization per Section 4.2). |

### 5.3 Anti-Circumvention

- Triggers using undefined classification values must be rejected by the Operator with status `BLOCKED`.
- Agents must not interpret undefined terms as aliases or synonyms of defined terms.
- The Operator must validate trigger vocabulary against this spec before execution (Validation Gate per AGENTS.md).

---

## 6. PR-Gating and Review Requirements

### 6.1 Universal PR-Gating Rule

**All changes to frozen artifacts must go through the pull-request workflow.** No exceptions.

Frozen artifacts include:
- All files under `docs/governance/`
- All files under `schemas/`
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md`
- Branch protection rules
- CI/CD configuration files

### 6.2 PR Requirements by Governance Profile

| Governance Profile | PR Required | Review Required | Verification Required | Merge Authority |
|---|---|---|---|---|
| G-Lite | Yes | No | Auto-verification | Auto-merge after verification pass |
| G-Std | Yes | Yes (1 reviewer) | Full verification | Human merge after review + verification |
| G-Full | Yes | Yes (2 reviewers) | Full verification + all gates | Human merge after all gates pass |

### 6.3 Review Scope

Every PR review must verify:

1. **File scope**: Changed files are within `allowed_files` defined by the trigger.
2. **Forbidden actions**: No forbidden actions (Section 3) were attempted or completed.
3. **Approval authority**: The change category matches the authorizing actor's authority level (Section 4).
4. **Vocabulary compliance**: No undefined classification terms introduced (Section 5).
5. **Schema compatibility**: Schema changes are non-breaking (Section 2.1 constraint).
6. **Companion spec alignment**: Changes do not contradict existing frozen specs.

### 6.4 Self-Review Prohibition

- An agent may not review its own PR.
- The Operator may not review a PR it created.
- The Coordinator may not review a PR it authored or triggered.
- Review must be performed by a distinct actor at the required authority level.

### 6.5 Verification Integration

- Every PR targeting frozen artifacts must pass through the Verification Module (defined in `VERIFICATION_HARDENING_SPEC.md`).
- Verification dimensions required depend on governance profile:
  - G-Lite: `functional` only
  - G-Std: `functional` + `governance_compliance` + `boundary`
  - G-Full: all dimensions including `stress`
- A `blocked` or `fail` verification result prevents merge regardless of review status.

---

## 7. Rollback and Recovery Model

### 7.1 Guardrail Violation Detection

A guardrail violation is detected when any of the following conditions are true:

| Violation Type | Detection Mechanism |
|---|---|
| Unauthorized file modification | Boundary dimension verification (B-EC1) |
| Forbidden action attempted | Allowed-tools whitelist denial + boundary verification |
| Self-approval attempted | Governance compliance dimension (GC-EC2) |
| Undefined vocabulary used | Operator validation gate (Section 5.3) |
| Schema breaking change | Functional dimension verification |
| Direct push to protected branch | GitHub branch protection + boundary verification |
| Force-push detected | Git history analysis in boundary dimension (B-EC3) |

### 7.2 Rollback Procedure

When a violation is detected:

1. **Immediate**: The violating PR must not be merged. If already merged, revert immediately.
2. **Notification**: Post a violation report to the target issue/PR with:
   - Violation type (from table above)
   - Agent that attempted the violation
   - Files affected
   - Commit SHA (if applicable)
   - Recommended rollback action
3. **Revert**: If the violating change was merged:
   - `git revert <merge-commit-sha>` on the target branch
   - Create a new PR for the revert (do not direct-push)
   - The revert PR must be reviewed by L3 (Controller)
4. **Ledger entry**: Record the violation in the dispatch ledger with `status=guardrail_violation`.
5. **Lockdown**: The violating agent's triggers are suspended pending Controller review.

### 7.3 Recovery Criteria

Recovery from a guardrail violation is complete when:

- The violating change is fully reverted (verified by diff comparison).
- The dispatch ledger reflects the violation and recovery.
- The Controller has reviewed the violation and authorized resumption.
- A new trigger (if needed) is issued with explicit scope confirmation.

### 7.4 Partial Rollback

If a PR contains both authorized and unauthorized changes:

- The entire PR must be reverted (not partial cherry-pick).
- A new PR with only the authorized changes must be created.
- The new PR must go through the full gating process again.

---

## 8. Agent Authority Boundaries

### 8.1 Program Controller (Human)

| Authority | Scope |
|---|---|
| Full authority over all IEF artifacts | All repos, all branches, all files |
| Exclusive owner of classification vocabulary | Section 5 |
| May delegate L3 authority for bounded tasks | Section 4.3 |
| May override any guardrail with explicit decision | Documented in directive comment |
| May not be automated or impersonated by any agent | Hard boundary |

### 8.2 Coordinator Agent

| Authority | Scope |
|---|---|
| Create trigger JSON for authorized task types | triggers/ directory |
| Select workers and configure allowed-tools | Per task type mapping |
| Delegate to PM for multi-slice orchestration | Within Controller-authorized scope |
| Update dispatch state after cycle completion | state/ directory |
| **May not** modify frozen specs without Controller authorization | Section 3.1 |
| **May not** self-approve or self-unblock | Section 3.3 |
| **May not** modify classification vocabulary | Section 5.2 |

### 8.3 PM Agent (Project Manager)

| Authority | Scope |
|---|---|
| Decompose Controller-authorized work into slices | Within authorized scope |
| Create trigger JSON for sub-slices | triggers/ directory |
| Track slice completion and dependencies | state/ directory |
| **May not** expand scope beyond Controller authorization | Hard boundary |
| **May not** authorize changes to frozen artifacts | Reserved for L3 |
| **May not** modify its own authority boundaries | Section 3.1 |

### 8.4 Operator Agent

| Authority | Scope |
|---|---|
| Execute exactly one bounded worker cycle per trigger | Per AGENTS.md operator flow |
| Validate trigger and directive before execution | Validation gates |
| Commit and push worker output to target branch | Within allowed_files only |
| Post delivery reports | Target PR/issue |
| **May not** decide project direction | Hard boundary |
| **May not** expand scope | Hard boundary |
| **May not** modify files outside allowed_files | Hard boundary |
| **May not** merge PRs or close issues | Hard boundary |
| **May not** retry without new GitHub evidence | Hard boundary |
| **May not** redefine Protocol schemas or Governance profiles | Hard boundary |

### 8.5 Worker Agents (Claude CLI, Qoder CLI, Gemini CLI)

| Authority | Scope |
|---|---|
| Read and modify files within allowed_files | As specified in trigger |
| Execute allowed-tools only | As specified in trigger whitelist |
| Commit changes with descriptive messages | Target branch only |
| **May not** modify any file outside allowed_files | Hard boundary |
| **May not** perform destructive git operations | Unless explicitly whitelisted |
| **May not** interact with external services | Unless explicitly whitelisted |
| **May not** self-replicate or spawn sub-processes | Unless explicitly whitelisted |

### 8.6 Authority Escalation Prevention

No agent may:
- Grant itself permissions it does not currently hold.
- Modify the approval matrix (Section 4) without Controller authorization.
- Create new agent roles or redefine existing roles.
- Bypass the PR-gating requirement (Section 6) for any frozen artifact.
- Delegate authority it does not hold.

---

## 9. Interaction with Companion Specifications

This spec interacts with the following IEF governance documents:

| Companion Spec | Interaction |
|---|---|
| `VERIFICATION_HARDENING_SPEC.md` | Verification Module enforces boundary and governance dimensions per Section 6.5 |
| `FAILURE_REPLAY_MODEL.md` | Rollback evidence (Section 7) must be traceable per replay model |
| `IKE_CONSUMER_STABILITY_SPEC.md` | Schema evolution (Section 2.1) must maintain consumer stability guarantees |
| `CONTROL_PLANE_FREEZE_SPEC.md` (G8-1) | This spec extends the freeze to cover evolution, not just contracts |
| `AUTHORIZED_MUTATION_MATRIX.md` (future) | When created, must be consistent with Section 4 approval matrix |

In case of conflict between this spec and a companion spec, the **more restrictive rule applies** unless the Controller explicitly resolves the conflict via directive.

---

## 10. Compliance Checklist

For any proposed change to the IEF program, verify:

- [ ] Change is within an allowed evolution path (Section 2)
- [ ] Change does not violate any forbidden path (Section 3)
- [ ] Approving actor has sufficient authority (Section 4)
- [ ] No new classification vocabulary introduced without Controller authorization (Section 5)
- [ ] Change goes through PR workflow (Section 6)
- [ ] PR review covers all required scope items (Section 6.3)
- [ ] Reviewer is not the same agent as the author (Section 6.4)
- [ ] Verification Module passes at required dimensions (Section 6.5)
- [ ] Agent authority boundaries are respected (Section 8)

---

*End of specification.*
