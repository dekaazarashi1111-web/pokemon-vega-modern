# T02 — Exact ROM/RAM/save/ID audit

- Lane: `qa`
- Depends on: `T00`

## Objective

Turn the initial binary conflict report into a complete machine-readable compatibility model for source porting.

## Execute

1. Run bundled exact audit tools against clean/Vega/Factory references.
2. Extract every CFRU/DPE fixed ROM address from hooks, byte replacements, repoints, repointall, routine pointers, linker files, and special inserts. Evaluate active config/include conditions and calculate actual emitted write spans; do not treat every `.org` site as a one-byte write.
3. For each site, capture clean bytes, Vega bytes, Factory bytes, intended symbol, write length, and proposed resolution.
4. Disassemble a bounded context around code hooks and identify whether Vega changed the containing function.
5. Build a RAM ownership map from CFRU linker files, DPE sources, and any discoverable Vega use.
6. Build save-block, script-special, flag, var, trainer, species, move, ability, item, and map-ID inventories.
7. Generate overlap validators that fail the build when a new unclassified conflict appears.
8. Inventory Vega map groups, headers, layouts, warp/heal/Fly/Escape state, hidden-item flag width, and signed map-ID call paths needed by the Kanto importer.
9. Extract the original Vega encounter tables and unlock dependencies needed to prove a non-destructive Tohoku overlay.
10. シオウの3個目バッジ取得とアーシア島D・Hビル初回攻略完了の実flag/script終端、早期到達可能な港map、NPC表示条件を抽出し、`KANTO_TRAVEL_UNLOCKED` の一回性latch元として分類する。
11. 早期渡航の境界以外でKanto側が参照または書込みしてはならないVega badge/story/HM/warp/item flagの所有権リストを作る。
12. ダッシュ、自転車、field/battle文章printerとdelay、経験値分配、item-use、預かり屋/孵化、summary、PC、技思い出し、設定保存のVega実hook・table・制御codeを抽出する。
13. 移動高速化で通過し得るtile callback、文章即時化で保持すべき明示wait/効果音/改ページ/選択肢、自動戦闘を禁止すべきbattle種別を分類する。
14. Factory参照をoracleとして、施設用hook、`FLAG_BATTLE_FACILITY`、flag/var/script special、trainer/map/music ID、BP/連勝record、rental生成、party backup、RAM/save領域、中断・全滅・復元経路を抽出する。
15. Vegaのミラージュバトルを同じ粒度で監査し、持込party施設とレンタル施設のstate/hook/rewardが衝突せず共存する割当を確定する。
16. BP、調査point、arcade coin候補について、Vegaのcoin case/残高、既存ミニゲーム完了hook、V2の調査state、上限、表示/減算routineを監査し、再利用・新規割当・DEFERを分類する。

## Required outputs

- `reports/generated/address_audit.csv`
- `reports/generated/semantic_conflicts.md`
- `reports/generated/ram_map.csv`
- `reports/generated/save_map.csv`
- `reports/generated/id_inventory.json`
- `reports/generated/vega_map_inventory.csv`
- `reports/generated/vega_encounter_inventory.csv`
- `reports/generated/qol_hook_inventory.csv`
- `reports/generated/facility_audit.md`
- `tools/validate/address_assertions.py`

## Acceptance gates

- [ ] Every fixed write is classified as VEGA, CFRU, PORT, RELOCATE, SAME_TARGET, or UNKNOWN.
- [ ] UNKNOWN entries have evidence and an assigned follow-up task.
- [ ] RAM and save ranges include owner and lifetime.
- [ ] Audit can be rerun after source updates.
- [ ] Map group limits, reserved values, and every state domain needed by dual-region travel are classified.
- [ ] 早期解禁元の実flagは「3個目バッジ＋アーシアD・Hビル攻略後」にだけ成立し、数値とscript contextの証拠がある。
- [ ] QOL実装に必要な全hook、save field、tableと、Vega側のexpected bytesが未分類なく記録される。
- [ ] Battle Factoryとミラージュバトルの全固定write、RAM/save、ID、script境界が分類され、raw固定値を統合版へ持ち込まない再配置案がある。
- [ ] 採用候補通貨ごとにsave owner、bit幅、上限、獲得/消費hookが確定し、根拠のない通貨はrelease有効化されない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T02 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T02:`.
5. If another task is READY, continue without waiting for approval.
