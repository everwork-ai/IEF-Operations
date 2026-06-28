# Dashboard Auto-Update Policy

**Classification**: Declarative Configuration Document  
**Status**: Draft  
**Created**: 2026-06-28  
**Authorization**: Controller-directed (DASHBOARD_AGENT_AUTO_UPDATE_AUTHORIZED)  
**Scope**: Passive read-only projection refresh policy for IEF Dashboard

---

## 1. Data Source Declaration

### 1.1 Primary Data Source

**Operations Ledger** — the single source of truth for all dashboard projections.

| Source | Location | Purpose |
|---|---|---|
| Tasks ledger | `IEF-Operations/tasks.json` | Task state, phase tracking, execution status |
| GitHub PRs | All 5 IEF repos (see §1.3) | Merge status, review gates, delivery evidence |
| GitHub Issues | `IEF-Operations`, `IEF-Program` | Open work items, directives, escalation state |

### 1.2 Secondary Data Source

**Controller Decisions** — GitHub issue comments authored by the Controller or Coordinator relay.

| Source | Location | Purpose |
|---|---|---|
| Controller decisions | GitHub issue comments on active anchor | Authorization state, phase transitions, planning directives |
| Coordinator relays | GitHub issue comments (relay chain) | Relayed Controller decisions with evidence chain |

### 1.3 Repository Scope

The dashboard auto-update pipeline may read from exactly these repositories:

1. `everwork-ai/IEF-Operations` — governance docs, dashboard, tasks ledger
2. `everwork-ai/IEF-Program` — program-level coordination, directives
3. `everwork-ai/IEF-Runners` — runner contract interfaces
4. `everwork-ai/IEF-Knowledge` — knowledge base contracts
5. `everwork-ai/IEF-Sandbox` — experimental/sandbox work

**No other repositories may be queried.** Any data source outside this set is explicitly forbidden.

### 1.4 Forbidden Data Sources

- Webhook payloads or push notifications
- External APIs (non-GitHub)
- Email, chat, or messaging system state
- Inferred or computed state not directly derivable from §1.1/§1.2
- Human input or manual annotations not committed to the ledger

---

## 2. Refresh Model

### 2.1 Trigger

**Scheduled cron** — every 12 hours.

| Field | Value |
|---|---|
| Frequency | Every 12 hours (00:00 and 12:00 UTC) |
| Trigger type | Time-based cron schedule |
| Execution window | Single atomic refresh cycle |
| Timeout | 300 seconds per refresh cycle |

### 2.2 Method

**Pull-based regeneration** — the Dashboard Agent pulls data from GitHub API and regenerates the dashboard data block.

```
┌─────────────────────────────────────────────────────────────┐
│  Cron Trigger (every 12h)                                   │
│    │                                                         │
│    ├─► Step 1: Fetch PRs from all 5 repos via gh CLI        │
│    ├─► Step 2: Fetch open issues (Operations + Program)     │
│    ├─► Step 3: Compute module progress percentages          │
│    ├─► Step 4: Regenerate dashboard-data JSON block         │
│    ├─► Step 5: Commit updated dashboard.html to main       │
│    └─► Step 6: Post update summary to IEF-Operations issue │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Passive-Only Constraint

The refresh model is **strictly passive**:

- ✅ Pull GitHub API data on schedule
- ✅ Regenerate static JSON projection
- ✅ Commit to main branch
- ❌ No webhook ingestion
- ❌ No event streaming
- ❌ No push notifications that affect state
- ❌ No reactive triggers based on external events
- ❌ No real-time or near-real-time updates

The Dashboard Agent observes state changes but does not cause them. It is a read-only projection of the Operations ledger.

---

## 3. Data Pipeline (Declarative)

### 3.1 Step 1: Fetch Open/Closed PRs

**Action**: Query GitHub API for pull request state across all 5 IEF repositories.

**Required data per PR**:
- PR number and title
- State (open, closed, merged)
- Head SHA and base branch
- Review status (pending, approved, changes requested)
- Merge authorization status (from Controller decisions)
- Created/updated timestamps

**Implementation constraint**: Use `gh` CLI only. No raw REST API calls, no third-party SDKs.

**Example query pattern**:
```
gh pr list --repo everwork-ai/IEF-Operations --state all --json number,title,state,headRefOid,baseRefName,reviews,createdAt,updatedAt
```

### 3.2 Step 2: Fetch Open Issues

**Action**: Query GitHub API for open issues on `IEF-Operations` and `IEF-Program`.

**Required data per issue**:
- Issue number and title
- Labels (especially `ACTION REQUIRED`, `COORDINATOR_RELAY`)
- Comment count and latest comment timestamp
- Assignees
- State (open/closed)

**Scope**: Only open issues. Closed issues are historical and not needed for live dashboard state.

### 3.3 Step 3: Compute Module Progress Percentages

**Action**: Derive module completion percentages from PR and issue state.

**Computation rules**:

| Module | Progress Metric |
|---|---|
| Governance | % of governance PRs merged on IEF-Operations |
| Execution | % of execution enforcement PRs merged |
| Knowledge | % of knowledge base contract PRs merged |
| Runners | % of runner interface PRs merged |
| Sandbox | % of sandbox/experimental PRs merged |

**Derivation logic**:
- Merged PR = 100% for that PR's scope
- Open PR with approval = partial progress (weighted by review status)
- Open PR without review = minimal progress
- No PR = 0% for that scope

**Forbidden computations**:
- Do not infer phase transitions from PR state alone
- Do not compute "overall project completion" as a weighted average (phases are gated, not linear)
- Do not derive Controller intent from comment sentiment or keyword analysis

### 3.4 Step 4: Regenerate Dashboard Data Block

**Action**: Replace the `<script id="dashboard-data" type="application/json">` block in `dashboard.html` with freshly computed data.

**Data block schema**:
```json
{
  "generated_at": "<ISO-8601 timestamp>",
  "source_sha": "<commit SHA of tasks.json>",
  "modules": {
    "governance": { "progress": 0.85, "prs": [...], "issues": [...] },
    "execution": { "progress": 0.60, "prs": [...], "issues": [...] },
    "knowledge": { "progress": 0.40, "prs": [...], "issues": [...] },
    "runners": { "progress": 0.20, "prs": [...], "issues": [...] },
    "sandbox": { "progress": 0.10, "prs": [...], "issues": [...] }
  },
  "active_anchor": "everwork-ai/IEF-Program#15",
  "quiet_cycles": 3,
  "last_dispatch": "<ISO-8601 timestamp>",
  "controller_decisions": [ ... ]
}
```

**Regeneration constraints**:
- Must be idempotent: same input → same output
- Must be deterministic: no random ordering, no timestamp-dependent sorting
- Must preserve HTML structure: only the JSON content changes, not surrounding markup

### 3.5 Step 5: Commit Updated Dashboard

**Action**: Commit the updated `dashboard.html` to the `main` branch.

**Commit message format**:
```
dashboard: auto-update <ISO-8601 date> — <brief summary>

Generated from tasks.json at <source_sha>
Modules updated: <list of modules with changed data>
```

**Commit constraints**:
- Single commit per refresh cycle
- No force push
- No rebase or history rewrite
- Direct push to main (no PR required for dashboard data updates)

### 3.6 Step 6: Post Update Summary

**Action**: Post a comment to the active IEF-Operations issue summarizing the refresh.

**Summary format**:
```markdown
## Dashboard Auto-Update Summary

- **Timestamp**: <ISO-8601>
- **Source SHA**: <tasks.json commit SHA>
- **Modules refreshed**: <count>
- **Data changes detected**: <yes/no>
- **Commit**: <commit SHA>
- **Status**: SUCCESS | PARTIAL | FAILED

### Changes
- <module>: <old progress> → <new progress>
- ...
```

**Posting constraints**:
- One comment per refresh cycle
- Post to active anchor issue only
- Do not tag or mention individuals
- Do not include raw JSON in comment (link to commit instead)

---

## 4. Failure Handling

### 4.1 Partial Failure — Single Repo API Call Fails

**Condition**: One or more (but not all) GitHub API calls fail during Step 1 or Step 2.

**Handling**:
1. Skip the failed repo(s)
2. Use last known state from previous successful refresh for those repos
3. Mark the refresh as `PARTIAL` in the summary comment
4. Include which repos were skipped and why
5. Proceed with Steps 3–6 using available data

**Rationale**: A single repo's API failure should not block the entire dashboard refresh. The dashboard is a projection, and partial data is better than stale data — as long as the partial nature is clearly marked.

### 4.2 Total Failure — All API Calls Fail

**Condition**: All GitHub API calls fail (network issue, auth failure, GitHub outage).

**Handling**:
1. Do NOT overwrite existing `dashboard.html`
2. Do NOT commit
3. Post a failure summary comment with error details
4. Mark the refresh as `FAILED`
5. Wait for next scheduled cycle (do not retry within the same cycle)

**Rationale**: If all data sources are unavailable, the existing dashboard is the best available state. Overwriting with empty or error data would be worse than staleness.

### 4.3 Commit Failure

**Condition**: The git commit or push operation fails.

**Handling**:
1. Retry once with a fresh `git pull --ff-only` to resolve potential conflicts
2. If retry succeeds: proceed normally
3. If retry fails: mark as `FAILED`, post failure summary, do not retry again

**Rationale**: Transient conflicts (another commit landed between pull and push) are recoverable. Persistent failures indicate a deeper issue that requires human intervention.

### 4.4 Data Integrity Failure

**Condition**: Computed data appears inconsistent or violates known invariants.

**Examples**:
- Progress percentage > 100% or < 0%
- PR listed as merged but head SHA doesn't exist on remote
- Active anchor issue is closed

**Handling**:
1. Do NOT commit suspect data
2. Mark as `FAILED` with specific integrity violation details
3. Fall back to last known good dashboard state
4. Post failure summary with the specific invariant that was violated

**Rationale**: Fabricating or inferring data to fill gaps violates the core compliance constraint (see §5.5). The dashboard must never misrepresent the Operations ledger.

### 4.5 Forbidden Recovery Actions

The following recovery actions are **explicitly forbidden**:

- ❌ Fabricate data to fill gaps
- ❌ Infer state from incomplete sources
- ❌ Use cached data older than 2 refresh cycles (24 hours)
- ❌ Retry failed API calls with exponential backoff within the same cycle
- ❌ Fall back to alternative data sources not listed in §1
- ❌ Manually edit the dashboard to "fix" inconsistencies
- ❌ Trigger a refresh outside the scheduled cron window to recover from failure

---

## 5. Compliance Constraints

### 5.1 Read-Only Projection

**The dashboard is a read-only projection of the Operations ledger.**

This means:
- The dashboard reflects state; it does not create state
- The dashboard displays decisions; it does not make decisions
- The dashboard shows progress; it does not drive progress
- The dashboard is a mirror, not an actor

### 5.2 No State Computation That Contradicts Operations Truth

**The dashboard must never compute state that contradicts the Operations ledger.**

| Operations Truth | Dashboard Must Show |
|---|---|
| Task marked COMPLETE in tasks.json | 100% progress for that task |
| PR not merged | Progress < 100% for that PR's scope |
| No Controller authorization | No merge-authorized flag |
| Phase not transitioned | Current phase, not next phase |

**Forbidden**: "Correcting" the dashboard to show what "should" be true based on inferred intent or expected state.

### 5.3 No Execution Triggers

**The dashboard must not trigger execution of downstream work.**

- No webhook calls to CI/CD systems
- No API calls that create issues, PRs, or comments (except the update summary in §3.6)
- No scheduling of operator dispatches
- No triggering of worker cycles
- No state transitions (phase changes, task completions)

The Dashboard Agent is a reporter, not an orchestrator.

### 5.4 No Merge or Phase Transition Authority

**The Dashboard Agent does NOT have**:
- Merge authority (cannot merge PRs)
- Phase transition authority (cannot advance phases)
- Dispatch authority (cannot trigger worker cycles)
- Planning authority (cannot create or approve plans)

These authorities remain exclusively with the Controller and Operator as defined in the IEF governance framework.

### 5.5 No Data Fabrication

**The dashboard must never fabricate data or infer state from incomplete sources.**

- If data is unavailable: show "unavailable" or last known state, not an estimate
- If computation fails: show the failure, not a fallback value
- If a repo is unreachable: skip it, don't guess its state
- If a PR's merge status is ambiguous: show the raw state, not an interpretation

---

## 6. Audit and Observability

### 6.1 Refresh Log

Each refresh cycle must produce a log entry with:

| Field | Purpose |
|---|---|
| Timestamp | When the refresh started |
| Duration | How long the refresh took |
| Status | SUCCESS / PARTIAL / FAILED |
| Repos queried | Which repos were successfully queried |
| Repos skipped | Which repos failed (with error) |
| Data changes | What changed from previous refresh |
| Commit SHA | The commit created (if any) |
| Summary comment | The comment posted (if any) |

### 6.2 Audit Trail

The audit trail must allow reconstruction of:
- When each dashboard state was generated
- What data sources were used
- What failures occurred and how they were handled
- Whether any compliance constraints were violated

### 6.3 Alerting

**Conditions requiring immediate alert** (posted as issue comment):
- 3 consecutive FAILED refreshes
- Active anchor issue is closed (no valid target for summaries)
- tasks.json is missing or malformed
- Controller decision contradicts previously recorded decision (evidence of data corruption)

---

## 7. Relationship to Existing Governance

### 7.1 Activation Policy Compliance

This auto-update policy operates under the **Enforcement Activation Policy** (see `ENFORCEMENT_ACTIVATION_POLICY.md`):

- The Dashboard Agent is activated by Controller directive
- Activation is scoped to passive projection refresh only
- Deactivation occurs when the Controller revokes authorization or the active anchor is closed without replacement

### 7.2 Execution Enforcement Phase Model Compliance

The Dashboard Agent respects the **Execution Enforcement Phase Model** (see `EXECUTION_ENFORCEMENT_PHASE_MODEL.md`):

- The dashboard reflects phase state; it does not enforce phase gates
- Phase transitions are computed by the Operator and authorized by the Controller
- The dashboard shows the results of those transitions, not the transitions themselves

### 7.3 Spec Governance Compliance

The dashboard data block schema is subject to the **Spec Governance Spectral Lint Scoping Plan** (see `SPEC_GOVERNANCE_SPECTRAL_LINT_PLAN.md`):

- Schema changes require Controller approval
- Backward-incompatible changes require a new policy document
- The dashboard data block is a governed artifact

---

## 8. Operational Parameters

### 8.1 Scheduling

| Parameter | Value |
|---|---|
| Cron expression | `0 0,12 * * *` (UTC) |
| Timezone | UTC |
| Execution window | 300 seconds |
| Concurrent executions | Forbidden (singleton lock required) |

### 8.2 Resource Limits

| Resource | Limit |
|---|---|
| API calls per refresh | Max 50 (across all repos) |
| GitHub API rate limit | Respect 5000/hour authenticated limit |
| Memory | Max 256MB for data processing |
| Disk | Max 10MB for dashboard.html |
| Network | Max 50MB downloaded per refresh |

### 8.3 Security

| Constraint | Requirement |
|---|---|
| Authentication | GitHub CLI (`gh`) with existing token |
| Secrets | No secrets in dashboard.html or commit messages |
| Network | HTTPS only for all API calls |
| Write scope | `dashboard.html` only (no other files) |
| Push scope | `main` branch only (no feature branches) |

---

## 9. Versioning and Change Control

### 9.1 Policy Version

This document is version 1.0 of the Dashboard Auto-Update Policy.

### 9.2 Change Process

Changes to this policy require:
1. Controller authorization (new directive comment)
2. New branch from current main
3. Updated policy document with version bump
4. PR with Coordinator relay evidence
5. Controller approval and merge

### 9.3 Schema Versioning

The dashboard data block schema (see §3.4) includes a `schema_version` field. Breaking changes to the schema require:
- New policy document version
- Migration plan for existing dashboard consumers
- Controller approval of the migration

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Operations Ledger** | The `tasks.json` file and associated GitHub artifacts that constitute the source of truth |
| **Dashboard Agent** | The automated process that executes the refresh pipeline defined in this policy |
| **Active Anchor** | The currently active GitHub issue that serves as the coordination point |
| **Projection** | A read-only derived view of the Operations ledger; the dashboard is a projection |
| **Refresh Cycle** | One complete execution of the 6-step pipeline defined in §3 |
| **Partial Refresh** | A refresh where some (but not all) repos were successfully queried |
| **Quiet Cycle** | A refresh where no data changes were detected |

---

## 11. Compliance Checklist

Before each refresh cycle, the Dashboard Agent must verify:

- [ ] Cron schedule is correct (every 12h, UTC)
- [ ] GitHub CLI authentication is valid
- [ ] Active anchor issue is open
- [ ] tasks.json exists and is parseable
- [ ] No concurrent refresh is in progress
- [ ] Previous refresh log is available for "last known state" fallback

After each refresh cycle, the Dashboard Agent must verify:

- [ ] Dashboard data block is valid JSON
- [ ] Progress percentages are in [0, 1] range
- [ ] No forbidden data sources were used
- [ ] No execution triggers were fired
- [ ] Commit message follows format in §3.5
- [ ] Summary comment follows format in §3.6
- [ ] Refresh log entry is complete

---

## Appendix A: Example Refresh Cycle

**Scenario**: Normal refresh, all repos available.

```
2026-06-28T00:00:00Z — Cron trigger fires
2026-06-28T00:00:05Z — Step 1: Fetch PRs from 5 repos (45 API calls)
2026-06-28T00:00:15Z — Step 2: Fetch open issues from Operations + Program (3 API calls)
2026-06-28T00:00:18Z — Step 3: Compute progress percentages
2026-06-28T00:00:20Z — Step 4: Regenerate dashboard-data JSON block
2026-06-28T00:00:22Z — Step 5: Commit dashboard.html (SHA: abc1234)
2026-06-28T00:00:25Z — Step 6: Post summary to IEF-Operations#15
2026-06-28T00:00:28Z — Refresh complete (28 seconds, STATUS: SUCCESS)
```

**Scenario**: Partial failure, one repo unavailable.

```
2026-06-28T12:00:00Z — Cron trigger fires
2026-06-28T12:00:05Z — Step 1: Fetch PRs from 5 repos
                         - IEF-Operations: OK
                         - IEF-Program: OK
                         - IEF-Runners: OK
                         - IEF-Knowledge: TIMEOUT (503)
                         - IEF-Sandbox: OK
2026-06-28T12:00:20Z — Step 2: Fetch open issues (OK)
2026-06-28T12:00:23Z — Step 3: Compute progress (Knowledge uses last known state from 2026-06-28T00:00:28Z)
2026-06-28T12:00:25Z — Step 4: Regenerate dashboard-data JSON block
2026-06-28T12:00:27Z — Step 5: Commit dashboard.html (SHA: def5678)
2026-06-28T12:00:30Z — Step 6: Post summary to IEF-Operations#15 (STATUS: PARTIAL, Knowledge skipped)
2026-06-28T12:00:33Z — Refresh complete (33 seconds, STATUS: PARTIAL)
```

---

## Appendix B: Failure Scenarios

| Scenario | Detection | Handling | Recovery |
|---|---|---|---|
| GitHub API 503 | HTTP status code | Skip repo, use last known state | Next cycle retries automatically |
| GitHub API 401 | HTTP status code | Total failure, do not commit | Alert posted, human intervention required |
| tasks.json missing | File not found | Total failure, do not commit | Alert posted, human intervention required |
| Merge conflict | Git push rejected | Retry once with fresh pull | If retry fails, alert posted |
| Progress > 100% | Invariant check | Do not commit, use last good state | Alert posted with specific violation |
| Active anchor closed | Issue state check | Do not commit, alert posted | Controller must open new anchor |
| Concurrent refresh | Lock file exists | Abort immediately | Previous cycle must complete or timeout |

---

## Appendix C: Authorization Chain

```
Controller (ChatGPT)
  │
  ├─► Directive: DASHBOARD_AGENT_AUTO_UPDATE_AUTHORIZED
  │   (Issue #15, comment 4824527629, 2026-06-28T03:16:56Z)
  │
  └─► Relay: Controller → Coordinator → Operator
      │
      └─► Operator: Executes this policy
          │
          └─► Dashboard Agent: Refresh pipeline (this document)
```

**Authorization scope**: Single declarative configuration document, passive read-only projection refresh only.

**Revocation**: Controller may revoke this authorization at any time by posting a comment to the active anchor issue with `DASHBOARD_AGENT_DEAUTHORIZED`.

---

*This document is a declarative configuration policy. It contains no executable code, no scripts, and no automation logic. The actual implementation of the refresh pipeline is the responsibility of the Dashboard Agent, which must conform to this policy.*
