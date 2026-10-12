# 館の北迂回13歩・プレッシャー野生1勝・Save61限定受入

`PASS_MANSION_NORTH_DETOUR_SAVE61_SCOPED`。Save60の14,6東から北側へ迂回し、25,6東まで新13歩。旧14,6→15,6への東不通入力は再走しない。新野生ハクタクン♂Lv9に1勝し通常保存・独立Continue。上階/有効階段/像の紙は未到達。

source `2bed90a568f9e7f650bc47739db51af97a5ab296` / run `37159098533` / job `111308580642`全8step成功。artifact `11286499716` / 171125bytes / SHA256 `b08e42f2388b32b46e6b5fef271c171eff3318940baaf97169657c2cc09e39b2`。72member/57画面/101+cold13入力。新controller27case、55新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 迂回とプレッシャーの限定観測

0〜17で14,6→14,5→15,5→16,5→16,6→24,6。向き変更4回、3で東向き後4も14,5を維持し5で15,5へ通過。近傍NPCが移動するがruntime identityや旧不通の因果を断定しない。18で25,6へ進み野生遷移、19暗転、20導入。21ハクタクン♂Lv9、22オノノクス♀Lv100/HP288/294、23プレッシャーpopupと「プレッシャーを はなっている！」。25slot0→26slot2→27slot3つばめがえしPP11、28撃破。選択は1コマンド、相手確定0、実保存PPは11→9で2消費。観測した能力表示と整合するが全技/特性一般検証には昇格しない。

29field、30〜34menu0→4、35確認/36上書き、37〜49保存中。49counter61でも部分write、50〜53成功文言、54field。progress29/54/cold0/cold1の全画面byte一致、全SaveRTCも一致。勝利残留flags4/outcome1とwire field=falseを追加戦闘や未復帰扱いしない。

## 限定差分と未完

party600bytes中slot3 PPの1byteだけ変化し残り599byte保持。HP288/294・PP15,10,15,9、ミュウツー全HP/PP、EXP/held item・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save60bank57344byte保持。42checksum、6974byte/1716範囲。aux4021=76→89、RAM台帳は観測25の技menuで変化、runtime owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明を保持。

次は25,6から未通過9歩の階段接尾辞。有効階段/上階/紙は未到達、旧20,24着地点不発も再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: Save61 artifact11286499716のstory-fast.srm（131088bytes/SHA256 4bb9bb7761d2983164e0aa48687d0dae1ed893248b312af4f9ee36dbd873a092）だけから再開。map1/59・25,6東。新北迂回13歩とハクタクン♂Lv9野生1勝を限定受入。旧14,6→15,6不通辺は再走せず、14,5→15,5→16,5→16,6で通過。つばめがえし1コマンド/実PP11→9を区別し、相手プレッシャーpopup/文言と整合。HP288/294・PP15,10,15,9、ミュウツー全HP/PP、party残り599byte/Bag/17904円/RP0/badge1/story4071=9/4072=1保持。次は保存済未通過接尾辞25,6→26,6→27,6→28,6→28,7→28,8→28,9→28,10→29,10→30,10（behavior108階段）からmap1/60warp2へ。最初の新event/戦闘/不通境界で保存。上階/紙未到達、紙ownerはmap1/60背景16,28/item274/flag4383。27新controller/55新受入、101+cold13入力57画面72member/native2。49counter61でも部分write、50成功→54field。全SaveRTC/field画面同一。RAM台帳は観測25の技menuで変化しowner未解明。旧offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。旧迂回/戦闘/保存や旧20,24着地点不発を無影響再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
