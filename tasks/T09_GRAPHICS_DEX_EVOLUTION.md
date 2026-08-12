# T09 — Port graphics cries dex evolution learnsets

- Lane: `engine`
- Depends on: `T07, T08`

## Objective

Complete the non-battle Species surface so existing and appended species display, evolve, learn moves, register in the Dex, and persist.

## Execute

1. Extract Vega front/back sprites, palettes, shiny palettes, coords, icons, icon palettes, footprints, cries, and animations.
2. Convert or preserve Vega assets in DPE-generated tables.
3. Append missing DPE assets and verify compression/alignment.
4. Merge evolution tables using frozen Species and Move/Item IDs.
5. Merge level-up, egg, TM/HM, tutor learnsets.
6. Define regional/national dex numbering without breaking Vega completion events.
7. Add display tests for summary, party, PC, battle, evolution, and Dex screens.

## Required outputs

- `generated/engine/species_assets/`
- `generated/engine/evolutions/`
- `generated/engine/learnsets/`
- `reports/generated/dex_policy.md`
- `reports/generated/species_asset_validation.md`

## Acceptance gates

- [ ] All Vega species display their original intended assets.
- [ ] One appended species displays front/back/icon/cry and Dex entry.
- [ ] Evolution works across Vega-existing and appended targets.
- [ ] Vega Dex-dependent events remain reachable or have an explicit compatibility adapter.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T09:`.
4. Mark the task done with `python3 scripts/taskctl.py done T09 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
