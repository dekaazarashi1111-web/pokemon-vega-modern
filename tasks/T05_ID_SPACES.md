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
8. Vega既存IDを動かさず、経験アメXS/S/M/L/XLを末尾予約rangeへ追加する。孵化道具、power系、mint、特性カプセル/パッチ、ぎん/きんのおうかん、まるいおまもり、努力値reset用品をstable keyへ正規化し、名称、説明、icon、palette、pocket、価格、hold/field/battle effect、callbackを解決する。

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
- [ ] 全育成道具がstable item/effect keyと `docs/QOL_POLICY.md` の効果を持ち、既存Vega Item IDを1件も移動しない。供給keyはT12/T16で定義する。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T05 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T05:`.
5. If another task is READY, continue without waiting for approval.
