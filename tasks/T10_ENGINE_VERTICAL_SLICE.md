# T10 — Complete engine vertical slice

- Lane: `qa`
- Depends on: `T04, T05, T06, T07, T08, T09`

## Objective

Prove the integrated engine end-to-end before importing large Kanto content.

## Execute

1. Choose one appended species absent from Vega.
2. Choose one appended move, ability, held item, and evolution method.
3. Add a temporary debug gift or test map script that grants the species and item.
4. Test wild encounter, trainer battle, capture, level-up, move use, ability activation, item effect, evolution, Dex registration, save, restart, and load.
5. Run Vega baseline regression checkpoints.
6. Remove or guard debug-only access behind a build define.
7. Freeze engine manifest schema after the vertical slice passes.
8. Register the selected species through one Tohoku overlay fixture and prove that disabled/failed overlay selection returns the byte-equivalent original Vega encounter result.

## Required outputs

- `reports/generated/engine_vertical_slice.md`
- `tests/fixtures/engine_slice.json`
- `config/feature_matrix.csv`

## Acceptance gates

- [ ] All selected new elements work in one continuous save.
- [ ] Vega baseline smoke tests pass.
- [ ] No debug code is active in release config.
- [ ] Manifest schemas are versioned.
- [ ] The Tohoku overlay adds content without replacing an original Vega slot or 1% encounter.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T10:`.
4. Mark the task done with `python3 scripts/taskctl.py done T10 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
