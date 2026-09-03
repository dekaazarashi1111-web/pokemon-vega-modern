# Pokémon Vega Stage61 プレイWiki

現行Stage61 ROMに固定した、プレイヤー向け・Codex向けの参照資料です。

- ROM: `build/stages/61_critical_release_candidate.gba`
- SHA-256: `60b83b8c50e54c3af42daa23b9d82e96c1b769d816ce28ef8bfda1d5005aff0e`
- ポケモン: 1621 ID（内部・フォームを含む）
- 技: 1063 ID
- 特性: 312 ID
- アイテム: 999 ID

## 読む順番

- Codexの検索手順: [CODEX_INDEX.md](CODEX_INDEX.md)
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

## 再生成・検査

```bash
make stage61-wiki
make stage61-wiki-check
```

生成物は時刻を含まず、同じ入力から同じbyteになります。機械可読の完全データは `data/*.jsonl` です。
