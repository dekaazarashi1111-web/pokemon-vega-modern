# 再現ビルドパイプライン

## 原則

最終ROMを手作業で継ぎ足さない。全工程をコマンド1つで再現できる状態を維持します。

```text
inputs/private/clean.gba
  -> build/reference/vega.gba
  -> build/stages/03_harness.gba
  -> build/stages/04_moves.gba
  -> build/stages/06_battle_core.gba
  -> build/stages/10_engine_slice.gba
  -> build/stages/13_kanto_slice.gba
  -> build/final/vega_modern_kanto.gba
  -> dist/vega_modern_kanto.bps
```

## 各stageの要件

- 入力hashを記録する。
- 出力hashを記録する。
- 適用module一覧を記録する。
- ROM領域割当mapを出力する。
- expected-byte assertionに失敗したらそのstageを中止する。
- 前stageを上書きしない。

## T03 harness

```bash
make harness
make harness-check
```

`make harness` はclean ROMとVega IPSから毎回作り直し、Vega既知hash、32 MiB `0xFF` 拡張、allocator、expected-byte、no-op module、連続2 build、libmGBA smokeを1回のtask固有gateで確認します。生成ROMは `build/stages/03_harness.gba`、machine-readable metadataは `build/stages/03_harness.json`、人間向け結果は `reports/generated/harness_smoke.md` です。`make harness-check` はエミュレータを再実行せず、現在の入力/config fingerprintと公開済み成果を照合します。

## 最終目標コマンド

T18では次を実装します。

```bash
make clean-build
make final
make release-patch
make verify-release
```

`make final`は私有入力が無ければ明確に失敗してよいが、ソースのみのCIは`make validate`で通るようにします。
