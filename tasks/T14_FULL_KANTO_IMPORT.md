# T14 — Import selected full Kanto map set

- Lane: `maps`
- Depends on: `T11, T13`

## Objective

Scale the proven importer to the chosen Kanto mainland map scope while preserving Vega.

## Execute

1. Generate a scope manifest marking each map INCLUDE, DEFER, or REBUILD.
2. Import cities, routes, required interiors, gyms, caves, and dungeons in batches.
3. Remap all connections and warps to KANTO IDs.
4. Retain NPC coordinates/local scripts where safe; replace story-global scripts with stubs or KANTO scripts.
5. Create unreachable-map, one-way-warp, duplicate-local-id, missing-tileset, and invalid-connection validators.
6. Add map batch smoke reports and size/allocation reports.
7. Keep Sevii deferred unless explicitly included in the scope manifest.

## Required outputs

- `content/kanto_map_scope.csv`
- `generated/maps/kanto/`
- `reports/generated/kanto_connectivity.md`
- `reports/generated/kanto_size.md`

## Acceptance gates

- [ ] Every included map is reachable or intentionally gated.
- [ ] No warp points to a Vega map by accidental original ID reuse.
- [ ] No Map ID, local object ID, flag, or var collision.
- [ ] ROM allocation remains non-overlapping.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T14:`.
4. Mark the task done with `python3 scripts/taskctl.py done T14 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
