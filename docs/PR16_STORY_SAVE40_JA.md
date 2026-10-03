# 504番道路の正規event・Save40 限定受入

`PASS_ROUTE504_MOSGIS_EVENT_SAVE40_SCOPED`。Save39の71,9から通常24歩で60,10の座標eventへ入り、モスギスとD・H団人物の会話/追跡演出を完了。正規scriptでstory4071=8→9、拡張flag4370をセット。60,10西の通常Save40/独立Continueまで限定受入。戦闘0。全story・全国図鑑・自然成長は未完。

測定source `c51b505a4541b91951d660aea6cf1d931a06b490` / run `37129549744` / job `111221756160` はfailureを保持。156/cold13入力の両nativeは正常終端し、保存/Continue後に旧Save35洞窟専用trace parserが今回のカメラ座標差を拒否した。保存原本を改作せず、今回専用独立parserと原本32受入/拒否試験で回収。追加native0。artifact `11276815366` / 591258bytes / SHA256 `5f7bb21e21652641f23df582c33731c98f7d66557add3c99e5078a55e46257ee`、全99member/83画面。

新13controllerは元jobの成功logを継承。静的run37129298036の全8step成功、地形1440マス/11node（5root/4unique）/168命令・診断0を採取。既存map view/既受入gameplayの再走0、ROM/fixture/compile0。次作業は保存済地形を再利用する。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/legacy flag不変。S61Eはbyte258=3→7（flag4370のみ）とCRC正常、旧4367〜4369保持。正規story4071=8→9、補助4021=40→63/4022=0→3のownerは未解明。42sector checksum/旧Save39bank57344byte/6931byte1698範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400・4072=1/badge1を保持。

30〜55はeventカメラ座標で、主人公live60,10を維持し56で操作へ復帰。カメラの48,8等を主人公の移動/warpにしない。57〜61は実menu cursor0→4、64〜75は12部分write、75counter40でもFlashは未確定、76〜79成功文言/安定全Flash、80field。cold0/1も60,10西。進行最終/cold ledger `8d9929bc88d9ea0adcd06aff00a88aafbe57a707af12fb94fd4cc065c521f41d` は一致するが、前Save39で生じた旧cold差のownerを解明したとはしない。

次: Save40 artifact11276815366のstory-fast.srm（cf8fc894e9542afbfa411db72f26411bec5dae3220bc8f8104cf71bfc109add1、131088bytes）だけから再開。map3/44（504番道路）・60,10西・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。通常24歩から座標60,10のモスギス/D・H団人物の追跡eventを完了し、正規flag4370・4071=9、Save40/独立Continueを限定受入。戦闘0。次は西59,10→58,10→56,10の西段差候補から504を先へ。保存済behavior57は西向き段差の比較定義だが現候補の実通過は未受入。全1440地形/11node東側ownerは保存済原本を再利用し、無影響再採取しない。最初の新戦闘/eventまたは通常回復地点で保存、PPをhost補充しない。本runの156/cold13入力・83画面・13controller/32受入試験は再走しない。元run37129549744のfailureは正常保存/Continue後に旧洞窟専用parserがeventカメラ座標を拒否したもの。artifact全99memberを改作せず保持しnative再走0で回収。30〜55のカメラ座標は主人公live60,10と区別、56field復帰。通常Saveは各行menu cursor0→4を画像検証。75counter40は部分write、76成功文言/安定全Flash→80field。今回の進行最終/cold RAM ledgerと全Save/RTCは一致。ただしSave39の旧cold RAM差ownerは未解明。Save36の保存後parser回収、Save37/39の一時Flash一致、Save38のtrainer103と未受入再戦1029、Save39初回TrainerCard未保存を保持。残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
