# ADR — Use CHECK and COMMIT Permission Terms

## Status

Accepted for the BAD-rendered demo.

## Decision

The rendered Judge API and all related documentation, debug panel output, and
tests use:

- `CHECK`: a soft feasibility query that acquires no resource.
- `COMMIT`: a hard claim that records the requested resource lease.

The older source names `START` and `HOLD-RESOURCE` are retained only as
provenance terminology when referring to the original demo.

## Consequences

- The re-render intentionally uses current CIRA/architecture terminology.
- Organisms express the same two-phase interaction structure with clearer
  vocabulary: CHECK while arming, COMMIT when the gesture commits.
- No compatibility alias is required in the new `bad_demo` package.

## Evidence

- Original terminology: `src/demo/app.py`.
- Historical mapping: `docs/book/34_appendix_historical-note.md`.
- Current architecture terms: CIRA implementation brief.

