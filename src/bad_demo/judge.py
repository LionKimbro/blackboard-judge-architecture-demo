"""Resource-only coordination authority for interaction organisms."""

from . import organisms

CHECK = "CHECK"
COMMIT = "COMMIT"

coordination = {}


def initialize_judge():
    coordination.clear()
    coordination.update({"pointer-owner": None, "active-gesture": None,
                         "resource-holds": {}, "leases": {}, "judge-notes": []})


def clear_coordination():
    initialize_judge()


def get_permission(organism_name, request, resources):
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


def maintain_judge():
    """Release resource leases held by organisms that are no longer active."""
    active = organisms.get_active_organism_names()
    for name in list(coordination["leases"]):
        if name not in active:
            for resource in coordination["leases"].pop(name):
                if coordination["resource-holds"].get(resource) == name:
                    coordination["resource-holds"].pop(resource)
    if coordination["pointer-owner"] not in active:
        coordination["pointer-owner"] = None
        coordination["active-gesture"] = None
