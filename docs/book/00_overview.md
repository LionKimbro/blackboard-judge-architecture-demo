# 00 — Overview

## Purpose

This manual describes the **Tokenizer–Organism Interaction Architecture** for Tkinter Canvas applications. It defines a structured pipeline for implementing complex, multi-gesture user interactions with strict separation between perception, behavior, coordination, and rendering.

---

## The Pipeline

Every interaction cycle follows this sequence:

```
RAW → DERIVED → ORGANISMS → EFFECTS → WORLD MODEL → PROJECTION
                    ↕
                  JUDGE
```

1. **RAW** — Raw input snapshot for the current frame (mouse position, button states, time).
2. **DERIVED** — Tokenizers read RAW and compute interpreted perceptual facts.
3. **ORGANISMS** — Stateful processes read RAW and DERIVED, petition the Judge, and emit effects.
4. **JUDGE** — Arbitrates resource ownership; grants or denies organism requests.
5. **EFFECTS** — Outputs of organisms; either mutate the world model (persistent) or signal the projection system to render a transient overlay for this frame (volatile).
6. **WORLD MODEL** — Authoritative persistent state; mutated only via effects.
7. **PROJECTION** — Reconciles the world model and volatile effects against the canvas; issues minimal create/update/delete operations.

---

## Layer Summary

| Layer | Reads | Writes | Holds State |
|---|---|---|---|
| RAW | Tk events | RAW.current, RAW.previous | No (snapshot) |
| DERIVED | RAW.current, RAW.previous, DERIVED.previous | DERIVED.current | Minimal (tokenizer-local) |
| ORGANISMS | RAW, DERIVED | Effects | Yes (FSM state) |
| JUDGE | Organism requests | Coordination record | Yes (resource table) |
| WORLD MODEL | — | — | Yes (durable) |
| PROJECTION | World model, volatile effects | Canvas | Yes (canvas state) |

---

## One Cycle

```
function run_cycle(raw_input):
    advance_snapshots()          # current → previous for RAW and DERIVED
    populate_raw(raw_input)      # install new RAW.current
    run_tokenizers()             # produce DERIVED.current
    run_organisms()              # each organism may call get_permission(), emit effects
    route_effects()              # apply world-mutation effects; retain volatile effects
    render_projection()          # reconcile canvas against world + volatile effects
```

The cycle is triggered by Tk event callbacks. A periodic timer may also trigger cycles so time-based organisms can progress without pointer activity.

---

## Files in This Manual

| File | Contents |
|---|---|
| `01_core_principles.md` | Invariants and separation of concerns |
| `02_data_contracts.md` | Field definitions for each layer |
| `10_raw.md` | RAW input snapshot specification |
| `11_tokenizers.md` | Tokenizer protocol and canonical set |
| `12_organisms.md` | Organism template and examples |
| `13_judge.md` | Judge protocol and resource model |
| `14_world_model.md` | World model structure and mutation rules |
| `15_projection.md` | Reconciliation algorithm and canvas mapping |
| `20_example_marquee_selection.md` | Full pipeline: marquee selection |
| `21_example_node_linking.md` | Full pipeline: edge creation by drag |
| `22_example_drag_and_resize.md` | Full pipeline: drag and resize |
| `30_failure_modes.md` | Anti-patterns and how they manifest |
| `31_design_notes.md` | Design rationale |
| `32_appendix_patterns.md` | Reusable pseudocode patterns |
