# T12 — Build symbolic content schema and generators

- Lane: `content`
- Depends on: `T00`

## Objective

Allow encounter, trainer, item, gym, and event design to proceed in parallel without waiting for numeric IDs.

## Execute

1. Finalize CSV schemas for maps, encounters, trainers, items, gym rewards, and progression.
2. Implement validators for keys, slots, level ranges, move count, duplicate rewards, and unresolved references.
3. Implement generators that consume a later ID-resolution file but can run now in dry-run mode.
4. Create content templates for mainland Kanto.
5. Define default postgame level bands and biome tags as proposals, not hard-coded ROM data.
6. Add report generation showing each species first availability, evolution-item availability, and trainer usage.

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

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T12:`.
4. Mark the task done with `python3 scripts/taskctl.py done T12 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
