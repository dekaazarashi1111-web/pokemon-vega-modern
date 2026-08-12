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

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T06:`.
4. Mark the task done with `python3 scripts/taskctl.py done T06 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
