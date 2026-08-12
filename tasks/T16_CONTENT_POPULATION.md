# T16 — Populate encounters trainers and items

- Lane: `content`
- Depends on: `T12, T14, T15`

## Objective

Fill Kanto with the expanded roster while preserving a sensible postgame curve and making important evolution lines obtainable.

## Execute

1. Assign biome and level-band metadata to each wild-enabled map.
2. Populate land/water/rock-smash/fishing tables using symbolic species keys.
3. Populate regular trainers, gym trainers, bosses, and optional rematches.
4. Set moves, held items, abilities, and AI profiles appropriate to progression.
5. Place field items, hidden items, evolution items, TMs, and gym rewards.
6. Generate first-availability, duplicate-role, level-curve, type-distribution, and evolution-access reports.
7. Run automatic balance lint, then perform at least one human pass for each city/route batch.

## Required outputs

- `manifests/kanto_encounters.csv`
- `manifests/kanto_trainers.csv`
- `manifests/kanto_items.csv`
- `reports/generated/kanto_content_audit.md`

## Acceptance gates

- [ ] Every referenced key resolves.
- [ ] No required evolution item is permanently unobtainable.
- [ ] No trainer has invalid move/item/species combinations.
- [ ] Level curve has no unexplained extreme jumps.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T16:`.
4. Mark the task done with `python3 scripts/taskctl.py done T16 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
