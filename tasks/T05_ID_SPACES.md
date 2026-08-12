# T05 — Unify Type Ability Item ID spaces

- Lane: `engine`
- Depends on: `T02, T03`

## Objective

Create stable generated ID spaces for types, abilities, held items, field items, balls, and evolution items.

## Execute

1. Extract Vega current tables and ID usage.
2. Map identical upstream entities to Vega IDs when semantically equivalent.
3. Append new entities into explicit reserved ranges.
4. Separate field item ID, hold effect, battle effect, pocket, icon, description, and script callback mappings.
5. Generate headers/tables and remove duplicated hand-written numeric constants.
6. Validate all references across CFRU/DPE/Vega adapter sources.
7. Create text-width reports for Japanese names/descriptions.

## Required outputs

- `manifests/ability_ids.csv`
- `manifests/item_ids.csv`
- `manifests/type_ids.csv`
- `generated/engine/ids/`
- `reports/generated/id_space_report.md`

## Acceptance gates

- [ ] No duplicate IDs or unresolved symbols.
- [ ] Vega-existing items/abilities preserve behavior.
- [ ] New items have valid pocket/icon/description/effect fields.
- [ ] Fairy and any added types have complete effectiveness/display mappings.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T05:`.
4. Mark the task done with `python3 scripts/taskctl.py done T05 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
