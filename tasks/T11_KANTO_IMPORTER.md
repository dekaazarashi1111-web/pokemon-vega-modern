# T11 — Build Kanto map importer

- Lane: `maps`
- Depends on: `T00, T02`

## Objective

Create a repeatable map conversion/import pipeline that assigns new KANTO IDs and preserves selected layouts/NPC placement without importing unsafe global story state.

## Execute

1. Inventory all original FireRed mainland maps from pokefirered and clean BPRJ; keep Sevii explicitly deferred.
2. Build a canonical intermediate model for map header, layout, tilesets, connections, warps, objects, coord events, bg events, scripts, text, and wild header.
3. Use pokefirered for semantic names and structure, but verify BPRJ-compatible raw assets against the clean Japanese ROM.
4. Implement export/import of a single harmless map into a new map group and ID.
5. Remap internal warps/connections and namespace all local symbols.
6. Strip or stub story-critical scripts while preserving NPC coordinates and local flavor events.
7. Round-trip the imported map and produce a structural diff.
8. Generate a crosswalk from V2's 47 logical Kanto locations to every required physical map, shared layout, tileset, and warp/script dependency.
9. Split physical IDs across safe KANTO outdoor/dungeon/indoor groups instead of exceeding signed 8-bit or reserved map values.

## Required outputs

- `tools/map_import/`
- `manifests/map_ids.csv`
- `manifests/kanto_maps.csv`
- `reports/generated/kanto_map_inventory.csv`
- `reports/generated/map_roundtrip.md`
- `reports/generated/kanto_v2_crosswalk.csv`

## Acceptance gates

- [ ] One map imports at a new KANTO ID without replacing a Vega map.
- [ ] Layout, collision, tileset, NPC coordinates, warps, and connections validate.
- [ ] Original global flags/vars are not reused.
- [ ] Importer is data-driven and repeatable.
- [ ] The scope distinguishes V2 logical locations from all included physical maps and resolves every physical dependency.

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T11 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T11:`.
5. If another task is READY, continue without waiting for approval.
