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
13. Battle Factoryのmode/tier、battle format、mechanic policy、rental set/pool、trainer、streak/BP reward、story-gated shop、遭遇credit/pool/NPCをsymbolic schemaへ追加する。FactoryとMirageのowner/state keyを分離する。
14. 遭遇NPC rowは `payment_kind=currency|credit`、`currency_key` または `credit_key`、`cost`、`pool_key`、`unlock_key`、`level/quality policy`、`presentation_profile=SIMPLE_EVENT` を必須とする。currencyは指定残高をcost分、creditはtyped creditを1個だけ減算し、同時指定を拒否する。専用捕獲map、ticket用full-screen UI、raw IDを拒否する。
15. 遭遇creditの通貨はBP、調査point、arcade coinを共通interfaceで表現し、`availability=ENABLED|DEFERRED` と既存ミニゲーム完了hookからのpoint加算をschema化する。T02/T08でownerと供給hookが確定しない通貨はDEFERREDを強制し、新規ミニゲームや専用交換UIはschema要件にしない。
16. Trainer rowへ `trainer_role`、`ai_profile_key`、自動推定との照合用 `expected_fight_style_key`、`team_stage`、`rematch_tier`、`league_stage`、`ev_spread_key`、nature/ability/item/moves、`mechanic_policy`、`unlock_key` を追加し、AI profileはT06の `AI_BASIC|AI_SEMI_SMART|AI_FULL_SMART` だけへ解決する。
17. Encounter rowには既存の `layer=original|overlay|dexnav|time|outbreak|fixed` を維持したまま、直交軸 `table_profile=NORMAL|RESEARCH`、base table、level delta/range、IV floor、hidden-ability/egg-move/held-item/shiny policy、unlockを追加する。NORMALを上書きせず、RESEARCHを既存scanner/DexNav/調査flagから明示選択する。
18. Validatorは違法move/item/ability、未解決AI profile、stage外levelまたはLv100超、解禁前gimmick、1 trainer戦で複数gimmick、全一般trainerへの一括rematch/level scale、NORMAL rare slot消失を拒否する。
19. Raid rowへ `raid_tier`、species/form/level/quality、partner pool、shield policy、reward pool、`capture_policy` / `shared_capture_key`、`reward_repeatability` / `claim_key`、unlock、`presentation_profile=SIMPLE_EVENT` を追加する。捕獲と報酬の反復性を混同せず、専用map/UI/cutsceneを要求せず、Raid固定Dynamax以外の複数gimmickを拒否する。

## Required outputs

- `content/README.md`
- `content/kanto_progression.csv`
- `content/schema/facility.schema.json`
- `content/schema/trainer_difficulty.schema.json`
- `tests/fixtures/facility_schema/`
- `tests/fixtures/trainer_difficulty_schema/`
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
- [ ] Facility/rental/BP/encounterの全参照がsymbolic keyで解決し、解禁前pool、同時複数ギミック、反復可能な伝説・幻poolをvalidatorが拒否する。
- [ ] 遭遇NPCは標準message/list/Yes-Noと通常scripted wild battleだけで生成でき、支払い前の容量確認と支払い済み保留遭遇を表現できる。
- [ ] BP/調査point/arcade coinの獲得・消費は同じsymbolic契約で検証され、未知通貨、負残高、二重減算を拒否する。
- [ ] 全trainer/AI/rematch/league/encounter table-profile rowがsymbolic keyだけで解決し、違法構成、隠れたlevel scaling、未解禁/複数gimmickを生成前に拒否する。
- [ ] Raid rowは既存NPC/標準battle UIで生成でき、未解禁pool、禁止種、反復報酬、Raid以外の複数gimmickをvalidatorが拒否する。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T12 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T12:`.
5. If another task is READY, continue without waiting for approval.
