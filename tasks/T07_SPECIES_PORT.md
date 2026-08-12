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
8. `manifests/species_ids.csv` に `is_official` とフォーム間で共有する `canonical_national_dex` を必須化し、公式100種捕獲がフォーム重複で水増しされないgenerator/validatorを追加する。

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
- [ ] 全Species/formがofficial判定とcanonical全国番号を持ち、まるいおまもり用の100種countは同一番号のformを1種として数える。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T07 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T07:`.
5. If another task is READY, continue without waiting for approval.
