# 33 — Appendix: Bid-Based Judge (Order-Independent Coordination)

> **This is an optional variant.** Do not mix with the default START/HOLD model in the same system. Use only when order-based HOLD resolution is insufficient for the application's needs.

---

## When to Consider This

The default CHECK/COMMIT model resolves conflicts by registration order: the first organism to successfully call `get_permission("COMMIT")` wins. This is simple, predictable, and sufficient for most applications.

It becomes awkward when:

- Priority between competing gestures should depend on input data, not on which organism was registered first.
- Registration order feels like the wrong place to encode policy — it is structural, invisible, and hard to reason about when priorities are complex.
- The application has many overlapping gestures whose relative precedence is context-dependent.

The bid-based judge moves conflict resolution from registration order into an explicit, inspectable policy function inside the judge.

---

## The Core Idea

Organisms **bid** for resources during a dedicated phase. Each organism either submits a bid or stays silent. The judge collects all bids, applies a policy, and marks winners. Organisms then read their own result and activate or clear accordingly.

Organisms remain fully independent. A bid is constructed only from `RAW`, `DERIVED`, and the organism's own local data. No organism knows what other bids were submitted or who else is competing.

---

## Organism Record (extended)

```
organism:
    name     : string
    active   : bool
    state    : string
    held     : dict
    data     : dict
    fn       : function
    bid      : dict | None   -- set during bidding phase; None if not bidding
    approved : bool          -- set by judge; True if this organism won
```

`bid` and `approved` are ephemeral — they exist only within a single cycle. Both are reset at the start of each bidding phase and must never be read or relied upon after `apply_decision` has run. Do not persist, cache, or carry bids across cycles.

---

## Revised Cycle

```
function run_cycle(raw_input):
    advance_snapshots()
    populate_raw(raw_input)
    run_tokenizers()

    -- Bidding phase: only IDLE organisms bid
    for each organism in organisms:
        organism.bid      ← None
        organism.approved ← False
        if organism.state == "IDLE":
            organism.fn.submit_bid(organism)

    -- Judge phase: set approved on winners
    judge_decide(organisms)

    -- Response phase: organisms check their own approved flag
    for each organism in organisms:
        organism.fn.apply_decision(organism)

    -- Step phase: active organisms emit effects
    for each organism in organisms:
        organism.fn.step(organism)

    route_effects()
    render_projection()
```

Only IDLE organisms bid. An organism already in ARMED or ACTIVE has already committed; it participates in `step()` but not in bidding.

---

## Organism Interface

### submit_bid

```
function organism_NAME.submit_bid(organism):
    if not [triggering condition from RAW / DERIVED]:
        return    -- stay silent; organism.bid remains None

    organism.bid ← {
        resource : "pointer",
        priority : [score computed from RAW, DERIVED, organism.data],
        claim    : { ... }    -- optional metadata for the judge
    }
```

### apply_decision

```
function organism_NAME.apply_decision(organism):
    if organism.bid is None:
        return    -- did not bid; nothing to apply

    if organism.approved:
        organism.state ← "ARMED"    -- or "ACTIVE" if no threshold phase needed
        organism.data  ← { ... }    -- record context for step()
    else:
        clear(organism)
```

### step

```
function organism_NAME.step(organism):
    if organism.state not in ("ARMED", "ACTIVE"):
        return

    -- progress state machine, emit effects as usual
```

---

## Judge Policy

```
function judge_decide(organisms):
    -- Group bidding organisms by resource.
    by_resource ← {}
    for each organism in organisms:
        if organism.bid is not None:
            resource ← organism.bid.resource
            by_resource[resource] ← by_resource.get(resource, []) + [organism]

    -- For each contested resource, pick a winner.
    for resource, candidates in by_resource:
        winner ← select_winner(candidates)
        winner.approved ← True


function select_winner(candidates):
    -- Policy is application-defined.
    -- May use bid.priority, bid.claim, condition counts, or any combination.
    -- Must produce exactly one winner per resource per cycle.
    return max(candidates, key=lambda org: org.bid.priority)
```

The policy function is the sole location for conflict resolution logic. It may be as simple as comparing a numeric priority, or as elaborate as the application requires. Whatever would otherwise be encoded in registration order lives here explicitly.

---

## Notes on Implementation

There are many valid ways to structure this pattern. The above is one clean form, not a prescription. Variations include:

- Using a shared bids list rather than organism-local fields.
- Separating `submit_bid` and `apply_decision` into a single function that runs twice.
- Allowing non-IDLE organisms to submit bids for resources they don't yet hold.
- Resolving multiple resources independently in a single judge pass.

What must remain constant across variations:

- Organisms do not mutate state during bidding.
- Bids depend only on `RAW`, `DERIVED`, and organism-local data.
- The judge produces exactly one winner per resource per cycle.
- Organisms read only their own result — never another organism's bid or approved flag.

---

## Comparison With START/HOLD

| | CHECK/COMMIT | Bid-Based |
|---|---|---|
| Conflict resolution | Registration order | Policy function in judge |
| Policy location | Implicit (organism list order) | Explicit (judge) |
| Organism independence | Full | Full |
| Cycle complexity | Simple | Higher (four organism phases) |
| When to use | Most applications | Complex overlapping gestures with data-driven priority |
