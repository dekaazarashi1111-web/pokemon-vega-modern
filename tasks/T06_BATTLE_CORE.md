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
10. CFRUのBattle Factory battle-side coreをallocator管理領域へ移植し、既存Vega種だけのsynthetic fixtureでLv.50 rental生成、facility battle flag、single 3v3、double 4v4、NPC partner multi、random、Little/Monotype/Unrestricted/OU/Uber/Camomons/GSのrule dispatchを検証する。link multiはrelease scope外とする。候補6→3、交換、連戦session、記録、図鑑、party復元はT08/T09後のT10で統合する。
11. 施設戦ではEXP、EV、なつき度、孵化歩数、捕獲、賞金、恒久的な道具消費/持出しを無効化するbattle境界を作る。
12. 標準、Mega、Z、Dynamax、Teraを別modeとして隔離し、Ultimateは入場時に1方式だけを選ぶ。複数ギミックの無条件同時使用を許可しない。

## Required outputs

- `overlays/cfru/`
- `config/cfru_vega_minimal.h`
- `reports/generated/battle_hook_matrix.csv`
- `reports/generated/battle_core_smoke.md`
- `reports/generated/facility_core_smoke.md`

## Acceptance gates

- [ ] Vega normal wild and trainer battles complete.
- [ ] Core status, priority, multi-target, switching, fainting, experience, and capture paths work.
- [ ] No unclassified hook overwrites Vega code.
- [ ] Optional feature disablement is explicit, not accidental.
- [ ] 全体学習装置、mint、特性slot、Hyper Trainingの各入力fixtureに対してbattle/stat accessorが正しい結果を返し、経験アメは他partyへ分配されない。save・summaryとの一致はT10で検証する。
- [ ] Synthetic fixtureのrental生成、facility flag、rule dispatch、各battle形式が通常Vega戦と独立して動き、施設中の成長・捕獲・道具変化をbattle結果へ出力しない。
- [ ] 各ギミックmodeは相互排他的で、mode終了時に一時battle stateが全て破棄される。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T06 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T06:`.
5. If another task is READY, continue without waiting for approval.
