# ミルジム第8ディグダ配置変更・Save86限定受入

`PASS_EIGHTH_DIGLETT_EVENT_SAVE86_SCOPED`。Save85のジム10/16・6,7南から移動も旋回もせずlocal10/6,8へ通常A。4372trueの未入力branchで4373/4377 set/remove6/11・4372 clear/add5。local10自体は残る。通常Save86/独立Continue、新戦闘0。

source `948cdf5ba094404c8c27e0464a7089aa280730ee` / run `37180080594` / job `111370697900`全8step成功。artifact `11294997639` / 144536bytes / SHA256 `c6a02d02c46e1ec2e3c5edff5f4a5dd93300809a354a9ceb8b6ccbebba4a9871`。43member/28画面/48+cold13入力。新controller31/新受入59。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始6,7南→1話しかけた台詞→2配置変更文言→3field。移動/旋回0。local10保持、右上local11/10,3が消えleader側の通路が開く見た目を確認。local6除去/local5復帰も保存flagsと限定43命令ownerで照合し、全変更object画面内とは主張しない。

4〜8menu0→4、9確認/10上書き、11〜20保存中。20で最終hashでもcounter85、21counter86でtext欄空白、22〜24成功文言、25field。今回party600byte/HP287/294・PP4,10,12,2/EXP/持物/全Bag・20664円・紙274一個・PC・physical flags/全legacy vars保持。S61E payload258:23→39/259:164→166で4373/4377 set・4372 clear、CRC確認。42checksum/7161byte1847範囲、旧Save85bank57344byte保持。

progress25/cold0/1全pixelと全SaveRTC一致、今回progress/cold RAM台帳保持。旧Save85 party raw241/341各+1と観測11RAM、aux4021/4022、過去差分のruntime ownerは未解明のまま。

## 次

[leader前13歩とlocal7の118命令17node](../content/modernization/pr16_story_save86_next_route.json)。6,7から東5/北4/西4で7,3西へ。西のleader6,3へ通常A。固定sourceのtrainer417/type1とbadge0x823 set命令を確認。原本party/技/physical remap/PP方針は次に確認する。

この13歩とleader到達・勝利は未入力。local11除去からの静的通行可能予測を、ジム攻略の受入にしない。最初の新event/戦闘後保存、未知NPC/境界は縮小停止。

Save86 artifact11294997639のstory-fast.srm（131088bytes/SHA256 d1ea60da2a4b4ea00fa6a6d70fde1c9be74b5c92fd90fc780b47737761041715）だけから再開。ミルジム10/16・6,7南。第8local10の4372true branchで4373/4377set/remove6/11・4372clear/add5、local10保持。次は東5/北4/西4の新13歩で7,3西へ、西のleader local7/6,3へ通常A。static trainer417/type1、badge0x823 setのsourceを118命令17nodeで固定。leaderの原本party/技/physical remapとPP方針は先に確認し、最初の新event/戦闘後通常保存。予期しないNPC/境界は縮小停止。leader経路/到達/勝利は未入力、ジム攻略未受入。旧switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、控えMewtwo354/354・PP10,20,15,10、Bag20664円・紙274一個/PC保持。今回party600byte/全SaveRTC/field全pixel/progressとcoldRAM/全legacyvars保持。旧Save85 raw241/341各+1・観測11RAM、aux4021:119→0・4022:4→3と過去差分runtime ownerは未解明。48+cold13入力28画面43member/native2、新controller31/新受入59。20最終hashでもcounter85/保存中→21counter86/text空白→22成功文言→25field。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
