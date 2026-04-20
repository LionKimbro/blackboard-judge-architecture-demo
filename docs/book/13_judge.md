# 13 — Judge

## Purpose

The Judge arbitrates access to shared resources. It tracks who owns what and answers permission requests from organisms with a yes or no. It contains no behavior logic and no application knowledge.

---

## Coordination Record

```
coordination:
    pointer_owner   : organism_name | None
    resource_holds  : { resource_id → organism_name }
    leases          : { organism_name → lease }

lease:
    resources   : set of resource_id
    kind        : "exclusive"
```

---

## Permission Protocol

Organisms call `get_permission()` as part of their own logic. There are two request types:

### START

Requested when an organism first attempts to engage with a gesture.

```
get_permission("START", resources) → bool
```

Granted when:
- The pointer is unowned, or owned by this organism.
- None of the listed resources are held by another organism.

On grant: the organism may proceed but has not yet locked resources. (It may be denied `HOLD-RESOURCE` later if conditions change.)

### HOLD-RESOURCE

Requested when the organism commits to an active gesture (e.g., drag threshold crossed).

```
get_permission("HOLD-RESOURCE", resources) → bool
```

Granted when:
- The pointer is unowned or owned by this organism.
- All listed resources are available (not held by another organism).

On grant: the organism is recorded as the exclusive holder of all listed resources and as the pointer owner.

---

## Implementation

```
function get_permission(request_type, resources):
    owner ← current_organism.name

    if request_type == "START":
        if pointer_owner not in (None, owner):
            return False
        for resource in resources:
            if resource_holds.get(resource) not in (None, owner):
                return False
        return True

    if request_type == "HOLD-RESOURCE":
        if pointer_owner not in (None, owner):
            return False
        for resource in resources:
            if resource_holds.get(resource) not in (None, owner):
                return False
        -- Grant: record ownership
        pointer_owner ← owner
        for resource in resources:
            resource_holds[resource] ← owner
        leases[owner] ← { resources: set(resources), kind: "exclusive" }
        return True

    return False
```

---

## Lease Maintenance

The Judge must release stale leases — leases held by organisms that are now IDLE. This is called once per cycle, typically at the start or end of the organism pass.

```
function maintain_judge():
    active_names ← { org.name for org in organisms if org.state != "IDLE" }

    for name in list(leases.keys()):
        if name not in active_names:
            release_lease(name)

    if pointer_owner not in leases:
        pointer_owner ← None


function release_lease(name):
    lease ← leases.pop(name, None)
    if lease is None:
        return
    for resource in lease.resources:
        if resource_holds.get(resource) == name:
            resource_holds.pop(resource)
    if pointer_owner == name:
        pointer_owner ← None
```

`maintain_judge()` is called once per cycle, after organisms have run. This ensures that when an organism returns to IDLE (by calling `clear()`), its lease is promptly revoked and the resources become available to other organisms in the next cycle.

---

## Resource Naming

Resources are strings. The architecture does not prescribe names; the application chooses them. Conventions:

- `"pointer"` — the pointer itself, used for gestures that claim mouse focus without needing a world object.
- Object ids (e.g., `"node-alpha"`) — specific world objects.
- Logical resources (e.g., `"viewport"`, `"group-selection"`) — abstract shared concerns.

Using the object id as the resource id means two organisms cannot hold the same object simultaneously, which is typically the desired behavior.

---

## What the Judge Must Not Do

- Check whether a pointer is over a specific area.
- Interpret gesture context (e.g., "this is a drag, not a click").
- Apply application-specific priority rules beyond resource availability.
- Emit effects.
- Modify the world model.
- Inspect `DERIVED` or `RAW`.

---

## Minimal Design

The judge should be as small as possible. Any logic that encodes application behavior belongs in the organisms, not the judge. When in doubt: if it requires knowledge of what the user is trying to do, it is not judge logic.
