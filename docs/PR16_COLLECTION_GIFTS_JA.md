# PR16 Issue19: Collection学習owner配布

状態 `FAIL`。学習owner限定受入 0/17、定義全体18件中1件は既存方針で保留。Actions終端 `False`。

source `194670bade3bcb584e651db301c09ba11c7eeb29` / run `36111746469`。候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes。ROM/runtime/原本方針は変更しない。

## 範囲と保留

固定form2と研究タマゴ15。初期party、開始場所、全unlock、未受領ownerはfixture。実NPCのroot/menu/page/選択、配布、原本初期技/PP、通常Save、fresh-core Continue、再訪取消を検証。ストーリー到達・研究ランク獲得・研究タマゴ孵化は含まない。7host書込APIを拒否し、getterはguard区間間の読み取り補助として分離。

ギザみみピチュー1281は `EXCLUDED_REMAKE_FORM_IDENTITY_ONLY` / `IDENTITY_ONLY_NO_REPLACEMENT` / payloadなし。自動fallback禁止・既存4技保持を優先し、通常ピチューの技流用や空4技を成功期待値にしていない。この配布初期技は未受入。初回run36110983368はこの期待値境界で停止、native/host0。旧22unit成功原本を継承し再実行しない。

| case | species | level | egg | 原本4技 | 実測run |
| --- | ---: | ---: | ---: | --- | ---: |

未成功学習owner `[]`。全party200byte/元party100byte、owner CRC/claim bit、4技/PP/PP Ups/HP/egg getter、frame/counterをraw textで照合。固定claim保持は確認するが、二重受取の実選択は含まない。

今回新scope-unit 9、旧unit実行 0、host compile 0、native 0。受入済み自然配布/孵化3・EXP/Bag/egg8/旧野生/ARM/Wikiは再実行しない。

## 次

Collection配布の失敗原本を確認し未成功caseだけ修復。受入済みcaseは再実行しない。
