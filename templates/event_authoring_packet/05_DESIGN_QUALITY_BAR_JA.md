# 設計品質ゲート

## 物語

- カントーへ行く理由、前半4認定の小さな完結、殿堂入り後に戻る理由、League後の完結がつながっている。
- 認定章は単なる8連戦ではなく、各地域の人・環境・施設を知る節目になっている。
- 主要actorは目的、判断基準、口調が区別できる。
- sidequestは追加Speciesの一覧紹介だけでなく、住民の生活、土地、戦術、二地方交流のいずれかを描く。
- 元FireRedの物語をなぞらず、既存mapを新しい役割で活用する。

## プレイ体験

- カントー進行は任意で、Vega本編を妨げない。
- 高難度警告、回復、無料帰還が常に機能する。
- decline、敗北、容量不足、resetで取り逃しや二重報酬が起きない。
- 再訪台詞があり、完了後もNPCが不自然に初回説明を繰り返さない。
- 1会話を短くし、長い説明は複数NPCや再訪へ分散する。

## 実装容易性

- mapとhostはcatalogの実在key。
- 新規stateは最小限で、同じ意味を複数flagへ保存しない。
- 既存trainer/acquisition/serviceを参照し、同じsystemを再設計しない。
- `SIMPLE_EVENT` stepだけで表現できる。
- batchごとに独立したacceptance testとrollback境界がある。
- event titleや人向け説明にしかない挙動がなく、機械正本へすべて落ちている。

## 会話

- game textはcharmapと18 glyph幅を満たす。
- 新規台詞であり、原作文章の転載ではない。
- speakerの立場と現在stateに合う。
- unlock前、進行中、完了後の違いを短く示す。

## 完了判定

次のどれかが残る場合は未完成です。

- `open_questions`が1件以上。
- placeholder、TODO、TBD、仮、未定がある。
- validatorがFAIL。
- event bibleとJSON/CSVのevent数・名称・順序が食い違う。
- 数値IDやROM addressを推測している。
- 実装不能な演出を「Codex側で調整」として残している。
