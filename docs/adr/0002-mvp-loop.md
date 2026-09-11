# 0002. MVP loop: one segment, speed, human-gated drone

- Status: Accepted
- Date: 2026-09-11

## Context

A thin first cut needs one nerve and one dangerous action. Energy was a poor first domain. A full traffic bureau (speeding, jam, resident text, critic agent) is v1.

## Decision

MVP is one road segment. A simulator sends a live speed tape (~40s) then a collapse to zero. A **code rule** opens a case (works with no LLM key). The console always offers **send a drone**. The model, if present, only writes why. After yes, **application code** sets drone status (`idle` / `in_flight` / `on_site`). No `fly()` tool. Reject leaves the drone idle and writes audit.

Console: React from the start. No map.

## Consequences

Interesting-ness comes from the duty minute (tape → card → flight status), not from more sensors. Extra event types and a second agent voice wait for v1.
