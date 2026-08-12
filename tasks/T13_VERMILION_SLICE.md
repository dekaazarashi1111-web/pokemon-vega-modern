# T13 — Implement Vermilion postgame vertical slice

- Lane: `maps`
- Depends on: `T10, T11, T12`

## Objective

Deliver the first playable postgame Kanto loop: unlock, travel, town, NPCs, gym, reward, save, and return.

## Execute

1. Add a temporary or real postgame unlock condition in Vega.
2. Create Vega-side port NPC and two-way travel.
3. Import Vermilion port/city and required interiors under new KANTO IDs.
4. Preserve NPC placement where useful; remap scripts, flags, trainer IDs, item flags, and text.
5. Import the gym layout and puzzle, replacing progress vars with KANTO vars.
6. Generate gym trainers and boss party from symbolic content manifests.
7. Grant an independent KANTO gym-clear flag and configurable reward.
8. Test save/load inside Kanto and return to Vega.

## Required outputs

- `src/kanto/vermilion/`
- `content/vermilion/`
- `reports/generated/vermilion_slice.md`

## Acceptance gates

- [ ] Travel is reversible and does not alter Vega warps.
- [ ] Gym puzzle resets/finishes correctly.
- [ ] Trainer and reward IDs are new and namespaced.
- [ ] Save/load and return travel work.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T13:`.
4. Mark the task done with `python3 scripts/taskctl.py done T13 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
