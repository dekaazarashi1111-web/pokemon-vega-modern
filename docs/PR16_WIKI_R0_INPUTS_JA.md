# Wiki R0 入力監査と継続点

**入力監査だけが完了。R0は未完成・閲覧依頼前です。**

決定 `OWNER-20261010-WIKI-FIRST` / 入力HEAD `a0c9d36342dff35228247391cfeb299d12ed9c79`。現在の作業選択は [固定状態JSON](../content/modernization/pr16_wiki_first_execution_plan.json) のみを正とします。

[入力manifest](../content/modernization/pr16_wiki_r0_input_manifest.json) で既存Wikiの機械可読入力を元のsize/SHA-256へ結合しました。旧Wiki生成器・受入済み試験・ROM再構成・nativeは実行していません。

| 入力 | identity | 採用範囲 |
| --- | --- | --- |
| 旧P08 | `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38` | 能力・技・特性等の数値原本。後継ROMでの意味同値は未証明。 |
| Issue19後継 | `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` | 後継の現役習得経路。旧P07履歴と混在させない。 |

## 次の具体作業

1. 旧能力/技/特性/進化/機構tableと後継候補の非変更rangeまたは同一semantic hashを結合する。
2. 正式registryの1671 ID/stable keyと後継ownerの実対応を照合し、現在の習得経路だけを採用する。
3. 候補識別子付き別R0へ比較/個別/逆引き/メガ/Gmax/Z/供給/限界を生成し、リンク・決定性・check無書込を検証する。

保存容量784分類/90未知/安全容量0は保留正本のまま。全クリ走破は対象外でありPASSではありません。数値同値が未証明のためreview_readyはfalse、所有者承認・配布・baseline切替を追加しません。
