# T16 — Populate encounters trainers and items

- Lane: `content`
- Depends on: `T12, T14, T15`

## Objective

Populate both Tohoku and Kanto with the expanded roster while preserving Vega encounters, a sensible dual-region curve, and complete evolution access.

## Execute

1. Assign biome and level-band metadata to each wild-enabled map.
2. Populate land/water/rock-smash/fishing tables using symbolic species keys.
3. Populate regular trainers, gym trainers, bosses, and optional rematches.
4. Set moves, held items, abilities, and AI profiles appropriate to progression.
5. Place field items, hidden items, evolution items, TMs, and gym rewards.
6. Generate first-availability, duplicate-role, level-curve, type-distribution, and evolution-access reports.
7. Run automatic balance lint, then perform at least one human pass for each city/route batch.
8. Populate Tohoku's 49 logical overlay locations and Kanto's 47 logical ecology locations from normalized V2 data.
9. Verify all 541 families have both regional routes and all 125 special species share one capture key across regions.
10. カントーのLv.68〜100を `FIXED_HIGH_LEVEL_OPTIONAL` として生成し、party平均による動的scalingを入れない。
11. 初回到着の警告、強制戦闘なしの安全地帯、無料帰還を検査し、強力な店売り・報酬・重要道具は専用進行条件でgateする。

## Required outputs

- `manifests/kanto_encounters.csv`
- `manifests/kanto_trainers.csv`
- `manifests/kanto_items.csv`
- `reports/generated/kanto_content_audit.md`

## Acceptance gates

- [ ] Every referenced key resolves.
- [ ] No required evolution item is permanently unobtainable.
- [ ] No trainer has invalid move/item/species combinations.
- [ ] Level curve has no unexplained extreme jumps; Kanto's declared fixed high-level optional policy is reported as intentional rather than silently ignored.
- [ ] Tohoku fallback tables preserve every original Vega slot and rare encounter when overlays are disabled.
- [ ] V2 logical locations resolve to the imported physical map graph.
- [ ] 早期配置には推奨レベル警告があり、post-HoF限定個体・報酬は殿堂入り前に解禁されない。

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T16:`.
4. Mark the task done with `python3 scripts/taskctl.py done T16 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
