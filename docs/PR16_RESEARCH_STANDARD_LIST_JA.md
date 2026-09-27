# PR16 受付STANDARD_LIST

Task: `USER-20260927-RESEARCH-STANDARD-LIST`

標準リスト失敗原本を先に読む。成功した入力/生成物を再実行せず、変更された障害層だけ修正する。 次の独立境界は自然稼得RP→ショップ支出、通常ストーリー進行。数値2境界/旧4入口/旧稼得/BP/P08は再実行しない。

## 実装

固定c3971e83の後処理層。既存の受付数値script/text、研究owner、volatile、canonicalは不変。未参照FF領域0x09F4A800/2048byteとlocal4 script pointerだけを所有。744byte独立Thumbコード、212byteイベント、実差分933byte、全ROM rollback一致。stock task/window/menu APIで「ポイントとランク」「ポイントのあつめかた」「おわる」、B取消、両機能からlistへ戻る。task/window解放・入力debounce・資源不足時の非待機終了。新EWRAM0。正本recipeは `content/modernization/pr16_research_standard_list_thumb_recipe.json`。新親では再監査を要求する。

## 検証境界

host/event30検査はrun36310534280から再利用。誤ったARM/Thumb veneerによるnative失敗run36311122801を旧checkpointに保持。17 delegateをSTT_FUNC .thumb_setへ修正し、run36311386781のARM生成とELF8検査を再利用。初回run36310336114の暗黙memcpyリンク失敗を保持。今回の新しい連続入力1processは起動前0RP fixture、屋外prefix後は物理keyだけ。3回訪問、2機能選択、B取消2回、終了行1回。所有task/window、全owner/ledger/Bag/party/Flash/counter、展開文言と22画面を照合。7方式書込み拒否、厳格host compile、新oracle27検査。件数の実績/失敗有無はcheckpoint原本が優先。通常ストーリー到達や自然稼得支出は未受入。

## 現在地

`STOPPED_STANDARD_LIST_MEASUREMENT` / source `995e87e0e38c167f52c1ed2feeca6324fe6e017b` / run `36311562940`。画面視認と自己run終端を自動成功へ昇格しない。

## Thumb境界の修正

現在の候補は32MiB `e98d4b517fa6f8c8356acbe482117aa79c1e8d84a1e2b111f62ddb070571b817`。旧37f73b80は実測failureであり採用しない。C本体/イベント/旧owner/数値表示のbyteは不変。新しい正本は `content/modernization/pr16_research_standard_list_thumb_checkpoint.json` と `content/modernization/pr16_research_standard_list_thumb_recipe.json`。旧失敗原本を消去しない。
