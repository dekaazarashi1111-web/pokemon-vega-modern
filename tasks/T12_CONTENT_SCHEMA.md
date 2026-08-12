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
10. T11前はlogical map keyとdry-run reportを検証し、build-mode physical-map emissionを明示的に拒否する。T12はT11を待たず完了でき、実crosswalkのbindingは両方へ依存するT13が所有する。
11. `docs/QOL_POLICY.md` の育成機能、道具、service、供給tier、反復可否、badge/D・H/Hall of Fame/Kanto League unlockと `field_pc_allowed` をraw numeric IDなしのsymbolic schemaへ追加する。mapの未設定値はfalseとする。
12. 新規eventへ `presentation_profile` を追加し、既定 `SIMPLE_EVENT` は標準message/condition/flag/reward/battle/warpだけを許可する。専用UI/cutscene/minigame参照をvalidatorで拒否する。

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
- [ ] T12はT11前でも完了できる。未解決physical mapはdry-runで明示され、build-mode emissionはactionable errorで失敗し、crosswalk bindingをT13へ引き渡す。
- [ ] The schema rejects early-access rows that lack the level warning/safe-route policy and rejects post-HoF content reachable only from `KANTO_EARLY_ACCESS`.
- [ ] 育成道具のfirst-availabilityとrepeatabilityを機械出力でき、後半限定道具の早期無限入手をvalidatorが拒否する。
- [ ] 全新規eventが明示profileを持ち、`SIMPLE_EVENT` は既存UI/script部品だけで生成できる。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T12 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T12:`.
5. If another task is READY, continue without waiting for approval.
