# ChatGPT Pro への渡し方

このパケットは、Pokémon Vega Modern Stage 35へ追加するカントーイベントを、後続のCodexが再解釈せず実装できる形で設計してもらうためのものです。ROM、セーブ、私有入力は含みません。

## 手順

1. このZIPをChatGPTの新しいチャットへ1個の添付ファイルとして追加する。
2. ZIPと同じ場所にある`*_PROMPT_JA.txt`（内容はZIP内`01_CHATGPT_PRO_PROMPT_JA.txt`と同一）の全文を、そのチャットへ送信する。
3. ChatGPTがパケットを展開・読取し、`submission/` を作成して検証するまで待つ。
4. 最終回答から `Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip` をダウンロードする。
5. ZIPを開いたり編集したりせず、そのままCodexへ渡す。

ChatGPTから文章だけが返り、ZIPが添付されていない場合は、次の一文だけ送ってください。

```text
設計説明だけで終了せず、添付パケットの出力契約どおり submission/ を作り、validatorをPASSさせたZIPを添付してください。
```

## 受領時に確認する表示

ChatGPTの最終回答には、最低限次が表示される想定です。

- `VALIDATION=PASS`
- event / dialogue / placement / batch の件数
- `open_questions=0`
- 出力ZIPの添付

これらが表示されても、ZIPの中身はCodex側で同じvalidatorを再実行して確認します。
