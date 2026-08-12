# T06 — Port CFRU battle core

- Lane: `engine`
- Depends on: `T04, T05`

## Objective

Run the CFRU battle engine on top of Vega without replacing Vega story/map content.

## Execute

1. Start from the minimal CFRU config, not the full Factory config.
2. Port battle hooks category by category: setup, turn order, move execution, abilities, items, UI, AI, animations.
3. For each hook, assert expected Vega bytes and adapt the containing Vega function if it diverged.
4. Relocate inserted code/data into allocator-owned extension sections.
5. Disable optional systems that are not required for the first vertical slice.
6. Add battle-script command table validation and bounded disassembly snapshots.
7. Run smoke tests after each hook category and keep bisectable commits.
8. 全体学習装置ON/OFF、mint補正、特性slot、SV式Hyper Trainingの実効IV=31を入力として受けるbattle/stat accessorを作る。save fieldとsummary UIへの接続はT08/T09後のT10で行う。
9. 経験アメはbattle分配を通さず選択個体だけを処理できる境界を作る。

## Required outputs

- `overlays/cfru/`
- `config/cfru_vega_minimal.h`
- `reports/generated/battle_hook_matrix.csv`
- `reports/generated/battle_core_smoke.md`

## Acceptance gates

- [ ] Vega normal wild and trainer battles complete.
- [ ] Core status, priority, multi-target, switching, fainting, experience, and capture paths work.
- [ ] No unclassified hook overwrites Vega code.
- [ ] Optional feature disablement is explicit, not accidental.
- [ ] 全体学習装置、mint、特性slot、Hyper Trainingの各入力fixtureに対してbattle/stat accessorが正しい結果を返し、経験アメは他partyへ分配されない。save・summaryとの一致はT10で検証する。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T06 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T06:`.
5. If another task is READY, continue without waiting for approval.
