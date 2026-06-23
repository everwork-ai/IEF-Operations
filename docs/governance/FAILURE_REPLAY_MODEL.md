# Failure Replay Model — Stage G (G8-2)

> **Status:** Frozen Specification  
> **Created:** 2026-06-23T12:18+08:00  
> **Authority:** Program Controller STAGE_G_G7_FINAL_REVIEW_RESULT (G8-2 AUTHORIZED)  
> **Baseline:** IEF-Operations `main` @ `31bc466`  
> **Companion spec:** `VERIFICATION_HARDENING_SPEC.md`  
> **Schema reference:** `schemas/RESULT_SCHEMA_V2.json`  

---

## 1. Purpose

This document defines the **input → evaluation → output traceability model** for the IEF Verification Module. It specifies how every verification result can be traced back to its exact inputs, how deterministic re-evaluation works, and how failures are replayed for debugging and audit.

The replay model ensures that:

1. Every `VerificationResult` is fully traceable to its `VerificationRequest` and evidence sources.
2. Re-evaluation of the same input under the same schema version produces the same result.
3. Failure diagnosis can reconstruct the exact evaluation path that produced a given result.
4. Audit trails are complete and tamper-evident.

---

## 2. Traceability Chain

### 2.1 Full Traceability Path

```
VerificationRequest (input)
    │
    ├── verification_id ──────────────→ Unique result identifier
    ├── task_id ──────────────────────→ TaskEnvelope in Operations ledger
    ├── run_id ───────────────────────→ RunEvent chain in Operations ledger
    ├── governance_profile ───────────→ Governance policy (G-Lite/G-Std/G-Full)
    ├── artifact_refs[] ──────────────→ Actual artifact content (URI-resolvable)
    ├── context_refs[] ───────────────→ Context packs from Knowledge layer
    ├── allowed_files[] ──────────────→ Directive-defined file scope
    ├── forbidden_actions[] ──────────→ Directive-defined action constraints
    ├── review_result ────────────────→ G4 code review decision
    ├── ledger_entries[] ─────────────→ Operations ledger events for this run
    ├── requested_dimensions[] ───────→ Which dimensions to evaluate
    └── retry_count ──────────────────→ Number of prior attempts
         │
         ▼
    Evaluation Engine (deterministic, offline)
         │
         ├── Per-dimension criteria evaluation
         │     ├── criterion + evidence → pass/fail/conditional/skipped
         │     ├── result → severity (via allOf constraint)
         │     └── findings[] ← evidence-based string list
         │
         ├── Aggregation
         │     ├── dimension results → overall_result
         │     ├── dimension severities → overall_severity
         │     └── overall_severity → retry_eligible
         │
         └── Closure evaluation
               └── overall_result + governance_profile → closure_criteria_met
                    │
                    ▼
              VerificationResult (output)
```

### 2.2 Traceability Fields in VerificationResult V2

The V2 schema adds explicit traceability fields:

| Field | Purpose | Deterministic? |
|---|---|---|
| `input_fingerprint` | SHA-256 of the deterministic input fields | Yes |
| `schema_version` | Exact schema `$id` used for evaluation | Yes |
| `evaluation_criteria_version` | Version of the criteria catalog used | Yes |
| `dimensions_verified[].criteria_checked[].criterion_id` | Stable identifier for each criterion | Yes |
| `dimensions_verified[].evidence_refs` | URIs of evidence supporting this dimension | Yes |
| `failure_classification` | Primary failure category code (from VERIFICATION_HARDENING_SPEC §4.1) | Yes |
| `applicable_failure_categories[]` | All failure categories that apply | Yes |
| `coverage_bucket` | Input coverage bucket (from VERIFICATION_HARDENING_SPEC §2.1) | Yes |

---

## 3. Deterministic Re-Evaluation Model

### 3.1 Re-Evaluation Invariant

**Given:**
- The same `VerificationRequest` (byte-identical or fingerprint-identical)
- The same schema version (`$id` in `verification_result.schema.json`)
- The same criteria catalog version

**Then:**
- The `VerificationResult` MUST be identical in all deterministic fields
- `verification_timestamp` and `metadata` may differ (non-deterministic)

### 3.2 Re-Evaluation Procedure

```
Step 1: Retrieve Original Input
    - Fetch VerificationRequest from ledger or artifact store
    - Verify input_fingerprint matches stored value
    - If fingerprint mismatch → input was tampered → halt, escalate

Step 2: Retrieve Original Schema Version
    - Extract schema_version from original VerificationResult.metadata
    - Load that exact schema version (by $id)
    - If schema version no longer available → halt, escalate

Step 3: Retrieve Original Criteria Catalog
    - Extract evaluation_criteria_version from original result
    - Load that exact criteria catalog version
    - If catalog version no longer available → halt, escalate

Step 4: Re-Run Evaluation
    - Apply criteria to evidence (same rules, same order)
    - Apply result/severity constraints (allOf blocks)
    - Apply aggregation rules (Section 6.1 of VERIFICATION_MODULE.md)
    - Apply closure evaluation

Step 5: Compare Results
    - Compare all deterministic fields between original and new result
    - Exclude: verification_timestamp, metadata, decision_by, decided_at
    - If all deterministic fields match → REPLAY PASS
    - If any deterministic field differs → REPLAY FAIL → escalate
```

### 3.3 Re-Evaluation Output

Re-evaluation produces a `ReplayReport`:

```json
{
  "replay_id": "<UUID>",
  "original_verification_id": "<original verification_id>",
  "original_input_fingerprint": "<SHA-256>",
  "replay_input_fingerprint": "<SHA-256 — should match>",
  "schema_version": "<$id used>",
  "criteria_catalog_version": "<version used>",
  "replay_timestamp": "<ISO-8601>",
  "result": "PASS | FAIL",
  "differences": [
    {
      "field": "<JSON path>",
      "original_value": "<value>",
      "replay_value": "<value>",
      "explanation": "<why this might differ>"
    }
  ],
  "conclusion": "<summary>"
}
```

### 3.4 Re-Evaluation Triggers

Re-evaluation is NOT automatic. It is triggered only by:

| Trigger | Authorized By |
|---|---|
| Explicit Controller request | Program Controller via GitHub comment |
| Audit review | Human Owner during audit cycle |
| Schema migration | When migrating results to a new schema version |
| Failure investigation | When a `REPLAY_FAIL` is reported and needs diagnosis |

Re-evaluation is **never** triggered by:
- Time-based schedules
- Automatic retry logic
- Verifier self-assessment
- External CI/CD pipelines

---

## 4. Failure Replay for Diagnosis

### 4.1 Failure Reconstruction

When a verification produces `overall_result: fail` or `overall_result: blocked`, the failure can be reconstructed:

```
Step 1: Identify Primary Failure Category
    - Read failure_classification from VerificationResult
    - Map to VERIFICATION_HARDENING_SPEC §4.1 category

Step 2: Trace to Dimension
    - Find the dimension(s) with result: "fail"
    - Read dimensions_verified[].findings[]
    - Read dimensions_verified[].criteria_checked[]

Step 3: Trace to Evidence
    - Read dimensions_verified[].evidence_refs[]
    - Fetch each evidence artifact
    - Verify evidence content matches what was evaluated

Step 4: Trace to Input
    - Read input_fingerprint
    - Fetch original VerificationRequest
    - Verify request fields that fed into the failing dimension

Step 5: Reconstruct Evaluation Path
    - For each criterion in criteria_checked[]:
      - criterion_id → which rule was checked
      - result → pass/fail/conditional/skipped
      - evidence → what evidence supported this result
    - Verify the evaluation path matches the criteria catalog
```

### 4.2 Failure Replay Report

```json
{
  "failure_replay_id": "<UUID>",
  "verification_id": "<original verification_id>",
  "failure_category": "FC-BOUNDARY",
  "failing_dimension": "boundary",
  "failing_criteria": [
    {
      "criterion_id": "B-1",
      "criterion_text": "No files modified outside allowed_files",
      "result": "fail",
      "evidence": "Commit abc123 modified src/main.py, not in allowed_files",
      "evidence_ref": "https://github.com/.../commit/abc123"
    }
  ],
  "input_summary": {
    "allowed_files": ["docs/SMOKE_TEST.md"],
    "forbidden_actions": ["merge", "close"],
    "governance_profile": "G-Lite"
  },
  "reconstruction": "Runner modified src/main.py in commit abc123. This file is not in the allowed_files list. Boundary dimension correctly evaluated as fail with critical severity.",
  "conclusion": "Verification result is correct. Failure is legitimate."
}
```

### 4.3 Failure Replay Categories

Each failure category from VERIFICATION_HARDENING_SPEC §4.1 has a specific replay procedure:

| Category | Replay Focus | Key Evidence |
|---|---|---|
| FC-SCHEMA | Request schema validation | Validation error list |
| FC-EVIDENCE | Missing evidence check | Governance profile requirements vs. provided fields |
| FC-BOUNDARY | Git diff analysis | Commit diffs vs. `allowed_files` |
| FC-GOVERNANCE | Ledger event sequence | `ledger_entries[]` sequence and gate events |
| FC-FUNCTIONAL | Artifact resolution | `artifact_refs[]` URI resolution and content |
| FC-STRESS | Stress test evidence | Stress run logs and behavioral observations |
| FC-INFRA | Infrastructure logs | Timeout logs, error traces |
| FC-DEDUP | Dedup cache lookup | Previously processed `verification_id` |
| FC-CONTRADICT | Cross-evidence comparison | Contradictory evidence pairs |
| FC-STALE | Timestamp comparison | Evidence timestamps vs. verification timestamp |

---

## 5. Input Fingerprint Specification

### 5.1 Fingerprint Composition

The input fingerprint is a SHA-256 hash of the canonical serialization of deterministic input fields:

```
fingerprint_input = JSON.stringify({
  "verification_id": "<uuid>",
  "task_id": "<uuid>",
  "run_id": "<uuid>",
  "governance_profile": "<G-Lite|G-Std|G-Full>",
  "artifact_refs": ["<sorted URIs>"],
  "context_refs": ["<sorted URIs>"],
  "allowed_files": ["<sorted paths>"],
  "forbidden_actions": ["<sorted actions>"],
  "review_result": {
    "decision": "<approved|rejected|rework|null>",
    "reviewer": "<identity|null>",
    "review_timestamp": "<ISO-8601|null>"
  },
  "ledger_entries": ["<sorted entry_ids>"],
  "requested_dimensions": ["<sorted dimensions>"],
  "retry_count": <integer>
}, null, 0)  // compact JSON, no whitespace

input_fingerprint = SHA-256(fingerprint_input)
```

### 5.2 Fingerprint Properties

| Property | Value |
|---|---|
| Algorithm | SHA-256 |
| Input | Canonical JSON (sorted keys, sorted arrays, compact serialization) |
| Output | 64-character hex string |
| Collision resistance | Cryptographic (2^128 security) |
| Deterministic | Same input → same fingerprint, always |
| Tamper-evident | Any input change → different fingerprint |

### 5.3 Fingerprint Usage

| Context | Usage |
|---|---|
| VerificationResult V2 | Stored in `input_fingerprint` field |
| Re-evaluation | Compare original fingerprint to re-computed fingerprint |
| Audit | Verify that the input was not modified between evaluation and audit |
| Dedup | Quick check: same fingerprint → same input (supplement to `verification_id` dedup) |

---

## 6. Schema Version Evolution and Replay Compatibility

### 6.1 Version Evolution Rules

| Change Type | Compatible? | Replay Impact |
|---|---|---|
| Add optional field to result | Yes | Old results remain valid; new field absent |
| Add new enum value to non-critical field | Yes | Old results remain valid |
| Change `allOf` constraint logic | **No** | Old results may not validate under new schema |
| Add required field | **No** | Old results lack the field |
| Remove enum value | **No** | Old results may contain removed value |
| Change result/severity mapping | **No** | Old results may violate new constraints |

### 6.2 Replay Under New Schema Version

When re-evaluating under a new schema version:

1. The new result gets a **new** `verification_id`.
2. The new result references the original via `parent_artifact`.
3. The new result records the new `schema_version` in metadata.
4. The original result remains valid under its original schema.
5. Both results coexist in the ledger; the newer one is marked as `supersedes: <original_verification_id>`.

### 6.3 Criteria Catalog Versioning

The criteria catalog is versioned independently of the schema:

```
criteria_catalog_version = "<governance_profile>-<date>-<revision>"
Example: "G-Std-2026-06-23-r1"
```

Criteria catalog changes require:
1. New version identifier
2. Documented diff from prior version
3. Controller approval for the change
4. Re-evaluation of affected results only if Controller requests it

---

## 7. Audit Trail Requirements

### 7.1 Minimum Audit Trail

For every verification, the following must be reconstructable:

| Item | Source | Retention |
|---|---|---|
| VerificationRequest | Ledger or artifact store | Permanent |
| VerificationResult | Ledger or artifact store | Permanent |
| Input fingerprint | VerificationResult V2 `input_fingerprint` | Permanent |
| Schema version used | VerificationResult V2 `metadata.schema_version` | Permanent |
| Criteria catalog version | VerificationResult V2 `metadata.evaluation_criteria_version` | Permanent |
| Evidence artifacts | Referenced by `artifact_refs[]` and `evidence_refs[]` | Permanent |
| Ledger events | Operations ledger (verification_requested → verification_completed) | Permanent |
| Replay reports | If re-evaluation occurred | Permanent |
| Failure replay reports | If failure diagnosis occurred | Permanent |

### 7.2 Tamper Evidence

The audit trail is tamper-evident through:

1. **Append-only ledger:** Ledger entries are never modified or deleted.
2. **Input fingerprint:** Any modification to the input changes the fingerprint.
3. **Schema version pinning:** Re-evaluation under a different schema produces a new result, not a modification.
4. **Evidence URI integrity:** Evidence artifacts are referenced by URI; modification at the URI target is detectable if content hashes are stored.
5. **Ledger sequence numbers:** Out-of-order or missing sequence numbers indicate tampering.

### 7.3 Audit Reconstruction Procedure

```
Step 1: Start from VerificationResult
    - Read verification_id, task_id, run_id
    - Read input_fingerprint

Step 2: Fetch VerificationRequest
    - From ledger or artifact store
    - Re-compute fingerprint
    - Verify fingerprint match

Step 3: Fetch Evidence
    - Resolve all artifact_refs[] and evidence_refs[]
    - Verify content (if hashes available)

Step 4: Fetch Ledger Events
    - All events for this task_id + run_id
    - Verify sequence ordering

Step 5: Verify Evaluation
    - Check that result matches criteria catalog version
    - Check that severity matches result/severity constraint
    - Check that aggregation matches rules

Step 6: Produce Audit Report
    - Audit pass/fail
    - List of any discrepancies found
    - Conclusion on result validity
```

---

## 8. Relationship to Other Specifications

| Specification | Relationship |
|---|---|
| `VERIFICATION_HARDENING_SPEC.md` | This document implements the replay model for the edge case coverage and failure classification defined there |
| `VERIFICATION_MODULE.md` | This document extends the evidence model (§5) and review criteria (§10) with traceability fields |
| `VERIFICATION_FIXTURES.md` | Fixture tests serve as replay validation: same input → same expected output |
| `RESULT_SCHEMA_V2.json` | V2 schema includes the traceability fields defined in §2.2 of this document |
| `CONTROL_PLANE_FREEZE_SPEC.md` (G8-1) | Replay model respects frozen layer boundaries; verifier remains evaluation-only |
| `STAGE_G_CONTRACT_LOCK.json` (G8-1) | Replay model does not introduce new mutation paths |

---

## 9. Non-Goals

- ❌ No automatic replay scheduling
- ❌ No continuous re-evaluation
- ❌ No replay-triggered lifecycle transitions
- ❌ No replay result auto-posting to GitHub
- ❌ No cross-verification trend analysis
- ❌ No machine-learning-based anomaly detection on replay results

---

## 10. Summary

| Aspect | Specification |
|---|---|
| Traceability | Full path from VerificationRequest → evaluation → VerificationResult with fingerprint |
| Re-evaluation | Deterministic: same input + same schema + same criteria = same result |
| Failure replay | 10 failure categories with specific reconstruction procedures |
| Fingerprint | SHA-256 of canonical JSON input; tamper-evident |
| Schema evolution | Compatible changes preserve old results; incompatible changes require new verification_id |
| Audit trail | Permanent, append-only, tamper-evident |

---

*Produced by ief-operator executing one bounded Stage G G8-2 cycle. Documentation only. No runtime changes.*
