# Pokémon Vega Stage61 プレイWiki

現行Stage61 ROMに固定した、プレイヤー向け・Codex向けの参照資料です。

- ROM: `build/stages/61_critical_release_candidate.gba`
- SHA-256: `734541807df91ca6f82211b57e0a56e6af6c1c70ec46b9f89cd6a89b3f701f3b`
- ポケモン: 1621 ID（内部・フォームを含む）
- 技: 1063 ID
- 特性: 312 ID
- アイテム: 999 ID

## 閲覧時の最優先ルール

通常のプレイ質問や「Wikiを見て教えて」という依頼では、該当する公開済みWikiページだけを読み、すぐ回答します。閲覧中に次の処理は絶対に実行しません。

- `make stage61-wiki` / `make stage61-wiki-check`などの生成・検査
- テスト、ROMのhash・byte照合、ビルド、エミュレータ実行
- generator、実装source、config、report、Git履歴、設計ログの追加調査
- 回答に不要な全ファイル走査や証拠の再検証

Wikiに答えがない、または記述が矛盾する場合は、不足している点とWikiだけから言える範囲を明示します。閲覧依頼の途中で勝手に検査へ進みません。ユーザーが再生成、検査、修正、または実装根拠の確認を明示的に依頼した場合だけ、閲覧とは別の保守作業として実行します。

## 読む順番

- Codexの検索手順: [CODEX_INDEX.md](CODEX_INDEX.md)
- マップ・ストーリー順・現在地ごとの解禁: [STORY_PROGRESSION.md](STORY_PROGRESSION.md)
- ジムリーダー・四天王・主要NPCの手持ちと技: [MAJOR_BATTLES.md](MAJOR_BATTLES.md)
- 伝説・幻・UB・パラドックス固定捕獲の場所・条件・遭遇時技: [LEGENDARY_ENCOUNTERS.md](LEGENDARY_ENCOUNTERS.md)
- ポケモンの入手・能力・特性・全習得技: [POKEMON_INDEX.md](POKEMON_INDEX.md)
- 主要アイテムの入手: [ITEM_GUIDE.md](ITEM_GUIDE.md)
- 全アイテム索引: [ITEM_INDEX.md](ITEM_INDEX.md)
- 全技: [MOVE_INDEX.md](MOVE_INDEX.md)
- 全特性: [ABILITY_INDEX.md](ABILITY_INDEX.md)
- タイプ相性: [TYPE_CHART.md](TYPE_CHART.md)
- 通常野生・生態オーバーレイ: [WILD_ENCOUNTERS.md](WILD_ENCOUNTERS.md)
- 入手方法・解禁条件の用語集: [GLOSSARY.md](GLOSSARY.md)
- 証拠レベルと既知制約: [RUNTIME_LIMITATIONS.md](RUNTIME_LIMITATIONS.md)

## 情報の信頼度

- `EXACT_ROM`: 現行ROMから直接抽出・参照整合を検査。
- `INHERITED_INTEGRATED`: 以前のstageで統合・検証済みの正本をStage61が継承。
- `DEFERRED_AUDIT`: 現行候補ROMでの全経路手動走破は未完了。

取得場所が複数ある場合、各ポケモンページは現ROMの通常野生・生態オーバーレイ、Raid、基本取得経路を併記します。`VEGA_EXISTING` itemなど精密場所が未抽出の情報は、推測で補いません。

## 保守専用の再生成・検査（閲覧時は実行禁止）

以下はWikiを更新する担当者向けです。通常の閲覧、プレイ質問、Wiki検索では絶対に実行しません。ユーザーから再生成・検査・修正を明示的に依頼された時だけ使います。

```bash
make stage61-wiki
make stage61-wiki-check
```

生成物は時刻を含まず、同じ入力から同じbyteになります。機械可読の完全データは `data/` 内のJSON/JSONLです。
