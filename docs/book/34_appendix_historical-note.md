# 34 — Appendix: Historical Terminology

This note exists so that older documents, code, or conversations using earlier terminology can be understood in relation to the current manual.

---

## Permission Request Types

| Current name | Former name | Notes |
|---|---|---|
| `CHECK` | `START` | The feasibility check an organism makes before entering ARMED. The old name implied something was beginning; the new name correctly describes the operation: it checks resource availability without locking anything. |
| `COMMIT` | `HOLD-RESOURCE`, `HOLD` | The hard lock an organism acquires when escalating from ARMED to ACTIVE. The old names described resource retention; the new name describes the organism's decision: it is committing to the gesture. |

These were renamed because `START` suggested that calling it initiated something (it does not — no lock is acquired), and `HOLD-RESOURCE` was verbose while `HOLD` alone was ambiguous. `CHECK` / `COMMIT` form a cleaner conceptual pair: feasibility vs. commitment.



