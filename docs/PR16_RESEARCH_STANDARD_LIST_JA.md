# PR16 受付STANDARD_LIST

Task: `USER-20260927-RESEARCH-STANDARD-LIST`

## 現在地

`MEASURED_STANDARD_LIST_PENDING_VISUAL_AND_TERMINAL_REVIEW`。source `164028f28c9fa753afa1525907e2824b17a16698` / run `36312254126`。正本は `content/modernization/pr16_research_standard_list_ui_checkpoint.json` と `content/modernization/pr16_research_standard_list_ui_recipe.json`。自己run終端と22実画面の視認前に正式受入へ昇格しない。

## 実装

固定c3971e83の後処理層。受付local4 script pointerと未参照FF領域0x09F4A800/2048byteだけを変更。新候補 `59ac6688576238f00dac88cccec1a42415f6f0e4f3f07d60411f6d3059bf61e6`。独立Thumbコード768byte、イベント212byte、実差分956byte、全ROM rollback一致。既存数値script/text、canonical、研究owner/volatile不変、新EWRAM0。

「ポイントとランク」「ポイントのあつめかた」「おわる」、B取消、両機能からlistへ戻る、3訪問の入力と資源解放を検査。全てstock task/window/menu APIを使い、taskだけが自分のwindowを一度解放。window pixelsは0x280..0x2f7、選択したユーザ枠は0x214..0x21c。ELFの18 delegateはSTT_FUNC/Thumbで型付けする。

## 過去の不具合と変更影響

run36310336114の暗黙memcpyリンク失敗、run36311122801の誤ったARM/Thumb veneer、run36311562940の会話窓消失と枠破損を原本のまま保持。後者のnative終了0/警告0だけでは受入できなかった。0x08110BF9は純粋入力でなくshared yes/no windowも削除するwrapperだったため、0x08110539へ接続を修正。0x080F89CDが返す0x214は枠タイルであり、文字タイルの確保に流用しない。元の厳格window再訪/解放oracleは変更していない。

既存canonical overlayにも同じ入力/枠APIの使用があるため、次の自然稼得RP→shop支出ではその実ウィンドウ所有関係を先に確認する。本タスクでは旧shopや受入済み数値境界のコード・結果を改作しない。

## 検証

run36312100158の変更影響host18件・ELF8件・ARM生成を再利用。イベント14件は完全不変を照合してrun36310534280を再利用。今回の新nativeは起動前0RP fixture、屋外prefix以降key入力だけ。3訪問、機能2行、B取消2回、終了行1回、22画面。新oracle27件を同じ原本に対して陽性前提付きで検査する。実績件数/失敗はcheckpointと原本が優先。旧数値2境界/旧4入口/旧稼得/BP/P08受入ケースの再実行0。

## 次の独立境界

このlistの22画面とrun終端を照合後、自然稼得RP→ショップ支出と通常ストーリー進行へ進む。今回はRP注入なしだが初期map/party/progressionはfixtureであり、自然到達・自然稼得支出は未受入。merge/release/baseline変更は禁止。
