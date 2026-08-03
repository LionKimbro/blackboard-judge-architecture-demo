# BAD Pseudocode System

This directory is the normative BAD design layer for the Blackboard-Judge demo.
It is semantic pseudocode and bounded design, not executable Python.  The
rendered application is planned for `src/bad_demo/`; the original demo in
`src/demo/` is preserved as source evidence.

## Layout

- `project-profile/` — target habitat, conventions, and project-wide assumptions.
- `modules/` — bounded sketches for renderable implementation regions.
- `interfaces/` — capabilities supplied by Python, Tkinter, and the host system.
- `aspects/` — cross-cutting contracts and rules that apply across modules.

## Reading and Rendering Rule

Each module sketch names both its **source evidence** and its **render target**.
The source evidence explains where the sketch came from.  The render target is
where a future BAD render should place the implementation.  A render may make
routine local decisions, but must not change a boundary, ownership rule, or
open decision without recording that change explicitly.

## Initial Scope

This first breakdown describes the current canvas demo at roughly one or two
levels above its Python implementation.  Deliberate differences from the
current source are recorded in `adr/` before they guide a render.

## Planned Render Map

| BAD sketch | Planned Python target |
| --- | --- |
| Application Shell | `src/bad_demo/app_shell.py` |
| Interaction Runtime | `src/bad_demo/runtime.py` |
| Tokenizers | `src/bad_demo/tokenizers.py` |
| Judge | `src/bad_demo/judge.py` |
| Interaction Organisms | `src/bad_demo/organisms.py` |
| Effects and World Mutation | `src/bad_demo/effects_world.py` |
| Projection | `src/bad_demo/projection.py` |
| Geometry and Query Helpers | `src/bad_demo/geometry.py` |
