# 紙保持の復路9歩・通常下降Save74限定受入

`PASS_MANSION_POST_LETTER_DESCENT_SAVE74_SCOPED`。Save73の像北隣16,27南から新復路9歩/転換6で上階hole5へ進み、入口階map1/59・warp8/20,24へ通常下降。通常Save74と独立Continue。新戦闘0、紙274/flag4383保持。

source `cd43872bf7177dd63cc1b9f3ff0a74d4b7b0a1ef` / run `37168945312` / job `111337754901`全8step成功。artifact `11290343975` / 136744bytes / SHA256 `e4396b58ff042623896289fe25714a8dfde3129e9fac5a64c5931b58a4439fb7`。61member/46画面/78+cold13入力。新controller30/新受入60。native2/record0/旧成功再走0/ROM変更0。

## 実下降・通常保存

15上階20,24で落下lock、16入口階20,24へ到着。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙一個/PC/S61E/全RAM台帳を保持。physical2056:0→1、aux4021:54→62/4022:1→4のみ、runtime owner未解明。

17〜21menu0→4、22確認/23上書き。24〜38保存中、37で最終Flashに一時一致しても38に再変化、counter74も38では保存中。39〜42成功文言、43field。progress43/cold0/cold1全画面byte一致、到着16はmap名bannerあり別画面。全SaveRTC一致、42checksum/6905byte1698範囲、旧Save73bank57344byte保持。

## 次の新しい退出経路

[静的南9歩/館退出候補](../content/modernization/pr16_story_save74_evidence/next-route.json)。入口階20,24から中央廊下20,33へ進み南出口。map3/2 warp7は15,19、通常door自動南1歩なら15,20だがnative未実測。館退出/紙の使用・引渡しは未受入。最初の新戦闘/event/退出で停止・保存する。

次: Save74 artifact11290343975のstory-fast.srm（131088bytes/SHA256 34a689de13a412f4d81f396aef0ec90291050ff3334fec2b048b203f3a8bd76b）だけから再開。上階の新復路9歩/転換6とhole5→入口階warp8の通常下降を受入、現在map1/59・20,24南。紙274一個/flag4383、全party600byte・HP288/294・PP9,10,15,2、Bag19416円/PC/RAM台帳を保持。次は入口階中央廊下20,24→20,33の新南9歩と南出口behavior101/warp1→ミルシティmap3/2 warp7・15,19へ通常退出する候補。door自動南1歩なら15,20もあり得るが未観測。最初の新戦闘/event/退出境界で止め通常保存する。旧像取得/上階復路/穴下降を成功caseとして再走しない。30新controller/60新受入、78+cold13入力46画面61member/native2。37最終Flash一時一致→38counter74も保存中/再変化→39成功→43field。全SaveRTC/最終field3画像全pixel一致、到着16はbannerあり別画面。physical2056:0→1/aux4021:54→62/4022:1→4のowner未解明。館退出/紙使用・引渡しは未受入、Flash未使用/がくしゅうそうち未装備、全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
