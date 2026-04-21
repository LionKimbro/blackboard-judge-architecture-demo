# 31 — Design Notes

## Why a Blackboard?

The term "blackboard" refers to the shared, readable state — RAW, DERIVED, the world model — that all layers write to or read from according to their role. Each layer has a defined relationship to the blackboard: some write a section, others read from it. No layer reads sections it is not permitted to read; no layer writes sections it does not own.

This is different from a message-passing architecture, where layers communicate only by sending explicit messages. In the blackboard model, the current state is always visible to the appropriate consumers without additional routing. Tokenizers write DERIVED; organisms read it directly. This is intentional: it keeps the per-cycle communication simple and synchronous.

---

## Why a Judge?

Without a Judge, organisms must negotiate among themselves. This produces organisms that are aware of each other — checking each other's state, deciding whether to yield, encoding priority rules. As the organism count grows, each new organism requires understanding all existing organisms.

The Judge externalizes the negotiation. Organisms ask a neutral party for permission; they receive yes or no. An organism does not need to know about other organisms to be denied a resource that another holds. Adding a new organism does not require modifying existing organisms, as long as the new one participates in the same permission protocol.

Application logic is expected to enter the Judge. UI interactions are inherently entangled — gestures compete, priorities depend on context, and new organisms do not naturally coexist with existing ones without coordination. That coordination has to live somewhere. The Judge is where it lives, by design.

When a new organism is added, the Judge will likely need to be updated: resources must be allocated, priorities must be expressed, and room must be made. This is an expected cost, not a failure. The goal is not to keep the Judge empty — it is to keep that complexity *out of the organisms* and centralized in one place. An organism that can be understood in isolation, exercised independently, and transplanted to another application is worth the cost of a Judge that must be consulted when the application grows.

Think of the Judge as the remainder of a division: when you modularize organisms as completely as possible, what is left over — the residual coordination logic that cannot be made local to any one organism — collects in the Judge. It cannot be eliminated; it can only be centralized.

---

## Why Two Permission Types?

`CHECK` and `COMMIT` serve different purposes.

`CHECK` is a soft feasibility test. It verifies that the resources the organism needs are not already locked by another, but does not lock them. This allows an organism to begin its ARMED phase — where it is watching for confirmation that the gesture is real — without preventing other organisms from also arming. Multiple organisms may be ARMED simultaneously, all having passed their CHECK.

`COMMIT` is a hard lock. It is called when the gesture has been confirmed (threshold crossed, intent established). At this point, the resource is locked exclusively. Only one organism may hold a given resource. This is where conflicts are resolved: the first organism to call `COMMIT` for a contested resource wins; later organisms are denied and clear.

  Note: For an alternative that resolves conflicts through an explicit bid-based priority policy rather than registration order, see `33_appendix_judge-bid-model.md`.

This two-phase design avoids premature locking. A single-click followed by a release should not leave a resource locked for the entire click duration if the organism never progressed past ARMED. The lock is acquired only when the intent is established.

---

## Why ARMED Before DRAGGING?

The ARMED state exists to absorb ambiguity. A press on an object might become a click (release quickly) or a drag (move enough). The organism cannot know which at press time.

ARMED lets the organism observe subsequent events without committing resources. On quick release, the organism clears cleanly, possibly emitting a click effect. On threshold crossing, the organism escalates and acquires the lock.

Without ARMED, the organism must either lock immediately at press (preventing other organisms from responding to a quick click on the same object) or use ad-hoc flags to defer locking (duplicating the ARMED concept without naming it).

---

## Why Volatile Effects?

Volatile effects allow organisms to communicate transient visual state — marquee rectangles, hover highlights, drag previews, edge previews — without storing that state in the world model.

The world model should contain only durable state: what exists, where it is, what is selected. A marquee rectangle is not a durable world entity; it is a rendering artifact of an in-progress gesture. If it were stored in the world model, the projection system would need to know to remove it when the gesture ends. The organism would need to explicitly clean up. Serialization would capture it.

Volatile effects solve all of this: they are emitted each cycle while active and simply absent when the gesture ends. The projection system finds them in the effect queue; if they are not there, they are not drawn.

---

## Why Reconciliation?

Reconciliation (diff-based projection) is the correct model for a retained-mode canvas. Tkinter Canvas items have identity: they persist between frames and can be moved or restyled without recreation.

Full clear-and-redraw works but wastes canvas operations and can cause flicker or selection loss if canvas items carry state (tags, bindings). More importantly, it misrepresents the semantics: a moving object is still the same object, not a new one.

Reconciliation makes the projection system a pure function of its inputs at the semantic level: given the same world model and volatile effects, it produces the same visual output. The implementation tracks canvas item identity to achieve this efficiently.

---

## Why Not Event-Driven Organisms?

An alternative design lets organisms subscribe to events — either raw input events (press, release, motion) or interpreted DERIVED events ("drag threshold crossed," "button pressed") — and activate only when a relevant event fires.

The theoretical appeal is efficiency: each condition is tested once, and only organisms that subscribed to that condition are notified. But tokenizers already achieve this. Every perceptual test runs exactly once per cycle, and every organism reads the result directly from DERIVED. There is no redundant testing to eliminate. Routing results through a subscription system rather than a shared blackboard would reduce per-cycle overhead by a negligible amount while adding a layer of indirection — topics, subscriptions, delivery order — that the cycle model simply does not need.

A further problem: the events an organism cares about depend on its current state. An organism in IDLE wants "button pressed"; in ARMED it wants "threshold crossed" and "button released"; in ACTIVE it wants "button released." A subscription system would therefore need to either (a) subscribe the organism to all events it might ever need in any state, and check state inside each handler anyway, or (b) track organism state and rewire subscriptions on every transition. Option (a) recovers most of the per-cycle cost; option (b) requires substantial infrastructure just to route events correctly. In neither case is the state logic eliminated — it is only moved around.

The cycle model is chosen because it is straightforward to think about. Every organism runs every cycle. State is read directly. There is no question of delivery order, missed events, or subscription management. The simplicity is worth more than the hypothetical optimization.

The one real cost is that organisms must be inexpensive when idle. An organism in IDLE that has nothing to do should return immediately. This is a convention, not an enforcement; the architecture assumes well-behaved organisms.

---

## Organism Registration Order as Priority

Organism priority is determined by registration order. When multiple organisms have passed `CHECK` and entered ARMED, they race to `COMMIT` when the threshold is crossed. Because organisms run in registration order each cycle, the first one in the list reaches `COMMIT` first; later organisms find the resource locked and clear themselves.

`CHECK` does not determine priority — it only tests feasibility. Multiple organisms may pass `CHECK` and be ARMED simultaneously. Priority is resolved at `COMMIT` time, by registration order.

This is a deliberate simplification. An explicit priority system would require organisms to declare priorities, and the Judge to compare them. With registration order, the priority is expressed structurally: the list of organisms is the policy.

The consequence is that registration order is load-bearing. It should be documented and treated as part of the system's specification, not as an implementation detail.

  Note: For an alternative that resolves conflicts through an explicit bid-based priority policy rather than registration order, see `33_appendix_judge-bid-model.md`.

