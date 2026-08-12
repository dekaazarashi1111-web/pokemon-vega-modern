# T08 — Resolve RAM and save compatibility

- Lane: `qa`
- Depends on: `T02, T03`

## Objective

Allocate CFRU/DPE state safely and define an explicit save compatibility policy.

## Execute

1. Merge RAM ownership maps and identify simultaneous-lifetime conflicts.
2. Move CFRU temporary state or Vega state as needed using named symbols instead of raw addresses.
3. Inventory Vega save sectors/blocks and CFRU save expansion changes.
4. Implement a save version marker and migration entry point.
5. Attempt direct Vega save compatibility first; implement one-time migration if practical.
6. Add save round-trip test fixtures and corrupted-version rejection.
7. Document whether old Vega saves are supported.
8. Allocate and test National Dex 1025 state, research rank, eight Kanto certifications, region/rotation/retry state, and 125 shared special-capture states.
9. `KANTO_TRAVEL_UNLOCKED`、`KANTO_VISITED`、`VEGA_HALL_OF_FAME`、認定章、現在地方、地方別heal/return anchor、初回警告確認をそれぞれ独立保存する。
10. 既存save移行では、早期checkpointまたは殿堂入りを満たすsaveに渡航権を1回だけ付与し、逆戻りさせない。
11. Escape/Teleport/dynamic warp/whiteoutが地方別anchorを使い、不正値時はクチバterminalまたはVega渡航元港へfail-safe復帰することを検証する。
12. `TEXT_SPEED`、孵化演出mode、全体学習装置ON/OFF、`natureMint`、Hyper Training 6能力bit、最大5個の預かりタマゴqueueをallocateする。badge等から導出できるQOL解禁条件は重複保存しない。
13. 新規saveとQOL fieldを持たない移行saveには `TEXT_SPEED=INSTANT`、`HATCH_MODE=FAST` を設定し、取得済み1個目badgeに応じて全体学習装置を既定ONにする。

## Required outputs

- `config/ram_layout.csv`
- `config/save_layout.csv`
- `overlays/save_migration/`
- `reports/generated/save_compatibility.md`
- `tests/test_save_layout.py`

## Acceptance gates

- [ ] No overlapping live RAM owners.
- [ ] New save data survives save/load and checksum validation.
- [ ] Unsupported old saves fail clearly rather than silently corrupting.
- [ ] Policy is documented and tested.
- [ ] Dual-region travel and shared capture state survive save/load without modifying Vega badges.
- [ ] 殿堂入り前のKanto内save/load/reset/heal/whiteoutで渡航権と帰還路が保持される。
- [ ] Kanto field permitや認定章はTohokuのHM/badge/story flagを変更しない。
- [ ] 育成・設定stateはparty↔PC、進化、save/load/reset後も保持され、タマゴqueueと個体dataに消失・複製がない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T08 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T08:`.
5. If another task is READY, continue without waiting for approval.
