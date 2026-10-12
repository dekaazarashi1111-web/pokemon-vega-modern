# 504上段西進・trainer114・Save43 限定受入

`PASS_ROUTE504_UPPER_TRAINER114_SAVE43_SCOPED`。Save42橋上47,13から西上段39,12へ進み、やまおとこのショウダイ（trainer114）へ通常勝利。イシズマイLv10/ダンゴロLv11/ワンリキーLv13/コジオLv12の4体。通常Save43/独立Continueを限定受入。38,12以西と26,11下り階段は未到達。

source `7bccc0c52b4232e8c4f98a81e5ed86ff73c97c57` / run `37133664958` / job `111233658951` 全8step成功。artifact `11277619007` / 543573bytes / SHA256 `2a595f712c4779e6af3b921ef4ea4dae40d1296c1ede9d32e65bb5400b7c9af3`。全105member/90画面/170+cold13入力。16controller成功logを継承し、新34原本受入/拒否試験だけを実行。native2/record0/旧受入再走0/ROM変更0。

実技cursor20/25/32/41/48ではどうだん5回、56でサイコブレイク1回。29/45/52の交代拒否3回。がんじょうを最初の2体で、ダンゴロのオレンのみを画像確認。主力party全600byte差分はoffset52:1→0/53:5→0/86:64→58だけ。HP320→315→314/354、全PP[0,0,0,0]。保存親から全8中間partyを独立再構成。通常報酬468円で13796→14264、physicalflag1394=trainer114だけ追加。保存map local3 script154581891から未知ownerのみ照合する。

Bag/HM05/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=96→104/4022=1→0はruntime owner未解明。42sector checksum/旧Save42bank57344byte/6881byte1710範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。RAM ledger全観測を固定し、進行最終/cold `7d8ac5c85ad718b9f0dd16de19bc3020c5ed2c448451bc32d0d6efd70f3dbaf3` は一致。Save39旧差owner未解明は保持。

64〜68通常menu実cursor0→4。71〜82部分write12状態、83counter43/安定全Flashだが文言は空白、84〜86成功文言、87field。cold0/1は39,12西。保存完了をcounter単独や途中hashだけで主張しない。全90画面を目視。

## 次checkpoint送信前の確認

新counterのPython AST、measure/accept import、CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を大小文字別に照合。受入試験の新counter ORIGINAL/ROMと親counter INPUTのenv集合をrecord側と比較。親artifact/run/source/全save SHA/counter/bank世代/manifest件数を原本で確認。送信treeと最終staged一覧を明示し旧正本との交差0を確認。専用宛先/private/source guardを維持。unittestはreturncode・全成功行・正確な終端で判定し、試験名skippedへのsubstring判定を禁止。記録器だけが失敗した場合は成功原logを継承し再試験しない。旧Save42の2回の記録失敗と30成功試験回収は旧正本のまま保全。

次: Save43 artifact11277619007のstory-fast.srm（80d9c9387937173a62283f1164cb6ff035ebd39eaa38f78a779da92691ae788f、131088bytes）だけから再開。map3/44・39,12西/上段elevation4・party4/RP0・14264円・badge1・story4071=9/4072=1。主力HP314/354、全PP[0,0,0,0]。trainer114ショウダイの4体へ通常勝利し468円/physicalflag1394だけを追加、Save43/独立Continueを限定受入。次は通常戦闘へ進む前に既存Bagと通常回復地点を確認する。既存のPP回復用品があれば通常BagUIで使用し、なければ静的地形とtrainer視線を照合し通常回復地点へ向かう有限候補を作る。host補充、負けによる回復の暗黙選択、全PP0の旧技選択loopはしない。回復後の未完候補は39,12→38,12→37,12→37,13から西上段、26,10→26,11→26,12の下り階段。今回39,12以西/下り階段は未到達。保存済1440地形/既存ownerを再利用し未知scriptだけ調べる。170/cold13入力・90画面・16controller/34受入試験を無影響再走しない。64〜68実menu0→4、71〜82部分write、83counter43/安定Flash/文言空白→84成功文言→87field。全Save/RTC/cold RAM ledger一致。Save39旧cold RAM差owner未解明、Save40保存後parser回収、Save41/42のrecord失敗履歴を保持。通常story/正規全国図鑑/分離progression自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達は未完。trainer352未受入、HM05所持だけ。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
