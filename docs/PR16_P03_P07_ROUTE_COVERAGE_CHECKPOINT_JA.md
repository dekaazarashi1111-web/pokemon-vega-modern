# PR #16 P03 / P07 経路被覆 checkpoint

## 結論

このcheckpointは、処理所有者ごとの有限な経路台帳である。

- **P03で残る追加実操作は1件だけ**: `P03_FIXED_FORM_TRANSITION_PHYSICAL`
- `P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL` はrun `34675976411` のnative代表受入で閉じた。
- Rotom bespoke transitionは既存の10ケースで受入済みである。
- **P07固有の追加実操作は0件**であり、親候補上の成功を後継候補へ接続する作業はP08が所有する。

正本は `content/modernization/pr16_p03_p07_route_coverage.json`、検証器は
`scripts/pr16_p03_p07_route_coverage.py` である。

## P03

### 既存成功へ接続した経路

レベル・進化習得、通常繁殖、Pichu/Happiny、通常技・タマゴ技のわざメモリー、
技忘れ、機械・教え技、共有タマゴ技、Rotom 5フォームは既存原本へ接続済みである。
通常繁殖を共有技の受入で代替せず、run `34434453733` の8ケースを保持する。

### generic form-change carry

61経路・10種の所有者は `generic_form_change_service` である。Shaymin代表について、
実FORM受付、入力だけの有限メニュー探索、同一個体の4技持越し、取消、通常save、
fresh Continueを2 process・5 fresh coreで受け入れた。

- receipt: `content/modernization/pr16_generic_form_acceptance.json`
- run: `34675976411`
- artifact: `10292791318`
- candidate: `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`

これは共有実装契約のnative representative acceptanceであり、61行を個別実行したという主張ではない。

### 残るfixed transition所有者

Stage73のフォーム契約70経路・19種の現在地は次のとおり。

| 所有者 | 経路 | 種 | 状態 |
|---|---:|---:|---|
| generic form-change carry | 61 | 10 | native代表受入済み |
| existing fixed transition | 4 | 4 | 実操作待ち |
| Rotom bespoke transition | 5 | 5 | 実受付で受入済み |

残る4経路はNecrozma Dusk Mane / Dawn WingsとZacian / Zamazenta Crownedである。
実際の固定遷移または戦闘変身入口から、専用技、4枠境界、取消または不成立、復帰、
戦闘後状態、許されるsave/Continue境界を確認する。generic FORMやRotomは繰り返さない。

## P07

静的照合は、採用追加1,073行、通常種からの保持499行、欠落・競合0である。
P07が親候補へ加えた変更面は、保持レベル310行、保持タマゴ189行、Happiny衝突adapterに限定され、
いずれも親候補上で実受入済みである。

- P07親候補: `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`
- 後継候補: `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`

後継候補への変更影響判定・代表回帰・証拠移送は `FINAL_NATIVE_ACCEPTANCE` のP08作業であり、
P07経路gapを再オープンしない。

## 検証

```bash
python scripts/pr16_generic_form_checkpoint.py
python scripts/pr16_p03_p07_route_coverage.py \
  --check-remaining content/modernization/p08_remaining_work.json
python -m unittest tests.test_pr16_generic_form_checkpoint
python -m unittest tests.test_pr16_p03_p07_route_coverage
```

P03全体、P08、clean-ROM再生成、release-ready、PRのdraft/merge状態はこのcheckpointで変更しない。
