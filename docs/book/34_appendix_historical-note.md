# 34 — Appendix: Historical Terminology

This note exists so that older documents, code, or conversations using earlier terminology can be understood in relation to the current manual.

---

## Permission Request Types

| Current name | Former name | Notes |
|---|---|---|
| `CHECK` | `START` | The feasibility check an organism makes before entering ARMED. The old name implied something was beginning; the new name correctly describes the operation: it checks resource availability without locking anything. |
| `COMMIT` | `HOLD-RESOURCE`, `HOLD` | The hard lock an organism acquires when escalating from ARMED to ACTIVE. The old names described resource retention; the new name describes the organism's decision: it is committing to the gesture. |

These were renamed because `START` suggested that calling it initiated something (it does not — no lock is acquired), and `HOLD-RESOURCE` was verbose while `HOLD` alone was ambiguous. `CHECK` / `COMMIT` form a cleaner conceptual pair: feasibility vs. commitment.

---

## Architecture Name

The architecture was originally called the **Tokenizer–Organism Interaction Architecture**. It was renamed to the **Blackboard-Judge Interaction Architecture** to reflect that the Judge — not the Tokenizer/Organism split — is the central insight. The Tokenizer/Organism separation is a valuable optimization that keeps organism code clean, but organism modularity is made possible by the Judge. The Tokenizer/Organism split eliminates redundant perception code; the Judge eliminates inter-organism coupling.
