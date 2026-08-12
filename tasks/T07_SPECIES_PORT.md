# T07 — Port DPE Species while freezing Vega IDs

- Lane: `engine`
- Depends on: `T03, T04, T05`

## Objective

Convert Vega existing species into DPE-compatible tables, map duplicates, and append species absent from Vega.

## Execute

1. Determine the exact Vega internal species count and all existing species IDs.
2. Extract names, base stats, types, abilities, growth, gender, egg groups, catch rate, EV yield, held items, and form metadata.
3. Create mapping between Vega species and DPE species using explicit review states.
4. Keep Vega IDs unchanged. Map DPE symbols for duplicate canon species to those IDs.
5. Append only missing species/forms after the frozen Vega range.
6. Generate DPE tables and constants from the mapping.
7. Add reference validators for trainer parties, wild tables, scripts, gifts, and evolutions.

## Required outputs

- `tools/engine/extract_vega_species.py`
- `manifests/species_ids.csv`
- `generated/engine/species/`
- `reports/generated/species_port.md`

## Acceptance gates

- [ ] Every Vega species ID is preserved.
- [ ] No duplicate canonical species is created unless explicitly marked as a form/variant.
- [ ] All existing Vega references resolve.
- [ ] One appended species can be created in party memory without crash.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T07:`.
4. Mark the task done with `python3 scripts/taskctl.py done T07 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
