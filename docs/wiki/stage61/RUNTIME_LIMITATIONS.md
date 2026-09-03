# Stage61 実行時の既知制約

[Wiki入口へ](README.md)

## ROM候補の状態

- SHA-256: `60b83b8c50e54c3af42daa23b9d82e96c1b769d816ce28ef8bfda1d5005aff0e`
- `candidate_status=CANDIDATE`
- strict全件監査: `DEFERRED_AUDIT`
- 通常野生、ecology、種族値、技性能、習得表、進化表は現ROMから直接抽出しています。
- 取得イベント、Raid、フォーム供給、item供給は統合済みのStage26/56/58正本を継承していますが、現SHAで全経路を手動走破したという意味ではありません。

## TM/HMと教え技

現ROMの互換bitsetは1種族16 byteです。しかし、実際の `gTMHMMoves` は58件（TM01–50＋HM01–08）だけで、V4設計資料の追加TM 51–120は実move tableへ接続されていません。さらにV4設計のTM51–58は、実行時HM slot 51–58と衝突します。

教え技も互換bitsetは64枠設計ですが、実 `gTutorMoves` に有効なMove IDがあるのは15件です。16件目は0、以後は別データをmove IDとして誤読するため使えません。

このWikiの各ポケモンページは、誤った「覚えられる技」を案内しないため、ゲーム内consumerが実際に参照できるTM/HM 58件と教え技15件だけを掲載します。未接続の設計bitは掲載対象外です。
