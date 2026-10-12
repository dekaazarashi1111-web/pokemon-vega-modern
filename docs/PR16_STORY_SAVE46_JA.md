# 下段西通路・Save46 限定受入

`PASS_ROUTE504_LOWER_WEST_SAVE46_SCOPED`。504番道路26,12南から3,12西へ、下段を27歩/5方向転換・戦闘0で通常通過。通常Save46/独立Continueを限定受入。回復施設到達・ミュウツーPP回復・オノノクス実技UIは未完。

source `78a91fbec8fa40863524b49e501ed204558a5031` / run `37137181984` / job `111243980063` 全8step成功。artifact `11278684880` / 453767bytes / SHA256 `f5fe71c1e324674f8adc69d94c39d8462da87dce46db41106074d0e64e1eddb1`。全75member/60画面/109+cold13入力。12新controller成功原log継承、新36原本受入拒否試験のみ。native2/record0/旧受入再走0/ROM変更0。

先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・全PP0。party600byte中、141=7→8/241=105→106の2byteだけ通常歩行観測7で変化。なつき度候補だがowner未解決で、全party不変/自然成長受入とはしない。598byteは不変、HP/PP/EXP等に差なし。Bag/14264円/費用0・道具消費0。

0〜32通常下段西進、33〜37menu実cursor0→4。40〜52部分Flash13観測/12種類。51/52同hashでも最終値ではなく書込み中。53counter46/最終Flash/文言遷移、54〜56成功文言、57field。cold0/1は3,12西で一致。全60原画を目視。

legacy flags/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=123→22/4022=4→1 owner未解明。42checksum/旧Save45bank57344byte/6892byte1708範囲/cold全SaveRTC一致。RAM ledgerは観測13で変化、最終/cold `d522ec8b2bf900af66d25b3c57b30c06498b37b8db79a057f83384303bc66cac` 一致。party2byte差/途中ledgerのowner未解決を明示し、Save39旧cold差/Save44並替差のowner未解明も保持。

保存済504地形1440cell/既存owner再採取0。全28vertexのelevation3だけを通常通過。既受入共通PPラベル/実cursor classifierはそのまま継承し、無影響20試験再走0。実オノノクス技UIは未観測のまま。

## 次checkpoint送信前の確認

AST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/save SHA/counter/bank/全member数、環境変数は新counter ORIGINAL/ROMと親counter INPUTの集合を照合。送信tree/staged一覧と旧正本の交差0、専用宛先/private/source guard、全成功行と正確なunittest終端を維持。記録器だけの失敗なら成功試験/nativeを再走しない。

次: Save46 artifact11278684880のstory-fast.srm（d4a2e1f06ecbb1dee1bd54bda6962c1993b51711a09607954fe7b67d1c568e47、131088bytes）だけから再開。map3/44・3,12西/下段elevation3・party4/RP0・14264円・badge1・story4071=9/4072=1。26,12から下段西通路27歩/5方向転換/戦闘0で到達。先頭オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP314/354・PP0、回復施設/回復未完。party全600byteのうち141=7→8/241=105→106の2byteだけ通常歩行観測7で変化、HP/PP/EXP等598byte不変。なつき度候補だがowner未解決、自然成長受入とはしない。RAM ledgerは観測13で変わり最終/cold一致、owner未解決。次は3,12から北3,11→3,10→3,9→2,9→2,5→6,5→6,6→10,6方面の未通過下段通路を有限候補にする。静的地形だけでは南端17,19へ直進できず北迂回候補、実到達ではない。南map3/23→3/2は接続候補で回復施設未同定。最初の新戦闘/event/未通過境界で通常Save、PPラベル/実cursorの既受入classifierを継承し初のオノノクス実技UIを原画像/残PPと照合。旧ミュウツー技名依存/PP0選択loop/host補充/ROM変更/故意の全滅なし。109+cold13入力・60画面・12controller36受入を無影響再走しない。40〜52部分Flash、51/52同hashも書込み中、53counter46/最終Flash→54成功文言→57field。全SaveRTC/cold一致、補助var4021=123→22/4022=4→1 owner未解明。Save39旧差/Save44並替差と旧失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。一般CIqol_production.c source不一致とfinalHEAD action_requiredを過大主張せず保持。全story/一般CI全成功/製品release未完、cleanROM二重生成/BPS固定/merge/release/baseline切替は別途判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
