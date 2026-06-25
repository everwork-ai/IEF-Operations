# IEF Verification Module — Minimal Implementation

> Independent validation authority for produced digital employees.  
> Skeleton implementation: schemas, validator interface, fixture tests.  
> No production daemon. No CI enforcement. No runtime integration.  
> Governance: G-Std | Schema: JSON Schema draft 2020-12

---

## 1. Purpose

The Verification Module validates that a digital employee (runner output) is fit for governed work before acceptance into the Operations ledger and Knowledge base. It sits between **Review** and **Knowledge Extraction** in the IEF core loop:

```
Request → Operations Task → Governance Policy → Knowledge Context
       → Runner Execution → Protocol Status/Artifact → Review
       → **Verification** → Knowledge Extraction → Better Future Execution
```

Verification is **not** review. Review assesses code quality. Verification validates end-to-end fitness: can the digital employee receive work, execute within boundaries, produce valid artifacts, and behave under pressure?

---

## 2. Responsibilities

### 2.1 Core responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| R1 | Functional verification | Validate digital employee can receive, execute, and deliver work |
| R2 | Governance compliance verification | Validate digital employee follows assigned governance profile |
| R3 | Boundary verification | Validate digital employee stays within authorized scope |
| R4 | Stress verification | Validate digital employee behavior under pressure |

### 2.2 Non-responsibilities

The Verification Module does **not**:
- Execute runners or produce artifacts
- Make governance decisions (reports evidence; Controller decides)
- Mutate production state
- Close issues or merge PRs
- Authorize Stage H transitions
- Operate autonomously without Controller oversight
- Implement verification runtime or daemon

---

## 3. Verifier Interface

### 3.1 Function signatures

```python
# Validate a VerificationRequest against the schema
def validate_request(request: dict) -> tuple[bool, list[str]]

# Validate a VerificationResult against the schema (enforces constraints)
def validate_result(result: dict) -> tuple[bool, list[str]]

# Validate a VerificationEvidence against the schema
def validate_evidence(evidence: dict) -> tuple[bool, list[str]]

# Check dimension-level result/severity constraint
def check_result_severity_constraint(result: str, severity: str) -> tuple[bool, str]

# Check overall-level result/severity constraint
def check_overall_constraint(overall_result: str, overall_severity: str) -> tuple[bool, str]

# Run fixture tests
def run_fixture_test(fixture_path: Path) -> tuple[bool, str]
def run_all_fixtures(fixtures_dir: Optional[Path] = None) -> tuple[int, int]
```

### 3.2 CLI usage

```bash
python scripts/verify.py --validate-request <path>
python scripts/verify.py --validate-result <path>
python scripts/verify.py --validate-evidence <path>
python scripts/verify.py --validate-ledger <path>
python scripts/verify.py --run-fixtures
```

---

## 4. Schema Files

### 4.1 New schemas

| File | Purpose |
|------|---------|
| `schemas/verification_request.schema.json` | Input: evidence and context for verification |
| `schemas/verification_result.schema.json` | Output: dimension-level results with constraints |
| `schemas/verification_evidence.schema.json` | Structured evidence supporting dimension results |

### 4.2 Extended schema

| File | Modification |
|------|-------------|
| `schemas/ledger_entry.schema.json` | +4 verification event types, +4 conditional payload constraints |

**New event types:** `verification_requested`, `verification_started`, `verification_completed`, `verification_failed`

**Total event types:** 22 (original) + 4 = **26**

### 4.3 Result/severity constraint (core invariant)

**Dimension level:**

| result | Allowed severity | Rationale |
|--------|-----------------|-----------|
| `pass` | `info` | No issues; informational only |
| `fail` | `error`, `critical` | Real problem exists |
| `conditional` | `warning` | Non-blocking concern |
| `skipped` | `info` | No findings |

**Overall level:**

| overall_result | Allowed overall_severity |
|----------------|--------------------------|
| `pass` | `info` |
| `fail` | `error`, `critical` |
| `conditional` | `warning` |
| `blocked` | any (typically `warning`) |

**Critical constraint:** `overall_severity == "critical"` → `retry_eligible` MUST be `false`

Enforced via `allOf` conditional blocks in JSON Schema draft 2020-12.

---

## 5. Evidence Model

### 5.1 Evidence types

| Type | Source | Required for |
|------|--------|-------------|
| Artifact evidence | Runner output | All dimensions |
| Ledger evidence | Operations ledger | Governance compliance, boundary |
| Execution log evidence | Runner logs | Functional, stress |
| Scope evidence | Directive / git | Boundary |
| Review evidence | Controller / reviewer | Governance compliance (G-Std+) |
| Test evidence | Test runner | Functional (G-Std+) |
| Stress evidence | Controlled stress run | Stress |

### 5.2 Governance profile requirements

| Profile | Minimum evidence |
|---------|-----------------|
| G-Lite | artifact_refs, allowed_files, forbidden_actions |
| G-Std | G-Lite + review_result + ledger_entries |
| G-Full | G-Std + full gate events (G1-G7) + context_refs |

### 5.3 Evidence chain integrity

Every piece of evidence traces back to:
1. Originating TaskEnvelope (`task_id`)
2. Run that produced it (`run_id`)
3. Ledger entry that recorded it (`entry_id` / `sequence`)
4. ArtifactRef pointing to it (URI)

---

## 6. Verification Dimensions

| Dimension | Purpose | Criteria |
|-----------|---------|----------|
| **Functional** | Can it receive, execute, deliver? | TaskEnvelope parseable, execution completes, artifacts produced, handoff valid |
| **Governance compliance** | Does it follow the assigned profile? | Gate adherence, evidence production, approval checkpoints, no self-acceptance |
| **Boundary** | Does it stay within scope? | File scope, action scope, cross-repo scope, authority scope |
| **Stress** | Behavior under pressure? | Failure recovery, scope creep resistance, token pressure, contradiction handling |

### 6.1 Aggregation rules

**Overall result:**

| Condition | overall_result |
|-----------|----------------|
| All dimensions pass | `pass` |
| Any dimension fail | `fail` |
| No fail, any conditional | `conditional` |
| Missing evidence, no fail | `blocked` |

**Overall severity:**

| Condition | overall_severity |
|-----------|------------------|
| All info | `info` |
| Any warning, no error/critical | `warning` |
| Any error, no critical | `error` |
| Any critical | `critical` |

---

## 7. Ledger Integration

### 7.1 Event sequence

```
seq N:   run_completed
seq N+1: review_completed (G4)
seq N+2: verification_requested      ← NEW
seq N+3: verification_started         ← NEW
seq N+4: verification_completed       ← NEW
         — OR —
seq N+4: verification_failed          ← NEW (infra failure)
```

### 7.2 State machine integration

Verification operates **within** the existing `review_pending` state. No new task states are introduced.

```
running → review_pending → [verification lifecycle events]
                          → completed (if pass)
                          → failed (if fail, no retry)
                          → running (if conditional, retry authorized)
                          → escalated (if cannot proceed)
```

---

## 8. Forbidden Actions — 14 Prohibitions

| # | Forbidden action | Enforcement |
|---|-----------------|-------------|
| F1 | Merge PRs | No GitHub write token; no `merge` field in schema |
| F2 | Close issues | Same as F1 |
| F3 | Modify files outside allowed_files | B-1 criterion checked |
| F4 | Authorize Stage H transitions | No state transition authority |
| F5 | Self-accept its own verification | `decision_by` must be Controller |
| F6 | Expand verification scope | `requested_dimensions` is input-bounded |
| F7 | Invent verification criteria | `criteria_checked` values are contract-defined |
| F8 | Mutate governance profiles | `governance_profile` is read-only input |
| F9 | Modify Operations schemas | Verification consumes schemas; does not write them |
| F10 | Trigger autonomous retries | `retry_eligible` is a flag; Controller authorizes |
| F11 | Execute runners | No runner invocation in interface |
| F12 | Modify Protocol contracts | Reads Protocol objects; does not write |
| F13 | Bypass ledger rules | Same append-only, immutable, ordered rules |
| F14 | Operate without directive | `verification_requested` must precede `verification_started` |

---

## 9. Rollback

| Component | Mechanism |
|-----------|-----------|
| Ledger entries | `ledger_correction` event with `corrected_entry_id` |
| VerificationResult | Correction entry references original `verification_id` |
| Task state | Not modified by verification; no rollback needed |
| Schema changes | `git revert` on the schema modification commit |

Rollback constraints:
- No deletion (append-only)
- No state mutation
- Controller authorization required (`rollback_authorized_by`)
- One correction per entry
- Chain always traceable

---

## 10. Review Criteria

| # | Criterion | How to check |
|---|-----------|-------------|
| RC-1 | Result validates against schema | `validate_result()` |
| RC-2 | All required dimensions present | `dimensions_verified` coverage |
| RC-3 | Evidence chain complete | `evidence_refs` resolve |
| RC-4 | Aggregation correct | Section 6.1 rules |
| RC-5 | Severity correct | Section 6.1 rules |
| RC-6 | Ledger events present | G-Std+ requires verification events |
| RC-7 | No forbidden actions taken | Execution log audit |
| RC-8 | Retry count consistent | Previous verification events count |
| RC-9 | Closure criteria evaluated | `closure_criteria_met` correctness |
| RC-10 | Decision authority preserved | `decision_by` is null or Controller |

---

## 11. Test Fixtures

| Test ID | File | Profile | Expected |
|---------|------|---------|----------|
| T1 | `glite_pass.json` | G-Lite | pass (info) |
| T2 | `glite_fail_boundary.json` | G-Lite | fail (critical) |
| T3 | `gstd_pass.json` | G-Std | pass (info) |
| T4 | `gstd_conditional_stress.json` | G-Std | conditional (warning) |
| T5 | `gfull_fail_governance.json` | G-Full | fail (error) |
| T6 | `blocked_missing_input.json` | G-Std | blocked (warning) |
| T7 | `retry_eligible_timeout.json` | Any | verification_failed event |

**Run:** `python scripts/verify.py --run-fixtures`

**Result (2026-06-21):** 7 passed, 0 failed, 7 total ✅

---

## 12. Dependencies

- Python 3.8+
- `jsonschema` (optional — falls back to basic validation)

No runtime dependencies. No daemon. No CI integration.

---

## 13. Non-Goals

- ❌ No production verifier daemon
- ❌ No CI enforcement
- ❌ No automatic GitHub comments
- ❌ No issue closure or PR merge
- ❌ No stage promotion
- ❌ No runtime deployment
- ❌ No modification of task.schema.json or run.schema.json

---

*Produced by ief-operator. Stage G G7-A minimal skeleton. One bounded cycle.*
