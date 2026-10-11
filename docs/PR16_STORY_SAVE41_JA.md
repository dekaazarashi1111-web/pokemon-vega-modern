# 504西段差と橋下・Save41 限定受入

`PASS_ROUTE504_WEST_LEDGE_UNDERPASS_SAVE41_SCOPED`。Save40の60,10から西へ進み、58,10→56,10の西段差を通常入力で通過し48,11の橋下に到達。48,11→47,11は3回未通過として保存し反復しない。通常Save41/独立Continueを限定受入。新戦闘0、正規story4071=9/4370は前Save40の受入を継承。全story・全国図鑑・自然成長は未完。

source `8c012df44845e982acef17db79396be6dd03dc14` / run `37130788526` / job `111225303265` 全8step成功。artifact `11277075434` / 315975bytes / SHA256 `ed8e6939b07adb649f61516fedbe5050a250d2f72875ac75014f7ac3781c129d`。全59member/44画面/77+cold13入力。新14controllerの成功logを継承、新26原本受入/拒否試験、native2/record0。ROM/fixture/compile/既受入再走0。測定receiptを独立episode解析前に保存する構成へ改め、前回の保存後parser failureでreceiptが欠けた問題を避けた。旧parserや旧受入条件は変更していない。初回record run37131369405はGUIDE宛先の旧名を専用宛先guardが事前拒否し、native/受入試験/正本書込0。新Save41宛先へ訂正して原本から記録。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/legacy flag/story4071=9/4072=1・badge1不変。補助var4021=63→75/4022=3→0だけでruntime ownerは未解明。42sector checksum/旧Save40bank57344byte/6866byte1695範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400を保持。

17〜21の通常menu cursor0→4を実画像確認。24〜36は13部分write、36counter41でもFlash未確定、37〜40成功文言/安定全Flash、41field復帰。cold0/1は同じ橋下48,11西。進行最終/cold ledger `7a0eb126f868227ffd18a5a2c776246c41194f69d437a834570c1964e4a5f117` は一致するがSave39の旧cold差owner未解明は維持。

保存地形1440cell/11nodeの再採取0。静的57vertexの候補のうち13vertexだけを通過し、次の47,11へは通れなかった。橋下elevation15と橋上elevation4を単純な隣接だけで接続するBFSはlive到達保証にならない。次候補は南の橋下を抜けて54,15階段へ。地形比較を実通過と同一視しない。

次: Save41 artifact11277075434のstory-fast.srm（a70b790da5894eac9f67e2a324c68e3513d86330491ef9451ffca06c792f0140、131088bytes）だけから再開。map3/44（504番道路）・48,11西・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。西段差58,10→56,10と橋下48,11までの通常移動、Save41/独立Continueを限定受入。戦闘0。48,11→47,11は3回未通過で反復しない。保存地形では48,11/12/13がelevation15の橋下、47,11は4であり単純BFSの高さ無視が誤候補だった。次は南48,12→48,13→48,14→48,15→49,15→50,15→50,16→51,16→52,16→53,16→54,16→54,15の階段behavior42/elevation0候補。54,14の上段elevation4や以西は静的候補で、実通過を先取りしない。橋の15は現在高度を保持し、階段0で高度を切り替える地形モデル候補を使う。全1440地形/既存ownerは原本を再利用。最初の新戦闘/event・未通過境界または通常回復地点で保存、PPをhost補充しない。77/cold13入力・44画面・14controller/26受入試験は無影響に再走しない。実menu cursor17〜21の0→4、36counter41は部分write、37成功文言/安定全Flash→41field。今回の進行最終/cold RAM ledgerと全Save/RTCは一致。Save39の旧cold RAM差owner未解明を保持。Save40の元parser failureは保存後回収済みで改作/再走しない。残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
