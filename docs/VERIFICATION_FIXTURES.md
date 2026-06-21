# IEF Verification Fixtures

> Test fixture documentation for the IEF Verification Module.  
> Each fixture defines a test scenario with expected outcomes.  
> Governance: G-Std  
> Schema version: JSON Schema draft 2020-12

**Produced by:** ief-operator  
**Timestamp:** 2026-06-21T23:20:00+08:00  
**Classification:** STAGE_G_G7A_VERIFICATION_MODULE_MINIMAL_IMPLEMENTATION

---

## 1. Overview

This document describes the fixture-based test suite for the IEF Verification Module. All tests are **fixture-based**: JSON input fixtures produce expected JSON output results. No runtime verifier daemon is required.

### 1.1 Test Strategy

Tests validate that:
1. Input fixtures validate against `verification_request.schema.json`
2. Output fixtures validate against `verification_result.schema.json`
3. Aggregation rules produce correct `overall_result` and `overall_severity`
4. Conditional constraints enforce required fields
5. Result/severity cross-field constraints are satisfied
6. Dedup rules reject duplicate verification_ids

### 1.2 Fixture Directory

All fixtures are located in: `tests/fixtures/verification/`

---

## 2. Fixture Test Matrix

| Test ID | Fixture File | Profile | Expected Result | Validates |
|---------|--------------|---------|-----------------|-----------|
| T1 | `glite_pass.json` | G-Lite | pass (info) | Happy path, minimal evidence |
| T2 | `glite_fail_boundary.json` | G-Lite | fail (critical) | Boundary violation, no retry |
| T3 | `gstd_pass.json` | G-Std | pass (info) | Full 4-dimension pass |
| T4 | `gstd_conditional_stress.json` | G-Std | conditional (warning) | Partial pass, retry eligible |
| T5 | `gfull_fail_governance.json` | G-Full | fail (error) | Missing independent review |
| T6 | `blocked_missing_input.json` | G-Std | blocked (warning) | Evidence gap, retry eligible |
| T7 | `retry_eligible_timeout.json` | Any | verification_failed event | Infrastructure failure |

---

## 3. Fixture Details

### 3.1 T1: G-Lite Pass (`glite_pass.json`)

**Scenario:** A documentation-only task under G-Lite governance. All artifacts present, no boundary violations.

**Input (VerificationRequest):**
- `verification_id`: `11111111-1111-1111-1111-111111111111`
- `governance_profile`: `G-Lite`
- `artifact_refs`: 1 artifact (SMOKE_TEST.md)
- `allowed_files`: `["docs/SMOKE_TEST.md"]`
- `forbidden_actions`: `["merge", "close", "rebase"]`
- `requested_dimensions`: `["functional", "boundary"]`

**Expected Output (VerificationResult):**
- `overall_result`: `pass`
- `overall_severity`: `info`
- `dimensions_verified`: 2 dimensions (functional, boundary) both pass
- `retry_eligible`: `false`
- `closure_criteria_met`: `true`

**Validation Points:**
- ✅ Request validates against schema
- ✅ Result validates against schema
- ✅ Dimension result/severity constraints satisfied (pass → info)
- ✅ Overall result/severity constraint satisfied (pass → info)

---

### 3.2 T2: G-Lite Boundary Fail (`glite_fail_boundary.json`)

**Scenario:** Runner modified a file outside `allowed_files`.

**Input (VerificationRequest):**
- `verification_id`: `22222222-2222-2222-2222-222222222222`
- `governance_profile`: `G-Lite`
- `allowed_files`: `["docs/SMOKE_TEST.md"]`
- `requested_dimensions`: `["boundary"]`

**Expected Output (VerificationResult):**
- `overall_result`: `fail`
- `overall_severity`: `critical`
- `dimensions_verified`: 1 dimension (boundary) fails with critical severity
- `findings`: `["File src/main.py modified but not in allowed_files"]`
- `retry_eligible`: `false` (critical severity)
- `closure_criteria_met`: `false`

**Validation Points:**
- ✅ Request validates against schema
- ✅ Result validates against schema
- ✅ Dimension result/severity constraint satisfied (fail → critical)
- ✅ Overall result/severity constraint satisfied (fail → critical)
- ✅ Critical severity enforces `retry_eligible: false`

---

### 3.3 T3: G-Std Pass (`gstd_pass.json`)

**Scenario:** Implementation task under G-Std. Review approved, all 4 dimensions pass.

**Input (VerificationRequest):**
- `verification_id`: `33333333-3333-3333-3333-333333333333`
- `governance_profile`: `G-Std`
- `review_result`: approved
- `ledger_entries`: present (required for G-Std)
- `requested_dimensions`: all 4 dimensions

**Expected Output (VerificationResult):**
- `overall_result`: `pass`
- `overall_severity`: `info`
- `dimensions_verified`: all 4 dimensions pass
- `retry_eligible`: `false`
- `closure_criteria_met`: `true`

**Validation Points:**
- ✅ Request validates against schema (G-Std requires review_result + ledger_entries)
- ✅ Result validates against schema
- ✅ All dimension result/severity constraints satisfied
- ✅ Overall result/severity constraint satisfied

---

### 3.4 T4: G-Std Conditional Stress (`gstd_conditional_stress.json`)

**Scenario:** G-Std task. All dimensions pass except stress: token budget was not constrained, so stress was not fully exercised.

**Input (VerificationRequest):**
- `verification_id`: `44444444-4444-4444-4444-444444444444`
- `governance_profile`: `G-Std`
- `review_result`: approved
- `requested_dimensions`: all 4 dimensions

**Expected Output (VerificationResult):**
- `overall_result`: `conditional`
- `overall_severity`: `warning`
- `dimensions_verified`: 3 pass, 1 conditional (stress)
- `findings`: `["Token budget was not constrained; stress not fully exercised"]`
- `retry_eligible`: `true`
- `closure_criteria_met`: `false`

**Validation Points:**
- ✅ Request validates against schema
- ✅ Result validates against schema
- ✅ Dimension result/severity constraints satisfied (pass → info, conditional → warning)
- ✅ Overall result/severity constraint satisfied (conditional → warning)

---

### 3.5 T5: G-Full Governance Fail (`gfull_fail_governance.json`)

**Scenario:** G-Full task. Independent review missing for G3 (code review gate). Required for G-Full but not present in evidence.

**Input (VerificationRequest):**
- `verification_id`: `55555555-5555-5555-5555-555555555555`
- `governance_profile`: `G-Full`
- `review_result`: approved
- `context_refs`: present (required for G-Full)
- `requested_dimensions`: all 4 dimensions

**Expected Output (VerificationResult):**
- `overall_result`: `fail`
- `overall_severity`: `error`
- `dimensions_verified`: 3 pass, 1 fail (governance_compliance)
- `findings`: `["G3 (code review) independent review not found in ledger entries"]`
- `criteria_checked`: `[{ "criterion": "GC-3: No self-acceptance", "result": "fail" }]`
- `retry_eligible`: `true`
- `closure_criteria_met`: `false`

**Validation Points:**
- ✅ Request validates against schema (G-Full requires context_refs)
- ✅ Result validates against schema
- ✅ Dimension result/severity constraint satisfied (fail → error)
- ✅ Overall result/severity constraint satisfied (fail → error)

---

### 3.6 T6: Blocked — Missing Input (`blocked_missing_input.json`)

**Scenario:** G-Std verification requested but no review_result provided (required for G-Std).

**Input (VerificationRequest):**
- `verification_id`: `66666666-6666-6666-6666-666666666666`
- `governance_profile`: `G-Std`
- `review_result`: **missing** (required for G-Std)

**Expected Output (VerificationResult):**
- `overall_result`: `blocked`
- `overall_severity`: `warning`
- `blocked_reason`: `"G-Std requires review_result but none provided in VerificationRequest"`
- `dimensions_verified`: `[]` (empty, verification could not proceed)
- `retry_eligible`: `true`
- `closure_criteria_met`: `false`

**Validation Points:**
- ⚠️ Request **fails schema validation** (G-Std conditional requires review_result)
- ✅ Result validates against schema (blocked requires blocked_reason)
- ✅ Blocked result allows any severity (warning is typical)

**Note:** The request intentionally fails schema validation to test the "blocked" path. In practice, the verifier would detect the missing evidence before schema validation.

---

### 3.7 T7: Retry-Eligible Timeout (`retry_eligible_timeout.json`)

**Scenario:** Verification infrastructure timed out before completing. This fixture produces a `verification_failed` ledger event, not a VerificationResult.

**Input:** N/A (infrastructure failure)

**Expected Output (Ledger Entry):**
- `event_type`: `verification_failed`
- `severity`: `error`
- `payload`:
  - `verification_id`: `77777777-7777-7777-7777-777777777777`
  - `failure_reason`: `"Verification timed out after 300 seconds"`
  - `retry_eligible`: `true`

**Validation Points:**
- ✅ Ledger entry validates against schema
- ✅ `verification_failed` event type has conditional severity constraint (error or critical)
- ✅ Payload includes required fields (verification_id, failure_reason)

---

## 4. Result/Severity Constraint Summary

The verification module enforces strict result/severity constraints to maintain logical consistency:

### 4.1 Dimension-Level Constraints

| Result | Allowed Severity | Rationale |
|--------|------------------|-----------|
| `pass` | `info` only | A passing dimension has no issues; severity can only be informational |
| `fail` | `error` or `critical` | A failing dimension must indicate a real problem |
| `conditional` | `warning` only | A conditional pass indicates a concern that doesn't block but warrants attention |
| `skipped` | `info` only | A skipped dimension has no findings; informational only |

### 4.2 Overall-Level Constraints

| Overall Result | Allowed Overall Severity | Rationale |
|----------------|--------------------------|-----------|
| `pass` | `info` only | All dimensions passed; no issues |
| `fail` | `error` or `critical` | At least one dimension failed |
| `conditional` | `warning` only | At least one dimension conditional, no failures |
| `blocked` | any (typically `warning`) | Missing evidence; severity depends on blocking reason |

### 4.3 Critical Severity Constraint

When `overall_severity` is `critical`, `retry_eligible` **must** be `false`. Critical issues are not retryable without human intervention.

---

## 5. Negative Test Cases (Invalid Combinations)

The following combinations are **invalid** and must be rejected by the schema:

| Result | Severity | Valid? | Reason |
|--------|----------|--------|--------|
| `pass` | `warning` | ❌ | Pass means no issues; warning indicates a concern |
| `pass` | `error` | ❌ | Pass means no issues; error indicates a problem |
| `pass` | `critical` | ❌ | Pass means no issues; critical indicates a blocker |
| `fail` | `info` | ❌ | Fail means a problem exists; info cannot convey failure |
| `fail` | `warning` | ❌ | Fail means a problem exists; warning is insufficient |
| `conditional` | `info` | ❌ | Conditional means a concern exists; info is insufficient |
| `conditional` | `error` | ❌ | Conditional means non-blocking; error implies blocking |
| `skipped` | `warning` | ❌ | Skipped has no findings; warning implies a concern |
| `skipped` | `error` | ❌ | Skipped has no findings; error implies a problem |

These constraints are enforced by `allOf` conditional blocks in `verification_result.schema.json`.

---

## 6. Running the Tests

### 6.1 Prerequisites

Install `jsonschema` (optional but recommended for full validation):

```bash
pip install jsonschema
```

### 6.2 Run All Fixtures

```bash
cd D:\code\IEF\IEF-Operations
python scripts/verify.py --run-fixtures
```

### 6.3 Validate a Single Fixture

```bash
python scripts/verify.py --validate-request tests/fixtures/verification/glite_pass.json
python scripts/verify.py --validate-result tests/fixtures/verification/glite_pass.json
```

### 6.4 Validate a Ledger Event

```bash
python scripts/verify.py --validate-ledger tests/fixtures/verification/retry_eligible_timeout.json
```

---

## 7. Test Evidence

When the fixture tests are run, the output should show:

```
Running 7 fixture tests from tests/fixtures/verification

======================================================================
Test T1: G-Lite happy path: documentation task, all artifacts present, no boundary violations
======================================================================
✅ Request validates against schema
✅ Expected result validates against schema
✅ Dimension result/severity constraints satisfied
✅ Overall result/severity constraint satisfied
✅ PASS: All constraints satisfied

======================================================================
Test T2: G-Lite boundary fail: runner modified file outside allowed_files
======================================================================
✅ Request validates against schema
✅ Expected result validates against schema
✅ Dimension result/severity constraints satisfied
✅ Overall result/severity constraint satisfied
✅ Critical severity correctly has retry_eligible=false
✅ PASS: All constraints satisfied

...

======================================================================
RESULTS: 7 passed, 0 failed, 7 total
======================================================================
```

---

## 8. Aggregation Rules

### 8.1 Overall Result Aggregation

| Condition | `overall_result` |
|-----------|------------------|
| All dimensions `pass` | `pass` |
| Any dimension `fail` | `fail` |
| No `fail`, any `conditional` | `conditional` |
| Any `blocked` (missing evidence), no `fail` | `blocked` |
| All dimensions `skipped` | `blocked` |

### 8.2 Overall Severity Escalation

| Condition | `overall_severity` |
|-----------|---------------------|
| All dimensions `info` | `info` |
| Any dimension `warning`, no `error`/`critical` | `warning` |
| Any dimension `error`, no `critical` | `error` |
| Any dimension `critical` | `critical` |

---

## 9. Governance Profile Requirements

| Profile | Minimum Evidence Required |
|---------|---------------------------|
| G-Lite | `artifact_refs` non-empty, `allowed_files` non-empty, `forbidden_actions` non-empty |
| G-Std | G-Lite + `review_result` present with `decision`, `ledger_entries` non-empty |
| G-Full | G-Std + `ledger_entries` contains events for all 7 gates (G1-G7), `context_refs` non-empty |

---

## 10. Non-Goals

- This document does **not** describe a production verifier daemon
- This document does **not** authorize runtime verification execution
- This document does **not** define CI/CD integration for automatic verification
- This document does **not** implement the verification logic (only fixtures and validation)

---

*Produced by ief-operator. One bounded cycle. G-Std governance. JSON Schema draft 2020-12.*
