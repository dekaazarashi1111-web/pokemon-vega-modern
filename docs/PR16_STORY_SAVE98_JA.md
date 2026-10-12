# 町北connection・Save98限定受入

`PASS_TOWN_NORTH_CONNECTION_SAVE98_SCOPED`。Save97から町の新35歩/6旋回、北端28,0で通常北入力、505番道路3/23・28,39北の最初fieldでSave98/独立Continue。

source `9b85267460cd408236d11e36f0926c40910ee418` / run `37195535335` / job `111416503730` 全8step成功。artifact `11300996343` / 349489bytes / SHA256 `cec6d1ff249b110924b24ff9e1130b199752bd84b509e00f5b65cdd27cd919f7`。84member/69画面/128+cold13入力。controller最終46case/59実行成功、新受入79。成功native2/失敗native1/preflight失敗1/記録native0/旧受入再走0。

## 境界と保存

固定ROMの両側behavior0x21=SAND、衝突0、相互direction2/1、offset0。warp/矢印/方向階段ではない。観測41が北端画面、42で505番道路へ通常connection。自動追加入力なし。43〜47menu0→4、48/49確認、50〜61保存中。62counter98/最終hashでも文言は空白、63成功文言、66clearfield。

66→cold0/1は128pixel差で雪粒子6矩形だけ。cold0/1間は全pixel一致。全SaveRTC131088byte/PC/S61E/旧Save97bank57344byte保持。全save差分7074byte1780範囲/42checksum。

## 歩行ownerの限定解決

[固定ROM証拠](../content/modernization/pr16_story_save98_walk_owner.json)。0x806cf40は4021を+1&127、0時に6体へevent5/AdjustFriendship。0x806cf90は4022を+1 mod5。0x8042db8はfield32のfriendshipを読み書きし、Get/Set handler0x803f74a/0x803fea4はsubstruct0+9、この候補の順序固定substruct0=mon+32なのでraw41。固定上流のVAR_HAPPINESS_STEP_COUNTER/VAR_POISON_STEP_COUNTERと一致。

Save97のcounter122から6歩目（観測8）でraw41/141/241が48→49/13→14/111→112。通常保存の600byte差も同じ3byteだけ、597byte保持。総36歩で4021=(122+36)%128=30、4022=(4+36)%5=0。HP/PP/EXP/持物保持。4体目raw341=65保持。共通機構はsourceと固定ROMとsave算術で照合したが、個別乱数分岐のPC traceは未採取。過去原本を書き換えず、同fieldの意味だけを後続証拠として参照する。過去全実行を再traceした主張はしない。RAM観測42/physical2056等の別ownerは未解明。

## 失敗履歴

run37195233466/job111415610355は初回42controller成功後、6歩目のparty hash guardでnative停止。artifact11301280087、9画面28入力、通常save0、Save97全byte保持。診断600byteの上記3byteだけのpreimage SHAが一致し、位置/位相限定で復旧した。

run37195440238/job111416217704は影響16controller成功後、診断bytearrayをbytes-only identityへ渡してpre-native停止。artifact11301235609、native0。identity guardは緩めずbytesへ確定、新契約1caseだけ検査。これらを成功へ換算しない。

## 次

[61歩の静的候補](../content/modernization/pr16_story_save98_next_route.json)。未戦闘pairの視界過大近似を避け、既勝利1054/1055は再戦しない。12歩目32,31から草地がある。Ranger local9はmovement2/range2で動く。未知event/野生戦で縮小停止し、会話は実object/画面確認後の別区間。高度0/behavior42の段差もpreflightする。現happiness30で次周期まで98歩。

Save98 artifact11300996343のstory-fast.srm（131088bytes/SHA256 af8190f911ef0e182b22860531c8d0f1a160a57556600a16044edcfca8553cec）だけから再開。505番道路3/23・28,39北。町北35歩/6旋回/通常北connection1歩、通常Save98/独立Continueを限定受入。次はRangerの静的初期位置18,27へ向かう61歩候補。未戦闘pair1113/physical1282は未勝利、local3/8の移動範囲と全方向視界過大近似を避ける。1054/1055のphysical1406/1407は勝利済み。最初の草32,31は12歩目、未知wild/trainer/NPC eventで縮小停止。Rangerはmovement2/range2で動くため、18,28での北Aを盲目的に送らず実object/画面を確認する。会話は後続。段差32,14/22,20はbehavior42/高度0で別途preflight。町/博物館/封書/受付の成功区間再走なし。HP277/294/PP3,9,8,2/ミュウツー全HP/PP/23114円/4061/紙274=0/4382/4383/バッジ2/PC/S61E保持。party600byteの597保持、raw41/141/241各+1を通常saveで確認。固定ROMの歩行friendship event5/field32→raw41と4021mod128/4022mod5を解決、122+36→30、4+36→0。個々の乱数branchのPC trace未採取。過去offset41/歩数変数の原本は保持し本証拠へ参照、全過去実行を再traceしたとしない。RAM観測42とphysical2056等は別の未解明。現counter30、次friendship周期まで98歩。69画面128+cold13入力、62counter98/最終hash/空白→63成功文言→66clearfield。progress/cold雪6粒128pixel差、cold間全pixel一致。初回partyguard失敗1/native1/Save97保持とpreflight型失敗1/native0を保存。controller最終46/59実行成功、新受入79、成功native2/失敗native1/記録native0/旧成功再走0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。warp-tableの座標だけで発火可能と判断しない。毎回固定ROMのtile behaviorと必要方向を確認し、通常着地/矢印/方向階段/境界connectionを区別する。実画面の出口は裏付け。無入力自動歩行は実測まで未確認。
