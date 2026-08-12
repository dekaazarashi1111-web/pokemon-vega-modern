# T08 — Resolve RAM and save compatibility

- Lane: `qa`
- Depends on: `T02, T03`

## Objective

Allocate CFRU/DPE state safely and define an explicit save compatibility policy.

## Execute

1. Merge RAM ownership maps and identify simultaneous-lifetime conflicts.
2. Move CFRU temporary state or Vega state as needed using named symbols instead of raw addresses.
3. Inventory Vega save sectors/blocks and CFRU save expansion changes.
4. Implement a save version marker and migration entry point.
5. Attempt direct Vega save compatibility first; implement one-time migration if practical.
6. Add save round-trip test fixtures and corrupted-version rejection.
7. Document whether old Vega saves are supported.

## Required outputs

- `config/ram_layout.csv`
- `config/save_layout.csv`
- `overlays/save_migration/`
- `reports/generated/save_compatibility.md`
- `tests/test_save_layout.py`

## Acceptance gates

- [ ] No overlapping live RAM owners.
- [ ] New save data survives save/load and checksum validation.
- [ ] Unsupported old saves fail clearly rather than silently corrupting.
- [ ] Policy is documented and tested.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T08:`.
4. Mark the task done with `python3 scripts/taskctl.py done T08 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
