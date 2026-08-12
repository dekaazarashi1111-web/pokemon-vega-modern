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

## Required outputs

- `reports/generated/address_audit.csv`
- `reports/generated/semantic_conflicts.md`
- `reports/generated/ram_map.csv`
- `reports/generated/save_map.csv`
- `reports/generated/id_inventory.json`
- `reports/generated/vega_map_inventory.csv`
- `reports/generated/vega_encounter_inventory.csv`
- `tools/validate/address_assertions.py`

## Acceptance gates

- [ ] Every fixed write is classified as VEGA, CFRU, PORT, RELOCATE, SAME_TARGET, or UNKNOWN.
- [ ] UNKNOWN entries have evidence and an assigned follow-up task.
- [ ] RAM and save ranges include owner and lifetime.
- [ ] Audit can be rerun after source updates.
- [ ] Map group limits, reserved values, and every state domain needed by dual-region travel are classified.
- [ ] 早期解禁元の実flagは「3個目バッジ＋アーシアD・Hビル攻略後」にだけ成立し、数値とscript contextの証拠がある。

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T02:`.
4. Mark the task done with `python3 scripts/taskctl.py done T02 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
