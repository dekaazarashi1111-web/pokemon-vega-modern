# T15 — Implement postgame unlock and gym progression

- Lane: `content`
- Depends on: `T13, T14`

## Objective

Turn imported Kanto maps into a coherent Vega postgame progression without reusing original badge/story state.

## Execute

1. Select the exact Vega completion condition that unlocks Kanto and document it.
2. Implement port NPC visibility and travel gating.
3. Define KANTO gym flags and progression checks.
4. Retain gym puzzles but replace badge scripts and HM checks with independent KANTO logic.
5. Define route gates, key items, dungeon access, boss sequence, and final Kanto objective.
6. Provide a fallback fast-travel terminal for development builds.
7. Generate a progression graph and detect impossible prerequisites.

## Required outputs

- `content/kanto_progression.csv`
- `generated/kanto/progression/`
- `reports/generated/progression_graph.md`

## Acceptance gates

- [ ] Kanto unlock cannot trigger before intended Vega completion.
- [ ] All included Kanto areas have a valid progression path.
- [ ] Gym flags do not modify Vega badges.
- [ ] Development shortcuts are disabled in release config.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T15:`.
4. Mark the task done with `python3 scripts/taskctl.py done T15 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
