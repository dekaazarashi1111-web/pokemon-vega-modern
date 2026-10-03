# 504橋下・階段・橋上・Save42 限定受入

`PASS_ROUTE504_UNDERPASS_STAIRS_UPPER_BRIDGE_SAVE42_SCOPED`。Save41の橋下48,11から南へ抜け、54,15の階段で上段へ。橋上48,13から47,13西へ通常通過、Save42/独立Continueを限定受入。21歩/8方向転換、戦闘0。旧48,11→47,11は未通過のままで再試行0。全story・全国図鑑・自然成長は未完。

source `0dd57e34888b7d3de23bf5a42153a3f936a5f61d` / run `37132139175` / job `111229185172` 全8step成功。artifact `11277536596` / 409650bytes / SHA256 `04bb37913134e5b62c1bcb7004d4f14bd7c4b0c4591148a2b0f83ec0018ebaef`。全72member/57画面/103+cold13入力。新16controller成功logを継承、二回目record run37132813539の新30原本受入/拒否試験成功logを継承、記録時試験再実行0、native2/record0。ROM/fixture/compile/既受入再走0。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/legacy flag/story4071=9/4072=1・badge1不変。補助var4021=75→96/4022=0→1だけでruntime owner未解明。42sector checksum/旧Save41bank57344byte/6871byte1715範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400を保持。

30〜34の通常menu cursor0→4を実画像確認。37〜48と50は13部分write。49は最終Flashと一時一致するが書込中/counter41であり完了とはしない。50でcounter42/Flash再変化、51〜53成功文言/安定全Flash、54field。cold0/1も橋上47,13西。全57画面を確認。進行最終/cold ledger `7a0eb126f868227ffd18a5a2c776246c41194f69d437a834570c1964e4a5f117` は一致するがSave39旧差owner未解明を維持。

初回record run37132651122はGUIDE定数の旧Save41宛先を専用guardがartifact取得/受入試験/正本書込前に拒否。native0/試験0/正本書込0。Save42宛先へ訂正し、失敗終端を保持して記録。第二record run37132813539は30試験全成功後、成功した試験名のskippedへ粗いsubstring判定が誤反応。原試験log/705byte artifact11277088734を不変継承し、成功行と正確な終端を検査する。旧run結論はfailureのまま、試験/nativeを再走しない。

保存地形1440cell/11nodeの再採取0。橋tileのelevation15は進入した高さを保持し、54,15のelevation0階段から上段へ進める候補を今回の通常通過で限定裏付けた。すべての橋/階段の一般的到達保証にはしない。22vertexの今回候補全部を通過、以西は次の未受入区間。

## 次のcheckpointをActionsへ送る前のローカル確認

1. 新counterを1つ定め、ASTで全Pythonの構文と定数を照合する。importするmeasure/accept、CP/JSON、GUIDE/MD、EVIDENCE、VISUAL、OUT、workflow名、CODE列挙、test名が同じ新counterであること。文字列一括置換の小文字/大文字漏れを個別に検出する。
2. 環境変数は受入試験が読む新counterのORIGINAL/ROMと、実入力である親counterのINPUTの3名をrecord側定義と集合比較する。親artifact/run/source/save SHA、Save counter、bank世代、manifest件数を実原本と照合し、親を新counterへ一括置換しない。
3. 送信予定tree/staged pathsの全一覧を表示し、意図した新規text pathだけか、既存受入source/旧GUIDE/旧checkpointとの交差が0か確認する。CP/GUIDE/EVIDENCE専用宛先guardと既存private/source guardは弱めず保持する。
4. 新試験名/件数と成功原logの一致を確認する。unittestの成否はreturncodeと全成功行/正確な終端で判定し、試験名内のskipped等へのsubstring判定を使わない。既に成功した試験を記録器だけの失敗で再走しない。失敗runはそのまま保存し、以後は原本再利用で回収する。

本Save42のGUIDE旧名漏れと試験名substring誤判定は両方とも履歴へ保持した。次workerは上の4点をpush前に済ませ、既存の専用宛先/private/source guardを引き続き使用する。

次: Save42 artifact11277536596のstory-fast.srm（c1959acc33cd7592ff4c3202e5fc5f4397215315127ebe257cd27486997aa144、131088bytes）だけから再開。map3/44（504番道路）・47,13西/橋上elevation4・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。橋下48,11から南通路、54,16→54,15階段→54,14上段、橋上49,13→48,13→47,13を通常通過し、Save42/独立Continueを限定受入。戦闘0。旧48,11→47,11は未通過のまま、今回再試行0。橋下/橋上の異なる高さを同じ経路にしない。次候補は47,13→46,13→46,12から上段を西へ。保存地形の42,12/37,13/34,13→33,13→31,13→30,10→26,10→26,11階段→26,12下段を候補とし、最初の新戦闘/event・未通過境界または通常回復地点で保存。保存済1440地形/既存ownerを再利用し、未知scriptだけ追加調査。PPはslot1残5/slot0残1を基準に通常技入力、host補充しない。今回103/cold13入力・57画面・16controller/30受入試験を無影響再走しない。30〜34実menu0→4、49は最終Flash一時一致/書込中、50counter42で再変化、51成功文言/安定全Flash→54field。今回全Save/RTC/cold RAM ledger一致。Save39旧cold RAM差owner未解明、Save40保存後parser failureの回収、Save41初回record guard failureを保持。残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
