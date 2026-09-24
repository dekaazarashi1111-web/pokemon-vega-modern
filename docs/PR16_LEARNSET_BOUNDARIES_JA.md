# PR16 Issue19: 戦闘EXP境界

状態 `PASS_BATTLE_EXP_BOUNDARIES`、入力HEAD `32b2ebfb0bfd2cd4679d378dca113a2e9ad534b9`、run `36068573757`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` は保存済みrecipeの復元のみ。ARM/原本生成/ROM変更と、変更影響がない受入済みcase再実行は0。

## 保存されたnative成功

- `butterfree-exp-known`: run `36068573757`、通常Save/fresh Continueまで。
- `butterfree-exp-multilevel`: run `36067198527`、通常Save/fresh Continueまで。
- `butterfree-exp-replace`: run `36068573757`、通常Save/fresh Continueまで。
- `butterfree-exp-summary-refuse`: run `36068573757`、通常Save/fresh Continueまで。

## 今回の検証

新unit 10、host compile 1、native process 3。未成功: []。原本証拠は `content/modernization/pr16_learnset_boundaries_evidence/36068573757`。

開始個体・EXP・能力値・進行はfixture。野生生成の既受入testは呼ばず通常歩行遭遇を共通setupとして利用。勝利/EXP/習得/Save/Continue区間は3組の書込barrierを使う。summaryでB取消して中止を確定する拒否と、最初の質問での拒否を区別。

## 未完と次

保存native成功は再実行せずcompleteでActions終端だけ照合。

## HP保存整合性の変更影響

初回run36065509607の3caseは技/PP検査成功だが、保存原本でHP999>最大HP106を確認したため、現行HP gateの受入から失効。履歴は上書きせずsuperseded_acceptancesとhealth-impact.jsonへ保存。複数レベル上昇の正常HP成功run36067198527は再実行しない。今回の変更影響あり再実行は 3 case、影響なしの受入済み再実行は0。

- `butterfree-exp-known`: Lv43 HP 104/104 → Lv44 HP 106/106。通常Save/fresh Continue一致。run `36068573757`。
- `butterfree-exp-multilevel`: Lv10 HP 32/32 → Lv16 HP 45/45。通常Save/fresh Continue一致。run `36067198527`。
- `butterfree-exp-replace`: Lv43 HP 104/104 → Lv44 HP 106/106。通常Save/fresh Continue一致。run `36068573757`。
- `butterfree-exp-summary-refuse`: Lv43 HP 104/104 → Lv44 HP 106/106。通常Save/fresh Continue一致。run `36068573757`。

新HP gateでも開始個体/EXP/能力/進行はfixture。野生/配布/孵化/form/進化/共有EXP全体の受入へ昇格しない。今回の選択経路は `scripts/pr16_exp_health_policy.py`。追加unitは累計36種、最新実行10件。変更なし26件はhash付き成功原本で照合する。
