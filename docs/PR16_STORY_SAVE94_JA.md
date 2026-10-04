# 博物館2階・Save94限定受入

`PASS_MUSEUM_SECOND_FLOOR_SAVE94_SCOPED`。Save93の支払済み1階14,5東から西6南3/旋回2、8,8で東入力を1回だけ行い、2階6/1・11,8東へ到着。追加自動歩行なし。通常Save94と独立Continueを受入。紙274一個・23114円/4061=1・バッジ2・全party600byte/HP277/PP3,9,8,2保持。

source `b773e5611b374491a793985ef53c282912e35a5a` / run `37189671003` / job `111399049470` 全8step成功。artifact `11298740300` / 212641bytes / SHA256 `87fd0d3f983d81cfc9964bc7a143fdf2988d8abf84e0aa2d272e465d70078abb`。56member/41画面/70+cold13入力。controller最終41case。43実行=初回38成功1失敗+修正1成功+東方向影響3成功。新独立受入67。成功native2/未保存失敗native1/pre-native失敗1/記録native0/旧成功無影響再走0。

## 診断履歴

run37189414997は親routeの末尾1byteを誤って加えたbindingで1検査だけ失敗、native0。原本11998byteへ修正し当該1検査だけ通過。run37189493180は13画面36入力/native1、方向階段8,8を南入力して1階8,9へ進み安全停止。Save93/RTC全保持。固定ROMのbehavior0x6Cとsource-lockのpret/pokefirered commit c75f352304d529f6ba92d4f74b9cf8b5c3810788にあるIsDirectionalStairWarpMetatileBehaviorを照合し、東入力だけへ修正。旧failure結論は保持。成功prefix0〜11を失敗原本と別に改作しない。

## 保存・表示・差分

13〜17menu0→4、18/19確認、20〜34保存中。34counter94でも途中hashと保存中文字、35最終hash/成功文言、38unlock field telemetry。ただし38画像にはcard/成功文言が残留。cold0/1のfield表示を別確認し、全画面一致とは主張しない。progress→cold差分19884/19904pixelはcard/成功文言の矩形内、cold間263pixelはNPC矩形x66..94/y19..38内。主人公・他地形は同一。全131088byteSaveRTCはcold/120frame後も一致。

全party/HP/PP/Bag/紙/所持金/受付4061/S61E/PC保持。42checksum/7062byte1772範囲、旧Save93bank57344byte保持。1階8,7の観測10でRAM ledger変化。physical2056:1→0、4001:2→0/4021:74→83/4022:1→0と今回RAMのruntime ownerは未解明。前回受付の4001/4061 ownerと混同しない。過去Save92/91/89/87等の未解明ownerも保持。

## 次

[local2への新13歩と紙引渡しowner](../content/modernization/pr16_story_save94_next_route.json)。2階11,8東から4,8へ、南向きに4,9のlocal2へ通常会話。バッジ2083と紙274を確認後、removeitem274x1/setflag4382の実命令がある。未実行の引渡しはまだ受入しない。NPCのruntime位置は初期座標と別に扱い、未知障害・会話・戦闘で縮小停止。505道路レンジャーはさらに後続。

Save94 artifact11298740300のstory-fast.srm（131088bytes/SHA256 a306d040197e63d32a3a3d3380041af66c05ec17b8dbe52225320dad4046bb4f）だけから再開。西6南3/旋回2、階段8,8の東入力で2階6/1・11,8東へ到着。追加自動歩行なし。通常Save94/独立Continueを完了。次は新13歩でlocal2の北隣4,8へ、南向き会話で紙274一個の引渡しと4382setを最初の新境界として保存。505道路レンジャーは後続。受付/階段/旧成功を再走しない。23114円/4061=1/バッジ2/紙274一個/4383/未引渡し4382/未完4380/全party600byte/HP277/294/PP3,9,8,2保持。新RAM差分は1階8,7の観測10、physical2056:1→0、4001:2→0/4021:74→83/4022:1→0はowner未解明。過去Save93受付4001/4061のowner解決とは別。全41画面70+cold13入力、成功native2/初回未保存失敗native1/初回pre-native失敗1。controller最終41case、実行43=初回38成功1失敗+修正1成功+東方向影響3成功。新受入67、旧成功無影響再走0。20〜34保存中/34counter94途中hash、35成功文言/最終hash→38unlock。38画像には成功overlay残留、coldのfieldを別確認。cold263pixel差分はNPC矩形66,19〜94,38、全画面一致は未主張。全SaveRTC一致/S61E/PC保持。紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。
