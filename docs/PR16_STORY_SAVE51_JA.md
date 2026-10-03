# 505番道路の高台東階段・ワタミ戦・Save51限定受入

`PASS_ROUTE505_WATAMI_SAVE51_SCOPED`。22,18北から新27歩/8方向転換、高度4の東側を横断して32,14階段で高度3へ、31,24南でスキーヤーのワタミとsingle戦1勝。通常Save51/独立Continueだけを受入。南接続/正常回復は未完。

source `7bfc8f61d793c5533c0e6aed3e75dadd178fbac3` / run `37145425150` / job `111268239135`全8step成功。artifact `11281768926` / 534884bytes / SHA256 `b69798df6353d1ef77547ba193b4ab6615485679472694ff2f4eb3a3439edfbe`。全112member、97画面、184+cold13入力。新22controller原log継承、44新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## 通常入力と戦闘

35〜37は接近会話、38〜69はワタミ戦、ココガラ/イシズマイ/ビッパ/クヌギダマの4体。67勝利、69賞金1400円、70field。15640→17040円。trainer1055は同ROM remapでphysicalflag1407、保存差はその1bitだけ。

44/45/46は技cursor0→2→3。46/52/58/64でつばめがえしを選択、49/55/61の交代確認はBで拒否。新controllerは選択コマンド4と相手確定0を分離し、保存byte55=18→14から実PP4を独立確認。ダブルtarget分離のnative実証は今回は0、全4技のnative受入でもない。旧Save50のraw used6/実PP2は原本のまま保持。

オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・全PP0。他2体は技ID全0。今回のparty差は1byteだけ、全員HPを保持。正常回復は未完。

## 全保存境界

全Bag/所持品/PC/S61E/badge1/story4071=9/4072=1は不変。RAMledger42/63とaux4021=37→63はruntime owner未解明、cold最終ledgerは一致。旧Save50の歩行byte41など未解明差も保持。

71〜75通常menu cursor0→4、76確認、77上書き、78〜89は12種類の部分write。90安定Flash/counter51でも成功文言なし、91〜93成功文言、94field。cold0/1は31,24南で全SaveRTC一致。42sector checksum、旧Save50bank57344byte保全、6944byte/1717差分範囲。

## 再利用と次区間

Save50で保存した未通過47歩候補、terrain/map/scriptsをそのまま再利用。追加読取0、既受入57歩の再走0。今回新27歩を通過し、南接続前まで候補残20歩。28,27/29,27の未戦闘trainer付近を通るため、視界を避けられる安全な候補があるか必要な属性だけ確認して回復を優先する。必須storyは省略しない。

全国図鑑/自然EXP・技習得・進化/全story/研究施設自然到達/releaseは未完。一般CI既知source不一致とaction_requiredを全green扱いしない。

次: Save51 artifact11281768926のstory-fast.srm（131088bytes/SHA256 8661346e2de9bc73fc61d5a63af5bd6acd10008486b54c66c9459820a5447d65）だけから再開。505番道路22,18→新27歩/高台東階段→31,24南/高度3でワタミのsingle戦1勝、通常Save51/独立Continue全SaveRTC一致を限定受入。party4/RP0/17040円/badge1/story4071=9/4072=1。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0、他2体技ID全0。正常回復が最優先。保存済みroute index84から残20歩と南connection→map3/2の28,0が候補。28,27/29,27の未戦闘trainerの視界を避けられるか、保存済みterrain/graphと必要な未読object属性だけで確認してから進む。最初の新戦闘/event/未通過境界/接続/実回復で保存。新controllerは選択とtargetを分離しSave50実PPへ再束縛、今回はsingleなので選択4/target0/実PP4だけをnative確認、次回実PP14へ再束縛。ダブルtarget分離native未実証。42/63RAMledgerとaux4021=37→63のowner未解明。90安定Flash/counter51→91成功文言→94fieldを分離。原本184+cold13入力97画面/22controller44受入/112memberを無影響再走0。旧Save50 raw6/実PP2・partybyte41/旧ledger差、旧失敗を保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知source不一致/action_requiredを全成功にしない。
