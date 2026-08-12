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
8. Normalize V2 evolution data by removing semantic duplicates, adding from/to form keys, canonicalizing National Dex types, and resolving every required item/counter before generation.
9. かわらずの石、あかいいと、power系、父母双方のタマゴ技、共通level技、ball/特性slot/隠れ特性、おこうbaby、メタモン、異親ID6回判定、リージョンフォームを含む現代式孵化を固定RNG fixtureで実装する。
10. 新規専用pageを作らず、summary既存情報欄/PC右欄のcompact IV/EV切替、タマゴIV表示、既存画面を使う無料技思い出し、タマゴPC直接送信、最大5個queue、孵化演出3 modeを実装する。
11. まるいおまもりの公式Species 100種捕獲/quest解禁と、タマゴ生成check成功率2倍を実装する。

## Required outputs

- `generated/engine/species_assets/`
- `generated/engine/evolutions/`
- `generated/engine/learnsets/`
- `reports/generated/dex_policy.md`
- `reports/generated/species_asset_validation.md`
- `tests/fixtures/breeding_matrix.json`

## Acceptance gates

- [ ] All Vega species display their original intended assets.
- [ ] One appended species displays front/back/icon/cry and Dex entry.
- [ ] Evolution works across Vega-existing and appended targets.
- [ ] Vega Dex-dependent events remain reachable or have an explicit compatibility adapter.
- [ ] Every generated evolution row has unambiguous form identity and resolvable requirements.
- [ ] `docs/QOL_POLICY.md` の孵化matrix、IV/EV境界、まるいおまもり、満杯party/boxが欠落・複製・範囲外readなしで通る。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T09 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T09:`.
5. If another task is READY, continue without waiting for approval.
