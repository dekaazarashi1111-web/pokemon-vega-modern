# ミルジムleader417勝利・バッジ/TM37・Save87限定受入

`PASS_GYM_LEADER417_BADGE_SAVE87_SCOPED`。Save86の6,7南から東5/北4/西4の新13歩で7,3西。leaderナギナタの6体に1勝、アルネブバッジ/バッジ2個・TM37どろばくだんitem325一個・賞金2500円を通常取得。Save87/独立Continue。退出と紙引渡しは未入力。

source `9f3f1af9d38af8d98864985b98053077503dfb31` / run `37181111601` / job `111373714539`全8step成功。artifact `11294659819` / 463299bytes / SHA256 `59bf341a0c3648ca2dca77c32d56db18b2e7d9d9116c04b92f7e5522b2c7580e`。127member/112画面/216+cold13入力。新controller37/新受入65、native2/記録native0/旧受入再走0/ROM変更0。

## 実編成と測定前原本の訂正

測定前の[preparation](../content/modernization/pr16_story_save87_preparation.json)はVega残存table0x081FDFD8の3体を読んだ。現consumerではなかった。[active trainer訂正](../content/modernization/pr16_story_save87_active_trainer.json)で、現ROMの24consumer pointer→table0x09329070→trainer417/party0x09352320の6体を確認し、全画面に照合した。過去原本は改作せず、native再走もしない。

実出現順はサイホーンLv23/エビワラーLv23/モグリューLv24/アオガラスLv24/ダグトリオLv25/ファイマーLv25。tableの最後2枠と実選出順は異なる。ドラゴンクロー1/かわらわり4/じしん1、交代取消5。PP予算8選択内の6選択、実PP消費6。HP287→282→277/294、PP4,10,12,2→3,9,8,2。つばめがえし2を保持。

## 保存境界

74勝利、77/78バッジ、81賞金、83TM収納、84〜86説明、87field。88〜92menu0→4、93/94確認、95〜104部分保存。105counter87/最終hashでもtext空白、106〜108成功文言、109field/cold0/1全pixel一致。全131088byteSaveRTC一致。

party592byte保持、差分8byte=実PP3/HP1/raw41系列4。raw41/141/241/341のownerは未解明、全party8段階hashは保存byteから独立再構成。全BagはTM枠2の325一個追加のみ、所持金20664→23164円、紙274一個/PC/S61E/通常story変数を保持。physical flags158clear/659,1203,1545,1697,2083setはsourceの勝利/報酬/旧trainer265自動setへ照合。新戦闘はleader1勝だけ。

補助vars4021,4022,40AA,40AC,40AD,40AEとRAM22/43/63/85のruntime owner未解明。過去差分も解決扱いしない。42checksum、全Save7194byte/1842範囲、旧Save86bank57344byte保持。

## 次

[退出用local10新分岐](../content/modernization/pr16_story_save87_next_route.json)。東4/南4/西5で6,7、南へ通常A。4373trueの第9switchは未入力。静的47命令7nodeから4373/4377clear・4376set、local6/11復帰/local10除去を予測。旧3branchと区別し最初の新event後保存。ジム退出/博物館の封書引渡しは未受入。

Save87 artifact11294659819のstory-fast.srm（131088bytes/SHA256 9c49fdef23b321415e82bffe0b239b5acff9cb4356e7cc3aea1a9aa25027028c）だけから再開。ミルジム10/16・7,3西、leader417新1勝・バッジ2個/0x823・TM37item325一個を通常取得。HP277/294、PP3,9,8,2、所持金23164円、紙274一個保持。次は東4/南4/西5の13歩で6,7、南旋回してlocal10/6,8へ通常A。未入力4373true分岐で4373/4377clear・4376set、local6/11復帰/local10除去の退出用第9switch。最初の新event後保存。旧3branch/switch/勝利trainerの再走0、未知NPC/境界は縮小停止。退出は静的にはlocal8まで13歩と2相互作用、出口へ10歩が続くが未測定。第9switch→退出→博物館2階local2へ封書引渡し→505レンジャー。leader実6体/実技6使用を全112画面とactive table0x09329070・24consumerで照合。測定前の残存原本3体誤認はactive_trainer.jsonで訂正、原本を改作せず再走0。216+cold13入力/127member/native2、新controller37/新受入65。105counter87/最終hashでもtext空白、106成功文言、109field/cold全pixel/全SaveRTC一致。party8byte差分のうちPP3/HP1以外のraw41/141/241/341、RAM22/43/63/85と補助vars6件・旧Save85/過去差分runtime owner未解明。紙引渡し/退出/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備、Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
