# ADR — Use Retained-Mode Canvas Reconciliation

## Status

Accepted for the BAD-rendered demo.

## Decision

Projection uses retained-mode reconciliation.  It computes the desired
long-lived Canvas items from world state, compares them with its own current
item registry, then creates, updates, or deletes only the required items.

Projection may maintain a private mapping from logical visual keys to Canvas
item handles.  A tag scheme is also allowed when it makes projection ownership
clear.  Neither mapping nor tags are semantic world state.

## Immediate Effects

Immediate/volatile visual effects are not retained model items.  At the start
of each projection pass, Projection deletes every Canvas item that it owns and
tags as `immediate`.  It then creates the current frame's immediate items with
that tag.  An immediate therefore exists for exactly one rendered frame unless
the continuity/organism layer emits it again next cycle.

## Consequences

- The render differs intentionally from the original redraw-all demo.
- Stable world visuals retain their Canvas identity when their logical keys
  remain present.
- Projection needs explicit private bookkeeping and a documented key/tag
  convention.
- Tests should verify creation, update, deletion, and immediate cleanup
  behavior where they can do so without a live GUI.

## Evidence

- Original behavior: `src/demo/app.py` — `render_projection()`.
- Architecture target: `docs/book/15_projection.md`.

