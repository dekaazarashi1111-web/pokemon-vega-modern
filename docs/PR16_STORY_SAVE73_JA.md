# 像のだいじなふうしょ取得Save73限定受入

`PASS_MANSION_STATUE_LETTER_SAVE73_SCOPED`。Save72の上階16,27西から南へ向き、ミュウツーの像を初めて調べた。画面で「だいじなふうしょ」を大切なものポケットへ入れ、通常保存・独立Continue。新戦闘/歩行0。

source `b8f41b6a86eb0f818500efcd371865416d47dd64` / run `37167891735` / job `111334594492`全8step成功。artifact `11290362029` / 121392bytes / SHA256 `4cfa44f350645f267ca6ab9834cdace7299d6761bac35d0aea23d8823ba53313`。47member/32画面/53+cold13入力。新controller32/新受入62。native2/record0/旧成功再走0/ROM変更0。

## 取得・通常保存

0西→1南、2像を調べた、3だいじなふうしょ取得表示、4解錠。key_items slot4 (0,0)→(274,1)、全他Bag/19416円保持。像script149012422のadditem274/setflag4383と、S61E payload259:32→160/CRCを独立照合。全legacy flags/vars/RAM台帳と全party600byte/HP288/294・PP9,10,15,2/PCを保持。

5〜9menu0→4、10確認/11上書き。12〜25保存中、24で最終Flashに一時一致しても25に再変化、counter73も25では保存中。26〜28成功文言、29field。progress1/4/29/cold0/cold1全画面byte一致、全SaveRTC一致。42checksum/6849byte1672範囲、旧Save72bank57344byte保持。

## 次の新しい復路

[静的9歩hole下降候補](../content/modernization/pr16_story_save73_evidence/next-route.json)。16,27から上階20,24のbehavior102/warp5へ行き、下階map1/59のwarp8/20,24へ降りる候補。下階で不発だった着地点へ同じ入力を繰り返す話ではない。実下降/館退出/紙使用・引渡しは未受入。最初の新戦闘/event/下降で停止・保存する。

次: Save73 artifact11290362029のstory-fast.srm（131088bytes/SHA256 1790277ae4ff1fbb3242a3e58578dfbc66aa98b9e274e42d9811ffb438eb22bb）だけから再開。上階map1/60・16,27南。通常南向き1回→像を初めて調べ、実画面でだいじなふうしょ取得、key_items slot4にitem274が0→1、expanded4383が0→1。通常Save73/独立Continueを限定受入。新戦闘/歩行0、全party600byte・HP288/294・PP9,10,15,2/他Bag・19416円/PC保持、legacy全flags/vars/RAM台帳保持、S61E payload259が32→160だけでCRC正常。次は紙取得後の新復路9歩、16,27→17,27→17,26→17,25→18,25→18,24→18,23→19,23→20,23→20,24の上階hole behavior102/warp5から下階map1/59・warp8/20,24へ通常南入力で降りる候補。最初の新戦闘/event/下降境界で保存する。下階warp8は旧不発着地点、上階holeとは別。像取得や旧routeを成功caseとして再走しない。32新controller/62新受入、53+cold13入力32画面47member/native2、旧成功再走0。24最終Flash一時一致→25counter73も保存中→26成功→29field。全SaveRTC/field5画像全pixel一致。紙の使用/引渡し・hole下降/館退出は未受入。旧offset41/2056/aux/40acのruntime owner未解明、Flash未使用/がくしゅうそうち未装備、全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
