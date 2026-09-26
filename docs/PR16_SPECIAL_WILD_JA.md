# PR16 Issue19: 釣り・隠し野生の特殊技順

状態 `PASS_SPECIAL_WILD_BOUND_DIRECT_SCOPED`。run `36213677615` / source `804417f6f8fa4fc88f882ac96d6f0a1720811500`。

親候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91`。後継 `0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0`。

## 原本と厳密な研究表binding

旧36152934075の正常8callと旧36155273674の17unitは保存再利用。旧失敗checkpoint/監査JSONは改作しない。

監査36155747573は完了success。846行中130行だけmap3/19→255/255、他9フィールドは一致。宣言hash・実表10152byte/hash・offset・literal参照・差分全件/順序を照合し、全846行を再符号化する。近似一致や任意差分許可ではない。

130行の無効化意図/原stage由来は未裁定。ROM研究表は変更せず、map3/19はfixture/受入から除外する。716不変行と現ROM釣りheaderの交差だけを使用。

## 修復/受入境界

両経路で旧特殊技喪失を観測してから、釣り0x09392722・隠し0x0939274AのBLだけをNOP化。全8byte差分/全ROMrollback/同じ親から2独立replay。共通initializer・land・owner・戻り値は不変。

開始map/flag/profile/RNG/入口registerはfixture。7host書込み禁止下の直接CPU診断であり、通常釣竿/スキャナーUI・捕獲・Save/fresh Continueの受入ではない。

- control-fishing-no-rule: NO_SPECIAL_UNCHANGED; species 41; moves [250, 48, 62, 182] → [250, 48, 62, 182]; PP [15, 20, 20, 10] → [15, 20, 20, 10]; calls 1。

- control-hidden-parent: NO_SPECIAL_UNCHANGED; species 586; moves [717, 724, 201, 153] → [717, 724, 201, 153]; PP [10, 10, 10, 5] → [10, 10, 10, 5]; calls 1。

- control-hidden-repaired: NO_SPECIAL_UNCHANGED; species 586; moves [717, 724, 201, 153] → [717, 724, 201, 153]; PP [10, 10, 10, 5] → [10, 10, 10, 5]; calls 1。

- parent-fishing: SPECIAL_SLOT_OVERWRITTEN; species 492; moves [240, 349, 200, 225] → [240, 349, 200, 63]; PP [5, 20, 10, 20] → [5, 20, 10, 5]; calls 2。

- parent-hidden: SPECIAL_SLOT_OVERWRITTEN; species 1540; moves [207, 368, 253, 120] → [207, 368, 253, 1036]; PP [15, 20, 10, 5] → [15, 20, 10, 5]; calls 1。

- repaired-fishing: SPECIAL_SLOT_PRESERVED; species 492; moves [240, 349, 200, 225] → [240, 349, 200, 225]; PP [5, 20, 10, 20] → [5, 20, 10, 20]; calls 1。

- repaired-hidden: SPECIAL_SLOT_PRESERVED; species 1540; moves [207, 368, 253, 120] → [207, 368, 253, 120]; PP [15, 20, 10, 5] → [15, 20, 10, 5]; calls 1。

新binding unit 0（継承 19）、新header unit 8 / host 1 / native 7 / ARM0 / 受入再実行0。保存case再利用 []。Actions終端・全step・両artifact公開・非force pushの照合済み。

失敗 `None`。証拠 `content/modernization/pr16_special_wild_evidence/36213677615`。

1281 identity-only、旧Wiki、BP/P08、active baselineは不変。Issue19未完、release_ready=false、未merge。

## 完了照合

run 36213677615 / source `804417f6f8fa4fc88f882ac96d6f0a1720811500` / 成果commit `dcce2ff32dd304df18c840d08e0bc9fb65086a9e` は完了success。候補 `0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0`。headerは265件、重複map0/0の18件はfixtureに採用せず、一意なmap3/38を使用。

19 binding unitはrun36213386688の成功原本を継承（同run全体failureは維持）。header8unitと7native process/8callはrun36213677615で成功。今回の終端確認は新terminal8unitと原本再照合のみで、旧試験/native/host/ARM/ROM再実行0。通常UI・捕獲・保存は未受入。

## 次
Issue19: 候補0205af9bの特殊野生2callsite修復は直接診断7process/8callまで完了。保存recipeを親b7790902へ適用して全ROM hashを照合し、次は未受入の通常釣竿（map3/38）・スキャナー（map3/63）UI→特殊個体捕獲→通常Save→fresh Continue。開始map/party/item/flag/RNGのfixtureと観測後のキー入力を明確に分離し、7host書込み禁止でhook通過・個体100byte・4技/PP/PP Upsを確認する。今回19+8unit/直接7process、旧研究孵化15・配布17・野生EXP・Bag・egg・ARM・Wikiを影響なしに再実行しない。map3/19の130行無効化の由来は別の未裁定項目で、表は改作しない。
