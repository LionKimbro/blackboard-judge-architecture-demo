# Project Profile — Blackboard-Judge BAD Render Demo

## Target

- Language: Python 3.10 or later.
- Host platform: Windows 11 desktop application.
- Rendered package target: `src/bad_demo/`.
- User-interface toolkit: Python Tkinter.
- Direct-manipulation surface: `tkinter.Canvas`.
- Test target: ordinary Python tests under `tests/`, runnable without opening a
  Tk window where practical.

## Purpose

Render a small, inspectable demonstration of the Blackboard-Judge interaction
architecture.  The demonstration supports object selection, marquee selection,
single-object dragging, group dragging, resize handles, hover feedback, and an
optional quantization grid.

The rendered demo is a controlled re-expression of `src/demo/app.py`, not a
replacement for that original source.

## Project-Wide Assumptions and Rules

- Tkinter widgets, their callbacks, and all Canvas operations run on the
  Tkinter main thread.
- Callbacks are thin adapters: they normalize toolkit input and advance or
  request the interaction cycle; they do not contain gesture behavior.
- The world model is authoritative for durable demo state.  Canvas items are
  projection artifacts, never the source of semantic truth.
- Raw input, perceptual facts, organism behavior, coordination, durable world
  mutation, and projection have separate owners.
- Persistent profile or project data, if introduced, is UTF-8 JSON.  The
  current demonstration has no persistence requirement.
- Shared program context is visible and inspectable.  Arguments express real
  caller choices rather than stable context or current machine state.
- Startup work occurs from an explicit entry point; imports stay passive.

## Governing References

### B.A.D. Method (Bounded Agentic Development)
- `C:\lion\github\bad-development-ruminition\docs\distillation\basic-method.md`

### Project Folder Structure
- `C:\lion\github\lions-documents\raw\0012__python-2026-03-project-structure-agent-guide-short.md`

### Programming Guidelines
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0100_globals.style-card.md`
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0210_function_names.style-card.md`
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0220_function_arguments.style-card.md`
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0400_machines.style-card.md`
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0410_registers.style-card.md`
- `C:\lion\github\lions-documents\coding-guidelines\style-cards\0800_python_rules.style-card.md`
- `C:\lion\github\lions-documents\raw\0010__lions-tkinter-development-conventions_v1.json`

### CIRA Architecture

- `C:\lion\github\reducer-core-architecture\docs\raw\0004__cira_agentic-implementation-brief.json`


## Local Architecture References

- `docs/book/00_overview.md`
- `docs/book/01_core_principles.md`
- `docs/book/02_data_contracts.md`
- `docs/book/10_raw.md`
- `docs/book/11_tokenizers.md`
- `docs/book/12_organisms.md`
- `docs/book/13_judge.md`
- `docs/book/14_world_model.md`
- `docs/book/15_projection.md`

There are also examples and design notes and appendixes in the docs/book for perusal.

Do not waste tokens reading the large .PNG image file in the directory.
