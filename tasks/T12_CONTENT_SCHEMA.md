# T12 — Build symbolic content schema and generators

- Lane: `content`
- Depends on: `T00`

## Objective

Allow dual-region encounter, trainer, item, gym, ecology-overlay, and event design to proceed in parallel without waiting for numeric IDs.

## Execute

1. Finalize region-keyed CSV schemas for maps, encounters, Tohoku overlays, trainers, items, gym rewards, shared capture state, events, and progression.
2. Implement validators for keys, slots, level ranges, move count, duplicate rewards, and unresolved references.
3. Implement generators that consume a later ID-resolution file but can run now in dry-run mode.
4. Create content templates for Tohoku and mainland Kanto.
5. Import V2 only through a normalization layer that canonicalizes ID types, adds form keys, removes semantic duplicates, and rejects missing item/counter references.
6. Define symbolic unlock phases for Vega pre-entry, Kanto early access, each Kanto certification, Vega Hall of Fame, and Kanto League; do not collapse them into a story/postgame boolean.
7. Add reports for first availability, evolution-item availability, trainer usage, 541-family dual-region coverage, and 125 shared special-capture keys.
8. Add `recommended_level_min/max`, `difficulty_policy`, `mandatory`, and `warning_key`; represent Kanto Lv.68–100 as a fixed optional high-level policy rather than dynamic party scaling.
9. Normalize V2 K-E01, the research pass, champion-assuming dialogue, and the mandatory Lv.70-range ship battle into an early research invitation, progress-aware dialogue, and an optional result-independent battle.

## Required outputs

- `content/README.md`
- `content/kanto_progression.csv`
- `tools/content/`
- `reports/generated/content_schema.md`

## Acceptance gates

- [ ] All content files validate with symbolic keys only.
- [ ] Generators fail on unresolved key in build mode and allow explicit dry-run mode.
- [ ] No content file contains raw Species/Move/Item numeric IDs.
- [ ] Reports can detect unobtainable evolution lines.
- [ ] V2's 59 checks are independently reproducible and the known V1-derived semantic issues fail before normalization.
- [ ] Logical V2 location keys cannot be emitted until they resolve through the T11 physical-map crosswalk.
- [ ] The schema rejects early-access rows that lack the level warning/safe-route policy and rejects post-HoF content reachable only from `KANTO_EARLY_ACCESS`.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T12:`.
4. Mark the task done with `python3 scripts/taskctl.py done T12 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
