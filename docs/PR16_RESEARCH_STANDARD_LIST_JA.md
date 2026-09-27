# PR16 受付STANDARD_LIST

Task: `USER-20260927-RESEARCH-STANDARD-LIST`

標準リスト失敗原本を先に読む。成功した入力/生成物を再実行せず、変更された障害層だけ修正する。 次の独立境界は自然稼得RP→ショップ支出、通常ストーリー進行。数値2境界/旧4入口/旧稼得/BP/P08は再実行しない。

## 実装

固定c3971e83の後処理層。既存の受付数値script/text、研究owner、volatile、canonicalは不変。未参照FF領域0x09F4A800/2048byteとlocal4 script pointerだけを所有。744byte独立Thumbコード、212byteイベント、実差分950byte、全ROM rollback一致。stock task/window/menu APIで「ポイントとランク」「ポイントのあつめかた」「おわる」、B取消、両機能からlistへ戻る。task/window解放・入力debounce・資源不足時の非待機終了。新EWRAM0。正本recipeは `content/modernization/pr16_research_standard_list_recipe.json`。新親では再監査を要求する。

## 検証境界

run36310534280のARM生成1回とhost/event30検査を保存再利用。初回run36310336114の暗黙memcpyリンク失敗を保持。今回の新しい連続入力1processは起動前0RP fixture、屋外prefix後は物理keyだけ。3回訪問、2機能選択、B取消2回、終了行1回。所有task/window、全owner/ledger/Bag/party/Flash/counter、展開文言と22画面を照合。7方式書込み拒否、厳格host compile、新oracle27検査。件数の実績/失敗有無はcheckpoint原本が優先。通常ストーリー到達や自然稼得支出は未受入。

## 現在地

`STOPPED_STANDARD_LIST_MEASUREMENT` / source `a06f61d9ed78061d59f2b7cb681efdfe55d3daaa` / run `36311122801`。画面視認と自己run終端を自動成功へ昇格しない。
