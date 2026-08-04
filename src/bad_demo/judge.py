"""Resource-only coordination authority for interaction organisms."""

CHECK = "CHECK"
COMMIT = "COMMIT"


def clear_coordination(coordination):
    coordination.update({"pointer-owner": None, "active-gesture": None,
                         "resource-holds": {}, "leases": {}, "judge-notes": []})


def get_permission(coordination, organism_name, request, resources):
    """Return whether an organism may check or commit its requested resources."""
    for resource in resources:
        owner = coordination["resource-holds"].get(resource)
        if owner not in (None, organism_name):
            coordination["judge-notes"].append(f"denied {request}: {resource} held by {owner}")
            return False
    if request == CHECK:
        return True
    if request != COMMIT:
        return False
    for resource in resources:
        coordination["resource-holds"][resource] = organism_name
    coordination["leases"][organism_name] = list(resources)
    if "pointer" in resources:
        coordination["pointer-owner"] = organism_name
        coordination["active-gesture"] = organism_name
    return True


def maintain_judge(coordination, organisms):
    """Release resource leases held by organisms that are no longer active."""
    active = {org["NAME"] for org in organisms if org["STATE"] != "IDLE"}
    for name in list(coordination["leases"]):
        if name not in active:
            for resource in coordination["leases"].pop(name):
                if coordination["resource-holds"].get(resource) == name:
                    coordination["resource-holds"].pop(resource)
    owner = coordination["pointer-owner"]
    if owner not in active:
        coordination["pointer-owner"] = None
        coordination["active-gesture"] = None
