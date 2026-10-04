# 南隣NPC迂回・南東階段Save70限定受入

`PASS_MANSION_SOUTHEAST_STAIR_SAVE70_SCOPED`。Save69の入口階26,28南から、南隣NPCを避ける新9歩/転換5で南東階段30,29へ。通常東入力で上階33,29東向きへ初到着し、通常保存・独立Continue。戦闘0、紙側は未到達。

source `6f4a3adcfe115f28851bd9f9b9dd2209a37dc36d` / run `37165369734` / job `111327062964`全8step成功。artifact `11288833014` / 138756bytes / SHA256 `5a1e40adc7cff652e1a1ee03d6f4ea58615ce732609c6a217cf7e8ca3970d4ea`。60member/45画面/77+cold13入力。新controller27/新受入59。native2/record0/旧成功再走0/ROM変更0。

## 迂回・階段・通常保存

0〜14南隣NPCを西〜南側から避ける新9歩/転換5。26,28→25,28→25,30→27,30→27,29→階段30,29。通常東8frame+待機で15上階33,29へ。到着bannerあり、host teleport0。

16〜20menu0→4、21確認/22上書き、23〜37保存中。37counter70でも部分writeで未完、38〜41成功文言、42field。progress42/cold0/cold1全画面byte一致、全SaveRTC一致。到着15はbannerがあるため最終画面とは同一ではない。

## 保存境界・次の紙側

全party600byte/HP288/294・PP10,10,15,2/Bag19416円/PC/S61E/旧Save69bank57344byte保持。physical2056:1→0、aux4021:20→29/4022:0→4、RAM台帳22変化のownerは未解明。42checksum/6851byte1668範囲。

[次の未通過25歩](../content/modernization/pr16_story_save70_evidence/next-route.json)は上階33,29→34,29→34,31→17,31→17,27→紙側16,27。紙/像16,28のitem274・flag4383は静的ownerだけで、取得未完。

次: Save70 artifact11288833014のstory-fast.srm（131088bytes/SHA256 94fd92a46700adcf4b5b1f8ddb811ad54ee080f488e60e844a08fe475139411a）だけから再開。下階26,28の南隣NPCを迂回する新9歩/転換5で南東階段30,29へ。通常東8frame+待機で上階map1/60・33,29東へ初到着、通常Save70/独立Continueを限定受入。戦闘0、全party600byte/HP288/294・PP10,10,15,2/Bag19416円/PC/S61E保持、RP0/badge1/story4071=9/4072=1。physical2056:1→0、aux4021:20→29/4022:0→4、RAM台帳22変化owner未解明。次は上階南側の未通過25歩33,29→34,29→34,31→17,31→17,27→紙側16,27。初の新event/戦闘/不通境界、または紙側到着で通常保存。紙・像16,28/item274/flag4383は静的ownerのみ、取得未完。27新controller/59新受入、77+cold13入力45画面60member/native2、旧成功再走0。37counter70でも部分write/保存中、38成功→42field。全SaveRTC/最終field全pixel一致、到着15のみbannerあり。旧offset41/2056/aux/40acのruntime owner未解明を保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
