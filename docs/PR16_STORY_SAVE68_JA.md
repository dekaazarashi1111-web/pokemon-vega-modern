# 上階穴の通常落下・Save68限定受入

`PASS_MANSION_HOLE_DESCENT_SAVE68_SCOPED`。Save67の上階31,20南から南1歩で穴31,21へ入り、入口階map1/59・31,22へ初の通常落下。通常保存・独立Continue。戦闘0、紙側の南東階段は未到達。

source `765a16442d7cbac2223e5c4913c31cd90da3b574` / run `37163733877` / job `111322303638`全8step成功。artifact `11287919858` / 109087bytes / SHA256 `443d3cb41be7f3773e9fea0ac3f33813b57b1847ccde1bd912ec3bac351156e4`。44member/29画面/47+cold13入力。新controller27/新受入53。native2/record0/旧成功再走0/ROM変更0。

## 穴・通常落下・保存

0上階31,20南、1穴31,21で落下中、2入口階31,22へ到着/こころのやかたbanner。静的warp4→warp7だけでなく、通常南入力と待機による実map移動を確認。host teleport0。

3〜7menu0→4、8確認/9上書き、10〜22保存中。21最終Flash hashに一時一致しても未完、22counter68で再変化、23〜25成功文言、26field。progress26/cold0/cold1全画面byte一致、全SaveRTC一致。到着2にはbannerがあり最終画面との同一は主張しない。

## 保存境界と次の接続

party600byte/HP288/294・PP13,10,15,2/全RAM台帳/Bag19104円/RP0/全legacy vars/PC/S61E payload/旧Save67bank57344byte保持。physical2056:0→1だけ、runtime owner未解明。42checksum/6868byte1677範囲。Flash未使用/がくしゅうそうち未装備。

[次の下階16歩](../content/modernization/pr16_story_save68_evidence/next-route.json)は31,22→26,22→26,29→南東階段30,29。上階33,29への接続と紙側16,27は未実測。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。一般CI既知不一致/action_requiredを全成功にしない。

次: Save68 artifact11287919858のstory-fast.srm（131088bytes/SHA256 f54e7eca96b2808752f7c5c3e6701cca162b569ab16394b50307717b58ec868e）だけから再開。上階31,20南→穴31,21へ通常南1歩、behavior102の初落下で入口階map1/59・31,22南に到着。通常Save68/独立Continueを限定受入、戦闘0、party600byte/HP288/294・PP13,10,15,2/全RAM台帳/Bag19104円/RP0/badge1/story4071=9/4072=1/全legacy vars/PC保持。physical2056:0→1だけruntime owner未解明。次は保存済下階未通過16歩:31,22→26,22→26,29→南東階段30,29、上階33,29の到着候補で通常保存。初の新event/戦闘/不通境界で停止。さらに上階33,29→34,29→34,31→17,31→17,27→紙側16,27は静的候補、南東階段/紙の実測は未完。27新controller/53新受入、47+cold13入力29画面44member/native2、旧成功再走0。21Flash最終hash一時一致でも保存中、22counter68で再変化、23成功→26field。全SaveRTC/最終field全pixel同一、到着2はbannerあり別画像。旧offset41/2056/aux/40acのruntime owner未解明は保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/旧成功無影響再走/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
