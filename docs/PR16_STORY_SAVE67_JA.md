# 上階の穴手前まで新14歩・野生オタクン1勝・Save67限定受入

`PASS_MANSION_UPPER_HOLE_APPROACH_SAVE67_SCOPED`。Save66から上階の未通過14歩/転換2。31,20南の穴手前でオタクン♂Lv9に新1勝、通常保存・独立Continue。穴へあと1歩、落下と紙は未受入。

source `f184a49f8a736ed83f5b29d208dfb72db9e50e4b` / run `37163246411` / job `111320883103`全8step成功。artifact `11288432849` / 157034bytes / SHA256 `12d05e3effff6ae123a73e4cc60c19e342ae454ea21be51a4a9e1df53c2bbb84`。68member/53画面/93+cold13入力。新controller27/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 新経路・戦闘・保存

0〜16で上階25,12→25,16→31,16→31,20、14歩/転換2。17暗転、18導入、19オタクン♂Lv9、22ドラゴンクロー選択、23使用、24撃破、25field。PP14→13、つばめがえし2温存。

26〜30menu0→4、31確認/32上書き、33〜45保存中。45counter67でも部分write、46〜49成功文言、50field。progress25/50/cold0/cold1全画面byte一致、全SaveRTC一致。

## 変化したbyteと保持境界

party offset41/141/241/341は観測4から各+1、runtime owner未解明。保存byteから中間party hashを独立再構成し、23でPP52:14→13だけを追加。合計5byte差分、残595byte/HP288/294/ミュウツーHP・PP/EXP/持物保持。RAM台帳は観測3で変化、owner未解明。Bag/19104円/RP0/全flags/PC/S61E/旧Save66bank57344byte保持、aux4021:124→10だけ。42checksum/6866byte1681範囲。

[次の未通過1歩](../content/modernization/pr16_story_save67_evidence/next-route.json)は31,20→穴31,21。落下先候補は入口階31,22、その先の南東階段/紙側は未実測。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未受入。一般CI既知不一致/action_requiredを成功にしない。

次: Save67 artifact11288432849のstory-fast.srm（131088bytes/SHA256 a4543c8c8d1b47668159adc71a0aff60f2bcf58ac91139d50d6eb201bd9677f5）だけから再開。上階接尾辞新14歩/転換2、map1/60・31,20南でオタクン♂Lv9に新野生1勝。ドラゴンクロー1選択/実PP14→13、通常Save67/独立Continue、HP288/294・PP13,10,15,2。次は南へ穴31,21まで未通過1歩、落下が起きれば入口階map1/59・31,22で保存。初の新event/戦闘/不通境界で通常保存し、穴下階接続を判定。穴→南東階段30,29→上階33,29→紙側16,27は未実測。歩行中観測4で4体のoffset41/141/241/341が+1、PP1と合わせ5byte変化、残595byte保持。offset41と観測3のRAM台帳変化のruntime owner未解明。Bag/19104円/RP0/badge1/story4071=9/4072=1/全flags/PC保持、aux4021:124→10だけowner未解明。27新controller/56新受入、93+cold13入力53画面68member/native2。45counter67部分write→46成功→50field、全SaveRTC/field全pixel同一。Flash未使用/がくしゅうそうち未装備、つばめがえし2温存。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。旧成功無影響再走/host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
