# Codex用 Stage61 Wiki索引

プレイ中の質問では、原則としてスクリプトやgeneratorを調べる前にこのWikiを使います。

1. 名前・key・IDを `docs/wiki/stage61/data/search_index.jsonl` で検索する。
2. `page` で示されたMarkdownだけを読む。
3. 精密な再検証が必要な場合だけ `data/*.jsonl` と [証拠・制約](RUNTIME_LIMITATIONS.md) を確認する。

```bash
rg 'リープン|SPECIES_KEY_VEGA_001' docs/wiki/stage61/data/search_index.jsonl
rg 'マスターボール|ITEM_KEY_MASTER_BALL' docs/wiki/stage61/data/search_index.jsonl
```

現行ROM SHA-256: `44e951e20e7985b6f4480a04ff997cc77e6305dd0945eb90cfed7e3c6d85ae4e`。ROMが変わった場合は `make stage61-wiki` で再生成し、`make stage61-wiki-check` を通すまで旧Wikiを現行扱いしません。
