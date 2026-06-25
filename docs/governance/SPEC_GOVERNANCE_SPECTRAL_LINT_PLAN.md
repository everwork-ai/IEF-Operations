# Spec Governance Spectral Lint — Scoping Plan

> **Status:** SCOPING ONLY — no CI enforcement, no build gates, no spec mutations  
> **Created:** 2026-06-25  
> **Owner:** IEF Coordinator (relay from Controller directive)  
> **Directive:** IEF-Operations#4 — Spec Governance Spectral Lint Scope  

---

## 1. Lintable Spec Inventory

### 1.1 IEF-Operations (`everwork-ai/IEF-Operations`)

This is the primary governance repo with the highest concentration of machine-readable specs.

**JSON Schemas (`schemas/*.json`) — 9 files:**

| File | Draft | Description |
|------|-------|-------------|
| `run.schema.json` | 2020-12 | Run lifecycle and event sequence |
| `task.schema.json` | 2020-12 | Task lifecycle and state management |
| `workflow.schema.json` | 2020-12 | Multi-step task graph and approval checkpoints |
| `ledger_entry.schema.json` | 2020-12 | Immutable ledger entry for event sourcing |
| `verification_request.schema.json` | 2020-12 | Verification module input contract |
| `verification_result.schema.json` | 2020-12 | Verification module output (V2 hardened) |
| `verification_evidence.schema.json` | 2020-12 | Evidence artifacts for verification decisions |
| `IKE_READ_MODEL_VERSION_1.json` | 2020-12 | External consumer read model contract |
| `RESULT_SCHEMA_V2.json` | 2020-12 | Hardened verification result with replay support |

**OpenAPI / YAML Specs — 2 files:**

| File | Format | Description |
|------|--------|-------------|
| `docs/VERIFICATION_SPEC_V0.yaml` | OAS 3.1.0 | Verification module specification (planning-only) |
| `docs/governance/IEF_TO_IKE_DATA_CONTRACT_OAS31.yaml` | OAS 3.1.0 | IEF → IKE read-only data contract |

**Lint target file patterns:**
- `schemas/*.json`
- `docs/**/*.yaml` (where YAML contains OpenAPI or structured specs)
- Excludes: `*.md` files (governance prose, not machine-lintable)

### 1.2 IEF-Adapters (`everwork-ai/IEF-Adapters`)

**OpenAPI Contracts (`contracts/*.yaml`) — 1 file:**

| File | Format | Description |
|------|--------|-------------|
| `contracts/ADAPTER_CONTRACT_V0.yaml` | OAS 3.1.0 | Adapter behavior contract — event translation, host surface declarations, error handling |

**Lint target file patterns:**
- `contracts/*.yaml`
- `specs/*.yaml` (future)

### 1.3 IEF-Runners (`everwork-ai/IEF-Runners`)

**OpenAPI Contracts (`contracts/*.yaml`) — 1 file:**

| File | Format | Description |
|------|--------|-------------|
| `contracts/RUNNER_INTERFACE_V0.yaml` | OAS 3.1.0 | Runner interface contract — identity, acceptance, lifecycle, artifacts, errors |

**Lint target file patterns:**
- `contracts/*.yaml`
- `specs/*.yaml` (future)

### 1.4 IEF-Knowledge (`everwork-ai/IEF-Knowledge`)

**No lintable specs.** The repo contains runtime configuration (`config.yaml`) and session indexing state (`index.json`), neither of which are IEF contracts or governance specs. IEF-Knowledge is a consumer-facing knowledge store, not a contract publisher.

**Lint target file patterns:**
- `contracts/*.yaml` (future, if Knowledge publishes contracts)
- `specs/*.yaml` (future)

### 1.5 Consolidated Inventory

| Repo | JSON Schemas | OAS/YAML Specs | Total Lintable |
|------|-------------|---------------|----------------|
| IEF-Operations | 9 | 2 | 11 |
| IEF-Adapters | 0 | 1 | 1 |
| IEF-Runners | 0 | 1 | 1 |
| IEF-Knowledge | 0 | 0 | 0 |
| **Total** | **9** | **4** | **13** |

---

## 2. Proposed Baseline Spectral Rules

### 2.1 Rule Categories

The baseline ruleset is organized into four categories, each targeting a specific quality dimension of IEF specs.

**Category A — Schema Validity (JSON Schema files)**

These rules validate that JSON Schema files are well-formed and follow IEF conventions.

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `ief-schema-001` | error | File must declare `$schema` pointing to a recognized JSON Schema draft (2020-12 preferred) |
| `ief-schema-002` | error | File must declare `$id` with a valid `https://ief.dev/schemas/` URI |
| `ief-schema-003` | error | File must declare `title` (non-empty string) |
| `ief-schema-004` | error | File must declare `description` (non-empty string) |
| `ief-schema-005` | warning | File must declare `type: "object"` at root |
| `ief-schema-006` | warning | File must declare `required` array with at least one entry |
| `ief-schema-007` | info | File should use `additionalProperties: false` for strict contracts |
| `ief-schema-008` | warning | All properties should have `description` fields |
| `ief-schema-009` | error | `$ref` targets must be resolvable (sibling files or inline) |
| `ief-schema-010` | info | Enum fields should have at least 2 values |

**Category B — OpenAPI / YAML Contract Validity**

These rules validate that OpenAPI 3.1 specs are well-formed and follow IEF conventions.

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `ief-oas-001` | error | File must declare `openapi: 3.1.0` |
| `ief-oas-002` | error | `info.title` must be present and non-empty |
| `ief-oas-003` | error | `info.version` must be present and follow semver pattern (x.y.z) |
| `ief-oas-004` | warning | `info.description` must be present and non-empty |
| `ief-oas-005` | info | `info.license` should be present |
| `ief-oas-006` | info | `info.contact` should be present |
| `ief-oas-007` | warning | `components.schemas` must be non-empty (specs without schemas are unusual) |
| `ief-oas-008` | error | All `$ref` pointers in `components.schemas` must resolve |
| `ief-oas-009` | warning | `paths` or `tags` should be present (empty specs are suspicious) |
| `ief-oas-010` | info | `x-ief-metadata` extension should be present for frozen contracts |

**Category C — Naming Conventions**

These rules enforce consistent naming across all IEF specs.

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `ief-naming-001` | warning | Schema filenames must use `kebab-case.json` or `kebab-case.yaml` (exceptions: `RESULT_SCHEMA_V2.json`, `IKE_READ_MODEL_VERSION_1.json` — grandfathered) |
| `ief-naming-002` | warning | Schema property names must use `snake_case` |
| `ief-naming-003` | warning | Schema definition names (in `components.schemas`) must use `PascalCase` |
| `ief-naming-004` | info | Enum values should use `snake_case` or `kebab-case` consistently within a schema |
| `ief-naming-005` | warning | Version identifiers in filenames must follow pattern: `*_V{N}.*` or `*_VERSION_{N}.*` |

**Category D — Cross-Reference and Consistency**

These rules validate cross-spec consistency and reference integrity.

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `ief-xref-001` | error | All `$ref` references to sibling files must resolve to existing files |
| `ief-xref-002` | warning | Version fields across related schemas should be consistent |
| `ief-xref-003` | info | `required` fields should reference properties that exist in the same schema |
| `ief-xref-004` | warning | Schemas referenced from OAS specs should be valid JSON Schema |

### 2.2 Example Ruleset Structure (`.spectral.yaml`)

```yaml
# .spectral.yaml — IEF Baseline Spectral Ruleset
# This is an EXAMPLE for scoping purposes. Not deployed.

extends:
  - spectral:oas  # Built-in OpenAPI rules
  - spectral:json-schema  # Built-in JSON Schema rules (if available)

rules:
  # === Category A: Schema Validity ===
  ief-schema-001-schema-declaration:
    description: "JSON Schema files must declare $schema"
    severity: error
    given: "$"
    then:
      field: "$schema"
      function: truthy

  ief-schema-002-id-uri:
    description: "JSON Schema files must declare $id with ief.dev URI"
    severity: error
    given: "$"
    then:
      field: "$id"
      function: pattern
      functionOptions:
        match: "^https://ief\\.dev/schemas/"

  ief-schema-003-title-required:
    description: "JSON Schema files must declare title"
    severity: error
    given: "$"
    then:
      field: "title"
      function: truthy

  ief-schema-004-description-required:
    description: "JSON Schema files must declare description"
    severity: error
    given: "$"
    then:
      field: "description"
      function: truthy

  # === Category B: OpenAPI Contract Validity ===
  ief-oas-001-version:
    description: "OpenAPI specs must declare openapi: 3.1.0"
    severity: error
    given: "$"
    then:
      field: "openapi"
      function: pattern
      functionOptions:
        match: "^3\\.1\\.0$"

  ief-oas-002-info-title:
    description: "OpenAPI specs must declare info.title"
    severity: error
    given: "$.info"
    then:
      field: "title"
      function: truthy

  ief-oas-003-semver:
    description: "info.version must follow semver"
    severity: error
    given: "$.info"
    then:
      field: "version"
      function: pattern
      functionOptions:
        match: "^\\d+\\.\\d+\\.\\d+"

  # === Category C: Naming Conventions ===
  ief-naming-003-pascal-schemas:
    description: "Schema definitions must use PascalCase"
    severity: warning
    given: "$.components.schemas"
    then:
      field: "@key"
      function: pattern
      functionOptions:
        match: "^[A-Z][a-zA-Z0-9]*$"

  # === Category D: Cross-Reference ===
  ief-xref-001-ref-resolution:
    description: "$ref targets must resolve"
    severity: error
    given: "$..$ref"
    then:
      function: schema
      functionOptions:
        schema:
          type: string
          pattern: "^(#|\\.\\./|https?://)"
```

### 2.3 Severity Legend

| Level | Meaning | CI Behavior (when enabled) |
|-------|---------|---------------------------|
| `error` | Violation must be fixed before merge | Blocks PR merge |
| `warning` | Violation should be addressed | PR annotation, non-blocking |
| `info` | Suggestion for improvement | Logged only, no annotation |
| `hint` | Style preference, optional | Logged only, no annotation |

---

## 3. CI Integration Approach

### 3.1 GitHub Actions Workflow Structure

The recommended approach is a **reusable workflow** in IEF-Operations that each repo can call.

```yaml
# .github/workflows/spectral-lint.yml (EXAMPLE — not deployed)
name: Spectral Lint

on:
  pull_request:
    paths:
      - 'schemas/**'
      - 'contracts/**'
      - 'specs/**'
      - 'docs/**/*.yaml'
  push:
    branches: [main]
    paths:
      - 'schemas/**'
      - 'contracts/**'
      - 'specs/**'
      - 'docs/**/*.yaml'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Spectral
        uses: stoplightio/spectral-action@latest
        with:
          file_glob: "schemas/*.json contracts/*.yaml specs/*.yaml docs/**/*.yaml"
          spectral_ruleset: ".spectral.yaml"

      - name: Run Spectral
        run: |
          npx @stoplight/spectral-cli lint \
            --ruleset .spectral.yaml \
            --format github-actions \
            "schemas/*.json" \
            "contracts/*.yaml" \
            "specs/*.yaml" \
            "docs/**/*.yaml"
```

### 3.2 Multi-Repo Matrix Strategy

For cross-repo linting from a single workflow (e.g., in IEF-Operations or a central IEF-Program repo):

```yaml
jobs:
  lint-matrix:
    strategy:
      matrix:
        repo:
          - name: IEF-Operations
            patterns: "schemas/*.json docs/**/*.yaml"
          - name: IEF-Adapters
            patterns: "contracts/*.yaml"
          - name: IEF-Runners
            patterns: "contracts/*.yaml"
    steps:
      - uses: actions/checkout@v4
        with:
          repository: "everwork-ai/${{ matrix.repo.name }}"
      - name: Lint ${{ matrix.repo.name }}
        run: |
          npx @stoplight/spectral-cli lint \
            --ruleset .spectral.yaml \
            ${{ matrix.repo.patterns }}
```

### 3.3 Local Pre-Commit Hook Option

For developer local validation before pushing:

```bash
#!/bin/bash
# .git/hooks/pre-commit (or via lefthook/husky)
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(json|yaml)$' | grep -E '(schemas|contracts|specs|docs)/')
if [ -n "$FILES" ]; then
  npx @stoplight/spectral-cli lint --ruleset .spectral.yaml $FILES
fi
```

### 3.4 Spectral CLI Invocation Patterns

| Context | Command |
|---------|---------|
| Local, all specs | `spectral lint --ruleset .spectral.yaml "schemas/*.json" "contracts/*.yaml" "docs/**/*.yaml"` |
| Local, single file | `spectral lint --ruleset .spectral.yaml schemas/run.schema.json` |
| CI, JSON output | `spectral lint --ruleset .spectral.yaml --format json --output results.json ...` |
| CI, GitHub Actions | `spectral lint --ruleset .spectral.yaml --format github-actions ...` |
| Dry-run / report | `spectral lint --ruleset .spectral.yaml --format pretty ... 2>&1 \| tee lint-report.txt` |

### 3.5 Custom Ruleset Packaging

The `.spectral.yaml` ruleset file should live at the root of IEF-Operations and be referenceable by other repos via:
- Git submodule pointing to IEF-Operations
- Published npm package (`@ief/spectral-rules`) — future option
- Direct copy with version pinning — simplest initial approach
- Shared ruleset URL fetched at CI time

---

## 4. Failure Behavior (Phased)

### 4.1 Phase 0: Report-Only

- Spectral runs manually or in a non-blocking CI job
- Results logged to a file or CI artifact
- No PR annotations, no status checks
- Purpose: establish baseline violation count
- Duration: 1–2 weeks

### 4.2 Phase 1: Warning Annotations

- Spectral runs on every PR touching spec files
- Violations appear as PR review comments (warning level)
- Status check is **non-blocking** (shows as "pending" or "success" regardless)
- Purpose: visibility without disruption
- Duration: 2–4 weeks

### 4.3 Phase 2: Required Check (New Specs Only)

- Spectral runs as a required status check
- Only **new or modified** spec files must pass
- Existing unchanged specs are exempt (via suppression file)
- `error` severity blocks merge; `warning` does not
- Purpose: prevent new violations while grandfathering existing
- Duration: 4–8 weeks

### 4.4 Phase 3: Full Required Check

- All spec files must pass (suppressions sunset)
- Both new and existing specs enforced
- `error` severity blocks merge
- Purpose: full compliance
- Timeline: after baseline violations are resolved

### 4.5 Phase Transition Criteria

| Transition | Criteria |
|-----------|----------|
| 0 → 1 | Baseline violation count documented; ruleset stable for 1 week |
| 1 → 2 | No new violations introduced in 2 weeks; team familiar with ruleset |
| 2 → 3 | All baseline violations resolved or have documented sunset plan |

---

## 5. Adoption Phases

### 5.1 Phase Overview

| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| **0 — Scoping** (current) | This document. Inventory and rule design. | 1 day |
| **1 — Baseline Ruleset + CI Scaffold** | Create `.spectral.yaml`, validate rules against all 13 specs, CI workflow skeleton (disabled/non-blocking). | 2–3 days |
| **2 — Report Mode Across All Repos** | Enable Spectral in report-only mode across IEF-Operations, IEF-Adapters, IEF-Runners. Document baseline violations. | 1–2 days |
| **3 — Warning Mode with PR Annotations** | Enable PR annotations (non-blocking). Monitor for false positives. Tune rules. | 1 week monitoring |
| **4 — Required Check for New/Changed Specs** | Enable required check for `paths` matching PR diffs. Grandfather existing specs. | 2–3 days setup |
| **5 — Full Enforcement** | All specs must pass. Suppressions sunset. Baseline violations resolved. | Ongoing remediation |

### 5.2 Effort Breakdown

**Phase 1 (Baseline Ruleset):**
- Write `.spectral.yaml` ruleset: 4–6 hours
- Test against all 13 spec files: 2 hours
- Tune false positives: 2–4 hours
- CI workflow scaffold: 2 hours

**Phase 2 (Report Mode):**
- Enable CI across 3 repos: 1 hour per repo
- Baseline audit and violation documentation: 4 hours
- Write suppression file for known violations: 2 hours

**Phase 3 (Warning Mode):**
- Configure GitHub Actions annotations: 2 hours
- Monitor and triage false positives: ongoing (1 week)

**Phase 4 (Required Check for New Specs):**
- Configure path-based required checks: 2 hours
- Write suppression file for grandfathered specs: 2 hours
- Document process for new spec authors: 2 hours

**Phase 5 (Full Enforcement):**
- Remediation work per violation (see Section 8): variable
- Suppression sunset: 1 hour per batch

---

## 6. Avoiding Blockage of Existing Merged Contracts

### 6.1 Grandfathering Strategy

Existing merged contracts are **frozen at their current state** and should not be broken by new lint rules. The strategy:

1. Run Spectral in report-only mode against all existing specs
2. Document every violation with a rationale (accepted risk, known deviation, etc.)
3. Create a suppression file listing each accepted violation
4. Existing specs pass CI as long as their suppressions are active
5. New specs or modifications must pass without suppressions

### 6.2 Suppression File Approach (`.spectral-suppressions.yaml`)

Spectral supports a suppressions file that exempts specific violations:

```yaml
# .spectral-suppressions.yaml (EXAMPLE)
# Each entry: file path + rule ID + optional justification

suppressions:
  # IEF-Operations schemas — naming convention grandfathered
  - path: "schemas/IKE_READ_MODEL_VERSION_1.json"
    rule: "ief-naming-001"
    reason: "Legacy naming — UPPER_SNAKE_CASE predates kebab-case convention"

  - path: "schemas/RESULT_SCHEMA_V2.json"
    rule: "ief-naming-001"
    reason: "Legacy naming — UPPER_SNAKE_CASE predates kebab-case convention"

  # VERIFICATION_SPEC_V0 — empty paths is intentional
  - path: "docs/VERIFICATION_SPEC_V0.yaml"
    rule: "ief-oas-009"
    reason: "Verification operates within lifecycle, not as HTTP service. Empty paths is by design."

  # Cross-repo references may not resolve in isolated lint
  - path: "docs/VERIFICATION_SPEC_V0.yaml"
    rule: "ief-xref-001"
    reason: "References sibling schemas via relative path; may not resolve in CI checkout"
```

### 6.3 Suppression Granularity

Suppressions support three levels of granularity:

| Level | Syntax | Use Case |
|-------|--------|----------|
| **Per-file, per-rule** | `path: "file.yaml"`, `rule: "rule-id"` | Preferred — most specific |
| **Per-file, all rules** | `path: "file.yaml"` | For specs known to have many accepted deviations |
| **Per-rule, all files** | `rule: "rule-id"` | For rules not yet enforced across any repo |

### 6.4 Baseline Compliance Exceptions

For violations that are **by design** (not technical debt):

- Document the rationale in the suppression file `reason` field
- Link to the governing spec or Controller decision that authorized the deviation
- Mark as `permanent: true` in the suppression entry

For violations that are **technical debt** (should be fixed eventually):

- Document the remediation plan
- Set a sunset date in the suppression entry
- Track in a GitHub issue for visibility

### 6.5 Sunset Timeline for Suppressions

| Suppression Type | Sunset Policy |
|-----------------|---------------|
| Naming convention (legacy) | Permanent — grandfathered with documented exception |
| Structural (missing optional fields) | 90 days — fix in next spec revision |
| Cross-reference (unresolvable `$ref`) | 60 days — fix reference or restructure |
| Design deviation (by-design exception) | Permanent — no sunset, documented rationale |

---

## 7. Relationship to Future TypeSpec Migration

### 7.1 Spectral and TypeSpec — Complementary, Not Competitive

Spectral and TypeSpec operate at different layers of the spec lifecycle:

| Dimension | Spectral | TypeSpec |
|-----------|---------|----------|
| **Input** | Existing YAML/JSON spec files | TypeSpec DSL source (`.tsp` files) |
| **Validation** | Lints the output artifact | Generates the output artifact |
| **Scope** | Naming, structure, references, conventions | Type correctness, schema composition |
| **Enforcement** | Post-authoring check | Compile-time check |

### 7.2 Shared Validation Concepts

Both tools enforce these overlapping concerns:

| Concern | Spectral Approach | TypeSpec Approach |
|---------|------------------|-------------------|
| Required fields present | Rule checks `required` array | Compiler enforces model shape |
| Naming conventions | Pattern matching on keys | Decorator-based validation |
| Version consistency | Cross-file rule check | Import/version resolution |
| Reference integrity | `$ref` resolution check | Import resolution at compile |
| Enum validity | Pattern and value checks | Union type enforcement |

### 7.3 What Spectral Validates That TypeSpec Cannot

- **Post-hoc validation of hand-written YAML/JSON:** TypeSpec only validates what it generates. Spectral validates specs regardless of authoring tool.
- **Cross-repo reference integrity:** Spectral can check that `$ref` targets across repos exist (with appropriate tooling).
- **File-level conventions:** Filename patterns, directory placement, metadata extensions.
- **Legacy spec compliance:** Existing specs not (yet) migrated to TypeSpec still need validation.

### 7.4 What TypeSpec Replaces That Spectral Checks

- **Schema composition correctness:** TypeSpec's type system catches structural errors that Spectral rules can only approximate.
- **Model inheritance and mixins:** TypeSpec handles `extends`/`is` composition; Spectral would need complex rules.
- **Code generation consistency:** TypeSpec generates schemas, eliminating a class of "hand-written schema drift" that Spectral would catch.

### 7.5 Dual-Running Strategy During Migration

When IEF begins migrating specs to TypeSpec, the recommended approach:

1. **TypeSpec generates** the canonical YAML/JSON output
2. **Spectral validates** the generated output against IEF-specific conventions (naming, metadata, cross-references)
3. **Both tools run in CI:**
   - TypeSpec compilation must succeed (blocks on type errors)
   - Spectral lint on generated output must pass (blocks on convention violations)
4. **Hand-written specs** (not yet migrated) continue to be validated by Spectral alone
5. **Gradual migration:** As each spec moves to TypeSpec, its Spectral suppressions are removed and TypeSpec takes over structural validation

```
Authoring Flow (during migration):
  [TypeSpec source] → compile → [YAML/JSON output] → Spectral lint → CI pass/fail
  [Hand-written YAML/JSON] → Spectral lint → CI pass/fail
```

### 7.6 Spectral Ruleset Adaptation for TypeSpec

Some Spectral rules become redundant after TypeSpec migration:
- `ief-schema-001` through `ief-schema-006` — TypeSpec guarantees these
- `ief-oas-001` through `ief-oas-006` — TypeSpec OAS emitter guarantees these

Rules that remain valuable:
- `ief-naming-*` — conventions may not be enforced by TypeSpec defaults
- `ief-xref-*` — cross-repo integrity still needs checking
- `ief-oas-010` — `x-ief-metadata` is IEF-specific, not generated by TypeSpec
- Custom domain rules — IEF governance-specific constraints

---

## 8. Expected Cleanup Work for Baseline Compliance

### 8.1 Audit Methodology

This audit is based on inspection of all 13 lintable files across the three repos. Violations are categorized by rule and severity.

### 8.2 Estimated Violations Per Repo

**IEF-Operations (11 files):**

| Rule ID | Files Affected | Violation Type | Remediation |
|---------|---------------|----------------|-------------|
| `ief-naming-001` | 2 (`IKE_READ_MODEL_VERSION_1.json`, `RESULT_SCHEMA_V2.json`) | UPPER_SNAKE_CASE filenames | Grandfather (permanent suppression) |
| `ief-oas-009` | 1 (`VERIFICATION_SPEC_V0.yaml`) | Empty `paths: {}` | Grandfather (by-design, not an HTTP service) |
| `ief-xref-001` | 1 (`VERIFICATION_SPEC_V0.yaml`) | `$ref` to `../schemas/` may not resolve in isolated checkout | Fix with absolute URIs or restructure (60-day sunset) |
| `ief-schema-007` | ~5 schemas | Missing `additionalProperties: false` | Add to each schema (low effort, ~30 min each) |
| `ief-schema-008` | ~3 schemas | Some properties missing `description` | Add descriptions (medium effort, ~1 hour per schema) |

**Estimated IEF-Operations total:** ~12 violations (2 permanent, ~10 fixable)

**IEF-Adapters (1 file):**

| Rule ID | Files Affected | Violation Type | Remediation |
|---------|---------------|----------------|-------------|
| `ief-oas-010` | 1 (`ADAPTER_CONTRACT_V0.yaml`) | Has `x-ief-metadata` — **compliant** | N/A |
| `ief-naming-003` | 1 | Potential PascalCase violations in schema names | Audit and fix if needed |

**Estimated IEF-Adapters total:** ~1–3 violations (low effort)

**IEF-Runners (1 file):**

| Rule ID | Files Affected | Violation Type | Remediation |
|---------|---------------|----------------|-------------|
| `ief-oas-006` | 1 (`RUNNER_INTERFACE_V0.yaml`) | `info.contact` minimal (only `name` field) | Add email/url (trivial) |
| `ief-naming-003` | 1 | Potential PascalCase violations in schema names | Audit and fix if needed |

**Estimated IEF-Runners total:** ~1–3 violations (low effort)

### 8.3 Violation Categorization

| Category | Count | Severity | Effort |
|----------|-------|----------|--------|
| **Naming convention** (legacy filenames) | 2 | warning | Permanent suppression |
| **Structural** (missing `additionalProperties`) | ~5 | info | Low — 30 min per file |
| **Missing fields** (descriptions, contact) | ~5 | warning/info | Low-Medium — 1 hour per file |
| **Cross-reference** (`$ref` resolution) | 1 | error | Medium — may require restructure |
| **By-design exceptions** (empty paths) | 1 | warning | Permanent suppression |

### 8.4 Remediation Effort Estimate

| Priority | Work | Estimated Time |
|----------|------|---------------|
| P1 — Write suppression file | Document all accepted violations | 2 hours |
| P2 — Add `additionalProperties: false` | 5 schema files | 2.5 hours |
| P3 — Add missing `description` fields | Properties in ~3 schemas | 3 hours |
| P4 — Fix `$ref` resolution | `VERIFICATION_SPEC_V0.yaml` | 1–2 hours |
| P5 — Enrich `info.contact` | 1–2 OAS files | 30 min |
| **Total remediation** | | **~9–10 hours** |

### 8.5 Priority Ordering

1. **Write suppression file first** — unblocks CI enforcement for new specs immediately
2. **Fix `$ref` resolution** — error severity, must be resolved before Phase 2
3. **Add `additionalProperties`** — improves schema strictness, low risk
4. **Add missing descriptions** — improves documentation quality
5. **Enrich contact info** — nice-to-have, lowest priority

---

## Appendix A: Spectral CLI Reference

| Command | Purpose |
|---------|---------|
| `npm install -g @stoplight/spectral-cli` | Install Spectral CLI |
| `spectral lint <files>` | Lint one or more files |
| `spectral lint --ruleset <file>` | Use custom ruleset |
| `spectral lint --format json` | Output as JSON (for CI parsing) |
| `spectral lint --format github-actions` | Output as GitHub Actions annotations |
| `spectral lint --format pretty` | Human-readable output |
| `spectral lint --verbose` | Show all rules, including passing ones |
| `spectral lint --fail-severity error` | Exit non-zero only on errors |

## Appendix B: File Pattern Matrix

| Repo | Pattern | Current Files | Future Files |
|------|---------|--------------|-------------|
| IEF-Operations | `schemas/*.json` | 9 | Growth expected |
| IEF-Operations | `docs/**/*.yaml` | 2 | Governance specs may grow |
| IEF-Adapters | `contracts/*.yaml` | 1 | Adapter variants possible |
| IEF-Runners | `contracts/*.yaml` | 1 | Runner variants possible |
| IEF-Knowledge | `contracts/*.yaml` | 0 | If Knowledge publishes contracts |
| All repos | `specs/*.yaml` | 0 | Reserved for future use |

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **Spectral** | Open-source JSON/YAML linter by Stoplight, used for API spec validation |
| **Ruleset** | A `.spectral.yaml` file defining validation rules |
| **Suppression** | An exemption for a known violation, documented in `.spectral-suppressions.yaml` |
| **Grandfathering** | Accepting existing violations without requiring immediate remediation |
| **TypeSpec** | Microsoft's DSL for API description, compiling to OpenAPI/JSON Schema |
| **Baseline compliance** | The state where all existing specs pass lint (with suppressions for accepted deviations) |
| **Sunset** | A deadline after which a suppression expires and the violation must be resolved |

---

*This document is a scoping plan only. No CI workflows, ruleset files, or spec modifications are included. Implementation begins in Phase 1.*
