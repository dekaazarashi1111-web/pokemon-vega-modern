# NPC北迂回の新13歩・野生オタクン1勝・Save66限定受入

`PASS_MANSION_NORTH_DETOUR_WILD_SAVE66_SCOPED`。Save65からNPC25,6を北迂回、新13歩/転換5。上階25,12南でオタクン♂Lv10に新1勝、通常保存・独立Continue。穴・紙は未到達。

source `0c826eac9f4385d5187a2e14a1825c5960ba1770` / run `37162621003` / job `111319019754`全8step成功。artifact `11288387069` / 163102bytes / SHA256 `6318e2e6100c3cb116b01359ea206bf0cc7f683e9d1140977b41d24a6404e3ed`。70member/55画面/97+cold13入力。新controller27case/新受入55case。native2/record0/旧受入再走0/ROM変更0。

## 新歩行・野生戦

0〜18でNPC北迂回から新13歩/方向転換5。19暗転、20導入、21オタクン♂Lv10を拡大画面で確認。24ドラゴンクロー選択、25使用、26撃破、27通常field。選択1と実PP15→14を別確認、つばめがえし2は温存。保守的3PP/コマンド予約を実消費数として扱わない。

## 保存完了判定

28〜32menu0→4、33確認/34上書き、35〜47保存中。46のFlash hashが最終値でも保存画面は途中、47counter66でhash再変化、48〜51成功文言、52field。hash一致やcounterだけで完了にしない。progress27/52/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存境界

party600byteのoffset52だけ15→14、残り599byte/HP288/294/ミュウツー全HP/PP/EXP/持物/Bag/19104円/RP0/全flags/PC/S61E payload/旧Save65bank57344byte保持。aux4021:111→124だけ、runtime owner未解明。RAM台帳不変、42checksum/6860byte1673範囲。Flash未使用/がくしゅうそうち未装備。

[次の静的15歩](../content/modernization/pr16_story_save66_evidence/next-route.json)は25,12→25,16→31,16→穴31,21。穴・下階着地点・南東階段・紙側接続は未受入。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。一般CI不一致/action_requiredを全成功にしない。

次: Save66 artifact11288387069のstory-fast.srm（131088bytes/SHA256 5c415ce0cac66346d10309f6ec7b783fade9cdfb5902a5bf2c19845c930d50a5）だけから再開。NPC25,6を北迂回する新13歩/転換5、上階map1/60・25,12南でオタクン♂Lv10に野生1勝。ドラゴンクロー1選択/実PP15→14、通常Save66/独立Continue。HP288/294・PP14,10,15,2でつばめがえし2は温存、party残り599byte/Bag/19104円/RP0/badge1/story4071=9/4072=1/全flags/PC保持。次は保存済経路の未通過15歩:25,12→25,16→31,16→穴31,21。最初の新event/戦闘/不通境界で通常保存。穴→入口31,22/南東階段30,29→上階33,29→紙側16,27は未実測。選択コマンドと実PPを分け、通常技のみ/host補充なし。27新controller/55新受入、97+cold13入力55画面70member/native2/旧受入再走0。46Flash最終hash一致でも保存中、47counter66で再変化、48成功→52field。全SaveRTC/field画面同一。aux4021:111→124のruntime owner未解明、RAM台帳不変。旧offset41/2056/aux/40acの未解明は保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、回復再走/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
