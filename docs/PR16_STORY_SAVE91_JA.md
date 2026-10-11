# ミルジム退出・Save91限定受入

`PASS_GYM_EXIT_SAVE91_SCOPED`。Save90/9,11南から新10歩・旋回2・warp1。12で退出warp6,18、13でミルシティ3/2の20,11南へ到着。直後の通常Save91/独立Continueを受入。leader417勝利・バッジ2・TM37・紙274一個・23164円を保持。紙引渡しは未実行。

source `50150f7670e8bd7095066d6ff302d3da7bd40b75` / run `37185860784` / job `111387490615`全8step成功。artifact `11295979806` / 196440bytes / SHA256 `29aa44b30e138cdb9706f4023e415913d04eb29cf2ec537ae7ba2de0816152ed`。55member/39画面/69+cold13入力。初回33controller成功後、親route参照copyの末尾LF1byteをexact hashが拒否しnative0/入力0。repo原本17553byteに訂正、新binding2検査成功。原33を再走せず継承し新受入63。native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

14〜18menu0→4、19/20確認、21〜29部分hash/保存中。30/31は最終hashでも保存中文字/counter90。32counter91/台詞空欄、33〜35成功文言、36field。全131088byteSaveRTC一致。hashやcounterだけを保存完了としない。町NPC/花animationでfield/cold全pixelは異なる。主人公とジム背景の9216pixelは全一致。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/23164円/PC/今回RAM保持。町header→type3 map-script0x08214ee8の9命令を固定ROMで照合し、4372〜4378 clearとflyflag/endを同定。今回S61E payload258:87→7/259:164→160は4372/4374/4378clearだけ。42checksum、全Save7185byte/1833範囲、旧Save90bank57344byte保持。

physical2056:1→0（入場Save76は0→1）、legacy4021:39→49・40aa:2049→0・40ac:16→0・40ad:4→0・40ae:15→80を台帳化。これらruntime ownerと過去Save89RAM14/Save87raw41/RAM/補助変数ownerは未解明。今回保持やジムreset owner同定を他のowner解決へ昇格しない。

## 次

[博物館入口の新23歩](../content/modernization/pr16_story_save91_next_route.json)。南11東3南4西4北1で町19,25入口。最初の博物館1階map6/0へ到着直後保存。静的warp14,9/自動北1歩14,8はnative未確認。博物館2階local2への紙引渡しは別区間。

Save91 artifact11295979806のstory-fast.srm（131088bytes/SHA256 e61573b32ff8f319ee36fe0d4e29981a4d213ea764078bd290bf92fed622278b）だけから再開。ジム退出の新10歩/旋回2/warp1を完了、ミルシティ3/2・20,11南。町type3map-scriptが4372〜4378をclearし今回4372/4374/4378が1→0。バッジ2/leader417勝利/TM37/紙274一個/23164円、全party600byte/HP277/294/PP3,9,8,2・今回RAM保持。次は南11東3南4西4北1の新23歩で博物館入口19,25へ。最初のmap6/0到着後だけ保存。静的target14,9/自動北1歩14,8はnative未確認。2階local2への紙引渡しは別区間で未完。旧switch/leader/勝利trainer再走0、未知NPC/境界/戦闘は縮小停止。全39画面/69+cold13入力/native2/原33controller継承+新binding2/新受入63。初回LF参照hash誤差はnative前失敗/入力0を保持。21〜29部分hash、30/31最終hashでも保存中文字/counter90、32counter91空欄→33成功文言→36field。全SaveRTC一致。NPC/花animationで全pixel異なるが主人公/ジム背景9216pixel一致。physical2056clearと4021/40aa/40ac/40ad/40aeの5vars、過去Save89RAM14/Save87raw41/RAM等runtime owner未解明。紙引渡し/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備/Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
