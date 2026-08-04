# Aspect — Input Event Queue and Motion Coalescing

## Participating Modules

`canvas-host-window`, `event-queue`, `timer`, and `interaction-runtime`.

## System Rule

Tk callbacks do not call `interaction_runtime.run_cycle()` directly.  They post normalized
input events to Input Event Queue.  The periodic runtime update drains the
queue and advances the interaction architecture.

## Pointer-Motion Rule

- A pointer-motion event is a packet containing an ordered `samples` list.
- Each sample records the Canvas-relative `x`, `y`, and a monotonic `ms` time.
- When posting a motion event, Input Event Queue examines only its pending tail.
  If that tail is another pointer-motion event, it appends the new sample.
- If the queue tail is any other event, it appends a new motion packet instead.
- Runtime consumes the samples of a packet in order.  Coalescing therefore
  changes queue representation, not observed input order.

## Consequences

- Fast pointer movement does not create one queue record per Tk callback.
- The complete observed motion sequence remains available to the runtime.
- Button/key/control events preserve their ordering boundaries relative to
  motion packets.

## Does Not Mean

- A motion packet is not a durable history record.
- Coalescing does not combine motions that have already been drained.
- Projection and organisms do not read the event queue directly.
