# IEF Verification Module — Minimal Implementation

> Minimal skeleton implementation of the IEF Verification Module.  
> Includes schemas, validator interface, fixture tests, and documentation.  
> No production verifier daemon. No CI enforcement.  
> Governance: G-Std  
> Schema version: JSON Schema draft 2020-12

**Produced by:** ief-operator  
**Authorization:** Controller STAGE_G_G6_FINAL_REVIEW_RESULT (G7 UNBLOCKED)  
**Trigger:** STAGE_G_G7A_VERIFICATION_MODULE_MINIMAL_IMPLEMENTATION_DISPATCH  
**Timestamp:** 2026-06-21T23:20:00+08:00  
**Classification:** STAGE_G_G7A_VERIFICATION_MODULE_MINIMAL_IMPLEMENTATION

---

## 0. Executive Summary

This document describes the minimal implementation of the IEF Verification Module, produced as a Stage G G7-A execution cycle. The implementation includes:

- **3 JSON Schema files** defining verification request, result, and evidence structures
- **4 new ledger event types** added to `ledger_entry.schema.json` for verification lifecycle
- **7 fixture tests** covering pass/fail/conditional/blocked scenarios across all governance profiles
- **1 validator script** (`scripts/verify.py`) for schema validation and fixture test execution
- **3 documentation files** (this document, fixture docs, OpenAPI spec)
- **Result/severity constraint enforcement** as specified in G6-A Schema Fix (comment 4753183384)

**This is a skeleton implementation only.** No production verifier daemon, no CI enforcement, no automatic GitHub comments, no issue closure or PR merge, no stage promotion.

---

## 1. Source Inputs

This implementation was produced from the following authoritative sources:

| # | Source | Location | Purpose |
|---|--------|----------|---------|
| 1 | G6-A Implementation Plan | IEF-Program#11 comment 4716523157 | Complete verification module design |
| 2 | G6-A Schema Fix | IEF-Program#11 comment 4753183384 | Result/severity constraint correction |
| 3 | IEF Operations schemas | `D:/code/IEF/IEF-Operations/schemas/` | Existing core schemas (task, run, ledger_entry, workflow) |
| 4 | IEF Operations design | `D:/code/IEF/IEF-Operations/docs/CORE_SCHEMA_DESIGN.md` | Schema design rationale |

---

## 2. Files Created

### 2.1 New Schema Files (3)

| # | Path | Purpose | Governance |
|---|------|---------|------------|
| F1 | `schemas/verification_request.schema.json` | Input schema: what verification consumes | G-Std |
| F2 | `schemas/verification_result.schema.json` | Output schema: pass/fail/conditional with dimension-level granularity and result/severity constraints | G-Std |
| F3 | `schemas/verification_evidence.schema.json` | Evidence schema: what constitutes verification evidence | G-Std |

### 2.2 Modified Schema Files (1)

| # | Path | Modification | Governance |
|---|------|-------------|------------|
| M1 | `schemas/ledger_entry.schema.json` | Added 4 verification event types to the `event_type` enum: `verification_requested`, `verification_started`, `verification_completed`, `verification_failed`. Added 4 conditional `if/then` constraints for verification event payloads. | G-Std |

### 2.3 Test Fixtures (7)

| # | Path | Test ID | Scenario |
|---|------|---------|----------|
| F7 | `tests/fixtures/verification/glite_pass.json` | T1 | G-Lite happy path |
| F8 | `tests/fixtures/verification/glite_fail_boundary.json` | T2 | G-Lite boundary violation |
| F9 | `tests/fixtures/verification/gstd_pass.json` | T3 | G-Std full 4-dimension pass |
| F10 | `tests/fixtures/verification/gstd_conditional_stress.json` | T4 | G-Std conditional (stress warning) |
| F11 | `tests/fixtures/verification/gfull_fail_governance.json` | T5 | G-Full governance fail |
| F12 | `tests/fixtures/verification/blocked_missing_input.json` | T6 | Blocked (missing evidence) |
| F13 | `tests/fixtures/verification/retry_eligible_timeout.json` | T7 | Infrastructure timeout (ledger event) |

### 2.4 Documentation (3)

| # | Path | Purpose | Governance |
|---|------|---------|------------|
| F4 | `docs/VERIFICATION_IMPLEMENTATION_PLAN_V0.md` | This document | G-Std |
| F5 | `docs/VERIFICATION_SPEC_V0.yaml` | OpenAPI 3.1 discovery spec | G-Lite |
| F6 | `docs/VERIFICATION_FIXTURES.md` | Test fixture documentation with expected outcomes | G-Std |

### 2.5 Validator Script (1)

| # | Path | Purpose | Governance |
|---|------|---------|------------|
| S1 | `scripts/verify.py` | Schema validation and fixture test runner | G-Std |

### 2.6 Files NOT Created or Modified

| Path | Reason not touched |
|------|-------------------|
| Any file in IEF-Program, IEF-Protocol, IEF-Runners, IEF-Adapters, IEF-Knowledge | This cycle targets IEF-Operations only; supporting repo changes require separate triggers |
| `schemas/workflow.schema.json` | Workflows are not affected by verification in v0 |
| `schemas/task.schema.json` | Task schema is not modified; verification operates within existing `review_pending` state |
| `schemas/run.schema.json` | Run schema is not modified; verification events are ledger entries, not run state changes |
| Any CI configuration | No CI enforcement in this cycle |
| Any runtime code beyond `scripts/verify.py` | No runtime implementation in this cycle |

---

## 3. Minimal Verifier Interface

The verification module exposes exactly **3 functions**. These are interface contracts, implemented in `scripts/verify.py`.

### 3.1 Function Signatures

```python
# Function 1: Validate a VerificationRequest against the schema
def validate_request(request: dict) -> tuple[bool, list[str]]:
    """
    Validate a VerificationRequest against the schema.
    
    Returns:
        (valid, errors) where valid is True if instance matches schema,
        and errors is a list of error messages.
    """

# Function 2: Validate a VerificationResult against the schema
def validate_result(result: dict) -> tuple[bool, list[str]]:
    """
    Validate a VerificationResult against the schema.
    Enforces result/severity constraints at dimension and overall levels.
    
    Returns:
        (valid, errors)
    """

# Function 3: Validate a VerificationEvidence against the schema
def validate_evidence(evidence: dict) -> tuple[bool, list[str]]:
    """
    Validate a VerificationEvidence against the schema.
    
    Returns:
        (valid, errors)
    """
```

### 3.2 Additional Helper Functions

```python
# Check result/severity constraint at dimension level
def check_result_severity_constraint(result: str, severity: str) -> tuple[bool, str]:
    """
    Check the result/severity constraint:
    - pass -> info only
    - fail -> error or critical
    - conditional -> warning only
    - skipped -> info only
    
    Returns:
        (valid, reason)
    """

# Check overall result/severity constraint
def check_overall_constraint(overall_result: str, overall_severity: str) -> tuple[bool, str]:
    """
    Check the overall result/severity constraint:
    - pass -> info
    - fail -> error or critical
    - conditional -> warning
    - blocked -> any (warning typical)
    
    Returns:
        (valid, reason)
    """

# Run a single fixture test
def run_fixture_test(fixture_path: Path) -> tuple[bool, str]:
    """
    Run a single fixture test.
    
    Returns:
        (passed, message)
    """

# Run all fixture tests
def run_all_fixtures(fixtures_dir: Optional[Path] = None) -> tuple[int, int]:
    """
    Run all fixture tests in the given directory.
    
    Returns:
        (passed_count, failed_count)
    """
```

### 3.3 CLI Usage

```bash
# Validate a VerificationRequest
python scripts/verify.py --validate-request <path>

# Validate a VerificationResult
python scripts/verify.py --validate-result <path>

# Validate a VerificationEvidence
python scripts/verify.py --validate-evidence <path>

# Validate a ledger entry
python scripts/verify.py --validate-ledger <path>

# Run all fixture tests
python scripts/verify.py --run-fixtures

# Run fixtures from a custom directory
python scripts/verify.py --run-fixtures --fixtures-dir <path>
```

---

## 4. Schema Details

### 4.1 VerificationRequest (F1)

**Purpose:** Defines the input to the verification module. Contains all evidence and context needed to perform verification.

**Required fields:**
- `verification_id` (UUID)
- `task_id` (UUID)
- `run_id` (UUID)
- `governance_profile` (G-Lite, G-Std, G-Full)
- `artifact_refs` (array of URIs)
- `allowed_files` (array of strings)
- `forbidden_actions` (array of strings)

**Conditional requirements:**
- G-Std and G-Full require `review_result` and `ledger_entries`

**Key design decisions:**
- `requested_dimensions` allows Controller to authorize skipping dimensions
- `retry_count` tracks previous verification attempts
- `metadata` allows arbitrary extension

### 4.2 VerificationResult (F2)

**Purpose:** Defines the output of the verification module. Contains dimension-level results, overall aggregation, and closure status.

**Required fields:**
- `verification_id`, `task_id`, `run_id` (UUIDs)
- `verification_timestamp` (ISO 8601)
- `verifier` (string)
- `governance_profile` (G-Lite, G-Std, G-Full)
- `dimensions_verified` (array of dimension results)
- `overall_result` (pass, fail, conditional, blocked)
- `overall_severity` (info, warning, error, critical)
- `retry_eligible` (boolean)
- `retry_count` (integer)
- `closure_criteria_met` (boolean)
- `parent_artifact` (URI)

**Result/severity constraints (from G6-A Schema Fix):**

At dimension level:
- `result == "pass"` → `severity` MUST be `"info"`
- `result == "fail"` → `severity` MUST be `"error"` or `"critical"`
- `result == "conditional"` → `severity` MUST be `"warning"`
- `result == "skipped"` → `severity` MUST be `"info"`

At overall level:
- `overall_result == "pass"` → `overall_severity` MUST be `"info"`
- `overall_result == "fail"` → `overall_severity` MUST be `"error"` or `"critical"`
- `overall_result == "conditional"` → `overall_severity` MUST be `"warning"`
- `overall_severity == "critical"` → `retry_eligible` MUST be `false`

**Conditional requirements:**
- `overall_result == "blocked"` requires `blocked_reason`

**Key design decisions:**
- `dimensions_verified` allows partial verification (some dimensions skipped)
- `decision_by` and `decided_at` track Controller acknowledgment
- `metadata` allows arbitrary extension

### 4.3 VerificationEvidence (F3)

**Purpose:** Defines structured evidence supporting a verification dimension result.

**Required fields:**
- `evidence_id` (UUID)
- `verification_id` (UUID)
- `dimension` (functional, governance_compliance, boundary, stress)
- `evidence_type` (artifact, ledger_event, execution_log, scope_comparison, review_result, test_result, stress_output)
- `source` (string)
- `content` (object)
- `collected_at` (ISO 8601)

**Optional fields:**
- `artifact_ref` (URI)
- `integrity_hash` (SHA-256)

### 4.4 Ledger Entry Extension (M1)

**Purpose:** Add 4 verification event types to the Operations ledger.

**New event types:**
1. `verification_requested` — Task enters `review_pending` and verification is required
2. `verification_started` — Verification process begins
3. `verification_completed` — Verification finishes with any result
4. `verification_failed` — Verification cannot complete (infra failure, timeout)

**Conditional payload constraints:**

For `verification_requested`:
- Required: `verification_id`, `governance_profile`, `requested_dimensions`

For `verification_started`:
- Required: `verification_id`, `verifier`

For `verification_completed`:
- Required: `verification_id`, `overall_result`, `dimensions_verified`

For `verification_failed`:
- Required: `verification_id`, `failure_reason`
- Severity MUST be `error` or `critical`

**Ledger event sequence example:**

```
seq 0:  run_prepared
seq 1:  run_started
seq 2:  progress (implementation work)
seq 3:  artifact_produced
seq 4:  run_completed
seq 5:  review_requested
seq 6:  review_completed (G4 code review)
seq 7:  verification_requested      ← NEW
seq 8:  verification_started          ← NEW
seq 9:  verification_completed        ← NEW (pass/fail/conditional/blocked)
        — OR —
seq 9:  verification_failed           ← NEW (infra failure, timeout)
```

---

## 5. Aggregation Rules

### 5.1 Overall Result Aggregation

| Condition | `overall_result` |
|-----------|------------------|
| All dimensions `pass` | `pass` |
| Any dimension `fail` | `fail` |
| No `fail`, any `conditional` | `conditional` |
| Any `blocked` (missing evidence), no `fail` | `blocked` |
| All dimensions `skipped` | `blocked` |

### 5.2 Overall Severity Escalation

| Condition | `overall_severity` |
|-----------|---------------------|
| All dimensions `info` | `info` |
| Any dimension `warning`, no `error`/`critical` | `warning` |
| Any dimension `error`, no `critical` | `error` |
| Any dimension `critical` | `critical` |

---

## 6. Governance Profile Requirements

| Profile | Minimum Evidence Required |
|---------|---------------------------|
| G-Lite | `artifact_refs` non-empty, `allowed_files` non-empty, `forbidden_actions` non-empty |
| G-Std | G-Lite + `review_result` present with `decision`, `ledger_entries` non-empty |
| G-Full | G-Std + `ledger_entries` contains events for all 7 gates (G1-G7), `context_refs` non-empty |

---

## 7. Fixture Tests

### 7.1 Test Strategy

All tests are **fixture-based**: JSON input fixtures produce expected JSON output results. No runtime verifier daemon is required.

Tests validate that:
1. Input fixtures validate against `verification_request.schema.json`
2. Output fixtures validate against `verification_result.schema.json`
3. Aggregation rules produce correct `overall_result` and `overall_severity`
4. Conditional constraints enforce required fields
5. Result/severity cross-field constraints are satisfied
6. Dedup rules reject duplicate verification_ids

### 7.2 Test Matrix

| Test ID | Fixture File | Profile | Expected Result | Validates |
|---------|--------------|---------|-----------------|-----------|
| T1 | `glite_pass.json` | G-Lite | pass (info) | Happy path, minimal evidence |
| T2 | `glite_fail_boundary.json` | G-Lite | fail (critical) | Boundary violation, no retry |
| T3 | `gstd_pass.json` | G-Std | pass (info) | Full 4-dimension pass |
| T4 | `gstd_conditional_stress.json` | G-Std | conditional (warning) | Partial pass, retry eligible |
| T5 | `gfull_fail_governance.json` | G-Full | fail (error) | Missing independent review |
| T6 | `blocked_missing_input.json` | G-Std | blocked (warning) | Evidence gap, retry eligible |
| T7 | `retry_eligible_timeout.json` | Any | verification_failed event | Infrastructure failure |

### 7.3 Running Tests

```bash
cd D:\code\IEF\IEF-Operations
python scripts/verify.py --run-fixtures
```

---

## 8. Forbidden Actions — 14 Explicit Prohibitions

Carried forward from G5-A Section 7. Each prohibition is mapped to a testable enforcement:

| # | Forbidden action | Enforcement mechanism | Test fixture |
|---|-----------------|----------------------|-------------|
| F1 | Merge PRs | Verification agent has no GitHub write token; result schema has no `merge` field | N/A (structural) |
| F2 | Close issues | Same as F1 | N/A (structural) |
| F3 | Modify files outside allowed_files | VerificationRequest.allowed_files checked; B-1 criterion | T2 (boundary fail) |
| F4 | Authorize Stage H transitions | No state transition authority in verifier interface | N/A (structural) |
| F5 | Self-accept its own verification | `decision_by` must be Controller, not verifier | T3, T5 |
| F6 | Expand verification scope | `requested_dimensions` is input-bounded; verifier cannot add dimensions | T1 |
| F7 | Invent verification criteria | `criteria_checked` values are contract-defined, not runtime-generated | All |
| F8 | Mutate governance profiles | `governance_profile` is read-only input | All |
| F9 | Modify Operations schemas | Verification consumes schemas; does not write them | N/A (structural) |
| F10 | Trigger autonomous retries | `retry_eligible` is a flag, not a command; Controller authorizes retry | T4, T6, T7 |
| F11 | Execute runners | No runner invocation in verifier interface | N/A (structural) |
| F12 | Modify Protocol contracts | Verification reads Protocol objects; does not write them | N/A (structural) |
| F13 | Bypass ledger rules | Verification events follow same append-only, immutable, ordered rules | T7 |
| F14 | Operate without directive | `verification_requested` event must exist before `verification_started` | T8 |

---

## 9. Rollback Pointer

### 9.1 What can be rolled back

| Component | Rollback mechanism | Scope |
|-----------|-------------------|-------|
| **Ledger entries** | Cannot be deleted (append-only). Corrections use `ledger_correction` event type with `corrected_entry_id`. | One correction entry per corrected event |
| **VerificationResult** | A `ledger_correction` entry can mark a VerificationResult as superseded. The original entry remains in the ledger. | The correction entry references the original `verification_id` |
| **Task state** | Task state is not modified by verification (verification operates within `review_pending`). No rollback needed. | N/A |
| **Schema changes** | If verification event types are added to `ledger_entry.schema.json` and need rollback, revert the schema file to the previous commit. | Git revert of the schema modification commit |

### 9.2 Rollback procedure

```
Step 1: Identify the verification_id to roll back
Step 2: Create a ledger_correction entry:
  {
    "entry_id": "<new UUID>",
    "task_id": "<original task_id>",
    "run_id": "<original run_id>",
    "event_type": "ledger_correction",
    "sequence": <next sequence>,
    "timestamp": "<now>",
    "corrected_entry_id": "<verification_completed entry_id>",
    "payload": {
      "correction_reason": "<reason for rollback>",
      "superseded_verification_id": "<original verification_id>",
      "rollback_authorized_by": "<Controller identity>"
    }
  }
Step 3: The task remains in review_pending; Controller decides next action
Step 4: If schema rollback needed: git revert <commit> on ledger_entry.schema.json
```

### 9.3 Rollback constraints

- **No deletion** — original verification entries are never deleted
- **No state mutation** — rollback does not change task or run status
- **Controller authorization required** — rollback must include `rollback_authorized_by`
- **One correction per entry** — a correction entry corrects exactly one original entry
- **Chain integrity** — the correction chain is always traceable: original → correction → (optional) re-correction

---

## 10. Review Criteria — What Controller Checks

### 10.1 Pre-acceptance checklist

When the Controller reviews a VerificationResult, the following criteria must be checked:

| # | Criterion | How to check | Fail condition |
|---|-----------|-------------|---------------|
| RC-1 | Result validates against schema | Run `validate_result()` | Schema validation errors |
| RC-2 | All required dimensions present | Check `dimensions_verified` covers all dimensions for the governance profile | Missing dimension for G-Std/G-Full |
| RC-3 | Evidence chain complete | Check `evidence_refs` resolve to valid artifacts | Broken or missing evidence refs |
| RC-4 | Aggregation correct | Verify `overall_result` matches dimension-level results per Section 5.1 rules | Aggregation mismatch |
| RC-5 | Severity correct | Verify `overall_severity` matches dimension-level severities per Section 5.2 rules | Severity mismatch |
| RC-6 | Ledger events present | Check `verification_requested`, `verification_started`, `verification_completed` events exist in ledger | Missing ledger events (G-Std+) |
| RC-7 | No forbidden actions taken | Audit verification agent's execution log for forbidden actions | Forbidden action detected |
| RC-8 | Retry count consistent | Check `retry_count` matches number of previous `verification_completed`/`verification_failed` events for same run | Retry count mismatch |
| RC-9 | Closure criteria evaluated | Check `closure_criteria_met` is correctly computed per G5-A Section 10 | Incorrect closure evaluation |
| RC-10 | Decision authority preserved | `decision_by` is null (pending) or Controller identity (acknowledged); never verifier | Verifier self-accepted |

### 10.2 Governance-profile-specific review criteria

| Profile | Additional review criteria |
|---------|---------------------------|
| G-Lite | RC-1 through RC-5 sufficient |
| G-Std | + RC-6 (ledger events), RC-8 (retry count), RC-9 (closure) |
| G-Full | + RC-7 (forbidden actions audit), RC-10 (decision authority), independent review of VerificationResult by a second reviewer |

### 10.3 Controller decision options

After review, Controller produces one of:

| Decision | Meaning | Next action |
|----------|---------|-------------|
| `accept` | VerificationResult is correct and complete | Task may proceed to completion |
| `accept_with_conditions` | Result accepted but with documented concerns | Task proceeds; conditions recorded in ledger |
| `reject` | VerificationResult is incorrect or incomplete | Re-verification required (new verification_id) |
| `escalate` | VerificationResult reveals critical issue | Task escalated; no completion |

---

## 11. Dependencies

This implementation has no runtime dependencies beyond Python 3.8+ and the optional `jsonschema` package.

### 11.1 Schema Dependencies

- `verification_request.schema.json` references `ledger_entry.schema.json` (for `ledger_entries` array items)
- `verification_result.schema.json` is self-contained
- `verification_evidence.schema.json` is self-contained
- `ledger_entry.schema.json` is extended with verification event types (no external references)

### 11.2 Python Dependencies

- `jsonschema` (optional) — for full JSON Schema draft 2020-12 validation
- If not installed, the validator falls back to basic required-field checks

---

## 12. Boundaries and Non-Goals

### 12.1 Hard boundaries

- [x] This implementation is **minimal skeleton only** — no runtime daemon
- [x] No autonomous verifier agent created or deployed
- [x] No CI enforcement introduced
- [x] No production integration
- [x] No new repositories created
- [x] No cross-repo mutations performed
- [x] No issue closure or PR merge
- [x] No Stage H transition authorized

### 12.2 Non-goals

- Implementation of verification runtime or daemon
- Deployment of verification agent
- CI/CD pipeline integration for automatic verification
- Verification of this implementation itself (that is Controller's review gate)
- Production use of verification schemas
- Modification of task.schema.json or run.schema.json

### 12.3 What this implementation enables

When Controller approves this implementation:
- IEF-Operations gains 3 new JSON Schema files for verification
- IEF-Operations ledger_entry.schema.json gains 4 verification event types
- Test fixtures exist for validation before any runtime implementation
- An OpenAPI spec document enables machine-readable discovery
- A2A-compatible AgentCard describes verification capabilities
- Supporting repos can reference verification schemas in their own contracts

---

## 13. Summary

This Verification Module Minimal Implementation includes:

1. **3 new schema files** (verification_request, verification_result, verification_evidence)
2. **1 modified schema file** (ledger_entry with 4 verification event types)
3. **7 fixture tests** covering pass/fail/conditional/blocked/retry across all governance profiles
4. **1 validator script** for schema validation and fixture test execution
5. **3 documentation files** (this document, fixture docs, OpenAPI spec)
6. **Result/severity constraint enforcement** as specified in G6-A Schema Fix
7. **14 forbidden actions** with enforcement mechanisms and test mappings
8. **10-point pre-acceptance checklist** with profile-specific additions

**Result:** Minimal skeleton implementation complete. No runtime daemon, no CI enforcement, no production integration. Schemas, fixtures, and validator ready for Controller review.

---

*Produced by ief-operator executing one bounded Stage G G7-A cycle from Controller authorization (G6 FINAL REVIEW RESULT: G7 UNBLOCKED). Schema creation, fixture tests, validator script, and documentation complete. No code changes beyond scripts/verify.py, no cross-repo mutations, no runtime deployment.*
