# Vega × DPE-JP/CFRU-JP 統合監査ワークスペース

この一式は、アップロードされたベガIPSとFactory UPSを実際に復号・比較し、
Vegaを基準にDPE-JP/CFRU-JPを移植するためのPhase 01成果物です。
ROM、IPS、UPS本体は含めていません。

## 現在の結論

- 単純なパッチ結合ではなく、Vegaを基準にDPE-JP/CFRU-JPをソース移植する必要があります。
- UPSはFireRed日本版Rev 0（CRC32 `3B2056E9`）を入力に、16 MiBから32 MiBへ拡張します。
- 両パッチが直接触る場所は775 bytes / 269 rangesです。
- そのうち169 ranges / 533 bytesはVegaの技名／技データポインタを含みます。
- 最初の実装対象はSpecies追加ではなく、VegaのMove ID・技表とCFRU戦闘エンジンの統合です。
- 現時点では起動可能な統合ROM／統合パッチは生成していません。

## 1. パッチだけで再解析

```bash
python3 tools/analyze_patches.py \
  "18年2月23日完成版ベガ.ips" \
  "factory_test_20260524.ups" \
  --out-dir reports
```

## 2. クリーンROMを使った厳密判定

両方が触る775 bytesについて、最終値が同じか異なるかを端末内だけで判定します。

```bash
python3 tools/verify_with_clean_rom.py \
  FireRed_JPN_Rev0_clean.gba \
  "18年2月23日完成版ベガ.ips" \
  factory_test_20260524.ups \
  --out-dir exact_audit
```

参照ROMもローカル生成する場合だけ、末尾に`--write-reference-roms`を付けます。
生成ROMはGitへcommitせず、再配布しないでください。

## 3. DPE-JP/CFRU-JP公開ソースの固定アドレス監査

公開リポジトリをローカルへcloneした後に実行します。

```bash
python3 tools/audit_source_addresses.py \
  "18年2月23日完成版ベガ.ips" \
  --cfru /path/to/CFRU-JP \
  --dpe /path/to/DPE-JP \
  --out-dir source_audit
```

`hooks`、`repoints`、`repointall`、`routinepointers`、`bytereplacement`、
`special_inserts.asm`を抽出し、Vega IPSが既に変更した場所を報告します。

## 4. 参照ROMを別々に生成

```bash
python3 tools/build_reference_roms.py \
  FireRed_JPN_Rev0_clean.gba \
  "18年2月23日完成版ベガ.ips" \
  factory_test_20260524.ups \
  --out-dir reference_roms
```

これは逆アセンブル・差分検証用です。統合ROMは生成しません。

## 主要ファイル

- `PHASE_01_STATUS.md`: 完了・未完了・Go/No-Go
- `reports/conflict_report.md`: 人間向け数値結果
- `reports/semantic_hotspots.md`: 技表、タマゴ技、文字列、格納領域の設計分析
- `reports/conflict_report.json`: 機械可読の全結果
- `reports/conflicts.csv`: 269件の直接二重変更
- `config/conflict_resolution_template.csv`: 移植判断を記録する作業表
- `CODEX_TASK_01.md`: 固定アドレス／依存関係監査
- `CODEX_TASK_02_MOVE_PORT.md`: 最初の実コード移植タスク

## 禁止事項

- Factory UPSをVegaへ強制適用する
- UPSのchecksum検証を無効化して重ねる
- 重複byteだけVega優先／Factory優先にして完成扱いする
- ROMや生成ROMを公開リポジトリへ置く
