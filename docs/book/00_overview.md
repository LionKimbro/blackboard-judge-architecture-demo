# 00 — Overview

## Purpose

This manual describes the **Blackboard-Judge Interaction Architecture** for Tkinter Canvas applications. It defines a structured pipeline for implementing complex, multi-gesture user interactions with strict separation between perception, behavior, coordination, and rendering.

The architecture's central insight is the **Judge**: a single coordination arbiter that insulates organisms from each other. An organism can be transplanted from one program to another — provided the world model is compatible — by rewiring the Judge and adjusting registration order, without modifying the organism itself. The organism is modular because it never encodes knowledge of other organisms; the Judge absorbs all of that.

The **Tokenizer/Organism split** complements this by keeping organism code clean: shared perceptual computations (hit-testing, drag thresholds, button transitions) live in tokenizers and are read by all organisms from `DERIVED`, rather than being duplicated inside each organism. This is a valuable optimization for maintainability, but it is not the source of modularity. Organisms coordinating through a Judge would remain modular even if they each performed their own environment sensing.

The blackboard — `RAW`, `DERIVED`, and the world model — is the shared medium through which all layers communicate without direct coupling.

**Projection** closes the loop. Organisms never touch the canvas directly; they emit effects, which mutate the world model or signal transient overlays. Projection then reconciles the current world model and volatile effects against the canvas, issuing the minimal set of create, update, and delete operations needed to bring it in sync. This keeps the canvas a pure view: it carries no authoritative state, imposes no constraints on organisms, and can be reconstructed at any time from the world model alone.

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
| DERIVED | RAW.current, RAW.previous, DERIVED.previous, world model | DERIVED.current | Minimal (tokenizer-local) |
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

On startup, a single **priming cycle** runs before any events arrive. It establishes `RAW.previous` and `DERIVED.previous` as meaningful baselines and performs the first projection render. All perception that depends on temporal deltas (motion, button transitions, drag thresholds) begins on the second cycle. See `10_raw.md`.

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
