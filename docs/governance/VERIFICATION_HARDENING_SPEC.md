# Verification Runtime Hardening Specification — Stage G (G8-2)

> **Status:** Frozen Specification  
> **Created:** 2026-06-23T12:18+08:00  
> **Authority:** Program Controller STAGE_G_G7_FINAL_REVIEW_RESULT (G8-2 AUTHORIZED)  
> **Baseline:** IEF-Operations `main` @ `31bc466`  
> **Prior slices:** G8-1 Control Plane Freeze (`bc4b93f`)  
> **Governance Profile:** Contract-Critical  
> **Schema Reference:** JSON Schema Draft 2020-12  

---

## 1. Purpose

This specification hardens the IEF Verification Module against edge-case gaps, non-deterministic replay, incomplete failure classification, and verifier scope drift. It extends the G7-A minimal implementation (comment `6287fcb`) and the G6-A schema fix (comment `4753183384`) with three hardening layers:

1. **Edge Case Coverage Rules** — exhaustive input-domain coverage for verification requests
2. **Deterministic Replay Guarantees** — identical input produces identical output across time, environment, and evaluator
3. **Failure Classification Completeness** — every failure mode maps to exactly one classification category with defined severity and retry semantics

This document does **not** introduce runtime verifier implementation, background execution services, autonomous evaluation triggers, CI integration, or production enforcement hooks. It is a specification-level hardening contract.

---

## 2. Edge Case Coverage Rules

### 2.1 Input Domain Coverage

Every `VerificationRequest` must be classified into exactly one coverage bucket before evaluation. No request may fall outside the defined domain.

| Coverage Bucket | Input Condition | Required Verifier Behavior |
|---|---|---|
| **CB-1: Standard** | All required fields present, governance profile matches evidence level, `requested_dimensions` non-empty | Proceed with full verification |
| **CB-2: Minimal Evidence** | Required fields present but evidence at minimum for governance profile (e.g., G-Lite with only `artifact_refs`) | Proceed but flag `evidence_minimal` in metadata |
| **CB-3: Evidence Gap** | Required fields present but governance-conditional requirements not met (e.g., G-Std without `review_result`) | `overall_result: blocked`, `blocked_reason` references missing evidence |
| **CB-4: Empty Dimensions** | `requested_dimensions` is empty array | `overall_result: blocked`, `blocked_reason: "No dimensions requested"` |
| **CB-5: All Skipped** | All `requested_dimensions` result in `skipped` | `overall_result: blocked`, `blocked_reason: "All dimensions skipped"` |
| **CB-6: Duplicate ID** | `verification_id` matches a previously processed request | Reject with `schema_validation_failed`; do not re-evaluate |
| **CB-7: Schema Invalid** | Any required field missing or type-mismatched | Reject with `schema_validation_failed` before evaluation |
| **CB-8: Governance Mismatch** | `governance_profile` value not in `{G-Lite, G-Std, G-Full}` | Reject with `schema_validation_failed` |
| **CB-9: Contradictory Evidence** | `review_result.decision = "rejected"` but `ledger_entries` contain `review_accepted` | Flag in findings; dimension result = `fail` for `governance_compliance` |
| **CB-10: Stale Timestamp** | `verification_timestamp` predates `review_result.review_timestamp` | Flag in findings; dimension result = `conditional` for `functional` |

### 2.2 Dimension-Level Edge Cases

Each dimension has specific edge cases that must be handled:

#### 2.2.1 Functional Dimension

| Edge Case | Condition | Result | Severity |
|---|---|---|---|
| F-EC1 | `artifact_refs` is empty | `fail` | `error` |
| F-EC2 | `artifact_refs` contains URIs that don't resolve | `conditional` | `warning` |
| F-EC3 | All `artifact_refs` resolve but content is empty | `fail` | `error` |
| F-EC4 | `artifact_refs` contains duplicate URIs | `conditional` | `warning` |

#### 2.2.2 Governance Compliance Dimension

| Edge Case | Condition | Result | Severity |
|---|---|---|---|
| GC-EC1 | `review_result` is null for G-Std/G-Full | `fail` | `critical` |
| GC-EC2 | `review_result.reviewer` matches runner identity (self-acceptance) | `fail` | `critical` |
| GC-EC3 | `ledger_entries` contains out-of-order sequence numbers | `fail` | `error` |
| GC-EC4 | `ledger_entries` contains duplicate `entry_id` values | `fail` | `error` |
| GC-EC5 | Required gate events missing for G-Full (G1–G7) | `fail` | `error` |
| GC-EC6 | `review_result.decision = "rework"` but no subsequent `task_resumed` event | `conditional` | `warning` |

#### 2.2.3 Boundary Dimension

| Edge Case | Condition | Result | Severity |
|---|---|---|---|
| B-EC1 | Commit diff shows files not in `allowed_files` | `fail` | `critical` |
| B-EC2 | `forbidden_actions` list is empty (no constraints defined) | `conditional` | `warning` |
| B-EC3 | Git history shows `merge` or `rebase` operations | `fail` | `critical` |
| B-EC4 | Commit targets a branch other than the authorized branch | `fail` | `critical` |
| B-EC5 | `allowed_files` contains glob patterns that can't be resolved | `conditional` | `warning` |

#### 2.2.4 Stress Dimension

| Edge Case | Condition | Result | Severity |
|---|---|---|---|
| S-EC1 | No stress evidence provided (no controlled stress run) | `skipped` | `info` |
| S-EC2 | Stress evidence shows timeout but runner reported `completed` | `fail` | `error` |
| S-EC3 | Stress evidence shows scope creep attempt (file modification outside scope under pressure) | `fail` | `critical` |
| S-EC4 | Stress evidence shows token budget exceeded | `conditional` | `warning` |
| S-EC5 | Stress dimension not requested but evidence exists | `skipped` | `info` |

### 2.3 Aggregation Edge Cases

| Edge Case | Condition | `overall_result` | `overall_severity` |
|---|---|---|---|
| A-EC1 | Mixed `pass` + `skipped` with no `fail` or `conditional` | `pass` | `info` |
| A-EC2 | Mixed `pass` + `conditional` + `skipped` | `conditional` | `warning` |
| A-EC3 | All dimensions `skipped` | `blocked` | `warning` |
| A-EC4 | One `fail` at `error` + one `fail` at `critical` | `fail` | `critical` |
| A-EC5 | One `conditional` + one `fail` | `fail` | per fail severity |
| A-EC6 | `blocked` at dimension level (evidence gap) + `pass` on all others | `blocked` | `warning` |

---

## 3. Deterministic Replay Guarantees

### 3.1 Core Invariant

**Identical `VerificationRequest` input MUST produce identical `VerificationResult` output regardless of:**

- Time of evaluation
- Environment (machine, OS, network)
- Evaluator identity
- Prior evaluation history (idempotent)

### 3.2 Deterministic Inputs

The following fields constitute the deterministic input fingerprint:

```
deterministic_input_fingerprint = SHA-256(
    verification_id ||
    task_id ||
    run_id ||
    governance_profile ||
    SORT(artifact_refs) ||
    SORT(context_refs) ||
    SORT(allowed_files) ||
    SORT(forbidden_actions) ||
    review_result.decision ||
    review_result.reviewer ||
    review_result.review_timestamp ||
    SORT(ledger_entries[].entry_id) ||
    SORT(requested_dimensions) ||
    retry_count
)
```

### 3.3 Deterministic Outputs

Given the same input fingerprint, the following output fields MUST be identical:

| Field | Deterministic? | Rationale |
|---|---|---|
| `overall_result` | **Yes** | Derived from dimension results via fixed aggregation rules |
| `overall_severity` | **Yes** | Derived from dimension severities via fixed escalation rules |
| `dimensions_verified[].result` | **Yes** | Derived from evidence evaluation via fixed criteria |
| `dimensions_verified[].severity` | **Yes** | Constrained by result/severity mapping |
| `retry_eligible` | **Yes** | Derived from `overall_severity` (critical → false) and `retry_count` |
| `closure_criteria_met` | **Yes** | Derived from `overall_result` and governance profile rules |
| `dimensions_verified[].findings` | **Yes** | Deterministic string list from evidence evaluation |
| `dimensions_verified[].criteria_checked` | **Yes** | Deterministic from criteria catalog and evidence |
| `verification_timestamp` | **No** — varies per invocation | Recorded at evaluation time; not part of result logic |
| `metadata` | **No** — may include environment info | Non-normative; not part of result logic |

### 3.4 Replay Procedure

To re-evaluate a verification:

1. Extract the original `VerificationRequest` from the ledger or artifact store.
2. Re-run evaluation using the same schema version (`$id` in `verification_result.schema.json`).
3. Compare the new `VerificationResult` against the original, excluding `verification_timestamp` and `metadata`.
4. If any deterministic field differs → **replay failure** → escalate to Program Controller.

### 3.5 Anti-Drift Rules

The verifier MUST NOT:

| Rule | Prohibition | Rationale |
|---|---|---|
| AD-1 | Invent new evaluation criteria not present in the criteria catalog | Criteria are contract-defined, not evaluator-discovered |
| AD-2 | Weight dimensions differently based on environment or time | Aggregation rules are fixed |
| AD-3 | Cache prior results and return them without re-evaluation | Replay must actually re-evaluate |
| AD-4 | Use model inference or probabilistic reasoning for result determination | Results are rule-derived, not model-derived |
| AD-5 | Consult external APIs or network resources during evaluation | Evaluation is offline-deterministic |
| AD-6 | Modify the input request before evaluation | Input is immutable once submitted |
| AD-7 | Return different results for the same input based on evaluator identity | Evaluator identity is irrelevant to result logic |
| AD-8 | Accumulate state across evaluations that affects future results | Each evaluation is stateless |

### 3.6 Schema Version Pinning

All evaluations MUST reference the exact schema version used:

```json
{
  "metadata": {
    "schema_version": "https://ief.dev/schemas/verification_result.schema.json",
    "schema_commit": "bc4b93f",
    "evaluation_deterministic": true
  }
}
```

If the schema version changes, prior results remain valid under their original schema. Re-evaluation under a new schema version produces a new `verification_id` and references the original via `parent_artifact`.

---

## 4. Failure Classification Completeness

### 4.1 Failure Categories

Every failure observed during verification MUST map to exactly one category:

| Category | Code | Description | `overall_result` | Default `overall_severity` | `retry_eligible` |
|---|---|---|---|---|---|
| Schema Validation Failure | `FC-SCHEMA` | Input does not validate against request schema | `blocked` | `error` | `true` |
| Evidence Gap | `FC-EVIDENCE` | Required evidence missing for governance profile | `blocked` | `warning` | `true` |
| Boundary Violation | `FC-BOUNDARY` | Runner modified files outside `allowed_files` or took forbidden actions | `fail` | `critical` | `false` |
| Governance Non-Compliance | `FC-GOVERNANCE` | Required gate events missing, self-acceptance detected, or ledger integrity failure | `fail` | `error` or `critical` | per severity |
| Functional Failure | `FC-FUNCTIONAL` | Artifacts missing, empty, or unresolvable | `fail` | `error` | `true` |
| Stress Failure | `FC-STRESS` | Runner behavior under pressure violates contract (scope creep, contradiction) | `fail` | `error` or `critical` | per severity |
| Infrastructure Failure | `FC-INFRA` | Verification infrastructure timed out or errored before completing | N/A (ledger `verification_failed` event) | `error` | `true` |
| Deduplication Hit | `FC-DEDUP` | `verification_id` already processed | N/A (reject, no result) | N/A | N/A |
| Contradictory Evidence | `FC-CONTRADICT` | Evidence sources contradict each other (e.g., review approved but ledger shows rejection) | `fail` | `error` | `true` |
| Stale Evidence | `FC-STALE` | Evidence timestamps are inconsistent (verification predates review) | `conditional` | `warning` | `true` |

### 4.2 Failure Classification Rules

```
R1: If request fails schema validation → FC-SCHEMA
R2: If request passes schema but governance-conditional requirements not met → FC-EVIDENCE
R3: If boundary dimension finds file/action violations → FC-BOUNDARY
R4: If governance_compliance dimension finds gate/ledger issues → FC-GOVERNANCE
R5: If functional dimension finds artifact issues → FC-FUNCTIONAL
R6: If stress dimension finds behavioral issues → FC-STRESS
R7: If verification infrastructure fails → FC-INFRA (no VerificationResult produced)
R8: If verification_id already processed → FC-DEDUP (reject, no result produced)
R9: If evidence sources contradict → FC-CONTRADICT
R10: If evidence timestamps inconsistent → FC-STALE
```

**Priority:** When multiple categories apply, the one producing the highest severity takes precedence for `blocked_reason` / primary findings. All applicable categories are listed in `findings`.

### 4.3 Severity Escalation from Failure Category

| Failure Category | Minimum Severity | Maximum Severity | Escalation Condition |
|---|---|---|---|
| FC-SCHEMA | `error` | `error` | Fixed |
| FC-EVIDENCE | `warning` | `error` | `error` if G-Full profile |
| FC-BOUNDARY | `critical` | `critical` | Fixed (boundary violations are always critical) |
| FC-GOVERNANCE | `error` | `critical` | `critical` if self-acceptance detected |
| FC-FUNCTIONAL | `error` | `error` | Fixed |
| FC-STRESS | `error` | `critical` | `critical` if scope creep under pressure |
| FC-INFRA | `error` | `critical` | `critical` if data loss suspected |
| FC-CONTRADICT | `error` | `error` | Fixed |
| FC-STALE | `warning` | `warning` | Fixed |

### 4.4 Retry Eligibility Matrix

| `overall_severity` | `retry_count` | `retry_eligible` | Rationale |
|---|---|---|---|
| `info` | any | `false` | No failure to retry |
| `warning` | any | `true` | Non-blocking concern; retry may resolve |
| `error` | 0 | `true` | First failure; retry authorized |
| `error` | 1 | `true` | Second attempt; retry still authorized |
| `error` | ≥2 | `false` | Repeated failure; escalate to Controller |
| `critical` | any | `false` | Critical failures require human intervention |

### 4.5 Failure-to-Ledger Event Mapping

| Failure Category | Ledger Event | Payload Fields |
|---|---|---|
| FC-SCHEMA | `verification_failed` | `verification_id`, `failure_reason: "schema_validation_failed"`, `validation_errors[]` |
| FC-EVIDENCE | `verification_completed` | Result with `overall_result: blocked`, `blocked_reason` |
| FC-BOUNDARY | `verification_completed` | Result with `overall_result: fail`, `overall_severity: critical` |
| FC-GOVERNANCE | `verification_completed` | Result with dimension-level findings |
| FC-FUNCTIONAL | `verification_completed` | Result with dimension-level findings |
| FC-STRESS | `verification_completed` | Result with dimension-level findings |
| FC-INFRA | `verification_failed` | `verification_id`, `failure_reason`, `elapsed_ms` |
| FC-DEDUP | No ledger event | Reject silently; return cached result reference |
| FC-CONTRADICT | `verification_completed` | Result with findings listing contradictions |
| FC-STALE | `verification_completed` | Result with `overall_result: conditional` |

---

## 5. Anti-Drift Rules — Preventing Verifier from Becoming Policy Engine

### 5.1 Role Boundary

The verifier is an **evaluation function**, not a **decision engine**. It:

- ✅ Evaluates evidence against fixed criteria
- ✅ Produces structured results with deterministic rules
- ✅ Reports findings and severity
- ❌ Does NOT decide whether to retry (reports `retry_eligible`; Controller decides)
- ❌ Does NOT decide whether to accept (reports `closure_criteria_met`; Controller decides)
- ❌ Does NOT decide governance policy (reads `governance_profile`; does not write it)
- ❌ Does NOT expand criteria catalogs (uses contract-defined criteria only)
- ❌ Does NOT initiate dispatch or lifecycle transitions
- ❌ Does NOT modify its own schemas or rules

### 5.2 Anti-Policy-Engine Constraints

| Constraint | Rule | Enforcement |
|---|---|---|
| APC-1 | Verifier output is a `VerificationResult`, not a directive or recommendation | Result schema has no `recommended_action`, `next_step`, or `suggested_fix` fields |
| APC-2 | Verifier does not rank or prioritize failures beyond severity | No `priority` field in dimension results; severity is the only ranking |
| APC-3 | Verifier does not condition results on external state (time, load, queue depth) | Evaluation is offline-deterministic (Section 3) |
| APC-4 | Verifier does not learn from past evaluations | No feedback loop, no weight adjustment, no criteria evolution |
| APC-5 | Verifier does not filter or suppress findings | All findings are reported; no `suppressed_findings` or `filtered_results` |
| APC-6 | Verifier does not aggregate across tasks | Each `VerificationResult` is scoped to one `task_id` + `run_id` |
| APC-7 | Verifier does not define or modify governance profiles | `governance_profile` is read-only input |
| APC-8 | Verifier does not authorize retries | `retry_eligible` is a boolean flag; authorization is Controller's responsibility |

### 5.3 Schema-Level Enforcement

The `RESULT_SCHEMA_V2.json` enforces anti-drift via:

1. **No extension fields:** `additionalProperties: false` on result and dimension objects (except `metadata`).
2. **No action fields:** No `action`, `recommendation`, `suggestion`, or `directive` properties anywhere in the schema.
3. **Fixed enums:** Result, severity, dimension, and governance profile values are closed enums.
4. **Conditional constraints:** `allOf` blocks enforce result/severity mapping; no override mechanism.
5. **Versioned schema:** `$id` includes version; schema evolution requires explicit version bump.

---

## 6. Relationship to Prior Slices

| Slice | Contribution | G8-2 Build-Upon |
|---|---|---|
| G6-A (Schema Fix) | Result/severity cross-field constraint | G8-2 extends with normalization rules and versioned evolution |
| G7-A (Minimal Implementation) | Schema files, fixture tests, module documentation | G8-2 hardens the schema with V2 and adds edge case coverage |
| G8-1 (Control Plane Freeze) | Frozen layer boundaries, no-implicit-state-source rule, mutation matrix | G8-2 respects frozen boundaries; verifier remains evaluation-only |

---

## 7. Non-Goals

- ❌ No runtime verifier daemon or service
- ❌ No background execution or scheduling
- ❌ No autonomous evaluation triggers
- ❌ No self-modifying rules or adaptive criteria
- ❌ No production enforcement hooks
- ❌ No CI/CD integration
- ❌ No auto-verification loop
- ❌ No model inference in evaluation logic
- ❌ No cross-task aggregation or trend analysis

---

## 8. Summary

| Layer | What G8-2 Adds |
|---|---|
| Edge Case Coverage | 10 input-domain buckets + 19 dimension-level edge cases + 6 aggregation edge cases |
| Deterministic Replay | Input fingerprint, deterministic output fields, replay procedure, 8 anti-drift rules |
| Failure Classification | 10 failure categories with severity ranges, retry eligibility, and ledger event mapping |
| Anti-Drift | 8 anti-policy-engine constraints + 5 schema-level enforcement mechanisms |

**Total rules defined:** 10 coverage buckets + 19 dimension edge cases + 6 aggregation edge cases + 8 anti-drift rules + 10 failure categories + 8 anti-policy constraints = **61 hardening rules**.

---

*Produced by ief-operator executing one bounded Stage G G8-2 cycle. Documentation and schema only. No runtime changes.*
