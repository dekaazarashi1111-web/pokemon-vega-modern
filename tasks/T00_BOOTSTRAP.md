# T00 — Bootstrap and pin inputs

- Lane: `platform`
- Depends on: `none`

## Objective

Create a reproducible private-input workspace, verify all hashes, pin upstream source, and produce clean/Vega/Factory references.

## Execute

1. Read `AGENTS.md`, `docs/INPUT_CONTRACT.md`, and `config/project.toml`.
2. Run bootstrap auto-discovery. Fix path detection code rather than manually renaming files when possible.
3. Verify clean ROM size, CRC32, MD5, and SHA-1. Fail clearly on mismatch.
4. Extract the prior audit ZIP if supplied; otherwise use bundled `audit_seed`.
5. Acquire CFRU-JP, DPE-JP, and pokefirered from supplied archives or clone them, then checkout the configured commits.
6. Record actual source commits, input hashes, tool versions, and resolved paths in `state/source-lock.json`.
7. Generate Vega and Factory reference ROMs in `build/reference/` and keep them untracked.
8. Run exact patch conflict verification and store generated reports.

## Required outputs

- `state/source-lock.json`
- `reports/generated/preflight.md`
- `reports/generated/exact_audit/`
- `build/reference/vega.gba`
- `build/reference/factory.gba`

## Acceptance gates

- [ ] Clean ROM is exactly CRC32 3B2056E9 and 16 MiB.
- [ ] Factory UPS validates against the clean ROM and produces 32 MiB.
- [ ] Vega reference is generated from clean input, not from a previously patched ROM.
- [ ] No private binary is tracked by Git.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T00:`.
4. Mark the task done with `python3 scripts/taskctl.py done T00 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
