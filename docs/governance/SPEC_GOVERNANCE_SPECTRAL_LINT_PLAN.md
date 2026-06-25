# Spec Governance Spectral Lint — Scoping Plan

> **Status:** SCOPING ONLY — no CI enforcement, no build gates, no spec mutations  
> **Created:** 2026-06-25  
> **Owner:** IEF Coordinator (relay from Controller directive)  
> **Directive:** IEF-Operations#4 — Spec Governance Spectral Lint Scope  

---

## Enforcement Deferral

> **This plan does NOT define enforcement behavior. Enforcement design is deferred until after the Classification Registry Spec is stable.**
>
> Follow-up recommendation: Enforcement design is to be scoped in a separate task after the Classification Registry Spec reaches stability.

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
| `ief-naming-001` | warning | Schema filenames must use one of: `kebab-case.json`, `kebab-case.schema.json`, `UPPER_SNAKE_CASE.json`, or `UPPER_SNAKE_CASE_V{N}.json` (all current filenames are compliant) |
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
  ief-naming-001-filename-convention:
    description: "Schema filenames must follow IEF naming patterns"
    severity: warning
    given: "$"
    then:
      field: "$id"
      function: pattern
      functionOptions:
        # Accepts: kebab-case, kebab-case.schema, UPPER_SNAKE_CASE, UPPER_SNAKE_V{N}
        match: "^[a-z][a-z0-9-]*(\\.schema)?\\.json$|^[A-Z][A-Z0-9_]*(\\.schema)?\\.json$"

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

# === Suppression overrides for grandfathered violations ===
# Spectral overrides disable specific rules for specific file paths.
# Use these instead of a separate suppressions file.
overrides:
  # VERIFICATION_SPEC_V0 — empty paths is intentional (not an HTTP service)
  - files:
      - "docs/VERIFICATION_SPEC_V0.yaml"
    rules:
      ief-oas-009-paths-or-tags: off

  # Cross-repo references may not resolve in isolated lint
  - files:
      - "docs/VERIFICATION_SPEC_V0.yaml"
    rules:
      ief-xref-001-ref-resolution: off
```

### 2.3 Severity Legend

| Level | Meaning |
|-------|---------|
| `error` | Violation must be fixed — spec is structurally or semantically broken |
| `warning` | Violation should be addressed — spec deviates from conventions |
| `info` | Suggestion for improvement — optional enhancement |
| `hint` | Style preference — optional, no action required |

---

## 3. Adoption Phases

### 3.1 Phase Overview

| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| **0 — Scoping** (current) | This document. Inventory and rule design. | 1 day |
| **1 — Baseline Ruleset** | Create `.spectral.yaml`, validate rules against all 13 specs, document baseline violations. | 2–3 days |
| **2 — Report Mode Across All Repos** | Run Spectral in report-only mode across IEF-Operations, IEF-Adapters, IEF-Runners. Document baseline violations. | 1–2 days |
| **3 — Rule Tuning** | Monitor for false positives. Tune rules. Expand coverage as new specs are authored. | Ongoing |

### 3.2 Effort Breakdown

**Phase 1 (Baseline Ruleset):**
- Write `.spectral.yaml` ruleset: 4–6 hours
- Test against all 13 spec files: 2 hours
- Tune false positives: 2–4 hours

**Phase 2 (Report Mode):**
- Run Spectral across 3 repos: 1 hour per repo
- Baseline audit and violation documentation: 4 hours

**Phase 3 (Rule Tuning):**
- Monitor and triage false positives: ongoing

---

## 4. Avoiding Blockage of Existing Merged Contracts

### 4.1 Grandfathering Strategy

Existing merged contracts are **frozen at their current state** and should not be broken by new lint rules. The strategy:

1. Run Spectral in report-only mode against all existing specs
2. Document every violation with a rationale (accepted risk, known deviation, etc.)
3. Add Spectral `overrides` in `.spectral.yaml` listing each accepted violation
4. Existing specs pass lint as long as their overrides are active
5. New specs or modifications must pass without overrides

### 4.2 Suppression via Spectral Overrides

Spectral supports suppression of specific rules for specific file paths using the `overrides` key in `.spectral.yaml`:

```yaml
# .spectral.yaml — overrides section (EXAMPLE)
# Each override: file glob + rule ID + disabled severity

overrides:
  # IEF-Operations schemas — naming convention grandfathered
  # (No longer needed — ief-naming-001 now accepts all current filename patterns)

  # VERIFICATION_SPEC_V0 — empty paths is intentional
  - files:
      - "docs/VERIFICATION_SPEC_V0.yaml"
    rules:
      ief-oas-009-paths-or-tags: off

  # Cross-repo references may not resolve in isolated lint
  - files:
      - "docs/VERIFICATION_SPEC_V0.yaml"
    rules:
      ief-xref-001-ref-resolution: off
```

For inline suppression within a spec file (when a single rule needs to be disabled for a specific line or block), use Spectral's inline comment syntax:

```yaml
# spectral-disable ief-rule-id
some_field: value
```

### 4.3 Override Granularity

Overrides support three levels of granularity:

| Level | Syntax | Use Case |
|-------|--------|----------|
| **Per-file, per-rule** | `files: ["file.yaml"]`, `rules: { rule-id: off }` | Preferred — most specific |
| **Per-file, all rules** | `files: ["file.yaml"]`, `rules: { all: off }` | For specs known to have many accepted deviations |
| **Per-rule, all files** | Remove or disable the rule in the `rules` section | For rules not yet enforced across any repo |

### 4.4 Baseline Compliance Exceptions

For violations that are **by design** (not technical debt):

- Document the rationale in a comment above the override entry
- Link to the governing spec or Controller decision that authorized the deviation
- Mark as permanent (no sunset date)

For violations that are **technical debt** (should be fixed eventually):

- Document the remediation plan
- Set a sunset date in a comment above the override entry
- Track in a GitHub issue for visibility

### 4.5 Sunset Policy for Overrides

| Override Type | Sunset Policy |
|---------------|---------------|
| Naming convention (legacy) | Permanent — grandfathered with documented exception |
| Structural (missing optional fields) | 90 days — fix in next spec revision |
| Cross-reference (unresolvable `$ref`) | 60 days — fix reference or restructure |
| Design deviation (by-design exception) | Permanent — no sunset, documented rationale |

---

## 5. Relationship to Future TypeSpec Migration

### 5.1 Spectral and TypeSpec — Complementary, Not Competitive

Spectral and TypeSpec operate at different layers of the spec lifecycle:

| Dimension | Spectral | TypeSpec |
|-----------|---------|----------|
| **Input** | Existing YAML/JSON spec files | TypeSpec DSL source (`.tsp` files) |
| **Validation** | Lints the output artifact | Generates the output artifact |
| **Scope** | Naming, structure, references, conventions | Type correctness, schema composition |
| **Enforcement** | Post-authoring check | Compile-time check |

### 5.2 Shared Validation Concepts

Both tools enforce these overlapping concerns:

| Concern | Spectral Approach | TypeSpec Approach |
|---------|------------------|-------------------|
| Required fields present | Rule checks `required` array | Compiler enforces model shape |
| Naming conventions | Pattern matching on keys | Decorator-based validation |
| Version consistency | Cross-file rule check | Import/version resolution |
| Reference integrity | `$ref` resolution check | Import resolution at compile |
| Enum validity | Pattern and value checks | Union type enforcement |

### 5.3 What Spectral Validates That TypeSpec Cannot

- **Post-hoc validation of hand-written YAML/JSON:** TypeSpec only validates what it generates. Spectral validates specs regardless of authoring tool.
- **Cross-repo reference integrity:** Spectral can check that `$ref` targets across repos exist (with appropriate tooling).
- **File-level conventions:** Filename patterns, directory placement, metadata extensions.
- **Legacy spec compliance:** Existing specs not (yet) migrated to TypeSpec still need validation.

### 5.4 What TypeSpec Replaces That Spectral Checks

- **Schema composition correctness:** TypeSpec's type system catches structural errors that Spectral rules can only approximate.
- **Model inheritance and mixins:** TypeSpec handles `extends`/`is` composition; Spectral would need complex rules.
- **Code generation consistency:** TypeSpec generates schemas, eliminating a class of "hand-written schema drift" that Spectral would catch.

### 5.5 Dual-Running Strategy During Migration

When IEF begins migrating specs to TypeSpec, the recommended approach:

1. **TypeSpec generates** the canonical YAML/JSON output
2. **Spectral validates** the generated output against IEF-specific conventions (naming, metadata, cross-references)
3. **Both tools run** in the validation pipeline
4. **Hand-written specs** (not yet migrated) continue to be validated by Spectral alone
5. **Gradual migration:** As each spec moves to TypeSpec, its Spectral overrides are removed and TypeSpec takes over structural validation

```
Authoring Flow (during migration):
  [TypeSpec source] → compile → [YAML/JSON output] → Spectral lint → pass/fail
  [Hand-written YAML/JSON] → Spectral lint → pass/fail
```

### 5.6 Spectral Ruleset Adaptation for TypeSpec

Some Spectral rules become redundant after TypeSpec migration:
- `ief-schema-001` through `ief-schema-006` — TypeSpec guarantees these
- `ief-oas-001` through `ief-oas-006` — TypeSpec OAS emitter guarantees these

Rules that remain valuable:
- `ief-naming-*` — conventions may not be enforced by TypeSpec defaults
- `ief-xref-*` — cross-repo integrity still needs checking
- `ief-oas-010` — `x-ief-metadata` is IEF-specific, not generated by TypeSpec
- Custom domain rules — IEF governance-specific constraints

---

## 6. Expected Cleanup Work for Baseline Compliance

### 6.1 Audit Methodology

This audit is based on inspection of all 13 lintable files across the three repos. Violations are categorized by rule and severity.

### 6.2 Estimated Violations Per Repo

**IEF-Operations (11 files):**

| Rule ID | Files Affected | Violation Type | Remediation |
|---------|---------------|----------------|-------------|
| `ief-naming-001` | 0 (pattern broadened) | Previously UPPER_SNAKE_CASE filenames — now compliant | N/A — rule updated |
| `ief-oas-009` | 1 (`VERIFICATION_SPEC_V0.yaml`) | Empty `paths: {}` | Override (by-design, not an HTTP service) |
| `ief-xref-001` | 1 (`VERIFICATION_SPEC_V0.yaml`) | `$ref` to `../schemas/` may not resolve in isolated checkout | Fix with absolute URIs or restructure (60-day sunset) |
| `ief-schema-007` | ~5 schemas | Missing `additionalProperties: false` | Add to each schema (low effort, ~30 min each) |
| `ief-schema-008` | ~3 schemas | Some properties missing `description` | Add descriptions (medium effort, ~1 hour per schema) |

**Estimated IEF-Operations total:** ~10 violations (1 permanent override, ~9 fixable)

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

### 6.3 Violation Categorization

| Category | Count | Severity | Effort |
|----------|-------|----------|--------|
| **By-design exceptions** (empty paths) | 1 | warning | Permanent override |
| **Structural** (missing `additionalProperties`) | ~5 | info | Low — 30 min per file |
| **Missing fields** (descriptions, contact) | ~5 | warning/info | Low-Medium — 1 hour per file |
| **Cross-reference** (`$ref` resolution) | 1 | error | Medium — may require restructure |

### 6.4 Remediation Effort Estimate

| Priority | Work | Estimated Time |
|----------|------|---------------|
| P1 — Add Spectral overrides | Document all accepted violations | 1 hour |
| P2 — Fix `$ref` resolution | `VERIFICATION_SPEC_V0.yaml` | 1–2 hours |
| P3 — Add `additionalProperties: false` | 5 schema files | 2.5 hours |
| P4 — Add missing `description` fields | Properties in ~3 schemas | 3 hours |
| P5 — Enrich `info.contact` | 1–2 OAS files | 30 min |
| **Total remediation** | | **~7–9 hours** |

### 6.5 Priority Ordering

1. **Add Spectral overrides first** — documents accepted deviations clearly
2. **Fix `$ref` resolution** — error severity, should be resolved before broader adoption
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
| `spectral lint --format json` | Output as JSON (for programmatic parsing) |
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
| **Override** | A Spectral mechanism to disable specific rules for specific file paths within `.spectral.yaml` |
| **Grandfathering** | Accepting existing violations without requiring immediate remediation |
| **TypeSpec** | Microsoft's DSL for API description, compiling to OpenAPI/JSON Schema |
| **Baseline compliance** | The state where all existing specs pass lint (with overrides for accepted deviations) |
| **Sunset** | A deadline after which an override expires and the violation must be resolved |

---

*This document is a scoping plan only. No CI workflows, ruleset files, or spec modifications are included. Enforcement design is deferred until after the Classification Registry Spec is stable.*
