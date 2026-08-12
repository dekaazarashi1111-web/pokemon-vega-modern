# T04 — Port Vega Move IDs into CFRU model

- Lane: `engine`
- Depends on: `T03`

## Objective

Keep all Vega Move IDs stable while generating CFRU-compatible move names, battle data, effects, descriptions, and animations.

## Execute

1. Revalidate the suspected Vega move-name and move-data tables from actual pointers.
2. Extract all Vega move records and normalized names into machine-readable data.
3. Build a canonical mapping between Vega moves and CFRU moves. Do not use fuzzy matches without a confidence/evidence field.
4. Reserve Vega IDs 0–511. Append non-Vega moves after the frozen range.
5. Convert Vega-exclusive effects to CFRU scripts or implement adapter effects.
6. Generate all move-related tables from one manifest.
7. Patch all relevant references to generated tables.
8. Add static tests for count, duplicate IDs, effect script validity, animation mapping, and text length.

## Required outputs

- `tools/engine/extract_vega_moves.py`
- `manifests/move_ids.csv`
- `generated/engine/moves/`
- `reports/generated/move_port.md`

## Acceptance gates

- [ ] Vega IDs 0–511 do not move.
- [ ] Every Vega-used move resolves to a valid CFRU battle record.
- [ ] Every added CFRU move has a unique appended ID.
- [ ] Vega early-game battles run without undefined move crashes.

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T04 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T04:`.
5. If another task is READY, continue without waiting for approval.
