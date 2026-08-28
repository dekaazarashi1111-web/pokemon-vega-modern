# ChatGPT Pro向けStage58完全版スナップショット

## 役割

Stage58時点の作業を別環境でそのまま再開できる、単一ZIPの自己完結スナップショットである。
ZIPの作成はpackage rootの`PACKAGE_NEXT_FULL_SNAPSHOT.py`、展開後の検証は`VERIFY_SNAPSHOT.py`を正とする。

## 必須収録

- `workspace/`の全source、完全な`.git`履歴、現在HEAD。
- Stage58 ROM、focused check用Stage57 ROM、Stage58標準QA save。
- `PRIVATE_INPUTS/`のclean/Vega/Factory ROMとIPS/UPS。
- `OFFLINE_TESTKIT/`のhost/ARM toolchain、mGBA、ROM/BPS tool。
- 固定上流`vendor/`、受領資料、全BPS、生成済みmanifest/report。
- `SNAPSHOT_STATE.json`、SHA-256 manifest、開始手順、次snapshot生成器。

## ChatGPT 512MB profile

ChatGPTへ単一ファイルで渡す版は、package rootの生成器へ`--profile chatgpt-512mb`を指定する。
このprofileは512,000,000 bytesを上限として強制し、Stage58の現行作業に不要な過去BPSと、
現行source／Git履歴へ統合済みのtrainer checkpoint ZIPだけを除外する。ROM原本、Stage57／58、
QA save、全source、Git全履歴、固定上流、host／ARM toolchain、mGBAは保持する。

## 容量削減のための除外

- 再生成可能なStage57/58以外の`build/stages/*.gba`。
- `build/battle-core/`、`build/upstream-cache/`、dot-prefixed一時build directory。
- `.local/`配下のmGBA一時save、bisect、iPad read-back、診断workspace。ただし固定`dialogue-tools`とStage58標準QA saveは保持する。
- `__pycache__`、pytest/mypy/ruff cache、過去の完全版ZIP。

除外した旧Stageは、同梱clean input、builder、固定toolchainから再生成する。
512MB profileの詳細はpackage rootの`CHATGPT_512MB_PROFILE_JA.md`を正とする。

## 検証

展開後の最上位で次を実行する。

```bash
python3 VERIFY_SNAPSHOT.py
```

完全なStage58再構築と全mGBA/clean gateは次を使う。

```bash
python3 BUILD_CURRENT_FROM_SOURCE.py
```
