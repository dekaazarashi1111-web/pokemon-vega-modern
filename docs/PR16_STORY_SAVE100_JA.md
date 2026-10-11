# 動的Ranger会話・ダグトリオ解放・Save100限定受入

`PASS_RANGER_TOWN_RELEASE_SAVE100_SCOPED`。Save99から通常2歩/2旋回で、実画面のRanger20,29の正面20,28南へ。連続2frameの位置を確認してA1回。町へのwarpと自動イベントを完了し、最初の操作可能field4,17北でSave100/独立Continue。

source `b83dcb3d7a0a5465606be442eb431c9d53e0acfe` / run `37198723726` / job `111425819528` 全8step成功。artifact `11302156714` / 316179bytes / SHA256 `2f336d128735e1a18da931eb69f069548bcfaec52d8481124a5b2ad2e645abc2`。69member/54画面/95+cold13入力。39controller（38+訂正1）/62新受入。成功native2/失敗0/事前失敗1/記録native0/旧成功再走0。

## 会話・町の連続script

観測0/1はRanger20,28、2から20,29へ移動。主人公は18,28→19,28→20,28、4/5で南向き正面を連続確認。6〜9で手紙到達を受けた台詞、10fade、11町5,16、12自動移動4,17。12〜19のキャプチャ/リリース台詞、20/21で3頭移動、23で障害消失、24別れ、25最初の操作可能field。NPCsceneのキャプチャをプレイヤーの捕獲/戦闘受入にしない。

固定会話は4382set/4380false→4072=2/4352clear/町warp。町の4072=2条件scriptが自動開始し、4380set/4352set/4072=3で終了。回復処理は別分岐なのでHP277/294とPP3,9,8,2保持。全party600byte/全Bag/23114円/紙0/4061=1/バッジ2保持。

通常2歩の4021=91→93/4022=1→3。scriptによる2歩は今回歩数counterへ加算されない。次friendship周期まで35歩。S61E payload差はbyte259の224→240、expanded4380だけ新set。CRC・全42sector checksum・PC・旧Save99 bank57344byte・全coldSaveRTC一致。全7145byte/1790範囲。

## 保存の中間状態・冷起動

26〜30通常menu0→4、31/32確認、33〜46保存中。45は最終Flashhashと同じでもcounter99、46はcounter100だが別途中hash、47で安定hash/保存成功文言、51でclearfield。瞬間hash/counterだけで完了扱いしない。

progress RAM454211fdからcold1a34e64cへ変化するがcold2観測は一致。全SaveRTC131088byte不変とは別の観測でありowner未解明。過去RAM53/42/physical2056の未解明も維持。progress/cold差564/408px、cold間588pxは目視確認した11tileの花animationだけで、主人公/通路は保持。全pixel一致とは主張しない。

## 事前失敗とbyte binding

run37198607755/job111425480014は親計画のhash不一致でnative0停止。artifact11302405444原本のfailure/manifestをそのまま保持。正本10384byteに対し転送写し10385byteだった。正本を改変せず、期待hashを正本の最終改行込みbyteへ訂正。初回38成功testを再走せず、新exact binding1caseのみ実行。JSON/text fixtureのSHAはGit正本の最終改行を含むbyte列から算出し、次commitをbranchへ反映する前にremote blob全byteを送信元と一致確認。改行正規化で差分を消さず、失敗原本は保持。受入済みunit/nativeは再走しない。

## 次

Save100 artifact11302156714のstory-fast.srm（131088bytes/SHA256 9a4185c74f4906eb05de0167f082fa70de166caf42c5aa6bf7a9fe85bfee77ff）だけから再開。ミルシティ3/2・4,17北。実Ranger20,29の正面20,28南から通常会話、warp5,16→自動2歩→ダグトリオ解放→最初fieldでSave100/Continueを限定受入。4072=3/4380set、4352最終set、4382/4383/紙0/4061=1/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。回復分岐なし/新戦闘0/プレイヤー捕獲0。次は西へ4歩、通常西connection3/24・53,13候補を固定床behavior0/offset4/逆offset-4/実画面で確認し、最初の新fieldでSave101/独立Continue。Ranger/解放scene/博物館/接近61歩を再走しない。4021=93/4022=3、通常2歩だけ加算でscript自動2歩は加算なし、次friendship周期35歩。progress RAM454211fdとcold1a34e64cは別hash、owner未解明。過去RAM53/42/2056も保持。95+cold13入力/54画面、45最終Flash一致でもcounter99/保存中、46counter100で別途中hash、47安定hash/成功、51clearfield。cold全SaveRTC保持、pixel差564/408/588は花animation11tileだけ。39controller=初回38成功＋訂正1、新62受入、native成功2/失敗0/事前失敗1/記録native0/旧成功再走0。初回run37198607755は正本写しの末尾改行hash差でnative0停止し原本不変。JSON/text fixtureのSHAはGit正本の最終改行を含むbyte列から算出し、次commitをbranchへ反映する前にremote blob全byteを送信元と一致確認。改行正規化で差分を消さず、失敗原本は保持。受入済みunit/nativeは再走しない。 Save99記録run37197809471全11step終端同期。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。全国図鑑/自然成長進化/全story/release未受入。一般CI既知qol_production.c不一致を全成功としない。warp-tableの座標だけで発火可能と判断しない。毎回固定ROMのtile behaviorと必要方向を確認し、通常着地/矢印/方向階段/境界connectionを区別する。実画面の出口は裏付け。無入力自動歩行は実測まで未確認。
