# PR16 Issue19: Collection配布の原本初期技

状態 `FAIL`。限定受入 0/18。Actions終端 `False`。

source `41cde956a32911242a7d12c41b2ada62f29494a3` / run `36110983368`。候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes。ROM・runtimeは変更しない。

## 範囲

18経路（固定form3、研究タマゴ15）の実NPC・root/menu/page/選択・配布・通常Save・fresh-core Continue・再訪取消。初期party、開始場所、全unlock、未受領ownerはfixture。ストーリー到達・研究ランク獲得・タマゴ孵化・全owner・releaseを含まない。

配布以降は7host書込APIを拒否し通常キー入力のみ。getterはguard外の読み取り補助として分離。4技/PP/PP Ups/HP/egg bit/元party100byte/全party200byte/owner CRCとclaim bit/Save counterをraw textで独立照合。固定配布のclaim bit保持は確認するが、二重受領の実選択はこの試験では行わない。

| case | species | level | egg | 原本4技 | 実測run |
| --- | ---: | ---: | ---: | --- | ---: |

未成功 `[]`。今回新unit 22、host compile 0、native process 0。旧自然供給3、EXP、Bag、egg8、通常野生、ARM/Wikiを再実行しない。source入力転送run36108830541/36109072704は検証件数へ数えない。失敗原本は成功に書き換えない。

## 次

Collection配布checkpointの失敗原本を確認し未成功caseだけ修復。保存成功と旧受入は再実行しない。
