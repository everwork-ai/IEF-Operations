# IEF-Work

> IEF Work Layer -- the work operating system for enterprise AI workers.

## One-sentence role inside IEF

Tracks tasks, run state, ownership, workflow progress, and execution lifecycle for all AI work managed by the IEF system.

## What this repository owns

- Task objects and lifecycle management
- Run objects and execution tracking
- Workflow objects and state machines
- Queues, priorities, and scheduling
- Dependencies, retry, and escalation logic
- Approval checkpoints and gates
- Run ledger / event log
- Artifact linkage and pointers
- Wake/resume/cancel mechanics

## What this repository explicitly does NOT own

- External runtime prompts (that is IEF-Adapters)
- Long-term policy definitions (that is IEF-Governance)
- Vendor-specific worker logic (that is IEF-Workers)
- External protocol standardization (that is IEF-Protocol)
- Knowledge storage and retrieval (that is IEF-Knowledge)

## Core objects

| Object | Description |
|---|---|
| `Task` | A bounded unit of work with type, risk level, owner, state |
| `Run` | A concrete execution attempt of a task or task slice |
| `Workflow` | A multi-step graph of tasks and approvals |
| `StatusEvent` | Typed update emitted during work (queued, running, blocked, completed, etc.) |
| `ArtifactRef` | Pointer to an artifact produced during execution |

## Inputs

- Work requests from adapters or external systems
- Protocol task envelopes from IEF-Protocol
- Policy requirements from IEF-Governance
- Context packs from IEF-Knowledge
- Worker capability matches from IEF-Workers
- Manual approvals from human operators

## Outputs

- Task instances with lifecycle state
- Run instances with status and logs
- Status transitions and events
- Worker assignments
- Approval requests
- Completion packages

## Dependencies on other IEF repos

| Dependency | Direction | Purpose |
|---|---|---|
| IEF-Governance | consumed | Policy rules, approval gates, risk classification |
| IEF-Protocol | consumed | Shared schemas for Task, Run, StatusEvent, Artifact |
| IEF-Knowledge | consumed | Context packs, project memory, playbook references |
| IEF-Workers | consumed | Worker capability matches and execution assignments |
| IEF-Adapters | produced | Work objects for external host environments |

## Current status

- [x] Repository created
- [ ] Task object schema defined
- [ ] Run object schema defined
- [ ] State machine defined
- [ ] Queue and assignment logic defined
- [ ] Artifact linkage defined
- [ ] Resume/cancel semantics defined

## Near-term roadmap

1. Define Task, Run, Workflow JSON schemas
2. Define minimum task lifecycle state machine
3. Define minimum run lifecycle state machine
4. Design queue and assignment logic
5. Design artifact linkage and pointer system
6. Design resume/cancel/wake mechanics

## Naming / glossary references

| Term | Meaning |
|---|---|
| Task | A bounded unit of work |
| Run | A concrete execution attempt |
| Workflow | A multi-step graph of tasks and approvals |
| StatusEvent | Typed update emitted during work |
| Artifact | A tangible output produced during work |

---

**This is the most important missing repository in IEF.**
Without this layer, IEF remains a set of valuable parts instead of a working system.

See [IEF Design Pack v0.2](https://github.com/brantzh6/IEF-Governance/blob/main/docs/IEF_Design_Pack_v0.2.md) for full architecture context.
