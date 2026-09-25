# PR16 Issue19: 釣り・隠し野生の特殊技順

状態 `STOPPED_SPECIAL_WILD_REPAIR`。run `36155273674` / source `28a138552429c5ff7473aafd316a929b601051dd`。

親候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。後継 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。

## 保存原本と修復境界

初回36152934075は研究表のないmap11/3で特殊技を観測できずfailure。通常個体8callは変更前後一致。原失敗CP/証拠は不変。13旧unitや同じ8callを再実行しない。

現候補の実入口はResearch Economyへ直接接続し、V4→QOLへ委譲する。旧Stage59ソースを現在の実到達経路へ読み替えない。846研究行と候補QOL blobの全table byte一致を要求し、実釣りheaderとの交差からfixtureを選ぶ。

修復は釣り0x09392722・隠し0x0939274Aの共通再初期化へのBLだけをNOP化。原候補2経路で実QOL特殊技第4枠が消えることを観測した後だけ生成する。共通initializer・land・戻り値・owner方針は変更しない。8byte限定差分、全ROM rollback、2独立replayを検査。

新開始map/進行flag/profile/RNGと入口レジスタはfixture。観測区間は7host書込み拒否下のCPU実行と読取のみ。通常釣竿/スキャナーUI、捕獲、Save/Continue、ストーリー到達は未受入。

新unit 17、host compile 0、native process 0、ARM0。受入済み再実行0。後継作成 0。Actions終端未確認。原本 `content/modernization/pr16_special_wild_evidence/36155273674`。

失敗記録 `{'message': 'exact authored846/QOL binary table', 'type': 'ValueError'}` / case別 `{}`。

1281 identity-only/自動fallback禁止、Issue19全体未完、release_ready=false、PR未merge、active baseline不変。

## 次
Issue19: 特殊野生修復checkpointの失敗原本を先に読み、未成功caseのみ修正する。保存成功の親診断や対照を再実行しない。Issue19: 特殊野生の2 callsite限定修復と直接native対照を保存。次は変更後候補で通常釣竿/スキャナーUI→捕獲→通常Save/fresh Continue。直接call fixtureを通常取得へ読み替えない。元親/同じ特殊技診断/受入済み研究孵化15・配布17・旧野生・EXP・Bag・egg・旧ARM・Wikiは変更影響がない限り再実行しない。
