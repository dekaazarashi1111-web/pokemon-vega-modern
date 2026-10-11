# 505番道路のペア迂回・ミルシティ到着・Save52限定受入

`PASS_MIRU_CITY_CONNECTION_SAVE52_SCOPED`。31,24南から20歩/4方向転換で未戦闘ペアを迂回し、28,39から南connection1回でミルシティ（map3/2）28,0南へ。戦闘0、通常Save52/独立Continue全SaveRTC一致を受入。回復施設/正常回復は未完。

source `2d43764b9253f306dcb8abcd23e040e7cecbd85f` / run `37146655614` / job `111271886470`全8step成功。artifact `11282311020` / 294099bytes / SHA256 `8d6ec9ce3876183af50999c7ba1a0e1a51cf430cb86318ebb861270c96143fd0`。全67member、52画面、94+cold13入力。18新controller原log継承、39新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## ペア回避と通常南接続

read-only run37146312453/job111270883481でlocal3/8のobject属性16byteのみ追加読取。2体とも高度3、movement8、移動範囲x/y=1、trainer type/range=1。movement8の未証明の意味に依存せず、移動範囲内の全位置・全方向視界を過大近似して避ける。既存terrain/map/scriptsは再採取0。

0〜24で32列経由の20歩、草地4tileを通るが遭遇0。25で画面にミルシティ表示、map3/2・28,0南へ。未戦闘ペアを倒した扱いにせず、必須storyを省略していない。

## 全保存とcold RAMの差

party全600byte/全員HP/PP/全Bag/所持品/PC/S61E/17040円/RP0/badge1/story4071=9/4072=1は不変。新接続後の保存差はphysicalflag2194=0→1、var4021=63→84/4022=0→1/40AE=91→80。これらのruntime ownerは未解明。

progress RAMledgerは全50観測で同一だが、coldでは別hashとなる。全Save/RTC一致とは分離して保持する。cold差のowner解明、全国図鑑受入や全story受入を主張しない。

26〜30通常menu cursor0→4、31確認、32上書き。33〜42部分write、43は最終Flash一時一致でもcounter51、44counter52で再差分・書込中文言、45〜48成功文言、49field。cold0/1は同位置。42sector checksum、旧Save51bank57344byte保全、7025byte/1743差分範囲。

オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・全PP0。他2体は技ID全0。回復が最優先。今回戦闘0のため、新ダブルtarget分離や未確認技枠のnative実証は追加0。

次: Save52 artifact11282311020のstory-fast.srm（131088bytes/SHA256 f3fc9b1d3121b049900defb5c2f031a0b397a10b34fa3464d51f355a87833028）だけから再開。505の未戦闘ペアを視界過大近似の外側で迂回、20歩+南connectionを戦闘0で通過しミルシティmap3/2の28,0南/高度3へ到着。通常Save52/独立Continue全SaveRTC一致を限定受入。party全600byte/HP/PP/Bag/17040円/RP0/badge1/story4071=9/4072=1不変。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0、他2体技ID全0。正常回復が最優先。保存済みtown collision/map/warpsから回復施設のowner・必要経路高度・必要eventだけ読取し、通常入口/会話/回復を目指す。最初の新story/event/未通過境界/新建物/実回復で保存、必須story省略なし。town新接続flag2194とaux4021=63→84/4022=0→1/40AE=91→80、およびcold RAMledger差のowner未解明を保持し次の限定調査で確認。progress ledger3c7c0390…は不変、cold def3a8d7…は別hash、全Save一致と混同しない。43最終Flash一時一致counter51→44counter52再差分→45成功/安定→49field。原本94+cold13入力52画面/18controller39受入/67memberを無影響再走0。doubletarget分離native未実証、旧失敗・Save50raw6/実PP2/partybyte41・旧ledger差は保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知source不一致/action_requiredを全成功にしない。
