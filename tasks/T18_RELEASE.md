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
8. 既定即時文章、移動速度、孵化演出、全体学習装置、育成/PC操作、解禁時期、save移行を利用説明とfeature matrixへ記載する。
9. Battle Factoryの操作、4段階解禁、rental/交換/連勝、BP shop、施設外NPC捕獲、Mirageとの役割分離、save復旧を説明し、移植元source/作者/利用条件とFactory参照hashをcredits/build metadataへ記録する。

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
- [ ] Release文書と `config/feature_matrix.csv` が `docs/QOL_POLICY.md` の全既定値・操作方法と一致する。
- [ ] Release archiveへFactory UPS/ROMを含めず、施設source provenance、解禁、操作、known issue、save互換性を再現可能な形で記載する。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T18 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T18:`.
5. If another task is READY, continue without waiting for approval.
