# 館の西廊下14歩・新野生1勝・Save58限定受入

`PASS_MANSION_WEST_HALL_SAVE58_SCOPED`。Save57の19,13北から北1/西12/南1の通常14歩。7,13で新バーニン♂Lv12に遭遇し、つばめがえし1回で通常撃破。Save58と独立Continue。HP288/294・PP[15,10,15,12]。上階/有効階段/像の紙は未到達。

source `0b04797685f2ab58748ae3995a87908ccbf57743` / run `37156185740` / job `111299923943`全8step成功。artifact `11285967181` / 163842bytes / SHA256 `5c534a49b2ca8be3732229c879c31a4b04847b8f10ff907a61e63dd335c687b3`。69member/54画面/95+cold13入力。新controller26case、51新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 通常入力と保存

0〜15暗所14歩と北→西→南の向き、16野生遷移/17暗転/18battle。19バーニン♂Lv12、20オノノクスLv100。22slot0/23slot2/24slot3の実技UIでつばめがえしPP13、25撃破/実PP12、26field。battle_flags4/outcome1とwire field:falseの残留を未復帰や追加勝利にしない。

27〜31通常menu0→4、32確認/33上書き、34〜46保存中。46counter58でも部分write、47〜50成功文言/安定Flash、51field。progress26/51とcold0/1は人物と床の暗所field全byte一致、全SaveRTCも一致。

## 限定差分と未完

全party600bytesの差分はslot3 PP13→12の1byteだけ。全HP/EXP/held item/残party・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save57bank57344byte保持。42checksum、6980byte/1725範囲。aux4021=38→52のruntime owner未解明。RAMledgerは野生出現観測19で39b9382b...へ変化しcoldまで同一、owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明も保持。

有効階段30,10への接尾辞44歩が残る。旧20,24着地点warpの不発原本はSave57に保持。紙16,28/item274/flag4383の静的ownerも既読原本を継承し再採取0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: Save58 artifact11285967181のstory-fast.srm（131088bytes/SHA256 35dd83901109efb4c39d1c8fa299bd9555d830f8683be6b9b6495fa32bf994dc）だけから再開。map1/59・7,13南。未通過接尾辞14歩と新野生バーニン♂Lv12へ1勝、つばめがえし1回/PP13→12、HP288/294・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1保持、Save58/独立Continueを限定受入。上階/有効階段/像の紙は未到達。次は保存済pr16_story_save58_measure.ROUTEの7,13からの接尾辞44歩、南7,16→西5,16→北5,6→東28,6→南28,10→東30,10のbehavior108階段warp5→map1/60warp2へ通常入力。最初の新event/戦闘/未通過境界で保存。到着候補32,10/33,10は未測定。旧20,24warp8は床behavior8上の着地点で不発、未保存失敗16入力3画面/native1のSave57原本を保持し同じ北歩行を繰り返さない。紙ownerはmap1/60背景16,28/script149012422・item274/flag4383と静的照合済みだが未取得。26新controller/51新受入、95+cold13入力54画面69member/native2を無影響再走0。RAMledgerは野生出現観測19で39b9382baeda2cb8d82ff8ff47f4b452d6c9cc0de27e46afa550374f7505747eへ変化しowner未解明、全coldSaveRTC/全暗所field画面同一。46counter58でも部分write、47成功→51field。旧RAM/offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
