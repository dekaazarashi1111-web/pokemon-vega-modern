# 紙保持の新南9歩・館退出Save75限定受入

`PASS_MANSION_EXIT_SAVE75_SCOPED`。Save74の入口階20,24南から新南9歩/20,33出口で追加南1入力。ミルシティmap3/2・warp7/15,19から自動南1歩で15,20に到着し通常Save75と独立Continue。新戦闘0、紙274/flag4383保持。

source `0845c4282b2ad508dd7046b6d61d6cf139a59fd7` / run `37169799589` / job `111340233315`全8step成功。artifact `11290759615` / 159269bytes / SHA256 `23c4f5700fb21060afedd06cba7a91987df309b209f34da5256f1b0f2ee67e96`。51member/36画面/63+cold13入力。新controller31/新受入63。native2/record0/旧成功再走0/ROM変更0。

## 実退出・通常保存

9入口階20,33は下向き矢印の出口field。追加南入力1回で10ミルシティ15,20南/町名banner。町に着いてからの方向入力0。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙一個/PC/S61Eを保持。physical2056:1→0、aux4021:62→71/4022:4→3/40ac:16→0。RAM台帳は7/20,31で変化。各runtime owner未解明。

11〜15menu0→4、16確認/17上書き。18〜28保存中、27/28は部分hashが同一、29counter75/最終Flashでも文言未完、30〜32成功文言、33field。全SaveRTC一致、42checksum/7003byte1728範囲、旧Save74bank57344byte保持。

町のNPC/水面animationによりprogress33/cold0/cold1の全画面は異なる。player/館外観112x89cropは全pixel一致。全画面一致へ昇格しない。

## 次の正規イベントownerを限定照合

[次の照合条件](../content/modernization/pr16_story_save75_evidence/next-route.json)。紙274/flag4383の消費・後続入口を保存済scriptから照合し、未読範囲だけ同一候補で読む。受取人や歩行先は未同定。館内/退出の無変更再走を避け、owner固定後の新しい区間へ進む。

次: Save75 artifact11290759615のstory-fast.srm（131088bytes/SHA256 6554c5f872f710b4dbef5a2db06fbf3d2b91ab3a2984008be53c7ce1ecf4ffb2）だけから再開。入口階20,24から新南9歩/出口追加南1入力で館退出、ミルシティmap3/2・15,20南への自動南1歩と通常Save75/独立Continueを受入。紙274一個/flag4383・全party600byte/HP288/294・PP9,10,15,2/Bag19416円/PC/S61E保持。次は保存済script graph/tableからitem274/flag4383のcheck/remove/clearとstory4071=9/4072=1の後続入口を限定照合し、未読consumerだけ同一候補ROMで読む。受取人/次目的地を推測せず、正規イベントownerと歩行経路を固定してからSave75以降の最初の新戦闘/event/退出境界へ進み通常保存する。旧像取得/館内/退出は再走しない。31新controller/63新受入、63+cold13入力36画面51member/native2。27/28部分hash安定→29counter75/最終Flashでも文言未完→30成功→33field。全SaveRTC一致、町のNPC/水面は画面差あり、player/館外観112x89crop全pixel一致。physical2056:1→0/aux4021:62→71/4022:4→3/40ac:16→0、RAM台帳は7/20,31で変化、owner未解明。紙使用/引渡し、全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。Flash未使用/がくしゅうそうち未装備。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
