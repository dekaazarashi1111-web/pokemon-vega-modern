# 入力契約

## 必須

| 入力 | 検証 |
|---|---|
| FireRed JPN Rev0 clean ROM | 16,777,216 bytes、CRC32 `3B2056E9`、MD5 `47596DB5A16556C60027E7BF372EC917`、SHA-1 `04139887B6CD8F53269ACA098295B006DDBA6CFE` |
| Vega 2018-02-23 IPS | 3,720,110 bytes、SHA-256 `94955C5830888C69A7DEE3696ABDA3B88F69184AF67F28A9FB77A8E8ABD77F5B` |
| Factory 2026-05-24 UPS | 16,012,506 bytes、SHA-256 `46EF4B008B7C68A94F919D037A0BBA31853B32AF3F50895E722E39DEEA336358`、input CRC32 `3B2056E9`、output 32 MiB |
| CFRU-JP source | pinを`source-lock.json`へ記録 |
| DPE-JP source | 同上 |

参照出力:

| 参照ROM | Size | CRC32 | SHA-256 |
|---|---:|---|---|
| Vega | 16,777,216 | `42A73E62` | `F600FB3FAA565BD335EA75114F9233F9A4FE97C12CFED145E0A7B48784D0C9D5` |
| Factory | 33,554,432 | `216AB7FD` | `570AC486F0E66563EE23278FF7EE34DD8DFEED11CBF37AB924D13EB2C62C0DA5` |

## 推奨

- 前回の`vega_cfru_integration_audit.zip`
- `pret/pokefirered` source。これは構造化されたMap/Eventの参照用であり、日本版BPRJの最終バイナリ位置の根拠にはしない。

## 原本ルール

物理原本は `userfile/imports/` に置き、`inputs/private` は安定名のGit管理外参照として読み取り専用にします。

```bash
python3 scripts/bootstrap_project.py --lock-inputs
```

ユーザーがファイルを差し替える時だけ書き込み権限を戻します。

入力名ではなくsize/hashで同一性を判定します。提供された適用済み2 ROMは、clean + 各patchから生成した参照とのbyte一致確認にだけ使い、ビルド入力にはしません。

## source取得

インターネット利用可能ならbootstrapがcloneします。利用不可ならsource ZIPを`inputs/source_archives`へ置きます。
