# PR16 Union Room Chat保存の失敗通知

正式ROM/Save101を保持し、Mystery Gift候補3bb4c51bを継承する。Union Room Chatの返値無視による完了文・SE_SAVEを局所修復する候補であり、全非START/全modeの受入ではない。

## 局所契約

内側保存gateはmode0、SP+8=0x0937767B、SP+16=0x08129A93に限定する。対象外は現行Mystery gateへ委譲し、main失敗は255、main成功かつdamaged bit31単独ならouterの実write/readbackへ進む。maskは改変しない。

PlaceStdMessageWindowの0x0812AF64から12byteをimmutable tailへ接続する。message9かつ56byte frameのSP+52=0x0812ACBFで、16bit attemptが1以外の場合だけlocal string r6を既存2行errorへ切替える。元template・AddWindow・placeholder展開・scroll・border・printer・DMAを保持し、成功文字列を一度表示して上描きしない。他のmessageとcallerは元文字列を保持する。

SaveAndExit state9の0x08129AC4から12byteを局所tailへ接続する。描画busy待ちは元のまま。成功は元SE_SAVE/ClearContinueGameWarpStatus2/state10/121frame閾値を保持。失敗は新規A/Bを待ってから一度だけclear、state12の元fade/cleanup/field帰還へ進む。自動retryやmutable latchを追加しない。

## 配置と検証境界

現行112ownerと全実byteを比較し、既存codec reservationの現行5152byteを保持。0x09FC1DB8以降1332byte全体が実際にblankであることを確認してから使う。旧余り記述を根拠に上書きしない。新mutable ownerなし、他111owner・全未宣言ROM byte不変、全ROM逆変換を確認する。

隔離実ARMは8保存結果×3stale attempt×2SP×2入力の96caller条件、720caller gate条件、200文字列条件を対象とする。物理Flash/描画はstubであり、実UI・通常通信・自然退出・field帰還の受入は別工程。

HOF/共通SaveFailed scratch衝突、mode4/5再erase、stale selector authority、sector31早期故障/原子性、残typed consumerは未完。正式ROM切替・trainer131後半へ進まず、最終目標はシオウPokecenter通常回復・保存・独立cold Continueを維持する。
