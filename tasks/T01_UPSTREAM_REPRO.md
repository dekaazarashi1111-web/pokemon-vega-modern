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
9. 固定commitで、現代孵化、全体学習装置、mint、特性カプセル/パッチ、王冠、経験アメ、再利用TM、DexNav、Raid、PC/summary拡張、自動戦闘に相当する実装・config・依存hookの有無を機械可読matrixへ記録する。名称だけで実装済みと判定しない。
10. 固定CFRU-JPの `frontier.c`、`frontier_records.c`、trainer/rental table、ランダム選出、連勝/BP、参加判定と依存configを機械可読matrixへ追加し、Factory参照ROMとの挙動対応を記録する。既に固定済みのFactory UPS/参照ROMを使い、再取込・再download・VegaへのUPS重ね掛けは行わない。
11. 固定CFRU-JPの `src/Battle_AI/{ai_master,ai_negatives,ai_positives,ai_advanced,ai_partner,ai_util}.c`、`battle_start_turn_start.c`、`end_turn.c`、AI hook、controller、damage/accuracy、switch/item/gimmick判断、`include/battle.h` のactive `aiFlags`、分散AI cache/history、trainer EV tableとconfigをpath/hash付きでinventoryする。古い `include/constants/battle_ai.h` や浮動HEADを実装根拠にしない。
12. single最大partyとdouble 4 battlerのcold/warm cache fixtureで固定CFRU AIの処理時間を計測し、T06で使うemulator/cycle計測条件と許容閾値をmachine-readableに固定する。

## Required outputs

- `infra/README.md`
- `infra/setup_toolchain.sh`
- `infra/toolchain_manifest.json`
- `config/cfru_minimal.h`
- `config/cfru_factory_like.h`
- `reports/generated/upstream_repro.md`
- `reports/generated/upstream_feature_matrix.csv`
- `scripts/build_upstream.py`

## Acceptance gates

- [ ] Pinned source builds without manual file editing.
- [ ] Build logs and tool versions are recorded.
- [ ] Minimal and Factory-like configs are explicit and diffable.
- [ ] Repeated builds from the same inputs have identical output hashes.
- [ ] Pinned upstream worktrees remain clean; every build runs in a disposable sandbox.
- [ ] grit, wav2agb, and mid2agb each pass one fixture conversion through the selected WSL-safe path; ARM tools, converters, Python, and headless emulator path/version/hash are recorded.
- [ ] Generated reports can be deleted and reproduced from a tracked command, input/source/config/tool fingerprint, and expected artifact hashes recorded in the run log or a tracked manifest.
- [ ] `docs/QOL_POLICY.md` の各機能について、upstream実装の有無、有効config、Vega adapter要否が根拠付きで分類される。
- [ ] Battle Factoryの各source/config/生成tableが固定commitから再現でき、Factory参照との一致・差異とVega adapter要否が根拠付きで分類される。
- [ ] CFRU AIのactive source、hook、flags、cache/RNG、knowledge access、EV依存とVega adapter要否が機械可読matrixへ入り、`VAR_GAME_DIFFICULTY` やlevel scalingを暗黙に有効化しない。
- [ ] `AI_BASIC=1`、`AI_SEMI_SMART=3`、`AI_FULL_SMART=5` のactive bit mappingと、worst-case single/doubleの性能基準・許容閾値が再現可能なfixtureで記録される。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T01 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T01:`.
5. If another task is READY, continue without waiting for approval.
