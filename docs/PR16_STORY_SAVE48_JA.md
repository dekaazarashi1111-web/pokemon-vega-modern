# 北迂回の残68歩・南端・Save48 限定受入

`PASS_ROUTE504_NORTH_DETOUR_SAVE48_SCOPED`。504番道路11,5東から17,19南へ68歩/21方向転換。ジュネが残る右隣12,5を11,4→12,4→13,4で避け、北迂回を完走した。戦闘/eventなし。Save48/独立Continueを限定受入。南接続・回復施設・ミュウツーPP回復は未完。

source `9b901795212fb59eff1d9189fbf084f8f6a63506` / run `37140030464` / job `111252353944` 全8step成功。artifact `11279239942` / 856285bytes / SHA256 `3b21ca77524cefa2d8ee8bdc4b9e87ff2441d30e3d04fa5892fabfffa3ce623a`。全134member/118画面/224+cold13入力。18新controller成功原log継承、新34原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。

## 保存・全境界

0〜89通常移動、90〜94通常menu実cursor0→4、95保存確認、96上書き確認。97〜110部分Flash14種類、110counter48はまだ部分write。111〜114成功文言/安定Flash、115field。cold0/1は17,19南で全SaveRTC一致。42checksum/旧Save47bank57344byte/6894byte1708範囲。

party全600byte・HP/PP/EXP/Bag/15224円/全legacy flag/PC/S61E/story4071=9/4072=1・badge1不変。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・PP0。新パネル判定/残PP束縛controllerは18新試験で照合したが戦闘なしのため新判定/slot3選択のnative実証は追加0。Save47でのslot0実使用4回だけを継承し、原used0誤陰性を改作しない。

補助var4021=40→108/4022=0→3、RAM ledger18/82差のowner未解決、最終/cold `9e4f38b66578ac978b454de0a9573e854c8449d017f5fd82ea4aa4c1ffb02606` 一致。Save46party2byte/途中ledger、Save39cold差/Save44並替差のowner未解明と旧失敗履歴を保持。

地形1440cell/既存owner再採取0。69vertex候補を全通過したが、map3/23南接続はまだ未受入。保存済み72×20地形の17,19南端から南connection offset-16の想定33,0へ新規入力で続ける。想定座標を実到達へ昇格しない。

## 次checkpoint送信前の確認

AST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。

次: Save48 artifact11279239942のstory-fast.srm（3095edcc45f08ff64cabe7a07c54098ec4b82f8ed874d6e103fafe9f7a2fb02f、131088bytes）だけから再開。map3/44・17,19南/下段3・party4/RP0・15224円・badge1・story4071=9/4072=1。Save47の右隣NPCを避け、11,5→11,4→12,4→13,4から北迂回残68歩/21turnを戦闘0で完走、通常Save48と独立Continue全SaveRTC一致。全party600byte/PP/HP/Bag/所持金/legacy flags/PC/S61E不変。オノノクスPP[11,10,15,20]、ミュウツーHP314/354・全PP0で回復未完。次は保存済map3/44高さ20/南connection offset-16→map3/23を参照し、17,19から南境界を越える新通常入力だけ。想定接続先33,0は静的候補で未受入。既存map3/23読取資料の北端通路26〜33と南connection→map3/2を使い、必要な新しい高度/ownerだけ追加照合。最初の新接続/戦闘/event/未通過境界または正常回復地点で保存。通常回復のHP/PPと原画が確認できるまで回復完了としない。新パネル判定a.classify_panelを継承、selectは実PP[11,10,15,20]に束縛。今回戦闘0で新判定/slot3選択のnative実証は追加0、Save47のslot0だけ受入済。97〜110部分write、110counter48でも未完、111成功文言/安定Flash→115field。aux4021=40→108/4022=0→3、RAMledger18/82差owner未解決、最終cold一致。Save47のraw used0誤陰性、Save46party2byte、Save39cold差/Save44並替差と旧失敗を保持。224+cold13入力/118画面/18controller34受入は無影響再走0。正規全国図鑑/通常story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。一般CI既知qol_production.c不一致とfinalHEAD action_requiredは全成功にしない。
