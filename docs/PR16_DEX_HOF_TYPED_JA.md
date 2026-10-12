# 旧egg donor残参照の根付き型分類

## 目的と境界

前工程は `pr16_dex_hof_song_checkpoint.json`。候補は32 MiB / SHA-256
`0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583`。
全874行の見かけ参照のうち560行を受入済みで、残314行を保持している。
本工程は固定inventoryを再利用して、新たなnumeric・palette・JP song consumerの意味を解決する。
未知をowner名、byteの見た目、領域の推測だけで除外しない。

新しい成果は `content/modernization/pr16_dex_hof_typed_checkpoint.json` と
同 `pr16_dex_hof_typed_evidence/` が正本。実測前の数字を成果へ先書きしない。
既受入560行の全fieldと874行のaddress/target/kind/size/SHA集合を完全保持する。
各4byteは現在候補から再照合するが、全ROMの再scanは行わない。

## 数値consumer

`scripts/pr16_dex_hof_typed_numeric.py` は固定serializer、table receipts、C ABI、
現在の115 actual owner after-SHAへ結合する。PLR1の既12行を再分類しない。
T09、Stage39、Stage66/67、P07のレベル行は各形式のレコード・終端・pointer表と分離して検証し、
paddingとpointer型を数値型として通さない。範囲を被覆できない行は未知のまま残す。

Stage39は下流でheaderのroot自体が変わるため、歴史的pool境界を固定P04容量receiptから解決し、
現在ownerのactual after-SHAと区別する。T09の14行、Stage39の15行のMOVE0/LEVEL0は固定原本と
serializer/consumerに存在する数値行として扱い、他ownerの条件を緩めない。

T09 tutorにはStage39の20→16byte stride patchがあるが、旧routineはtutor<64に制限される。
唯一残るBL形はspecies348のrow+8（第3u32）にあり、現供給wrapperの直接consumer-rootは
未証明なので未知のまま保留する。物理bit列らしさや旧source幅の比較だけで除外せず、機能不具合とも断定しない。

## Paletteの跨ぎ参照

`scripts/pr16_dex_hof_typed_palette.py` はpointer/tagの型別readを確認する。
8byte palette行の+2から始まる見かけのu32を、4byte pointer読取と2byte tag読取へ分解し、
実consumerのload境界、生成元、全row/owner identityを結ぶ。
異常・未知のpointerをpaletteらしいだけで許可しない。

## 拡張JP song interpreter

`scripts/pr16_dex_hof_song_extended.py` は既32窓・19固定sourceに追加JP窓を結び、
XCMDのsubcommandと12byte toneの変更を状態へ取り込む。旧formalのsemantic reviewは
現在候補の全SHAと各window identityが一致してからだけ利用する。
JPのPlayFanfare自身が14rowへ制限する有限consumer tableを追加し、既114 IDとは別に
12 IDを根付ける。選択126 IDとsource明示114、14rowを分離し、USの347曲上限をJPへ転用しない。

失敗trackで読んだ構造・command、VOICEでコピーした全tone、全song横断の競合を保持する。
同一幅の非pointer operandに許す別解釈と、opcodeやpointerとの競合を区別する。
共有memory/外部mutationを実際には扱っていないのに対応済みと宣言しない。
Song250/251のVOICE24と固定MIDIの14/13不一致はそのまま残す。
型付きsample prefix、DPCMの全実read footprint、実演奏開始受理は別々の主張である。

## 実行・証拠

新しいfail-closed unitだけを実行し、既受入controller配置を新read用に1回再構築する。
現候補全SHA、115owner after-SHA、全旧874hitを結合する。
固定公開20sourceに加え、numericのCFRU4sourceはsource-lock commitとGit blobで別viewへ
明示取得する。過去ROM再構築がvendorを用意するという仮定に依存しない。新native、旧heap試験、
既受入全ROMscanは実行しない。変更のない正式ROMとSave101は書き換えない。

producer / publication guard / upload / record consumerのpathとartifact名を機械照合する。
公開はsourceと最小address/size/SHA/textのみ。専用平坦dirの非空・完全UTF-8・末尾LFを検証し、
hidden、symlink、未知拡張子と未知ファイル名を拒否する。ROM断片、rawhex、ROM、入力save、
MIDI/WAV、runtime、runner、credentialsは追加公開しない。

成功後は固定再開MD/JSONと両append-onlyログを更新し、同branchへ非force pushする。
committed text全byte/末尾LF/Git blobを読戻し、終端Actions証拠を確認してpendingを閉じる。
一般CIの既知QOL source不一致、action_required/job0、Stage79既存cacheはこの受入と区別する。

## 完了の意味と次工程

型分類が増えてもdonorは未使用。未知0だけでなく間接参照と退役完全性を証明してから、
必要容量を明示leaseへ移す。115owner/52save subowner/残804byteという実配置を維持し、
32sector Ccontroller、S61E/MDX全writer/loader、Link exact-source/no-main/INITIAL、
全mode/早期31/species9bitと全保存入口の同期heap lifetimeへ接続する。

heap arena13352byteは保存退避53300byteでMallocInit前に壊れる。callbackを跨いで保持せず、
0804B85C/08002B80/08002948前に全出口Freeが必要。これは本工程で受入済みにしない。
その後正式候補切替、trainer131後半からシオウ通常回復・保存・独立cold Continueへ進む。
通常雑魚戦ごとのcheckpointは作らない。
