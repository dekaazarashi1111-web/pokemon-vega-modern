# Issue19: 自然野生初期技と戦闘EXP

状態 `FAIL` / run36040259713 / source `bb052880fe0658981c70e47c793c15a8524bf26d`。
候補 `8946438bc37fda468c53e41378a6f82fac8f0b1af7ac6785ef07ca708c2714a1`。受入済みentry repairの保存recipe適用だけで復元。ROM変更0、ARM0。

自然移動で発生した野生の4技/PPを固定原本のraw末尾4行窓→重複除外と独立照合する。
開始手持ちバタフリーLv43、EXPをLv44閾値-1、技53/89、能力値999、開始進行は明示fixture。
観測中は7API host書込禁止で通常移動/技選択/勝利EXP/空き枠497習得/通常Save/fresh Continueを行う。
fixture能力値は最終バランス・自然な手持ち取得・通常進行の受入ではない。
原本の初期技順は生の4行窓を先に取り、GiveMoveの既習得除外を後に適用する。独自sortや先行dedupは禁止。

新unit25、native0、成功0、fresh core0。
受入済みアメ11/Bag23/旧戦闘/egg8/旧host/ARM/Wikiの再実行0。
成功しても実観測owner/この空き枠ケースのみ。全owner・配布・孵化・form・EXP共有・置換・拒否・進化へ拡張しない。
Actions終端確認 `False`。原本 `content/modernization/pr16_learnset_natural_evidence/36040259713`。

## 次

Issue19: KeyErrorの保存原本を確認し、未成功の自然生成/戦闘EXP経路だけ修復する。既存アメ11/Bag23/旧戦闘/egg8/ARM/host/Wikiは再実行しない。
