# PR16 Issue19: 釣り・隠し野生の特殊技順

状態 `STOPPED_SPECIAL_WILD_BOUND`。run `36213386688` / source `af7a856d8ac04c2e3400cab550c02f0569185ae3`。

親候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。後継 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。

## 原本と厳密な研究表binding

旧36152934075の正常8callと旧36155273674の17unitは保存再利用。旧失敗checkpoint/監査JSONは改作しない。

監査36155747573は完了success。846行中130行だけmap3/19→255/255、他9フィールドは一致。宣言hash・実表10152byte/hash・offset・literal参照・差分全件/順序を照合し、全846行を再符号化する。近似一致や任意差分許可ではない。

130行の無効化意図/原stage由来は未裁定。ROM研究表は変更せず、map3/19はfixture/受入から除外する。716不変行と現ROM釣りheaderの交差だけを使用。

## 修復/受入境界

両経路で旧特殊技喪失を観測してから、釣り0x09392722・隠し0x0939274AのBLだけをNOP化。全8byte差分/全ROMrollback/同じ親から2独立replay。共通initializer・land・owner・戻り値は不変。

開始map/flag/profile/RNG/入口registerはfixture。7host書込み禁止下の直接CPU診断であり、通常釣竿/スキャナーUI・捕獲・Save/fresh Continueの受入ではない。

新unit 19 / host 0 / native 0 / ARM0 / 受入再実行0。保存case再利用 []。Actions終端は別途照合。

失敗 `{'message': 'unique wild map header', 'type': 'ValueError'}`。証拠 `content/modernization/pr16_special_wild_evidence/36213386688`。

1281 identity-only、旧Wiki、BP/P08、active baselineは不変。Issue19未完、release_ready=false、未merge。

## 次
Issue19: {'message': 'unique wild map header', 'type': 'ValueError'} を保存。次は未成功caseのみ修正。Issue19: 特殊野生の限定直接診断checkpointを確認し、成功caseを再実行しない。2callsite修復の全対照成功後は、別工程で通常釣竿/スキャナーUI→捕獲→通常Save/fresh Continueへ。map3/19の保存表130行は255/255のまま不変・由来未裁定で対象外。旧研究孵化15・配布17・野生・EXP・Bag・egg・ARM・Wikiは影響なしに再実行しない。
