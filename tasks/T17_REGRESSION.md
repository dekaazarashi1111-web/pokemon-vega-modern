# T17 — Run regression and playtest gates

- Lane: `qa`
- Depends on: `T10, T13, T16`

## Objective

Prove that the new engine and dual-region content preserve Vega completion, keep Tohoku ecology non-destructive, and make Kanto progression and return travel reliable.

## Execute

1. Create a versioned manual checkpoint matrix for Vega main story and postgame.
2. Create clean-start and migrated-save test paths.
3. Run all static/build validators.
4. Run engine vertical slice tests.
5. Run Vermilion and full Kanto connectivity/progression tests.
6. Perform targeted battle tests for status, switching, capture, evolution, forms, items, bosses, and save/load.
7. Triage failures into release blockers, known issues, or deferred enhancements.
8. Repeat from a clean build after fixes.
9. Exercise 49 Tohoku and 47 Kanto logical locations across time/method/unlock states, 34 event branches, and 125 shared special-capture states.
10. Run 200 region round trips including save/load, reset, heal, whiteout, and full-PC cases.

## Required outputs

- `tests/manual/VEGA_CHECKPOINTS.md`
- `tests/manual/KANTO_CHECKPOINTS.md`
- `reports/generated/regression_summary.md`
- `KNOWN_ISSUES.md`

## Acceptance gates

- [ ] All release-blocking tests pass from a clean build.
- [ ] Vega main progression remains completable to the defined gate.
- [ ] Kanto progression reaches its final objective.
- [ ] Known issues include reproduction steps and severity.
- [ ] No original Vega encounter disappears and no special species can be captured twice across regions.
- [ ] Every imported Kanto physical map is reachable or intentionally gated, and return travel is always possible.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T17:`.
4. Mark the task done with `python3 scripts/taskctl.py done T17 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
