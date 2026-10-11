# 登録text APIからの必要最小型と未完容量

## 対象

開始HEADは`4a1f89d01a19536f1894f40958edcd35f11c1045`、同branchのPR16専用作業。
直前のhealing/veil測定756分類/118未知を親とし、親37入力・19namespace・137changes/127witness・874hitを全文identityで保持する。
新しい2つのconsumer familyだけを対象とし、旧guardや受入済みnativeを再実行しない。

- 通信ミニゲーム記録文の3hit: `0x083E1F18`、`0x083E1F26`、`0x083E2014`
- 参加数制限文の2hit: `0x091492CA`、`0x091492E5`

各hitの4byteだけを型領域にする。text全文、table、consumer関数、登録根の保護窓は証明用であり、新規型領域へ広げない。
正式な5件追加/761分類/113未知は、現候補0641のActions測定と記録が成功した後にだけ成立する。

## 非pointerと判定するための最小十分契約

この判定はall-byte-startの32bit検索hitが、実登録されたtext serializer内の単byte/EOS fieldに跨がることの証明である。

1. 固定公開sourceのserializer/field幅、現JPの実登録slotまたはhook、実table cellと完全pointerを独立に結合する。近傍、symbol名、英語版住所、単一source-layout予測だけでrootを作らない。
2. 実API入口の条件を明記し、その入口から実table選択またはliteral読取、pointerの生成・保存・consumer引渡しを実命令で束縛する。対象text pointerをhost値として直接注入しない。
3. serializer起点から完全EOSまでのextentとconsumerの型付きreadを照合し、hitの全4byteを隙間なく被覆する。隣接2textなら両側に独立pointer/extent/consumerを必要とする。
4. source全文・最小窓SHA・実命令の独立encoderを結び、slot/pointer/field幅/EOS/consumer/型窓の改変とresealを拒否する。
5. new scope以外のaccepted、remaining unknownの全field、全19親witnessと133曲/50assetは変更しない。

この最小契約で「登録text consumerにおける型付きoccurrence」を分類する。全ゲームのあらゆる間接readerが同じbyteをpointerとして再解釈しないという全称命題は別義務であり、ここからは主張しない。
条件付きspecial/API呼出、有効index/resource、明示したopaque calleeの正常ABIや生成結果は前提として記録する。自然playからの全到達、全prefix handler成功、描画成功、全callee effects、普遍IRQ/heap寿命を余分に証明済みへ昇格しない。

## 実根

ミニゲーム記録文はspecial405/422の実slotからconstructor/task登録、printer、text literal/tableへ結合する。
参加数制限文は実hook `0x08124930`→`0x09121C90`、table `0x0916901C`、実LDRとstack保存、consumer call `0x09121DA2`→`0x08120AE8`へ結合する。
具体的なAPI条件、全pointer/extent、命令、最小保護窓は2つの新consumer moduleと独立review JSONを正本とする。

## 現候補・容量・保存境界

現候補は33554432 bytes / SHA256 `0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583`。
115 actual owner、52 save owner、save内残804byteを最新generation-writer checkpointの実owner hashに結合する。
旧egg15118byteは全域保護、donor安全容量0、leaseなし。単一controller6528byteは未配線。heap13352byteの普遍寿命とstock保存退避53300byteの境界は未完で、跨いで保持しない。
正式ROM/Save101/nativeは不変。間接参照完全性・対象退役・owner移管が閉じるまで、未知が減っただけでdonor安全を宣言しない。

## 検証・公開

新consumer、統合、chain/capacity、Actions公開/provenance契約だけを新scope試験とする。診断fixtureと現候補0641を厳密に分け、正式測定では1回の現候補再構成、全候補SHA・115owner・874hit・親完全性を確認する。
producer/guard/upload/recordのpathとartifact名を一致させ、success guard後の専用directoryだけをuploadする。
全公開textは非空・size上限内・UTF-8/LF。hidden/symlink/未知拡張子/余分なfile、receipt未知field、未解決source reviewを拒否する。
全receipt本文を実commit済みsnapshot・measurementへ結合する。ROM断片、rawhex、ROM、runtime、入力save、runner、credentialsは追加公開しない。
旧独立最終song/battle/Surf source reviewは未実施のまま保持し、拒否された旧操作を再実行しない。新規source-only reviewはこのbatchの新sourceだけである。

## 次工程

残unknownは実UI/script/asset登録cellと完全pointer/extentから調べる。公開general-script全配置予測の+8byte差を現ROMへ代用しない。
既Bag14/15、Fishingstate7、旧Defog/Dive、placeholder event、Credits paddingなどは新しい独立根が出るまで同じ無効候補を反復しない。
安全容量と間接参照・退役・owner移管、全保存入口のheap-ready/同期非再入/0804B85C退避前Freeを閉じてから、本controllerを全S61E/MDX writer/loader/Linkへ接続する。
最終図鑑修復後はtrainer131後半からシオウ通常回復・保存・独立coldContinueへ進む。全雑魚checkpointは作らない。
