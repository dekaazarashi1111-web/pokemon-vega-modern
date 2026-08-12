# T01 — Reproduce upstream DPE/CFRU builds

- Lane: `engine`
- Depends on: `T00`

## Objective

Make the pinned DPE-JP and CFRU-JP sources build reproducibly before adapting them to Vega.

## Execute

1. Inspect upstream README/build scripts and capture every toolchain dependency.
2. Create `infra/` setup scripts or a devcontainer that installs devkitARM and the Python version actually required by the pinned source.
3. Build DPE-JP on a disposable clean-ROM copy.
4. Build CFRU-JP on the DPE output using at least two configs: minimal features and Factory-like features.
5. Record source config defines and generated ROM hashes.
6. Compare the Factory-like build against Factory reference behavior and changed-address categories. Exact CRC equality is not required unless the same config is recovered.
7. Add a one-command upstream reproduction target.

## Required outputs

- `infra/README.md`
- `infra/setup_toolchain.sh`
- `config/cfru_minimal.h`
- `config/cfru_factory_like.h`
- `reports/generated/upstream_repro.md`
- `scripts/build_upstream.py`

## Acceptance gates

- [ ] Pinned source builds without manual file editing.
- [ ] Build logs and tool versions are recorded.
- [ ] Minimal and Factory-like configs are explicit and diffable.
- [ ] Repeated builds from the same inputs have identical output hashes.

## Finish

1. Run `make validate guard`.
2. Update reports and state.
3. Commit with a message beginning `T01:`.
4. Mark the task done with `python3 scripts/taskctl.py done T01 --summary "..."`.
5. If another task is READY, continue without waiting for approval.
