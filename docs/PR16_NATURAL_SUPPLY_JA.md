# PR16 Issue19: 通常配布・初期技孵化

状態 `PARTIAL_NATURAL_SUPPLY`、source `eacba232c1fd33c8096bd1a92e0adb4043b2320f`、run `36103989903`。Actions終端 `False`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` を保存recipeから復元。ROM/ARM/既受入case再実行0。

キャタピー649とVegaリープン1は親2体・開始地点だけfixture。通常育て屋へ預け、実歩行生成・受取・Save/fresh Continue・実歩行孵化・通常Save/fresh Continueを検証。期待初期技は公式/Vega採用原本の順序。旧条件付きegg8は再実行しない。

永遠の花フラエッテ1029はmap96/5 local15の実NPCからLv50を受取。開始party/場所/Ring/未受領flagはfixtureで、Ringの通常取得やストーリー到達の受入ではない。原本末尾4技204/235/382/738・PP・既存party不変・Save/fresh Continue・再配布なしを照合。12技全体の通常供給受入ではない。

保存成功 `['caterpie-initial-hatch', 'leepun-initial-hatch']`。未成功 `['floette-eternal-npc-initial']`。今回unit 12、host compile 1、native process 1。終端記録専用の場合これらの再実行0。

## 次

自然供給checkpointの失敗原本を確認し、未成功caseだけ修復。保存成功/旧受入は再実行しない。
