# T03 — Create rebuildable Vega module harness

- Lane: `engine`
- Depends on: `T01, T02`

## Objective

Create a deterministic build that starts from clean ROM, applies Vega, expands to 32 MiB, inserts a no-op module, and preserves boot/save behavior.

## Execute

1. Implement a stage-oriented build driver. Never modify inputs in place.
2. Apply Vega IPS and verify expected Vega reference hash.
3. Expand/copy to 32 MiB without overwriting Vega data.
4. Create a ROM allocator with named sections and overlap detection.
5. Create expected-byte assertions for every hook/repoint site.
6. Build and insert a minimal no-op ARM module in the extension area.
7. Add header/checksum fix only where needed and document it.
8. Produce a smoke-test ROM and report.

## Required outputs

- `scripts/build_project.py`
- `tools/rom_allocator.py`
- `config/rom_regions.csv`
- `overlays/vega_adapter/`
- `reports/generated/harness_smoke.md`

## Acceptance gates

- [ ] Two consecutive builds are byte-identical.
- [ ] No-op module insertion does not alter Vega-owned bytes except declared hooks/header.
- [ ] Title, new game, basic map movement, save and load still work.
- [ ] Allocator reports zero overlap.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T03:`.
4. Mark the task done with `python3 scripts/taskctl.py done T03 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
