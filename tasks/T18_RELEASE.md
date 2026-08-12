# T18 — Create reproducible release pipeline

- Lane: `platform`
- Depends on: `T17`

## Objective

Generate a clean distributable patch and documentation without including copyrighted ROM binaries or private inputs.

## Execute

1. Implement `make final` from clean inputs and pinned sources.
2. Generate final ROM checksum manifest locally.
3. Create a BPS or UPS patch from the specified clean input to final output.
4. Reapply the release patch to a fresh clean copy and verify byte-identical final hash.
5. Package README, changelog, credits, checksums, known issues, and save compatibility notes.
6. Scan the archive for ROMs, saves, original patches, and private paths.
7. Tag the source revision and store build metadata.

## Required outputs

- `scripts/build_release.py`
- `dist/release/`
- `CHANGELOG.md`
- `CREDITS.md`
- `reports/generated/release_verification.md`

## Acceptance gates

- [ ] Release patch round-trip produces exact final hash.
- [ ] Archive contains no ROM/save/original patch.
- [ ] Source pins and input hashes are documented.
- [ ] Release build is reproducible from a fresh checkout plus private inputs.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T18:`.
4. Mark the task done with `python3 scripts/taskctl.py done T18 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
