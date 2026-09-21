# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Desk cases

### Case
The occupancy object the duty operator works: one incident on a road segment, shown as a list row and a card with Send/Dismiss.

A Case carries a [Trigger kind](#trigger-kind) and a status. Send/Dismiss are enabled only while [Open](#open). The drone stub runs as a side effect of Send, after the row is already [Approved](#approved). The console list and card are this object, not the speed tape.

### Occupancy
The rule that a segment has at most one [Open](#open) Case at a time.

A later matching incident does not create a second Open Case. Occupancy marks the previous Open Case [Outdated](#outdated) and then opens the next.

### Trigger kind
The incident rule that opened the [Case](#case) — stored once on the Case, not inferred from the speed tape.

Show the stored strings on the list and card. Do not treat per-sample kind on [Last speeds](#last-speeds) as the Case identity, and do not invent display labels that drift from the stored value.

### Open
A Case waiting for a human Send or Dismiss.

Send/Dismiss are enabled only in this status. Occupancy allows at most one Open Case per segment. The drone stub does not fly while the row is still Open — Send first marks the Case [Approved](#approved), then the stub runs.

### Approved
Operator Send: the human confirmed the proposal. Not a system close.

### Rejected
Operator Dismiss only. Not a miss and not a system close.

### Outdated
A miss: Occupancy moved the slot to a newer Open Case because a later matching rule opened before the operator decided.

Outdated is not Rejected. Send/Dismiss are disabled. The desk must not render it as if someone pressed Dismiss.

### Last speeds
The recent speed tape for the segment on the case card.

Each sample may carry its own kind; that is event-row kind, not the Case [Trigger kind](#trigger-kind). The tape stays a speed table (event, segment, speed, recorded) — it does not gain a kind column from showing Trigger kind on the list and card.

## Relationships

- A Case has at most one Trigger kind. Occupancy writes it when the rule opens the row. The column is nullable; a legacy or test insert may be Open with no Trigger kind.
- Occupancy: at most one Open Case per segment.
- Open may become Approved, Rejected, or Outdated. Approved and Rejected are operator-only; Outdated is Occupancy.

## Flagged ambiguities

- "'rejected' had been the only close-looking chip for anything not open or approved — a miss is Outdated, not Rejected."
- "'kind' on a tape sample is not Trigger kind on the Case."
