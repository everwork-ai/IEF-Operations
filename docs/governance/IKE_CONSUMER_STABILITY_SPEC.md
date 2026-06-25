# IKE Consumer Stability Specification — Stage G (G8-3)

> **Status:** Frozen Specification  
> **Created:** 2026-06-23T18:32+08:00  
> **Authority:** Program Controller STAGE_G_G8-3_DISPATCH_AUTHORIZED (comment [4778235928](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4778235928))  
> **Baseline:** IEF-Operations `main` @ `31bc466`  
> **Prior slices:** G8-1 Control Plane Freeze (`bc4b93f`), G8-2 Verification Hardening (`7f5f957`)  
> **Governance Profile:** Contract-Critical  
> **External consumer:** IKE / MyAttention (`D:\code\MyAttention`)  

---

## 1. Purpose

This specification defines the **read-only consumer stability contract** between the IEF ecosystem (IEF-Program, IEF-Operations, IEF-Protocol, IEF-Governance) and the IKE / MyAttention runtime. IKE is an **external consumer** of IEF artifacts — it reads IEF outputs (governance profiles, verification results, lifecycle events, ledger entries, verification evidence) to align its own project coordination, but it does **not** write back to IEF, does **not** participate in the IEF control plane, and does **not** replace any IEF protocol with A2A or any other agent-to-agent contract.

This document does **not** introduce runtime integration, write-back paths, Knowledge promotion, CI hooks, or execution triggers. It is a specification-level read-only adoption boundary.

---

## 2. Read-Only Adoption Boundary

### 2.1 Core Principle

**IKE reads IEF. IEF does not read IKE. Neither side writes to the other.**

| Direction | Allowed? | Scope |
|---|---|---|
| IEF → IKE (push) | ❌ **No** | IEF does not push data to IKE |
| IKE → IEF (read) | ✅ **Yes** | IKE reads published IEF artifacts via defined read contract |
| IKE → IEF (write) | ❌ **No** | IKE never writes to IEF repos, schemas, or control plane |
| IEF → IKE (write) | ❌ **No** | IEF never writes to IKE state, registry, or ops files |
| IKE ↔ IEF (bidirectional sync) | ❌ **No** | No real-time sync; IKE polls on its own schedule |

### 2.2 What IKE May Read

| Artifact Type | IEF Source | Read Method | Refresh Cadence |
|---|---|---|---|
| Governance Profiles | `IEF-Governance` schemas and docs | Local clone or GitHub API | On schema version change |
| Verification Results (V2) | `IEF-Operations` `schemas/RESULT_SCHEMA_V2.json` | Local clone or GitHub API | On verification event |
| Verification Evidence | `IEF-Operations` evidence artifacts | Artifact URI resolution | On verification event |
| Ledger Entries | `IEF-Operations` `schemas/ledger_entry.schema.json` | Local clone or GitHub API | On ledger append |
| Lifecycle State | `IEF-Operations` task/run lifecycle docs | Local clone | On schema version change |
| Control Plane Freeze | `IEF-Operations` `docs/governance/CONTROL_PLANE_FREEZE_SPEC.md` | Local clone | On G8-1 amendment |
| Mutation Matrix | `IEF-Operations` `docs/governance/AUTHORIZED_MUTATION_MATRIX.md` | Local clone | On G8-1 amendment |
| Contract Lock | `IEF-Operations` `schemas/STAGE_G_CONTRACT_LOCK.json` | Local clone | On G8-1 amendment |
| Verification Hardening | `IEF-Operations` `docs/governance/VERIFICATION_HARDENING_SPEC.md` | Local clone | On G8-2 amendment |
| Failure Replay Model | `IEF-Operations` `docs/governance/FAILURE_REPLAY_MODEL.md` | Local clone | On G8-2 amendment |
| Protocol Schemas | `IEF-Protocol` TaskEnvelope, RunEvent, ArtifactRef, ContextRef | Local clone or GitHub API | On Protocol version change |

### 2.3 What IKE May NOT Read (Forbidden Sources)

Per the G7-B pilot truth hierarchy (comment [4762450559](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4762450559), SC-9):

| Forbidden Source | Rationale |
|---|---|
| Raw runner cache | Unreviewed, unverified, mutable |
| Adapter staging area | Pre-validation, not authoritative |
| Chat memory / model context | Ephemeral, non-durable |
| Unreviewed knowledge observations | Not yet promoted through governance gates |
| Private conversations | Not GitHub-visible, not auditable |
| IEF-Operations working branches (non-main) | Pre-merge, not authoritative |

### 2.4 What IKE May NOT Do

| Prohibition | Rationale |
|---|---|
| Write to any IEF repository | IKE is a consumer, not a contributor |
| Trigger IEF verification | Verification is Controller-authorized only |
| Modify IEF schemas | Schemas are owned by IEF-Operations / IEF-Protocol |
| Post comments on IEF PRs or issues | Only IEF agents and Controller may post |
| Interpret IEF results as actionable directives | Results are evidence; Controller decides action |
| Cache IEF results as IKE project truth | Results are point-in-time; freshness rules apply |
| Replace IEF Protocol with A2A agent card | A2A is a projection for discovery, not a contract replacement |
| Self-promote based on IEF verification results | Promotion is Controller-authorized only |

---

## 3. Source Freshness Rules

### 3.1 Freshness Model

Every IEF artifact consumed by IKE carries a **provenance triple**:

```
provenance = {
    source_repo: "<owner/repo>",
    source_commit: "<short SHA>",
    source_timestamp: "<ISO-8601>"
}
```

IKE MUST record the provenance triple for every IEF artifact it reads and uses.

### 3.2 Freshness Thresholds

| Artifact Type | Max Staleness | Action on Stale |
|---|---|---|
| Governance Profiles | 7 days | Warn; re-fetch on next cycle |
| Verification Results (V2) | 24 hours | Warn; re-fetch on next cycle; do not act on stale results |
| Ledger Entries | 1 hour | Re-fetch; ledger is append-only so stale reads are safe but incomplete |
| Lifecycle State docs | 30 days | Warn; re-fetch on next cycle |
| Control Plane Freeze | Until amended | No re-fetch needed unless amendment process triggered |
| Protocol Schemas | Until version bump | Re-fetch on `$id` version change |

### 3.3 Freshness Enforcement

```
Rule FR-1: IKE MUST NOT act on IEF data older than its freshness threshold
           without first attempting a re-fetch.

Rule FR-2: If re-fetch fails 3 consecutive times, IKE MUST mark the
           artifact as STALE in its own state and stop consuming it
           for decision-making.

Rule FR-3: Stale artifacts remain in IKE's local cache for audit
           purposes but are flagged with `stale: true` and
           `last_successful_fetch` timestamp.

Rule FR-4: IKE MUST NOT invent or fabricate IEF data when fetch fails.
           Missing data = missing data. Report the gap.
```

### 3.4 Provenance Recording

Every time IKE reads an IEF artifact, it records:

```json
{
  "artifact_type": "verification_result_v2",
  "source_repo": "everwork-ai/IEF-Operations",
  "source_commit": "7f5f957",
  "source_timestamp": "2026-06-23T12:18:00+08:00",
  "local_fetched_at": "2026-06-23T18:32:00+08:00",
  "freshness_status": "fresh | stale | fetch_failed",
  "consecutive_fetch_failures": 0,
  "schema_version": "https://ief.dev/schemas/RESULT_SCHEMA_V2.json"
}
```

---

## 4. Repeatability Requirements

### 4.1 Deterministic Read Contract

IKE's reads from IEF MUST be repeatable:

**Given:**
- The same IEF commit SHA
- The same schema version
- The same artifact URI

**Then:**
- The content returned MUST be byte-identical
- The parsed result MUST be structurally identical
- The provenance triple MUST match

### 4.2 Read Procedure

```
Step 1: Identify target artifact
    - artifact_type + source_repo + path/URI

Step 2: Fetch with provenance
    - Record source_commit (git rev-parse --short HEAD or API sha)
    - Record source_timestamp (commit date or API response date)
    - Record local_fetched_at

Step 3: Validate against schema
    - Load the schema version referenced in the artifact
    - Validate the artifact against that schema
    - If validation fails → mark as INVALID, do not consume

Step 4: Cache with provenance
    - Store artifact locally with provenance triple
    - Mark freshness_status based on threshold check

Step 5: Consume or skip
    - If fresh and valid → consume for IKE alignment
    - If stale → warn, attempt re-fetch, do not consume for decisions
    - If invalid → report, do not consume
```

### 4.3 Idempotent Reads

IKE MAY re-read the same artifact multiple times. Each read:
- Updates `local_fetched_at`
- Resets `consecutive_fetch_failures` to 0
- Does NOT change the cached content if the source commit is unchanged
- Does NOT change any IKE state derived from the artifact unless the content actually changed

---

## 5. Stop and Rollback Triggers

### 5.1 Stop Triggers (Immediate Halt)

IKE MUST stop consuming IEF data and halt alignment processing when:

| Trigger ID | Condition | Action |
|---|---|---|
| ST-1 | IEF repository is unreachable after 3 consecutive fetch attempts | Stop; report `IEF_UNREACHABLE`; do not use stale data for decisions |
| ST-2 | IEF schema `$id` version changes and IKE read model is not updated | Stop consuming that artifact type; report `SCHEMA_MISMATCH` |
| ST-3 | IEF Control Plane Freeze is amended in a way that affects IKE's read scope | Stop; re-evaluate read scope against new freeze spec |
| ST-4 | IEF Controller explicitly posts a `CONSUMER_HALT` directive | Stop immediately; do not resume until `CONSUMER_RESUME` is posted |
| ST-5 | IKE detects that it has written to an IEF repository (boundary violation) | Stop immediately; report `BOUNDARY_VIOLATION`; escalate to Controller |
| ST-6 | IKE detects that an IEF artifact was consumed from a forbidden source | Stop; report `FORBIDDEN_SOURCE_CONSUMED`; purge the data |

### 5.2 Rollback Triggers (Revert Cached State)

IKE MUST roll back its cached IEF data when:

| Trigger ID | Condition | Action |
|---|---|---|
| RT-1 | IEF ledger correction event is detected for a previously consumed verification result | Mark original result as `SUPERSEDED`; fetch correction |
| RT-2 | IEF schema is reverted (git revert on schema commit) | Invalidate all cached artifacts validated against the reverted schema |
| RT-3 | IEF Control Plane Freeze amendment removes an artifact type from IKE's read scope | Purge that artifact type from IKE cache; stop reading it |
| RT-4 | IEF verification result is re-evaluated under a new schema version (`supersedes` field populated) | Replace cached V1 result with V2 result; update provenance |
| RT-5 | IKE discovers a provenance mismatch (cached commit SHA ≠ source repo commit SHA) | Invalidate cache; re-fetch; report `PROVENANCE_MISMATCH` |

### 5.3 Rollback Procedure

```
Step 1: Detect trigger
    - Monitor IEF ledger events for corrections
    - Monitor IEF schema $id for version changes
    - Monitor IEF Control Plane Freeze for amendments
    - Verify provenance on every read cycle

Step 2: Classify scope
    - Which artifact types are affected?
    - Which cached entries are invalidated?

Step 3: Invalidate
    - Mark affected cached entries as INVALIDATED
    - Record invalidation reason and trigger ID

Step 4: Re-fetch (if applicable)
    - Fetch corrected/replaced artifacts
    - Validate against current schema
    - Update cache with new provenance

Step 5: Report
    - Log rollback event with trigger ID, affected artifacts, and resolution
    - If rollback affects IKE alignment state, flag alignment as STALE
      until next successful read cycle
```

### 5.4 Recovery After Stop

After a stop trigger fires:

1. IKE does NOT automatically resume.
2. The stop condition must be resolved (e.g., IEF becomes reachable, schema is updated, Controller posts resume).
3. IKE's next scheduled cycle checks whether the stop condition is resolved.
4. If resolved → resume reads with fresh provenance.
5. If unresolved → remain stopped; report status.

---

## 6. Alignment Mapping Rules

### 6.1 IEF → IKE Concept Mapping

Based on the G7-B pilot findings (comment [4762450559](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4762450559)):

| IEF Concept | IKE Equivalent | Mapping Status |
|---|---|---|
| G-Lite profile | IKE hard gates 1–5 | ✅ Mapped |
| G-Std profile | IKE hard gates 1–9 + review state | ✅ Mapped |
| G-Full profile | IKE hard gates + independent review + L5 evidence | ✅ Mapped |
| Classification (L/T/R/C) | Not in IKE | ⚠️ Gap — IKE should adopt |
| Task (13 states) | `active_pipeline` + `first_class_tasks` | ⚠️ Partial (3/13 states) |
| Ledger Entry (26 events) | `progress_log` (untyped) | ⚠️ 18/26 applicable, untyped |
| VerificationResult V2 | No IKE equivalent | ⚠️ Gap — IKE should adopt read model |
| VerificationEvidence | `docs/reviews/active/*` | ✅ Mapped |
| TaskEnvelope | IKE task packets (markdown) | ⚠️ Partial (format mismatch) |
| ArtifactRef | IKE `evidence[]` arrays | ✅ Mapped |

### 6.2 Mapping Rules

```
Rule MR-1: IKE MUST NOT assume 1:1 mapping between IEF and IKE concepts.
           Each mapping is documented in §6.1 with status.

Rule MR-2: Where IKE has no equivalent (VerificationResult, Classification),
           IKE MUST record the IEF concept as an external reference,
           not attempt to synthesize an IKE-internal equivalent.

Rule MR-3: Where mapping is partial (Task states, Ledger events, TaskEnvelope),
           IKE MUST document which subset is mapped and which is unmapped.
           Unmapped IEF states/events are ignored, not approximated.

Rule MR-4: IKE MUST NOT modify IEF schemas to improve mapping.
           Mapping gaps are IKE's responsibility to handle.

Rule MR-5: The A2A Agent Card projection from G7-B is for discovery only.
           It does NOT replace the IEF Protocol contract.
           IKE reads IEF Protocol schemas directly, not via A2A.
```

---

## 7. Anti-Integration Rules

### 7.1 Preventing Implicit Write-Back

| Rule | Prohibition |
|---|---|
| AI-1 | IKE MUST NOT post IEF verification results to IEF PRs or issues |
| AI-2 | IKE MUST NOT trigger IEF re-verification based on IKE-internal state changes |
| AI-3 | IKE MUST NOT use IEF results to automatically promote IKE tasks |
| AI-4 | IKE MUST NOT cache IEF results as authoritative IKE project truth |
| AI-5 | IKE MUST NOT interpret IEF `retry_eligible: true` as authorization to retry |
| AI-6 | IKE MUST NOT interpret IEF `closure_criteria_met: true` as authorization to close |
| AI-7 | IKE MUST NOT modify IEF schemas, even to add IKE-specific fields |
| AI-8 | IKE MUST NOT fork IEF schemas into IKE-local copies that drift from upstream |

### 7.2 Preventing A2A Protocol Replacement

| Rule | Prohibition |
|---|---|
| AP-1 | IKE MUST NOT use A2A Agent Card as a substitute for reading IEF Protocol schemas |
| AP-2 | IKE MUST NOT advertise IEF capabilities via A2A without explicit Controller approval |
| AP-3 | IKE MUST NOT implement A2A task delegation that routes work through IEF runners |
| AP-4 | A2A Agent Card is a **read-only projection** for external discovery; it carries no authority |

---

## 8. Relationship to Prior Slices

| Slice | Contribution | G8-3 Build-Upon |
|---|---|---|
| G7-B IKE Pilot (comment 4762450559) | Read-only pilot, 10/10 success criteria, adapter contract, A2A projection | G8-3 formalizes the read-only boundary and adds freshness/repeatability/rollback |
| G8-1 Control Plane Freeze (commit bc4b93f) | Frozen layer boundaries, no-implicit-state-source | G8-3 respects frozen boundaries; IKE is external to all three layers |
| G8-2 Verification Hardening (commit 7f5f957) | V2 schema, edge cases, failure classification, replay model | G8-3 defines how IKE reads V2 results with provenance and freshness |
| G5-A Verification Contract (comment 4715793643) | Verification module responsibilities, evidence model | G8-3 defines how IKE consumes verification evidence as read-only |

---

## 9. Non-Goals

- ❌ No runtime integration between IEF and IKE
- ❌ No write-back path from IKE to IEF
- ❌ No Knowledge promotion based on IEF reads
- ❌ No A2A replacement of IEF Protocol
- ❌ No automatic alignment or sync
- ❌ No CI/CD integration
- ❌ No shared execution or task delegation
- ❌ No IKE-authored IEF schema modifications

---

## 10. Summary

| Aspect | Specification |
|---|---|
| Adoption boundary | Read-only; no writes in either direction |
| Artifacts readable | 11 types (governance, verification, ledger, lifecycle, control plane, protocol) |
| Forbidden sources | 6 types (raw cache, staging, chat memory, unreviewed observations, private conversations, non-main branches) |
| Freshness rules | 4 rules (FR-1 through FR-4) with per-artifact thresholds |
| Repeatability | Deterministic read contract; idempotent reads; provenance recording |
| Stop triggers | 6 conditions (ST-1 through ST-6) |
| Rollback triggers | 5 conditions (RT-1 through RT-5) with defined procedure |
| Anti-integration | 8 anti-write-back rules (AI-1 through AI-8) + 4 anti-A2A rules (AP-1 through AP-4) |

**Total rules defined:** 4 freshness + 6 stop + 5 rollback + 5 mapping + 12 anti-integration = **32 consumer stability rules**.

---

*Produced by ief-operator executing one bounded Stage G G8-3 cycle. Documentation and schema only. No runtime changes.*
