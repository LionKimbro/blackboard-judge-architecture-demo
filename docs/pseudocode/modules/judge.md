# Module — Judge

## Source Evidence

`src/demo/app.py` — `maintain_judge()`, permission helpers, coordination
writers, and `get_permission()`.

## Render Target

`src/bad_demo/judge.py`

## OWNS

- COORDINATION: pointer owner, active gesture, resource holds, leases, hover
  target, and diagnostic notes.
- Permission decisions for CHECK and COMMIT requests.
- Releasing claims when their corresponding organism is no longer active.

## READS

- The requesting organism identity and requested resources.
- Minimal public organism state necessary to verify active leases.

## CALLS

- No behavior module.  This module is a coordination authority, not an
  interaction dispatcher.

## MAY SAFELY ASSUME

- Organisms ask permission instead of examining one another.
- An organism asks CHECK before it becomes armed and COMMIT only when it has
  established intent.

## ENSURES

- At most one exclusive pointer gesture owns the pointer at a time.
- Resource ownership is inspectable and released when stale.
- The Judge contains no hit-testing, gesture semantics, or world mutation.

## DOES NOT OWN

- RAW/DERIVED perception, organism FSM transitions, effects, world objects,
  selection semantics, or projection.

## Sketch

```text
function get_permission(request, resources=[]):
    if request == CHECK:
        return resources_are_available_or_already_mine(resources)
    if request == COMMIT:
        if resources_are_not_available(resources):
            return False
        record_resource_lease_for_current_organism(resources)
        return True
    return False
```

