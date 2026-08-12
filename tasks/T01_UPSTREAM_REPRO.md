# T01 — Reproduce upstream DPE/CFRU builds

- Lane: `engine`
- Depends on: `T00`

## Objective

Make the pinned DPE-JP and CFRU-JP sources build reproducibly before adapting them to Vega.

## Execute

1. Inspect upstream README/build scripts and capture every toolchain dependency and bundled converter hash.
2. Create `infra/` setup scripts that pin ARM tools and provide a WSL-safe wrapper for grit/wav2agb/mid2agb. Either pin native converters or hash/stage bundled PE tools into a Windows-launchable ASCII-path sandbox; never execute PE tools directly from a WSL UNC path. Use current Python first; add an isolated legacy runtime only if measured incompatibility requires it.
3. Never build in `vendor/upstream/**`. Create a disposable source sandbox from each pinned commit, give DPE a clean-ROM working copy and CFRU a dedicated copy of the selected DPE output, and record all source/config/tool fingerprints.
4. Build DPE-JP on a disposable clean-ROM copy using an explicit insertion region.
5. Build CFRU-JP on separate DPE outputs. Reproduce the pinned-current config as the baseline, derive and label a Factory-like candidate from measured Factory differences, then derive a minimal config by disabling feature clusters while retaining hard dependencies. Do not claim the pinned config is the Factory config without evidence.
6. Run two independent clean builds of every variant and require identical output hashes. Cache only artifacts keyed by input/source/config/tool fingerprints.
7. Compare the Factory-like build against Factory reference behavior and changed-address categories. Exact CRC equality is not required unless the same config is recovered.
8. Add a one-command upstream reproduction target and headless smoke prerequisites needed by T03.

## Required outputs

- `infra/README.md`
- `infra/setup_toolchain.sh`
- `infra/toolchain_manifest.json`
- `config/cfru_minimal.h`
- `config/cfru_factory_like.h`
- `reports/generated/upstream_repro.md`
- `scripts/build_upstream.py`

## Acceptance gates

- [ ] Pinned source builds without manual file editing.
- [ ] Build logs and tool versions are recorded.
- [ ] Minimal and Factory-like configs are explicit and diffable.
- [ ] Repeated builds from the same inputs have identical output hashes.
- [ ] Pinned upstream worktrees remain clean; every build runs in a disposable sandbox.
- [ ] grit, wav2agb, and mid2agb each pass one fixture conversion through the selected WSL-safe path; ARM tools, converters, Python, and headless emulator path/version/hash are recorded.
- [ ] Generated reports can be deleted and reproduced from a tracked command, input/source/config/tool fingerprint, and expected artifact hashes recorded in the run log or a tracked manifest.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T01:`.
4. Mark the task done with `python3 scripts/taskctl.py done T01 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
