# PR16 Issue19: 戦闘EXP境界

状態 `PASS_BATTLE_EXP_BOUNDARIES`、入力HEAD `324c7c8ab593a1dc21adf1b39dbd62707561b411`、run `36067198527`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` は保存済みrecipeの復元のみ。ARM/原本生成/ROM変更/受入済みcase再実行は0。

## 保存されたnative成功

- `butterfree-exp-known`: run `36065509607`、通常Save/fresh Continueまで。
- `butterfree-exp-multilevel`: run `36067198527`、通常Save/fresh Continueまで。
- `butterfree-exp-replace`: run `36065509607`、通常Save/fresh Continueまで。
- `butterfree-exp-summary-refuse`: run `36065509607`、通常Save/fresh Continueまで。

## 今回の検証

新unit 9、host compile 1、native process 1。未成功: []。原本証拠は `content/modernization/pr16_learnset_boundaries_evidence/36067198527`。

開始個体・EXP・能力値・進行はfixture。野生生成の既受入testは呼ばず通常歩行遭遇を共通setupとして利用。勝利/EXP/習得/Save/Continue区間は3組の書込barrierを使う。summaryでB取消して中止を確定する拒否と、最初の質問での拒否を区別。

## 未完と次

保存native成功は再実行せずcompleteでActions終端だけ照合。
