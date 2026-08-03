# Aspect — Blackboard-Judge Ownership Boundaries

## Participating Modules

`app-shell`, `runtime`, `tokenizers`, `judge`, `organisms`, `effects-world`,
and `projection`.

## System Rules

| Concern | Sole owner | Other modules may do |
| --- | --- | --- |
| Raw input snapshot | runtime | read it |
| Perceptual facts | tokenizers | read them after tokenization |
| Gesture episodes | organisms | observe only through declared facts/effects |
| Resource coordination | judge | ask permission |
| Durable object and selection state | world through effects-world | read it |
| Canvas manifestation | projection | never treat it as authority |

- Tokenizers perform perception, including hit-testing and drag-threshold
  recognition.  They do not emit effects or implement gestures.
- Organisms implement gesture episodes and emit effects.  They do not mutate
  the world or draw.
- The Judge knows resource ownership but not gesture meaning or hit geometry.
- Effects-world is the only writer of the durable world.
- Projection reads the world and current volatile effects; it does not decide
  semantic truth or mutate the world.

## Sources

- `docs/book/01_core_principles.md`
- `docs/book/11_tokenizers.md`
- `docs/book/12_organisms.md`
- `docs/book/13_judge.md`
- `docs/book/14_world_model.md`
- `docs/book/15_projection.md`

