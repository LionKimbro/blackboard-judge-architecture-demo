# 13 — Judge

## Purpose

The Judge arbitrates access to shared resources. It tracks who owns what and answers permission requests from organisms with a yes or no. It contains no behavior logic and no application knowledge.

---

## The Essential Role

The implementations below are models — examples of how a judge can be structured. The specific data fields, request types, and lease mechanics will vary from program to program depending on what organisms exist and where they might contest.

What is always true:

- The judge grants or denies permission to organisms.
- It mediates between organisms so that organisms do not have to mediate between each other.
- Each organism can focus entirely on its own view of the world — what it perceives, what state it is in, what it wants to do — without knowing that other organisms exist.
- The judge is what makes that insulation possible.

An organism that wants to act asks the judge. If granted, it proceeds. If denied, it yields. It does not need to inspect other organisms' state, check what else might be happening, or encode priority logic relative to its siblings. The judge absorbs all of that.

The shape of a judge — what it tracks, what it checks, how it communicates with organisms — should be designed around the specific contestation needs of the application. The two implementations below cover common cases, but they are possible starting points, not requirements.

---

## Base Implementation: Pointer-Only Judge

The minimal judge tracks a single thing: which organism currently owns the pointer.

```
coordination:
    pointer_owner : organism_name | None
```

Permission protocol:

```
function get_permission(request_type):
    owner ← current_organism.name

    if request_type == "CHECK":
        if pointer_owner not in (None, owner):
            return False
        return True

    if request_type == "COMMIT":
        if pointer_owner not in (None, owner):
            return False
        pointer_owner ← owner
        return True

    return False
```

Lease maintenance — called once per cycle after organisms run:

```
function maintain_judge():
    active_names ← { org.name for org in organisms if org.state != "IDLE" }
    if pointer_owner not in active_names:
        pointer_owner ← None
```

This is sufficient for most applications. Only one organism can be ACTIVE at a time because only one organism can hold the pointer. Conflicts resolve naturally: the first organism to call `get_permission("COMMIT")` wins; later organisms find the pointer taken and clear themselves.

### Two Request Types

**CHECK** — called when an organism begins its ARMED phase. Soft check: is the pointer free (or already mine)? Does not lock the pointer.

**COMMIT** — called when the organism commits to an active gesture (e.g., drag threshold crossed). Hard lock: sets `pointer_owner` to this organism.

The two-phase design avoids premature locking. An organism in ARMED is watching for intent confirmation; it has not committed. If the user releases before the threshold, the organism clears without ever having locked the pointer.

---

## Extended Implementation: Resource-Based Judge

Not all organisms need the pointer. A tooltip organism, for example, responds to motionlessness detected by a tokenizer and emits a volatile effect — it never needs pointer ownership, but it might want exclusive control of a `"tooltip"` slot so that only one tooltip is shown at a time.

The resource-based judge extends the base with a general named-resource locking system. Resources are arbitrary strings. The pointer itself may or may not be modelled as a resource — see below.

```
coordination:
    resource_holds  : { resource_id → organism_name }
    leases          : { organism_name → set of resource_id }
```

`"pointer"` is just another resource id. `resource_holds.get("pointer")` tells you who owns the pointer. No special field is needed.

Permission protocol (extended):

```
function get_permission(request_type, resources=[]):
    owner ← current_organism.name

    if request_type == "CHECK":
        for resource in resources:
            if resource_holds.get(resource) not in (None, owner):
                return False
        return True

    if request_type == "COMMIT":
        for resource in resources:
            if resource_holds.get(resource) not in (None, owner):
                return False
        -- Grant: record ownership of all requested resources.
        for resource in resources:
            resource_holds[resource] ← owner
        leases[owner] ← leases.get(owner, set()) | set(resources)
        return True

    return False
```

An organism that needs the pointer includes `"pointer"` in its resource list. An organism that does not need the pointer omits it entirely.

Lease maintenance (extended):

```
function maintain_judge():
    active_names ← { org.name for org in organisms if org.state != "IDLE" }

    for name in list(leases.keys()):
        if name not in active_names:
            release_lease(name)


function release_lease(name):
    resources ← leases.pop(name, set())
    for resource in resources:
        if resource_holds.get(resource) == name:
            resource_holds.pop(resource)
```

### When to Use the Extended Judge

The resource extension is useful when:

- Organisms exist that act independently of the pointer (tooltips, ambient animations, background processes).
- Two organisms might compete for the same named slot (e.g., only one tooltip at a time, only one status-bar message at a time).
- You want to prevent a specific object from being claimed even during the brief gap between one organism releasing and the next cycle running.
- Debugging: the resource table gives a precise, inspectable record of what is locked and by whom.


## What the Judge Must Not Do

- Check whether the pointer is over a specific area.
- Interpret gesture context (e.g., "this is a drag, not a click").
- Apply application-specific priority rules beyond resource availability.
- Emit effects.
- Modify the world model.
- Inspect `DERIVED` or `RAW`.

---

## Minimal Design

The judge should be as small as possible. Any logic that encodes application behavior belongs in the organisms, not the judge. When in doubt: if it requires knowledge of what the user is trying to do, it is not judge logic.

Priority between organisms is expressed by registration order, not by judge rules. See `12_organisms.md`.

When registration order is insufficient — for example, when priority between competing gestures should be data-driven rather than structural — an alternative bid-based coordination model is available. See `33_appendix_judge-bid-model.md`.
