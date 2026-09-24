# PR16 Issue19: 戦闘EXP境界

状態 `PARTIAL_BATTLE_EXP_BOUNDARIES`、入力HEAD `3121b03c779207cc120fb5dc83ac219d965106ea`、run `36065509607`。Actions終端確認 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` は保存済みrecipeの復元のみ。ARM/原本生成/ROM変更/受入済みcase再実行は0。

## 保存されたnative成功

- `butterfree-exp-known`: run `36065509607`、通常Save/fresh Continueまで。
- `butterfree-exp-replace`: run `36065509607`、通常Save/fresh Continueまで。
- `butterfree-exp-summary-refuse`: run `36065509607`、通常Save/fresh Continueまで。

## 今回の検証

新unit 20、host compile 1、native process 4。未成功: ['butterfree-exp-multilevel']。原本証拠は `content/modernization/pr16_learnset_boundaries_evidence/36065509607`。

開始個体・EXP・能力値・進行はfixture。野生生成の既受入testは呼ばず通常歩行遭遇を共通setupとして利用。勝利/EXP/習得/Save/Continue区間は3組の書込barrierを使う。summaryでB取消して中止を確定する拒否と、最初の質問での拒否を区別。

## 未完と次

Issue19: EXP境界の保存成功caseを再実行せず、失敗caseだけを修復する。全4caseの終端照合後は、最初の質問での拒否、戦闘EXP進化/共有、自然配布/孵化/form、釣り/隠し野生の特殊技順を限定追加。既受入野生初期技/EXP空き枠・アメ11/Bag23/egg8/旧host/ARM/Wiki/原本再採取は変更影響なし。全owner/Issue19/release/baseline切替は未完。
