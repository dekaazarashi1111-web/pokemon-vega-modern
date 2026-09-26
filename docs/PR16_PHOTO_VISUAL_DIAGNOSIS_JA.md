# PR16 写真Continue後の背景 — 保存対照の診断

Status: WIP_DIAGNOSTIC_NOT_FIX_ACCEPTANCE

開始HEAD `45114dd931e8e8b9e7263a774847a16d7896d3be`、固定source取得HEAD `75fdbd5d107bb3629d5947e9b3cb503076b1bf7c`。source取得run36254574262は成功。写真の既受入run36253608437は再実行していない。

## 新規の表示専用対照

候補 `5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab`、33554432bytesは不変。固定seedと写真0RP fixtureを使うが、写真イベント・RP稼得・取消・重複拒否は呼ばない。

1. 停止warp map96/37 (48,5) → 物理キーの通常Start Save 1回 → 独立coreの通常Continue。建物・木・地形が正常。warp/保存後/Continue後の3枚はすべてSHA-256 `ff4a943e8bf4084af8f5dbf7150c17d2e64b29a6b61dbd8ec30276448e7ff85e`。counter2→3→3。
2. 同じ停止warp → QOL保存delegate `0x09377661` 1回だけを既存scheduler fixtureで実行 → 独立coreの通常Continue。青い反復背景を再現。画面SHA-256 `e5dc8b65607ab06b09f9989ec991abb26334555d6833065d412baedd37118098`。counter2→3→3。これは保存delegateの診断であり自然UI到達の受入ではない。

各対照で全Bag/party600bytes/ledger2048bytes（自然minuteのみ除外）不変、Continue時の全Flash不変、警告/標準エラー0。各1host compile/1native process/2fresh cores。ARM compile/link0、ROM変更0。観測中の7API書込みを禁止し、scheduler引数準備は明示的なfixture区間と区別する。

両対照のmap番号96/37、座標48/5、保存layout ID497、RAM map header、layout `0x092A4498`、72×20、border/data/primary/secondary pointerは一致する。layoutやtilesetのポインタを盲目的に変更しない。

## 現在の絞り込み

通常Save前処理 `0x0806EE14` は `0x08058994` を呼ぶ。この本体はSaveBlock2+`0x898`へ15×14個のhalfword（420bytes）を保存する。通常Saveのこの範囲は実map view、直接delegate側では全420bytesが0だった。

Continue側 `0x08058A80` は `0x08058A14` の空判定後に保存viewを復元する。空判定本体の終端literal `0x08058A48` は `0x1FF` で、512halfwordを走査する。一方、直接delegateの保存view先頭512bytesは0だが、その直後のデータは非0を含む。保存view以外の隣接データを空判定に含める可能性がある。clear本体 `0x08058A54` とCPUコピーABI、隣接owner境界を次に照合してから最小修正を決める。

写真原本の青背景/台詞はartifact10910018130（SHA-256 `405b4ff811f27a91934610171da395f137046b4f1a155b488018574a64592afc`）から再取得・目視した。通常写真原本の受入を新しい試験結果へ読み替えない。原因の最終確定・修正受入・自然到達・他5活動・releaseはこのWIP時点では未完。作業継続時は同じ2対照を無変更で繰り返さず、clear/空判定の境界と修正影響だけを検証する。
