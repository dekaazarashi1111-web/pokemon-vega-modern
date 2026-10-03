# 上階の野生バーニン1勝・Save64限定受入

`PASS_MANSION_UPPER_WILD_SAVE64_SCOPED`。Save63から上階を新14歩・北/西への転換2、26,6西でバーニン♂Lv11と遭遇。つばめがえし1回で新1勝、通常保存・独立Continue。trainer戦0、穴と像の紙は未到達。

source `22b20697f6c99fad2884c32874138b65ab42e8c5` / run `37161289889` / job `111315087287`全8step成功。artifact `11286858775` / 165037bytes / SHA256 `317a4664070804c7a70ce265418401c08ba67e282f47ddf208cece07cd977187`。69member/54画面/95+cold13入力。新controller27case、53新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 新野生戦と保存

0開始、1〜16で新14歩/転換2。16transition、17全暗転、18導入、19野生バーニン♂Lv11。22〜24実技cursor0→2→3、24つばめがえし、25撃破/実PP6→5、26field。勝利後はwire field=false/flags4/outcome1が残るがcallback field/lock0、通常menu・保存と独立Continueを確認。追加勝利にはしない。

27〜31menu0→4、32確認/33上書き、34〜46保存中。46counter64でも部分write、47〜50成功文言、51field。progress26/51/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存差分・次の隣接NPC

party600byte中PP55の6→5だけ、残り599byte/HP288/294・ミュウツー全HP/PP・EXP/持物・全Bag/18744円/RP0・全legacy flags・PC/S61E全payload・旧Save63bank57344byte保持。aux4021:97→111/4022:3→0のruntime ownerは未解明。全RAM台帳不変。42checksum/6899byte1681範囲。

[隣接NPC候補](../content/modernization/pr16_story_save64_evidence/next-neighbor.json): 実画面の西隣25,6にNPC。保存済map1/60 local7/script154587024のtrainerbattle155命令を照合した。runtime object IDは未捕捉。次は西向きからA1回だけで会話/戦闘を観測し、最初の新境界で保存する。残りの上階静的候補は26歩。穴31,21→入口31,22→南東階段→紙側の接続は未実測。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。一般CI既知不一致/action_requiredを成功にしない。

次: Save64 artifact11286858775のstory-fast.srm（131088bytes/SHA256 7cab241382223fc8ddbd2d659f8c29619c5b9b0ff5fd6d24e9269b4f366833d0）だけから再開。上階map1/60・26,6西。上階新14歩/転換2、バーニン♂Lv11に野生1勝、つばめがえし1選択/実PP6→5、通常Save64・独立Continue済み。HP288/294・PP15,10,15,5、party残り599byte/Bag/18744円/RP0/badge1/story4071=9/4072=1/PC保持。西隣25,6には実画面NPC。保存済map1/60 local7・script154587024はtrainerbattle155だがruntime identityは未捕捉。次は西向きのままAを1回だけ押し、新会話/新戦闘/不応答を区別して最初の境界で保存。通行を無理に3回反復しない。応答受入後は未通過26歩の静的接尾辞26,6→25,6→24,6→23,6→23,11→25,11→25,16→31,16→穴31,21が候補。穴/南東階段/紙未到達。27新controller/53新受入、95+cold13入力54画面69member/native2。46counter64部分write、47成功→51field。全SaveRTC/field画面同一。勝利残留wire fieldfalse/flags4/outcome1を未復帰や追加勝利にしない。全RAM台帳/flags保持、aux4021:97→111/4022:3→0のruntime owner未解明。旧offset41/2056/aux404d/40ac未解明保持。Flash未使用/がくしゅうそうち未装備。旧経路/野生戦/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
