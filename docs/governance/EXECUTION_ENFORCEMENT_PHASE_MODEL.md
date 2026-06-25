# Execution Enforcement Phase Model — Stage D

> **Status:** Design Only — No CI Implementation  
> **Created:** 2026-06-26T08:00+08:00  
> **Authority:** Program Controller POST_MERGE_STAGE_D_NEXT_EXECUTION_GATE (P1)  
> **Baseline:** IEF-Operations `main` @ `c5ce98b`  
> **Governance Profile:** Contract-Critical  
> **Companion specs:** `EVOLUTION_GUARDRAIL_SPEC.md`, `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md`, `VERIFICATION_HARDENING_SPEC.md`, `IKE_CONSUMER_STABILITY_SPEC.md`

---

## 1. Purpose

This document defines the **phased enforcement model** for IEF specification governance. It describes how specs, contracts, schemas, and governance documents progress from informal drafts to fully locked, immutable artifacts.

The phase model provides a structured approach to **graduated enforcement**: specs are not immediately subject to the strictest controls. Instead, they move through a defined progression where each phase introduces additional validation, review, and enforcement requirements.

This is a **governance design document only**. It does not implement CI pipelines, Spectral rules, runtime enforcement, or automated blocking. Those are deferred to a future implementation phase after the Classification Registry Spec is stable (per `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md` Section: Enforcement Deferral).

---

## 2. Scope

### 2.1 What This Model Governs

The phase model applies to all **IEF governance and specification artifacts**:

| Artifact Category | Examples |
|---|---|
| JSON Schemas | `schemas/*.json` (task, run, workflow, ledger_entry, verification schemas) |
| OpenAPI Contracts | `docs/**/*.yaml` (VERIFICATION_SPEC, IEF_TO_IKE_DATA_CONTRACT, etc.) |
| Governance Specs | `docs/governance/*.md` (Evolution Guardrail, Verification Hardening, etc.) |
| Design Documents | `docs/*.md` (Core Schema Design, Task Lifecycle, Run Ledger, etc.) |
| Cross-repo Contracts | `IEF-Runners/contracts/*.yaml`, `IEF-Adapters/contracts/*.yaml`, `IEF-Knowledge/contracts/*.yaml` |

### 2.2 What This Model Does NOT Govern

- Runtime code (agent implementations, worker scripts, orchestration logic)
- Operational artifacts (delivery reports, trigger JSONs, dispatch ledger)
- Test fixtures (unless they encode contract behavior)
- README files and non-governance documentation
- Branch protection rules (governed by GitHub admin + Controller authority per `EVOLUTION_GUARDRAIL_SPEC.md` Section 4)

### 2.3 Relationship to Existing Specs

| Spec | Relationship |
|---|---|
| `EVOLUTION_GUARDRAIL_SPEC.md` | This model defines *how* specs reach the frozen state that the Guardrail protects. The Guardrail's PR-gating rules apply to Phase 2+ artifacts. |
| `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md` | Spectral linting is the *mechanism* for Phase 1–3 validation. This model defines *when* lint rules apply. |
| `VERIFICATION_HARDENING_SPEC.md` | Verification Module enforces boundary/governance dimensions. This model defines which phases require verification. |
| `IKE_CONSUMER_STABILITY_SPEC.md` | Consumer stability guarantees apply to Phase 3+ artifacts (externally visible contracts). |
| `FAILURE_REPLAY_MODEL.md` | Replay determinism applies to Phase 2+ verification-involved artifacts. |

---

## 3. Phase Definitions

### Phase 0 — Draft

**Characterization:** Informal, unstructured, no enforcement.

| Attribute | Value |
|---|---|
| **Enforcement level** | None |
| **Validation** | None (no automated checks) |
| **Review requirement** | None |
| **Merge authority** | Any contributor |
| **Modification rules** | Unrestricted (any agent or human may edit) |
| **Schema conformance** | Not required |
| **Spectral linting** | Not applied |
| **Verification Module** | Not invoked |
| **Branch policy** | Feature/draft branches only; no merge to `main` |

**Entry criteria:**
- New document or spec is proposed
- No prior review or validation has occurred
- Author declares intent to develop the artifact

**Exit criteria (to Phase 1):**
- Document reaches structural completeness (all sections present, no TODO/FIXME markers)
- Author declares the artifact ready for validation
- Coordinator or Reviewer acknowledges readiness

**Examples:**
- Initial draft of a governance spec in a feature branch
- Proposal document for a new contract
- Experimental schema in a personal fork

**Rollback:** N/A — Phase 0 artifacts have no enforcement state to roll back from.

---

### Phase 1 — Active (Validation Only / Report-Only)

**Characterization:** Structural validation active, but no blocking enforcement.

| Attribute | Value |
|---|---|
| **Enforcement level** | Report-only (warnings, no blocks) |
| **Validation** | Structural lint (JSON Schema validity, OAS 3.1 conformance, markdown structure) |
| **Review requirement** | Informal (advisory review recommended, not gated) |
| **Merge authority** | Coordinator + 1 reviewer (non-blocking) |
| **Modification rules** | Unrestricted modification; changes logged but not blocked |
| **Schema conformance** | Required (must validate against meta-schema) |
| **Spectral linting** | Active in report-only mode (all rules, no blocking) |
| **Verification Module** | Optional (may be invoked for early feedback) |
| **Branch policy** | Feature branch; PR required for merge to `main` |

**Entry criteria (from Phase 0):**
- Exit criteria from Phase 0 met
- Document passes structural validation (JSON Schema valid, OAS parseable)
- No unresolved structural issues (missing required sections, invalid references)

**Exit criteria (to Phase 2):**
- All Spectral lint rules pass (or documented exceptions filed)
- Verification Module invoked at minimum dimensions: `functional` + `boundary`
- At least one formal review completed (not necessarily approved)
- Author or Coordinator declares readiness for guarded enforcement
- Controller or delegate acknowledges Phase 2 readiness

**Examples:**
- `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md` (current state: scoping plan, lint rules defined but not enforced)
- New contract YAML that passes OAS 3.1 validation but hasn't been formally reviewed
- Schema additions that validate against meta-schema but lack full verification

**Rollback (to Phase 0):**
- Structural validation fails repeatedly with no remediation path
- Author withdraws the artifact
- Coordinator determines the artifact is not viable for governance use

---

### Phase 2 — Guarded (Soft Enforcement / Warnings)

**Characterization:** Validation produces warnings on PRs, but merges are not blocked. Review is mandatory.

| Attribute | Value |
|---|---|
| **Enforcement level** | Soft enforcement (warnings on PRs, review required, merge not blocked by lint alone) |
| **Validation** | Full Spectral lint + Verification Module at `functional` + `boundary` + `governance_compliance` |
| **Review requirement** | Mandatory (1 reviewer, may be Coordinator or human) |
| **Merge authority** | Human merge after review; lint warnings visible but non-blocking |
| **Modification rules** | Modifications allowed; breaking changes flagged as warnings |
| **Schema conformance** | Required + backward compatibility checks |
| **Spectral linting** | Active in warning mode (all rules; violations produce PR comments) |
| **Verification Module** | Required: `functional` + `boundary` + `governance_compliance` |
| **Branch policy** | PR required; review required; lint warnings visible |

**Entry criteria (from Phase 1):**
- Exit criteria from Phase 1 met
- All Spectral lint rules pass cleanly (no outstanding violations)
- Verification Module passes at `functional` + `boundary` dimensions
- At least one formal review completed (approved or with actionable feedback addressed)
- Controller or delegate explicitly authorizes Phase 2 transition

**Exit criteria (to Phase 3):**
- Spectral lint rules pass consistently across ≥3 consecutive PRs
- Verification Module passes at all required dimensions across ≥2 evaluation cycles
- No unresolved review comments or requested changes
- Breaking change analysis completed (per `IKE_CONSUMER_STABILITY_SPEC.md` if applicable)
- Controller explicitly authorizes Phase 3 transition

**Examples:**
- `VERIFICATION_HARDENING_SPEC.md` (frozen spec, under active review, verification required)
- `EVOLUTION_GUARDRAIL_SPEC.md` (frozen spec, review-gated, verification at multiple dimensions)
- Schemas that have passed initial review and are being validated against real workloads

**Rollback (to Phase 1):**
- Verification Module fails at required dimensions with no remediation within one review cycle
- Lint violations accumulate without resolution
- Reviewer or Controller determines the artifact is not ready for hard enforcement
- Breaking changes detected that violate consumer stability guarantees

---

### Phase 3 — Enforced (Blocking CI Rules)

**Characterization:** Validation failures block merges. Full verification required. No silent modification allowed.

| Attribute | Value |
|---|---|
| **Enforcement level** | Hard enforcement (lint failures block merge, verification failures block merge) |
| **Validation** | Full Spectral lint (blocking) + Verification Module at all required dimensions per governance profile |
| **Review requirement** | Mandatory per governance profile (G-Lite: 1, G-Std: 1, G-Full: 2) |
| **Merge authority** | Human merge after review + verification pass + lint clean |
| **Modification rules** | Modifications allowed only via PR; all changes trigger full validation pipeline |
| **Schema conformance** | Required + backward compatibility enforced (breaking changes blocked) |
| **Spectral linting** | Active in blocking mode (lint failures prevent merge) |
| **Verification Module** | Required per governance profile (see `EVOLUTION_GUARDRAIL_SPEC.md` Section 6.2) |
| **Branch policy** | PR required; review required; lint must pass; verification must pass |

**Entry criteria (from Phase 2):**
- Exit criteria from Phase 2 met
- Spectral lint rules have been stable (no rule changes) for ≥1 evaluation cycle
- Verification Module passes consistently at all required dimensions
- No unresolved breaking changes
- Controller explicitly authorizes Phase 3 transition (P0 decision for Contract-Critical artifacts)

**Exit criteria (to Phase 4):**
- Artifact has been in Phase 3 for ≥1 production release cycle (or equivalent stability period)
- No verification failures or lint violations in the stability period
- No unauthorized modification attempts detected
- Controller explicitly authorizes Phase 4 lock

**Examples:**
- `schemas/task.schema.json` (if fully validated, reviewed, and locked)
- `schemas/run.schema.json` (if fully validated, reviewed, and locked)
- Core contracts that are externally visible and consumer-facing

**Rollback (to Phase 2):**
- Verification Module fails at required dimensions
- Lint violations detected that indicate spec drift
- Breaking change introduced that was not caught during Phase 2
- Controller determines the artifact needs further refinement before full lock
- Rollback triggers immediate re-evaluation of all dependent artifacts

---

### Phase 4 — Locked (No Silent Modification Allowed)

**Characterization:** Immutable. Any modification requires Controller authorization + new PR + full verification + explicit unlock rationale.

| Attribute | Value |
|---|---|
| **Enforcement level** | Maximum (all Phase 3 rules + branch protection + unlock procedure) |
| **Validation** | Full Spectral lint (blocking) + full Verification Module + diff analysis |
| **Review requirement** | Controller (L3) review mandatory for any change |
| **Merge authority** | Controller only (after unlock procedure) |
| **Modification rules** | No modification without explicit unlock procedure (Section 5.4) |
| **Schema conformance** | Required + full backward compatibility + consumer stability guarantees |
| **Spectral linting** | Active in blocking mode + locked-artifact detection rules |
| **Verification Module** | Full verification at all dimensions + replay determinism check |
| **Branch policy** | Branch protection enabled; direct push forbidden; force-push forbidden |

**Entry criteria (from Phase 3):**
- Exit criteria from Phase 3 met
- Artifact declared stable by Controller
- Branch protection rules applied (GitHub admin action)
- Locked-artifact Spectral rules activated

**Modification procedure (unlock):**
1. Controller issues explicit directive comment authorizing the specific modification.
2. Branch protection is temporarily relaxed by GitHub admin (Controller or delegate).
3. A new PR is created with the modification.
4. Full verification pipeline runs (all dimensions + replay determinism).
5. Controller reviews and approves the PR.
6. PR is merged.
7. Branch protection is re-applied.
8. Unlock event is recorded in the dispatch ledger with reference to the Controller directive.

**Examples:**
- JSON Schema draft 2020-12 meta-schema (external standard, immutable by definition)
- Protocol v0.1.0 object definitions (if locked by Protocol repo)
- Core Operations schemas after production stabilization

**Rollback (to Phase 3):**
- Unlock procedure completed (artifact returns to Phase 3 with modified content)
- Controller determines the lock was premature
- Rollback from Phase 4 to Phase 3 requires the same unlock procedure as a modification

---

## 4. Phase Transition Matrix

### 4.1 Forward Transitions (Promotion)

| From | To | Authority Required | Evidence Required | Notification |
|---|---|---|---|---|
| Phase 0 | Phase 1 | Coordinator (L1) | Structural validation pass, author readiness declaration | Post transition notice to target issue |
| Phase 1 | Phase 2 | Controller or delegate (L3/L1-delegated) | Lint clean, verification pass (functional + boundary), 1 review | Post transition notice + verification report |
| Phase 2 | Phase 3 | Controller (L3) | Consistent lint/verification across ≥2 cycles, no unresolved reviews, breaking change analysis | Controller directive comment + transition report |
| Phase 3 | Phase 4 | Controller (L3) | Stability period completed, no violations, no unauthorized modification attempts | Controller directive comment + branch protection application |

### 4.2 Backward Transitions (Demotion / Rollback)

| From | To | Authority Required | Trigger | Recovery |
|---|---|---|---|---|
| Phase 1 | Phase 0 | Coordinator (L1) | Structural validation failure, author withdrawal | Address issues, re-enter Phase 1 |
| Phase 2 | Phase 1 | Coordinator or Reviewer (L1/L2) | Verification failure, lint violations, review rejection | Address failures, re-accumulate Phase 2 exit criteria |
| Phase 3 | Phase 2 | Controller (L3) | Verification failure, spec drift, breaking change | Root cause analysis, fix, re-accumulate Phase 3 exit criteria |
| Phase 4 | Phase 3 | Controller (L3) via unlock procedure | Authorized modification needed | Complete unlock procedure, modify, re-lock |

### 4.3 Skip Transitions

**No skip transitions are allowed.** An artifact must pass through each phase sequentially. Rationale:

- Phase 0 → Phase 2 would skip structural validation (Phase 1), allowing unvalidated specs into guarded enforcement.
- Phase 1 → Phase 3 would skip the review accumulation period (Phase 2), allowing unreviewed specs into hard enforcement.
- Phase 2 → Phase 4 would skip the stability period (Phase 3), allowing untested specs into immutable lock.

**Exception:** The Controller may authorize a skip transition with explicit rationale documented in a directive comment. This is expected to be rare and limited to:
- External standards adopted wholesale (e.g., JSON Schema meta-schema)
- Artifacts that have already passed equivalent validation in a different program context

---

## 5. Transition Evidence Requirements

### 5.1 Phase 0 → Phase 1 Evidence

| Evidence Item | Format | Validator |
|---|---|---|
| Structural completeness checklist | Markdown checklist in PR description | Coordinator review |
| JSON Schema validation result | `jsonschema` CLI output or equivalent | Automated |
| OAS 3.1 parse result | `swagger-cli validate` output or equivalent | Automated |
| Author readiness declaration | Comment on target issue/PR | Author (human or agent) |
| No TODO/FIXME markers | `grep -r "TODO\|FIXME"` output | Automated |

### 5.2 Phase 1 → Phase 2 Evidence

| Evidence Item | Format | Validator |
|---|---|---|
| Spectral lint results (all rules) | Spectral CLI output with rule-by-rule status | Automated (CI) |
| Verification Module result (functional + boundary) | `VerificationResult` JSON (per `VERIFICATION_HARDENING_SPEC.md`) | Verification Module |
| Formal review record | GitHub PR review (approved or changes-requested with resolution) | Reviewer |
| Phase 2 readiness declaration | Comment on target issue/PR | Author or Coordinator |
| Controller acknowledgment | Directive comment or PR approval | Controller or delegate |

### 5.3 Phase 2 → Phase 3 Evidence

| Evidence Item | Format | Validator |
|---|---|---|
| Spectral lint results across ≥3 consecutive PRs | Aggregated Spectral output | Automated (CI) |
| Verification Module results across ≥2 cycles | Aggregated `VerificationResult` records | Verification Module |
| Review resolution record | All review comments resolved (GitHub PR thread status) | Reviewer |
| Breaking change analysis | Impact assessment document (per `IKE_CONSUMER_STABILITY_SPEC.md`) | Reviewer + Coordinator |
| Consumer stability verification | Downstream consumer test results (if applicable) | Automated or manual |
| Controller authorization | Directive comment (P0 for Contract-Critical) | Controller (L3) |

### 5.4 Phase 3 → Phase 4 Evidence

| Evidence Item | Format | Validator |
|---|---|---|
| Stability period log | Duration record (≥1 production cycle) with no violations | Coordinator |
| Verification Module clean record | All verification results `pass` during stability period | Verification Module |
| Lint clean record | All Spectral runs clean during stability period | Automated (CI) |
| No unauthorized modification attempts | Git history analysis + boundary verification | Verification Module |
| Branch protection configuration | GitHub branch protection settings screenshot/record | GitHub admin |
| Controller lock authorization | Directive comment (P0) | Controller (L3) |

### 5.5 Unlock Procedure Evidence (Phase 4 modification)

| Evidence Item | Format | Validator |
|---|---|---|
| Controller unlock directive | Directive comment specifying exact modification scope | Controller (L3) |
| Branch protection relaxation record | GitHub admin action log | GitHub admin |
| Full verification pipeline result | `VerificationResult` at all dimensions + replay determinism | Verification Module |
| Controller PR review | GitHub PR review (approved) | Controller (L3) |
| Branch protection re-application record | GitHub admin action log | GitHub admin |
| Ledger entry | Dispatch ledger record of unlock event | Coordinator |

---

## 6. Current Phase Assignments

As of 2026-06-26, the following phase assignments are in effect:

### 6.1 IEF-Operations Artifacts

| Artifact | Current Phase | Rationale |
|---|---|---|
| `schemas/task.schema.json` | Phase 1 | Validates against JSON Schema 2020-12; reviewed in G8-1; not yet in blocking CI |
| `schemas/run.schema.json` | Phase 1 | Same as task.schema.json |
| `schemas/workflow.schema.json` | Phase 1 | Same as task.schema.json |
| `schemas/ledger_entry.schema.json` | Phase 1 | Same as task.schema.json |
| `schemas/verification_request.schema.json` | Phase 1 | Validates; reviewed; Spectral lint planned but not active |
| `schemas/verification_result.schema.json` | Phase 1 | Same as verification_request |
| `schemas/verification_evidence.schema.json` | Phase 1 | Same as verification_request |
| `schemas/IKE_READ_MODEL_VERSION_1.json` | Phase 1 | Consumer-facing; validated; not yet in blocking CI |
| `schemas/RESULT_SCHEMA_V2.json` | Phase 1 | Hardened; validated; not yet in blocking CI |
| `docs/VERIFICATION_SPEC_V0.yaml` | Phase 1 | OAS 3.1 valid; planning-only; Spectral lint scoped but not active |
| `docs/governance/IEF_TO_IKE_DATA_CONTRACT_OAS31.yaml` | Phase 2 | OAS 3.1 valid; reviewed; consumer stability spec applies |
| `docs/governance/EVOLUTION_GUARDRAIL_SPEC.md` | Phase 2 | Frozen spec; reviewed; verification required for changes |
| `docs/governance/VERIFICATION_HARDENING_SPEC.md` | Phase 2 | Frozen spec; reviewed; verification at multiple dimensions |
| `docs/governance/FAILURE_REPLAY_MODEL.md` | Phase 2 | Frozen spec; reviewed; replay determinism required |
| `docs/governance/IKE_CONSUMER_STABILITY_SPEC.md` | Phase 2 | Frozen spec; reviewed; consumer stability gates defined |
| `docs/governance/SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md` | Phase 1 | Scoping plan; lint rules defined but not activated |
| `docs/CORE_SCHEMA_DESIGN.md` | Phase 1 | Design document; reviewed; not enforcement-targeted |
| `docs/TASK_LIFECYCLE.md` | Phase 1 | Design document; reviewed; not enforcement-targeted |
| `docs/RUN_LEDGER.md` | Phase 1 | Design document; reviewed; not enforcement-targeted |

### 6.2 Cross-Repo Artifacts

| Artifact | Repo | Current Phase | Rationale |
|---|---|---|---|
| `contracts/RUNNER_INTERFACE_V0.yaml` | IEF-Runners | Phase 1 | OAS 3.1 valid; newly created; awaiting review |
| `contracts/ADAPTER_CONTRACT_V0.yaml` | IEF-Adapters | Phase 1 | OAS 3.1 valid; newly created; awaiting review |
| `contracts/CONTEXT_PACK_V0.yaml` | IEF-Knowledge | Phase 1 | OAS 3.1 valid; newly created; awaiting review |
| `contracts/RUN_SUMMARY_V0.yaml` | IEF-Knowledge | Phase 1 | OAS 3.1 valid; newly created; awaiting review |
| `contracts/KNOWLEDGE_BASE_INTEGRATION_V0.yaml` | IEF-Knowledge | Phase 1 | OAS 3.1 valid; newly created; awaiting review |

### 6.3 Phase Assignment Authority

- **Initial phase assignment** (Phase 0 or Phase 1): Coordinator (L1) may assign based on structural validation.
- **Phase promotion** (Phase 1+): Follows the transition matrix (Section 4).
- **Phase demotion**: Follows the transition matrix (Section 4).
- **Phase assignment disputes**: Controller (L3) has final authority.

---

## 7. Spectral Lint Rule Activation by Phase

This section maps Spectral lint rule categories (from `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md`) to enforcement phases.

### 7.1 JSON Schema Rules

| Rule Category | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| Meta-schema conformance | Off | Report | Warn | Block | Block |
| Required field presence | Off | Report | Warn | Block | Block |
| Type consistency | Off | Report | Warn | Block | Block |
| Enum completeness | Off | Report | Warn | Block | Block |
| Reference integrity (`$ref`) | Off | Report | Warn | Block | Block |
| Draft 2020-12 features | Off | Report | Warn | Block | Block |

### 7.2 OpenAPI Rules

| Rule Category | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| OAS 3.1 structural validity | Off | Report | Warn | Block | Block |
| Operation ID uniqueness | Off | Report | Warn | Block | Block |
| Schema component reuse | Off | Off | Warn | Warn | Block |
| Response completeness | Off | Report | Warn | Block | Block |
| Security scheme presence | Off | Off | Warn | Block | Block |
| x-ief-* extension validity | Off | Report | Warn | Block | Block |

### 7.3 Cross-Artifact Rules

| Rule Category | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| Evidence reference integrity | Off | Off | Warn | Block | Block |
| Governance profile consistency | Off | Off | Warn | Block | Block |
| Classification vocabulary compliance | Off | Report | Warn | Block | Block |
| Consumer stability (breaking changes) | Off | Off | Off | Block | Block |
| Replay determinism | Off | Off | Warn | Block | Block |

### 7.4 Rule Implementation Deferral

Per `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md`, Spectral rule implementation is deferred until after the Classification Registry Spec is stable. This phase model defines the *target state* for rule activation, not the current state.

Current state: All Spectral rules are in **Phase 1 report-only** mode (planned but not implemented).

---

## 8. Verification Module Integration

### 8.1 Verification Dimensions by Phase

| Dimension | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| `functional` | Optional | Optional | Required | Required | Required |
| `boundary` | Optional | Optional | Required | Required | Required |
| `governance_compliance` | Off | Off | Required | Required | Required |
| `stress` | Off | Off | Off | G-Full only | G-Full only |
| Replay determinism | Off | Off | Optional | Required | Required |

### 8.2 Verification Results and Phase Transitions

| Verification Result | Effect on Phase |
|---|---|
| `pass` at all required dimensions | Supports phase promotion (if other criteria met) |
| `pass` with `evidence_minimal` flag | Supports continued Phase 2; insufficient for Phase 3 promotion |
| `blocked` (missing evidence) | Blocks phase promotion; may trigger Phase demotion if unresolved |
| `fail` at any required dimension | Blocks phase promotion; triggers Phase demotion if currently in Phase 3 |
| `skipped` (dimension not applicable) | Neutral; does not support or block promotion |

### 8.3 Verification Frequency

| Phase | Minimum Verification Frequency |
|---|---|
| Phase 1 | On-demand (author or Coordinator may invoke) |
| Phase 2 | Every PR that modifies the artifact |
| Phase 3 | Every PR + periodic re-verification (≥1 per production cycle) |
| Phase 4 | Every unlock procedure + periodic integrity check (≥1 per production cycle) |

---

## 9. Governance Profile Interaction

The phase model interacts with governance profiles (`G-Lite`, `G-Std`, `G-Full`) defined in `EVOLUTION_GUARDRAIL_SPEC.md` Section 5.1.

### 9.1 Minimum Phase by Governance Profile

| Governance Profile | Minimum Phase for Frozen Artifacts | Review Requirement | Verification Requirement |
|---|---|---|---|
| G-Lite | Phase 2 | 1 reviewer | `functional` + `boundary` |
| G-Std | Phase 2 | 1 reviewer | `functional` + `boundary` + `governance_compliance` |
| G-Full | Phase 3 | 2 reviewers | All dimensions + replay determinism |
| Contract-Critical | Phase 3 | Controller review | All dimensions + replay determinism |

### 9.2 Profile-Phase Alignment

- An artifact governed at `G-Full` **must** reach at least Phase 3 (enforced).
- An artifact governed at `G-Lite` **may** remain at Phase 2 (guarded) indefinitely.
- Phase 4 (locked) is available for any governance profile but requires Controller authorization regardless of profile.

---

## 10. Rollback and Recovery Procedures

### 10.1 Phase Demotion Triggers

| Trigger | From Phase | To Phase | Authority |
|---|---|---|---|
| Structural validation failure | Phase 1 | Phase 0 | Coordinator |
| Lint violations unresolved for ≥2 cycles | Phase 2 | Phase 1 | Coordinator or Reviewer |
| Verification Module `fail` at required dimension | Phase 2 or 3 | Previous phase | Controller (Phase 3) or Coordinator (Phase 2) |
| Spec drift detected (unauthorized modification) | Phase 3 | Phase 2 | Controller |
| Breaking change introduced without analysis | Phase 3 | Phase 2 | Controller |
| Guardrail violation (per `EVOLUTION_GUARDRAIL_SPEC.md` Section 7) | Any | Phase 0 or 1 | Controller |

### 10.2 Demotion Procedure

1. **Detection**: Violation or failure detected by verification, lint, or review.
2. **Notification**: Post demotion notice to target issue/PR with:
   - Current phase and target phase
   - Trigger reason
   - Evidence (verification result, lint output, review comment)
   - Required remediation steps
3. **Enforcement**: Adjust CI/lint configuration to reflect new phase (if applicable).
4. **Ledger entry**: Record demotion in dispatch ledger.
5. **Remediation**: Author addresses issues.
6. **Re-promotion**: Artifact must re-accumulate all exit criteria for the demoted-from phase.

### 10.3 Emergency Rollback

For critical failures (e.g., guardrail violation, unauthorized modification):

1. Controller issues emergency rollback directive.
2. Artifact immediately demoted to Phase 0 or Phase 1 (Controller's discretion).
3. All dependent artifacts re-evaluated for impact.
4. Branch protection rules adjusted if necessary.
5. Full root cause analysis required before re-promotion.

---

## 11. Anti-Circumvention Rules

### 11.1 Phase Bypass Prevention

- No agent may skip phases without Controller authorization (Section 4.3 exception process).
- Phase assignments are recorded in this document and the dispatch ledger; discrepancies constitute guardrail violations.
- Agents must validate the current phase of an artifact before modifying it (if the artifact is Phase 3+, the modification must follow the full PR + review + verification pipeline).

### 11.2 Self-Promotion Prevention

- No agent may promote its own artifact to a higher phase.
- Phase promotion requires independent validation (Coordinator for Phase 0→1, Controller for Phase 2+).
- An agent that authors an artifact may declare readiness for phase transition but may not authorize it.

### 11.3 Phase Downgrade Resistance

- Once an artifact reaches Phase 3, demotion to Phase 2 or below requires Controller authorization.
- Agents may not unilaterally relax enforcement on Phase 3+ artifacts.
- CI configuration changes that reduce enforcement level are themselves Phase 3 changes (require Controller authorization).

---

## 12. Interaction with Companion Specifications

### 12.1 Evolution Guardrail Spec

This model defines the *progression* to the frozen state that the Evolution Guardrail protects. Key interactions:

- **Section 2 (Allowed Paths)**: Phase 0–1 artifacts follow the "Documentation and Operational Artifacts" path. Phase 2+ artifacts follow the "New Contract and Governance Files" path (Controller authorization required).
- **Section 3 (Forbidden Paths)**: All phases respect forbidden paths. Phase 3+ artifacts additionally enforce forbidden paths via CI blocking.
- **Section 6 (PR-Gating)**: Phase 1+ artifacts require PRs. Phase 2+ artifacts require PR + review. Phase 3+ artifacts require PR + review + verification.
- **Section 7 (Rollback)**: Phase demotion follows the rollback model in Section 10 of this document, which extends the Guardrail's rollback procedure.

### 12.2 Spectral Lint Plan

This model defines *when* Spectral rules activate. The Lint Plan defines *what* rules exist. Key interactions:

- **Enforcement Deferral**: Both specs defer CI implementation. This model defines the target activation phases.
- **Rule Categories**: Section 7 of this document maps rule categories to phases.
- **Lintable Spec Inventory**: Phase assignments (Section 6) reference the inventory from the Lint Plan.

### 12.3 Verification Hardening Spec

This model defines *when* verification is required. The Hardening Spec defines *how* verification works. Key interactions:

- **Edge Case Coverage**: Verification at Phase 2+ must satisfy all coverage buckets (CB-1 through CB-8).
- **Deterministic Replay**: Required for Phase 3+ artifacts.
- **Failure Classification**: Verification failures at Phase 3 trigger Phase demotion per Section 10.

### 12.4 IKE Consumer Stability Spec

This model defines *when* consumer stability guarantees apply. Key interactions:

- **Phase 3+**: Consumer stability guarantees are enforced (breaking changes blocked).
- **Phase 2**: Consumer stability analysis required for promotion to Phase 3.
- **Phase 0–1**: Consumer stability not enforced (artifact not yet consumer-facing).

### 12.5 Failure Replay Model

This model defines *when* replay determinism is required. Key interactions:

- **Phase 2**: Replay determinism optional (recommended for verification-involved artifacts).
- **Phase 3**: Replay determinism required (verification must be reproducible).
- **Phase 4**: Replay determinism required + integrity checks on unlock.

---

## 13. Compliance Checklist

For any artifact subject to the phase model, verify:

- [ ] Current phase is documented in Section 6 (or companion registry)
- [ ] Phase-appropriate validation is active (Section 7 for Spectral, Section 8 for verification)
- [ ] Phase-appropriate review requirements are met (Section 3 phase definitions)
- [ ] Phase transitions followed the evidence requirements (Section 5)
- [ ] No phase skips occurred without Controller authorization (Section 4.3)
- [ ] Anti-circumvention rules are respected (Section 11)
- [ ] Demotion triggers are monitored (Section 10)
- [ ] Companion spec interactions are satisfied (Section 12)

---

## 14. Future Work

The following items are deferred to future phases:

1. **CI Implementation**: Spectral lint pipeline integration (blocked by Classification Registry Spec stability).
2. **Automated Phase Tracking**: Machine-readable phase registry (currently maintained in this document).
3. **Phase Transition Automation**: Automated promotion/demotion based on CI results (requires CI implementation first).
4. **Cross-Repo Phase Synchronization**: Ensuring phase consistency across IEF-Operations, IEF-Runners, IEF-Adapters, IEF-Knowledge.
5. **Phase Metrics Dashboard**: Tracking time-in-phase, transition frequency, violation rates.

---

*End of specification.*
