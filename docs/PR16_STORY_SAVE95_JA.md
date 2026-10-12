# 封書引渡し・Save95限定受入

`PASS_LETTER_HANDOFF_SAVE95_SCOPED`。Save94の博物館2階11,8東から新13歩/5旋回/一時通行待ち1、4,8南でlocal2へ封書274一個を通常引渡し。Bag slot4は274x1→空、S61E payload259は160→224で4382だけset。4383とバッジ2/全party600byte/HP277/PP3,9,8,2/23114円/4061=1/PC保持。通常Save95と独立Continueを受入。

source `c334efffedc30d4b2a0ceae7782c382dbc4e8f5c` / run `37190913464` / job `111402700990` 全8step成功。artifact `11298657664` / 303237bytes / SHA256 `184fef2f402dd439ce195d49cf586b144191c9060a5ede59b96afca5c4cccf5a`。81member/66画面/118+cold13入力。controller最終46case、39+影響9=48成功実行。初回39のうち変更影響2だけ再検査/無影響成功再走0。新独立受入69。成功native2/未保存失敗native1/記録native0。

## 移動NPCと失敗履歴

run37190678835は21画面52入力/native1/通常保存0/Save94全保持。local2は初期座標4,9から左右へ歩くmovement type5で、最初A時は5,9にいた。元failure結論と全原画を保持。固定ROMのobject24byteとsource-lockのmovement enumを照合し、失敗原画19の内部128pixelを抽出、左右向きspriteのいずれかが正面4,9へ来るまで決定しない待機へ限定修正。成功19/20は未到着、21/22で連続確認し、90frame待機後23で会話開始。RAM座標書換えやNPC固定はしない。

## 会話・保存・境界

23「それはだいじなふうしょ」から37まで全15dialog。506前のダグトリオと505道路レンジャーへの案内を確認。38で最初fieldへ復帰して保存。39〜43menu0→4、44/45確認、46〜59保存中。59counter95でも部分hash/保存中文字、60最終hash/成功文言、63overlayなしfield。cold0/1も4,8南field。全131088byteSaveRTCはcold/120frame後保持。

63→cold0/1は744/920pixel、cold間1023pixel差。全差分はNPC3人の矩形x48..63/y45..70、x101..132/y83..102、x193..206/y1..38内のみ。主人公/地形は保持するが全画面一致は主張しない。Save差分7064byte1772範囲、42checksum、旧Save94bank57344byte保持。

RAM台帳は会話中32で変化しowner未解明。physical全保持、aux4021:83→96/4022:0→3 owner未解明。紙消費/4382のscript ownerとは別。過去Save94のRAM10/2056/3vars、Save93/92/91/89/87等も未解明のまま。全国図鑑/自然成長進化/全story/releaseは未受入。

## 次

[新復路13歩と下降階段](../content/modernization/pr16_story_save95_next_route.json)。4,8南から11,8へ新復路、0x6Fの西入力で1階へ初下降し最初fieldで保存。次の到達は静的候補だけで未受入。封書会話/受付/旧入館を繰り返さず、館退出後に505道路レンジャーへ進む。

Save95 artifact11298657664のstory-fast.srm（131088bytes/SHA256 7a23bd41f4c9131b3abc4dee4d9efd974ca9e9a681bf78cc835f4c0e3e240fa4）だけから再開。博物館2階6/1・4,8南で封書274を一個引渡し、4382setを通常保存/独立Continueで受入。新13歩/5旋回/障害待ち1、local2の左右移動を原画128pixelで2回確認してから会話、90frame待機/全15dialog。次は新復路13歩で11,8の0x6F方向階段へ、西入力で1階へ初下降し最初のfieldを保存。封書会話/50円受付/旧入館を再走しない。505道路レンジャーは退出後。23114円/4061=1/バッジ2/4383/未完4380/全party600byte/HP277/294/PP3,9,8,2保持。今回RAM差分は会話32、aux4021:83→96/4022:0→3 owner未解明、過去ownerも未解明のまま。66画面118+cold13入力。59counter95でも途中hash/保存中、60成功文言/最終hash→63clearfield。cold間1023pixel差分は3人NPCだけ、全画面一致とは主張しない。全SaveRTC/PC保持、S61Eは4382bitだけset。初回失敗native1/52入力21画面/Save94全保持、通常保存0。controller39+影響9=48成功実行/最終46case、影響ある旧2だけ再検査、無影響再走0。新独立受入69/成功native2/記録native0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。
