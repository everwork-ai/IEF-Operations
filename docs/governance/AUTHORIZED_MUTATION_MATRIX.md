# Authorized Mutation Matrix — Stage G (G8-1)

> **Status:** Frozen  
> **Created:** 2026-06-22T12:02+08:00  
> **Authority:** Program Controller DISPATCH_AUTHORIZED (comment [4763724671](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4763724671))  
> **Baseline:** IEF-Operations `main` @ `31bc466`  
> **Governance Profile:** Contract-Critical  

---

## 1. Purpose

This matrix enumerates **all mutation paths** within the IEF ecosystem during Stage G and classifies each as **ALLOWED** or **DENIED** for each actor and layer. It is a companion to the [CONTROL_PLANE_FREEZE_SPEC.md](./CONTROL_PLANE_FREEZE_SPEC.md).

**Mutation** = any action that changes persisted state in a repository, issue tracker, ledger, or external system.

---

## 2. Classification Legend

| Classification | Meaning |
|---|---|
| `ALLOWED` | The actor may perform this action without additional approval (within task scope). |
| `ALLOWED_GATED` | The actor may perform this action only with explicit Controller or Human Owner approval. |
| `DENIED` | The action is prohibited. Performing it is a boundary violation. |

---

## 3. Repository Mutation Matrix

### 3.1 IEF-Program

| Mutation Path | Program Controller | Coordinator | Operator | Runner | Human Owner |
|---|---|---|---|---|---|
| Open issue | ALLOWED | ALLOWED | DENIED | DENIED | ALLOWED |
| Close issue | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Post issue comment (directive) | ALLOWED | ALLOWED | DENIED | DENIED | ALLOWED |
| Post issue comment (report) | ALLOWED | ALLOWED | ALLOWED_GATED | ALLOWED_GATED | ALLOWED |
| Open PR | ALLOWED | DENIED | DENIED | DENIED | ALLOWED |
| Merge PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Close PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Modify file (any) | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Create/release tag | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |

### 3.2 IEF-Operations

| Mutation Path | Program Controller | Coordinator | Operator | Runner | Human Owner |
|---|---|---|---|---|---|
| Open issue | ALLOWED | ALLOWED | DENIED | DENIED | ALLOWED |
| Close issue | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Post issue comment (directive) | ALLOWED | DENIED | DENIED | DENIED | ALLOWED |
| Post issue comment (delivery report) | DENIED | ALLOWED | ALLOWED_GATED | ALLOWED_GATED | ALLOWED |
| Open PR | ALLOWED | DENIED | ALLOWED_GATED | DENIED | ALLOWED |
| Merge PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Close PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Create branch | ALLOWED | ALLOWED_GATED | ALLOWED_GATED | DENIED | ALLOWED |
| Push commit (allowed files only) | DENIED | DENIED | ALLOWED_GATED | DENIED | ALLOWED |
| Push commit (non-allowed files) | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Modify task lifecycle spec | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Modify run ledger schema | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Modify frozen governance spec | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |

### 3.3 IEF-Protocol

| Mutation Path | Program Controller | Coordinator | Operator | Runner | Human Owner |
|---|---|---|---|---|---|
| Modify Protocol schema | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Open PR | ALLOWED | DENIED | DENIED | DENIED | ALLOWED |
| Merge PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Publish new version | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |

### 3.4 IEF-Governance

| Mutation Path | Program Controller | Coordinator | Operator | Runner | Human Owner |
|---|---|---|---|---|---|
| Modify governance profile | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Open PR | ALLOWED | DENIED | DENIED | DENIED | ALLOWED |
| Merge PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |

### 3.5 IEF-Runners / IEF-Knowledge / IEF-Adapters

| Mutation Path | Program Controller | Coordinator | Operator | Runner | Human Owner |
|---|---|---|---|---|---|
| Any file modification | DENIED | DENIED | DENIED | DENIED | ALLOWED_GATED |
| Open PR | ALLOWED | DENIED | DENIED | DENIED | ALLOWED |
| Merge PR | ALLOWED_GATED | DENIED | DENIED | DENIED | ALLOWED |
| Contract planning | DENIED (blocked) | DENIED (blocked) | DENIED (blocked) | DENIED (blocked) | ALLOWED_GATED |
| Implementation work | DENIED (blocked) | DENIED (blocked) | DENIED (blocked) | DENIED (blocked) | ALLOWED_GATED |

> **Note:** IEF-Runners, IEF-Knowledge, and IEF-Adapters remain blocked from contract planning and implementation until Program Controller explicitly unblocks the next stage.

---

## 4. Cross-Cutting Mutation Paths

### 4.1 Dispatch & Authorization

| Mutation Path | Allowed Actor(s) | Classification |
|---|---|---|
| Issue `DISPATCH_AUTHORIZED` | Program Controller, Human Owner | ALLOWED |
| Issue `DISPATCH_PROPOSAL` | Coordinator | ALLOWED |
| Issue `DISPATCH_MODIFIED` | Program Controller, Human Owner | ALLOWED |
| Issue `DISPATCH_DEFERRED` | Program Controller, Human Owner | ALLOWED |
| Implicit dispatch (timeout-based) | _(nobody)_ | **DENIED** |
| Auto-dispatch after idle period | _(nobody)_ | **DENIED** |
| Standing delegation across slices | _(nobody without per-slice renewal)_ | **DENIED** |

### 4.2 Lifecycle State Transitions

| Transition | Allowed Actor(s) | Classification |
|---|---|---|
| `pending → dispatched` | Coordinator (with DISPATCH_AUTHORIZED) | ALLOWED_GATED |
| `dispatched → running` | Operator / Runner | ALLOWED |
| `running → completed` | Runner (exit 0 + evidence) | ALLOWED |
| `running → failed` | Runner (non-zero exit) | ALLOWED |
| `running → blocked` | Runner (blocker detected) | ALLOWED |
| `running → waiting_approval` | Runner (gate reached) | ALLOWED |
| `waiting_approval → running` | Program Controller / Human Owner (approval) | ALLOWED_GATED |
| `blocked → escalated` | Runner / Operator | ALLOWED |
| `review_pending → accepted` | Reviewer (with evidence) | ALLOWED_GATED |
| `completed → accepted` | Reviewer (with evidence) | ALLOWED_GATED |
| Self-approval (any gate) | _(nobody)_ | **DENIED** |

### 4.3 Ledger Operations

| Mutation Path | Allowed Actor(s) | Classification |
|---|---|---|
| Append event | Runner / Operator (during run) | ALLOWED |
| Emit correction event | Runner / Operator (with reason) | ALLOWED |
| Rewrite/overwrite event | _(nobody)_ | **DENIED** |
| Delete event | _(nobody)_ | **DENIED** |
| Reorder events | _(nobody)_ | **DENIED** |
| Move task out of terminal state via correction | _(nobody)_ | **DENIED** |

### 4.4 Evidence & Artifacts

| Mutation Path | Allowed Actor(s) | Classification |
|---|---|---|
| Attach artifact to run | Runner / Operator | ALLOWED |
| Attach context ref to task | Coordinator / Operator | ALLOWED |
| Claim completion without evidence | _(nobody)_ | **DENIED** |
| Treat chat memory as durable evidence | _(nobody)_ | **DENIED** |
| Treat private conversation as directive source | _(nobody)_ | **DENIED** |

---

## 5. Stage G Hard Gates

These denials are **absolute** for the duration of Stage G and cannot be overridden by Coordinator or Operator:

1. **No merge** — No actor except Human Owner may merge any PR in any IEF repo.
2. **No close** — No actor except Human Owner may close any core issue.
3. **No cross-repo modification** — An operator dispatched to one repo must not modify any sibling repo.
4. **No downstream unblock** — IEF-Runners, IEF-Knowledge, IEF-Adapters remain blocked until Controller explicitly opens the next stage.
5. **No runtime changes** — No execution engine code, no runner implementation, no adapter code.
6. **No implicit authorization** — No time-based, idle-based, or assumed authorization.
7. **No self-approval** — No layer or actor may approve its own work.
8. **No scope expansion** — An operator must not expand task scope beyond the trigger JSON `allowed_files`.

---

## 6. References

| Reference | Relationship |
|---|---|
| [CONTROL_PLANE_FREEZE_SPEC.md](./CONTROL_PLANE_FREEZE_SPEC.md) | Frozen boundary definitions |
| [STAGE_G_CONTRACT_LOCK.json](../../schemas/STAGE_G_CONTRACT_LOCK.json) | Machine-readable contract lock |
| [IEF-Operations V0](../IEF_OPERATIONS_V0.md) Section 8.5 | Agent boundary obedience rules |
| [IEF-Program#11 comment 4763724671](https://github.com/everwork-ai/IEF-Program/issues/11#issuecomment-4763724671) | Controller decision source |
