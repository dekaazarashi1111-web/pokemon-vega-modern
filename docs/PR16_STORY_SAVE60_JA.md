# 館の北廊下10歩・動的通行境界・Save60限定受入

`PASS_MANSION_DYNAMIC_EDGE_SAVE60_SCOPED`。Save59の5,7北から北1/東9の通常10歩で14,6東へ。15,6への東入力3回で移動せず、最初の未通過境界として保存・独立Continue。新戦闘0、全party600bytesとHP288/294・PP[15,10,15,11]保持。上階/有効階段/像の紙は未到達。

source `782cf85e25dc2bb3e73134af027431be9724e084` / run `37157997847` / job `111305340925`全8step成功。artifact `11286820207` / 131705bytes / SHA256 `48d6c06bd95ebead9c5dc0e7081277dfa660a3e6e869033e84b4b10c484a3670`。59member/44画面/75+cold13入力。新controller26case、51新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 通常入力・保存・動的境界

0〜11暗所10歩と北→東の向き、12〜14の東入力3回は14,6を維持。静的15,6のcollision0/elevation3/behavior8を通過保証と混同しない。右隣のNPCが画面11〜14で移動、cold0/1では東隣。保存済map1/59のlocal6初期14,4/script141180503は候補にすぎず、runtime local ID/不通因果は未同定。

15〜19通常menu0→4、20確認/21上書き、22〜36保存中。35のFlashは一時的に最終hashと一致するがcounter59/保存中文字。36counter60でも再び部分write、37〜40成功文言、41field。progress14/41とcold0/1は各core内で同一。進行41対cold1の画面差は近傍NPC211pixel、bbox[129,58,143,80]だけ。プレイヤー/床/暗所と全SaveRTCは一致するが、全field同一とは主張しない。

## 限定差分と未完

全party600bytes/HP/PP/EXP/held item・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save59bank57344byte保持。42checksum、6959byte/1713範囲。aux4021=66→76のruntime owner未解明。RAM台帳は全観測でSave59と同一。過去のRAM台帳/offset41/2056/aux/40ac未解明を解決済みにしない。

15,6に向かう同じ東入力を盲目的に再生せず、新しい通常会話または最小北迂回で動的境界を越える。最初の新event/戦闘/境界で保存。有効階段/上階/紙は未到達、旧20,24着地点不発も再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: Save60 artifact11286820207のstory-fast.srm（131088bytes/SHA256 40d65e6b41a49a59d295667ea30a88496da25c641ac8896059ed4d1fce196b0f）だけから再開。map1/59・14,6東。新10歩を限定受入、15,6への東入力3回は不通で停止。新戦闘0、全party600byte/HP288/294・PP15,10,15,11・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1/RAM台帳保持。近傍移動NPCを実画面で観測、local6初期14,4/script141180503は静的候補でruntime同定/不通因果は未確定。次はcold画面の東隣NPCへの通常A会話を有限入力で確認するか、保存済通行可床14,5→15,5→16,5→16,6へ最小北迂回して未通過接尾辞を進める。目標はbehavior108階段30,10→map1/60warp2。最初の新event/戦闘/不通境界で保存。旧14,6→15,6東3回や旧20,24着地点不発を盲目的に再走しない。上階/紙未到達、紙ownerはmap1/60背景16,28/item274/flag4383と静的照合済み。26新controller/51新受入、75+cold13入力44画面59member/native2を無影響再走0。35で最終Flash一致でもcounter59/保存中、36counter60でも部分write、37成功→41field。全SaveRTC同一、progress/cold画面は近傍NPC211pixel/bbox129,58,143,80だけ異なり全画面同一としない。旧RAM/offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
