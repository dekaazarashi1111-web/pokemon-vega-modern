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

## 容量削減のための除外

- 再生成可能なStage57/58以外の`build/stages/*.gba`。
- `build/battle-core/`、`build/upstream-cache/`、dot-prefixed一時build directory。
- `.local/`配下のmGBA一時save、bisect、iPad read-back、診断workspace。ただし固定`dialogue-tools`とStage58標準QA saveは保持する。
- `__pycache__`、pytest/mypy/ruff cache、過去の完全版ZIP。

除外した旧Stageは、同梱clean input、BPS、builder、固定toolchainから再生成する。

## 検証

展開後の最上位で次を実行する。

```bash
python3 VERIFY_SNAPSHOT.py
```

完全なStage58再構築と全mGBA/clean gateは次を使う。

```bash
python3 BUILD_CURRENT_FROM_SOURCE.py
```
