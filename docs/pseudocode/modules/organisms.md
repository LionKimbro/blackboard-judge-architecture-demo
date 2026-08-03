# Module — Interaction Organisms

## Source Evidence

`src/demo/app.py` — `evaluate_organisms()`, `organism_*`, and
`handle_*_state()` functions.

## Render Target

`src/bad_demo/organisms.py`

## OWNS

- Organism finite-state-machine records and organism-local held/data values.
- Gesture behavior for hover, single-object drag, resize, marquee selection,
  and selected-group drag.
- Emission of semantic world-mutation and volatile projection-preview effects.

## READS

- RAW and DERIVED facts.
- Current durable world objects and committed selection.
- Judge permission results.

## CALLS

- `judge.get_permission()`.
- Effect emission helpers.
- Geometry helpers for calculations that are not perception, such as a marquee
  rectangle or clamped resize result.

## MAY SAFELY ASSUME

- Tokenizers have completed this cycle.
- The world model remains stable while all organisms run.
- The effect queue is empty when evaluation begins.

## ENSURES

- Organisms express interaction as episodes, normally IDLE → ARMED → ACTIVE.
- A committed interaction changes the world only by emitting an effect.
- In-progress feedback is emitted as volatile projection effects.
- No organism encodes knowledge of a sibling organism's behavior or priority.

## DOES NOT OWN

- Hit-testing or drag-threshold recognition, resource arbitration, direct world
  mutation, or direct Canvas drawing.

## Included Organisms

- Hover highlight: stateless per-cycle preview when the pointer is available.
- Resize object: handle press, threshold commit, resize preview and final
  resize effect.
- Drag object: press, threshold commit, position preview and final move effect.
- Marquee select: empty-space press, threshold commit, candidate preview and
  final selection effect.
- Drag selection group: selected-object press, threshold commit, group preview
  and final bounded move effect.

