# Pokémon Vega Modern 全種入手設計・実装ソース

このパッケージは、添付された `v1.3.7` / snapshot `e0351f3deacc52816636e343ba748cb35d54e6bd` の証拠だけを入力として、単一ROM・通常プレイで合意対象を100%入手可能にするための全件表、共通runtime、generator、serializer、検証器、exact-ROM受入ケースをまとめたものです。ROM本体は含みません。

## 結論

- 完成数へ加算する一次収集対象: **1206種**（公式base 1025 + 真のVega固有181）。
- 進化入口として必要だが完成数へ加算しない恒常フォーム: **10種**。
- registry: 1621行、route: 1621行、静的到達検査対象: **1216行**。
- 追加・修正event: **201件**。内訳: CAPTURE 117, EGG 35, EVOLUTION_SUPPORT 23, FOSSIL 16, GIFT 8, SERVICE 1, TRADE_EMULATOR 1。
- release host: **24**。すべて既存Kanto objectのscript stub置換で、object追加は0。
- exact-ROM未添付のため、最終ROMへのsymbol binding、save allocation、legacy Tohoku入口、実機/mGBA受入は未実行です。

## 最初に読むファイル

1. `TARGET_DEFINITION.md`: 対象1206、フォーム、内部slotの確定。
2. `AUDIT_REPORT_JA.md`: 設計カバー率と実ROM証拠を分離した監査結果。
3. `IMPLEMENTATION_SPEC_JA.md`: transaction runtime、host、save、migration、fail-closed契約。
4. `PATCH_APPLY_ORDER.md`: repositoryへ入れる順序とrelease gate。
5. `OUTPUT_STATUS.json`: 各成果物の到達状態。

全件は `content/**`、割当・release契約は `manifests/**`、自動検査は `scripts/**` と `tests/**` にあります。

## ローカル静的検査

```bash
python scripts/validate_acquisition_content.py --package . --report reports/static_validation.json
python scripts/build_acquisition_content.py --package . --check
python tests/run_tests.py
```

`tests/run_tests.py` はcross-reference/new-game graph、再生成一致、負のfixture、host C runtimeを検査します。fail-closed adapterは意図的にABI probeを失敗させるため、実ROM用linkではrepository固有adapterへ差し替えます。

## ROM統合の入口

`PATCH_APPLY_ORDER.md` の順に、exact stage SHA確認 → engine adapter → save/flag/var owner → named allocator → internal wild Species sanitation → runtime build → map serializer → exact-ROM acceptanceを実行します。`READY_TO_SERIALIZE`以外のhostはrelease manifestへ入りません。
