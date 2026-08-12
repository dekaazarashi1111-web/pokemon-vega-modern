# T11 — Build Kanto map importer

- Lane: `maps`
- Depends on: `T00, T02`

## Objective

Create a repeatable map conversion/import pipeline that assigns new KANTO IDs and preserves selected layouts/NPC placement without importing unsafe global story state.

## Execute

1. Inventory all original FireRed mainland and Sevii maps from pokefirered.
2. Build a canonical intermediate model for map header, layout, tilesets, connections, warps, objects, coord events, bg events, scripts, text, and wild header.
3. Use pokefirered for semantic names and structure, but verify BPRJ-compatible raw assets against the clean Japanese ROM.
4. Implement export/import of a single harmless map into a new map group and ID.
5. Remap internal warps/connections and namespace all local symbols.
6. Strip or stub story-critical scripts while preserving NPC coordinates and local flavor events.
7. Round-trip the imported map and produce a structural diff.

## Required outputs

- `tools/map_import/`
- `manifests/map_ids.csv`
- `manifests/kanto_maps.csv`
- `reports/generated/kanto_map_inventory.csv`
- `reports/generated/map_roundtrip.md`

## Acceptance gates

- [ ] One map imports at a new KANTO ID without replacing a Vega map.
- [ ] Layout, collision, tileset, NPC coordinates, warps, and connections validate.
- [ ] Original global flags/vars are not reused.
- [ ] Importer is data-driven and repeatable.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T11:`.
4. Mark the task done with `python3 scripts/taskctl.py done T11 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
