# Interface — Monotonic Clock

## Provided By

Python standard library: `time.monotonic()`.

## Used For

- Producing monotonic millisecond values for RAW input snapshots.
- Measuring how long the pointer has been motionless.

## Relied-Upon Facts

- Values do not move backward during the process lifetime.
- The clock is not semantic application state; it is an observed input fact.

## Project Rules

- Wrap clock access in one function so tests can replace it deterministically.
- Tokenizers may compare RAW timestamps; organisms read the resulting derived
  facts rather than inventing independent timing state.

