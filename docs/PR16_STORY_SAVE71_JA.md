# 上階南側・野生バーニンSave71限定受入

`PASS_MANSION_UPPER_SOUTH_WILD_SAVE71_SCOPED`。Save70の上階33,29東から南側の新14歩/転換2で23,31へ。野生バーニン♂Lv13に遭遇、ドラゴンクロー1回で撃破し通常保存・独立Continue。紙側は未到達。

source `deed3d77e27ed77136e4d34ffd355304ddc0953c` / run `37166304017` / job `111329784622`全8step成功。artifact `11289573274` / 154287bytes / SHA256 `661336664f67be87322885ef11e015b433664c875ffdc9dffee746dbd51a6c62`。68member/53画面/93+cold13入力。新controller29/新受入62。native2/record0/旧成功再走0/ROM変更0。

## 初遭遇・通常保存・独立Continue

0〜16上階南側新14歩/転換2。16野生導入、17一時黒画面、18〜24戦闘、22ドラゴンクロー選択、23技使用/partyPP更新、24撃破、25通常field。勝利flags4/outcome1とwire field:falseが残っても、callback/lock/画面でfield復帰を確認する。

26〜30menu0→4、31確認/32上書き、33〜45保存中。44のFlashは最終hashと同一だが未完、45は再び部分write/counter71。46〜49成功文言、50field。progress25/50/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存境界・次の未通過区間

party600byte中599byte保持、差分offset52 PP10→9だけ。HP288/294・PP9,10,15,2/Bag19416円/PC/S61E/旧Save70bank57344byte保持。legacy flag差分0、aux4021:29→43/4022:4→0のowner未解明、全RAM台帳不変。42checksum/6877byte1684範囲。

[次の未通過11歩](../content/modernization/pr16_story_save71_evidence/next-route.json)は23,31→17,31→17,27→紙側16,27。紙/像16,28のitem274・flag4383は静的ownerだけで取得未完。旧14歩/野生戦/階段を再走しない。

次: Save71 artifact11289573274のstory-fast.srm（131088bytes/SHA256 87f67074b6d470df8260e15d2bd58566f949a6297318a1e7a9ee3d9b80cbb6fd）だけから再開。上階33,29東から新14歩/転換2、23,31で野生バーニン♂Lv13をドラゴンクロー1回で撃破し通常Save71/独立Continueを限定受入。HP288/294保持・PP9,10,15,2、全party599byte/Bag19416円/PC/S61E保持、RP0/badge1/story4071=9/4072=1。legacy flag差分0、aux4021:29→43/4022:4→0のowner未解明、全RAM台帳不変。次は同map1/60・23,31西から残り未通過11歩23,31→17,31→17,27→紙側16,27。初の新event/戦闘/不通境界、または紙側到着で通常保存。紙/像16,28/item274/flag4383は静的ownerのみ、取得未完。29新controller/62新受入、93+cold13入力53画面68member/native2、旧成功再走0。44は最終hash先行一致だが保存中、45counter71でも部分write→46成功→50field。勝利残留flags4/outcome1/wire field:falseを追加勝利や未復帰にしない。全SaveRTC/field4画面全pixel一致。旧offset41/2056/aux/40acのruntime owner未解明を保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
