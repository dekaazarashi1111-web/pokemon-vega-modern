# PR #16 Stage79 follow-up — 2026-09-09

Task: USER-STAGE79-PR16-RUNTIME-FOLLOWUP

## Status: PARTIAL — 5/7 domains PASS, P08 not promoted

The immutable product/harness validation run is [34302717908](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34302717908), at source commit `3c2794a191ae3ef014df6ab8e97de8103fb8eaaf`.

| Domain | Result |
| --- | --- |
| mega_shop | PASS |
| p03 | PASS |
| p04_mega_runtime | PASS |
| battle_policy | PASS |
| p05 | PASS |
| p02 | FAIL — no evolution scene is entered after the Rare Candy selection |
| floette | FAIL — acquisition save migration traverses beyond its table |

The five successful domains were freshly executed in this run, not inferred from stdout alone. The domain process exit status, JSON contract, fixed inputs and unchanged ROM checks remained enabled. The merge job correctly failed because two domains did not produce valid PASS records. Later documentation/CI-only commits must not be described as seven-domain PASS.

## Committed and verified repairs

### Factory map cross-stage contract

Source commit: `fe26265ee7eaf88fa425773f66a75765ba11f414`.

Stage68 owns the Mega Shop function/item/script ABI. Stage69 owns the cumulative Factory map, which preserves the original 14 objects and adds the Floette gift NPC as local ID 15. The old runner was comparing the cumulative map against the obsolete Stage68 14-object event pointer.

The Stage79 caller now validates the hashed Stage69 map descriptor and exact predecessor links, preserved objects/scripts/shop, and exact count 15. A Stage79 wrapper selects that count; the historical Stage68 runner retains its exact count 14. Neither an arbitrary object-count range nor a weakened shop price/unlock contract is accepted.

New regression suite: `tests/test_modernization_stage79_factory_map.py` (13 tests). [Repair run 34301807629](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34301807629) retained the pre-fix wrong-pointer failure, 35 passing post-fix tests, warning-as-error builds of both historical and cumulative runners, and `validated.patch`. Mega Shop then passed in the strict Stage79 run 34301854982 and again in 34302717908.

### Dropped physical controller input

Source commit: `3c2794a191ae3ef014df6ab8e97de8103fb8eaaf`.

A recognized action-selection callback may initially ignore physical A while its text/animation is still finishing. The old harness latched the attempted selection and suppressed every later press while that same gate remained active. The diagnostic trace stayed at main `08013861`, controller `0802dc15`, execution mask 1, command `12`, gate 1, after breaking only two of five shields.

The runner now releases the key and retries an unchanged recognized selection after 30 frames. The original overall frame bound, five shields, native damage, capture, and cleanup assertions remain unchanged. It still never sends a selection pulse for an unrecognized gate.

New regression suite: `tests/test_modernization_stage79_controller_input.py` (7 tests). It extracts and compiles the actual C predicate instead of reimplementing the predicate in Python. [Repair run 34302668497](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34302668497) records the old predicate failing for gates 1/2/3 and **42 tests passing** after repair (7.327 seconds). Battle policy subsequently passed the strict full-domain run 34302717908.

## Remaining failures — do not hide them with harness shortcuts

### Floette: a relocated start and mismatched compiled end pointers

The frozen Stage78 input is:

- Path: `build/stages/78_modernization_p05_eelevate_switch_ai.gba`
- SHA-256: `98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b`
- No ROM or save was changed by this follow-up.

[Trace run 34302526120](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34302526120), artifact `stage79-runtime-probe-floette`, shows `VegaAcqEngine_GetPending` (`092d1ce1`) entering the migration scan with a stable stack, then making hundreds of thousands of registration calls. The iterator leaves the collection table and enters unrelated ROM data. Raising the 60-million-step limit would not repair this.

[Read-only reference audit 34303136112](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34303136112) and [follow-up audit 34303410270](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34303410270) disassemble the exact frozen input. They establish:

| Literal address | Compiled meaning | Actual value |
| --- | --- | --- |
| `092d12c4` | collection iterator start | `0959d890` |
| `092d12c0` | collection iterator end | `092db7d8` |
| `092d12d0` | policy iterator start | `092d6c10` |
| `092d12cc` | policy iterator end | `0959d890` |

At `092d1240`, the collection pointer advances by 8 and compares for equality with the stale end. That end is below the relocated start. The next policy loop advances by 32 and likewise has a mismatched end. `tools/modernization_p04_species_runtime.py::_pointer_plan` treats every matching old-root literal as a table-start consumer, while `_apply_and_audit` rewrites it to the new start. This misses a compiled one-past-end and confuses a neighboring table's end alias with a start pointer. The blanket assertion that no old-root literal may remain also needs semantic, not merely numeric, correction.

Next implementation must distinguish start, relocated one-past-end, and preserved neighboring-table end consumers; verify original Stage69/capacity-manifest values and instruction contexts; add red/green boundary regressions; regenerate the product with audited lineage. Do not simply write these values into emulator RAM or modify the read-only test ROM. The current Stage79 orchestrator intentionally pins the exact Stage78 product; a repaired product requires an explicit reviewed identity/lineage update, not a suppressed hash check. Stage69/70 ROM files were not present in the GitHub Actions checkout during these audits, so historical values must be recovered from their pinned source/metadata or regenerated inputs before patching.

### P02: level jumps before evolution starts

The same diagnostic run's `stage79-runtime-probe-p02` artifact records:

- Frame 0: species 1, level 15, held item 0, selected item 68, callback `0811f3a9`, item-use callback `0937a05d`.
- Frame 139: species still 1, but level is already 100; neither evolution-begin nor evolution-update callback has appeared.
- It then returns through Bag/field callbacks. `physical_b` remains 0 because the evolution scene never began.

The level-15-to-100 jump occurs with the fixture containing exactly one Rare Candy. This is not evidence that cancellation passed, and returning to the field without ever entering evolution must remain a failure. The prior illegal opcode is no longer the current symptom.

The read-only audit identifies `GetSpeciesExp` at `090fc505`, base-stat root literal `090fc518 -> 09576c74`, and experience-table literal `090fc51c -> 09150064`. Its instruction sequence reads growth byte 19 from a 32-byte species row and uses `(growth * 256 + level) * 4` into the experience table. This locates the next consistency checks but does **not** yet establish the exact cause of the level jump. Verify current EXP and level-15/16 thresholds against the native stat-calculation path, then repair the actual runtime or fixture defect without relaxing level/evolution/move-replacement/cancel assertions.

The diagnostic PPM frame captures were black and are not relied on as visual evidence.

## Evidence and scope boundaries

Diagnostic-only runners carry a distinct fingerprint and an `acceptance_evidence: false` marker. They are not merged into official Stage79 evidence. No PASS record, coverage count, P08 gate, active Stage62 baseline, ROM, save, or historical contract was promoted or altered to conceal a failure. PR #16 remains unmerged. Bounded runtime PASS is not a claim that all P03/P05 product requirements or a full release are complete.

The original six wrapper regressions and 16 cumulative-orchestrator regressions remain enabled alongside the 20 new tests. A future seven-domain PASS must be obtained on a matching committed product/harness identity before integrating the cumulative runtime gate into P08.
