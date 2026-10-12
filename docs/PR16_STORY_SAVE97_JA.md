# 博物館退出・Save97限定受入

`PASS_MUSEUM_EXIT_SAVE97_SCOPED`。封書引渡し後のSave96から新13歩/3旋回。14,9の赤い南矢印へ追加南入力して町3/2・19,26南へ初退出、最初のfieldで通常Save97と独立Continueを受入。

source `4c61d6e9eaf5fe7fa64e8d477017448342d9819a` / run `37193900573` / job `111411662442` 全8step成功。artifact `11300361541` / 235132bytes / SHA256 `23b0b7b2e418218aab229e6dbeca030a03571ec701422df9692418c6d3dc84d7`。61member/46画面/80+cold13入力。controller最終48case/69実行68成功1失敗、新受入79。成功native2/退出失敗native1/記録native0/ROM変更0/旧受入再走0。

## 失敗と復旧

初回controller46件中45成功、1件はoff-warp変異fixtureに正当な1歩前の座標を使った誤検査。fixtureだけ訂正し1件成功、既成功45再走0。その後nativeは親static計画の13,9で南8回でも非発火し有限停止。run37193632724/artifact11299424063、58入力24画面、通常保存0、Save96全131088byte保持。失敗は削除・成功換算しない。

固定ROMでは13,9/15,9は普通床0x08、14,9だけ0x65南矢印。warp-table登録だけでは発火しない。固定上流c75f3523のTryArrowWarpと方向predicateも確認。修正影響22検査だけ通し、未受入退出区間から回復。入力原本・旧受入sourceは不変。

記録初回run37194559112はGUIDEが旧Save96宛先だったため、protected guardが書込み前に停止。native0/旧文書書込み0/77受入case未実行。新宛先を固定し、新規宛先2検査を含め79caseを初実行。未実行hash定数も固定済み復旧JSON参照へ直し、旧guardを緩めていない。

## 保存・保持・目視

0〜16は13歩/旋回3、17で町19,26南。18〜22menu0→4、23/24確認、25〜38保存中、38counter97でも途中hash。39で成功文言/安定最終hash、43でoverlayなしclearfield。hash/counter単独の完了主張なし。

43→cold0/1は768/626pixel、cold間752pixel差。左端NPC矩形x0..15/y83..102と花animation x64..143/y137..159だけ。全画面一致とはしない。SaveRTC全131088byte/PC/S61E/旧Save96bank57344byte保持。差分7043byte1752範囲、42checksum。

全party600byte/HP277/294/PP3,9,8,2/23114円/紙274=0/4382/4383/4061=1/バッジ2保持。4380未完。RAM台帳は観測5旋回で変化し、その後/cold保持。physical2056:1→0、aux4021:109→122/4022:1→4のruntime owner未解明。過去ownerを解決済みにしない。Save96のfresh import失敗・154moduleと有限1500修復を保持し、旧72受入の再走0。

## 次の境界

[町北35歩とnorth connection](../content/modernization/pr16_story_save97_next_route.json)。町28,0から北入力、map3/23・28,39が静的候補。座標/自動歩行はnative未確認。最初のfieldだけ保存。Ranger local9/18,27は後続。静的scriptは4382を条件に4072=2/4352clear/町warpだが、会話もstory進行もまだ未受入。

warp-tableの座標だけで発火可能と判断しない。毎回固定ROMのtile behaviorと必要方向を確認し、通常着地/矢印/方向階段/境界connectionを区別する。実画面の出口は裏付け。無入力自動歩行は実測まで未確認。

Save97 artifact11300361541のstory-fast.srm（131088bytes/SHA256 4871ba79e718ea8dc8bc701394846ce1b393cd41a5961564ed4d670437a52139）だけから再開。博物館退出後の町3/2・19,26南。新13歩/3旋回、14,9の0x65南矢印で退出、町warp19,25から自動南1歩を実測し通常Save97/独立Continue受入。次は保存next-routeの町北端28,0まで35歩、通常北入力でmap3/23へのconnectionを越え最初のfieldだけ保存。Ranger local9/18,27はさらに後続、4382setを条件に4072=2/4352clear/町warpへ進む静的ownerを保存したが未実行。封書会話/受付/階段/退出成功区間を再走しない。紙274=0/4382/4383/4380未完/4061=1/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。観測5でRAM台帳変更、physical2056clear、aux4021:109→122/4022:1→4と過去owner未解明。46画面80+cold13入力、38counter97でも保存中/途中hash→39成功文言/安定最終hash→43clearfield。cold差分752pixelは左端NPC/花animation内、全SaveRTC/PC/S61E/旧bank保持。controller最終48case/69実行68成功1失敗、新受入79。成功native2/退出失敗native1/記録native0。最初のfixture失敗と13,9通常床非発火の失敗原本は保持。Save96のimport連鎖154module/入口上限1500修復は不変、受入済み72再走0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。warp-tableの座標だけで発火可能と判断しない。毎回固定ROMのtile behaviorと必要方向を確認し、通常着地/矢印/方向階段/境界connectionを区別する。実画面の出口は裏付け。無入力自動歩行は実測まで未確認。
