# Codex用 Stage61 Wiki索引

プレイ中の閲覧質問では、このWikiだけを読み、生成・検査・ROM照合・実装調査へ脱線しません。`make stage61-wiki`、`make stage61-wiki-check`、テスト、ROM hash計算、generator・source・config・report・Git履歴の調査は絶対に実行しません。ユーザーが再生成、検査、修正、実装根拠の確認を明示的に依頼した場合だけ、別の保守作業として行います。

1. 出現場所・条件は [WILD_ENCOUNTERS.md](WILD_ENCOUNTERS.md) 内で場所名を検索する。通常野生、生態オーバーレイ、Raidの順に該当箇所だけ読む。
2. 名前・key・IDは `docs/wiki/stage61/data/search_index.jsonl` で検索する。
3. `page` で示されたMarkdownだけを読む。
4. Wikiに答えがない、または記述が矛盾する場合は、その不足を明示して回答を止める。閲覧依頼の最中にWiki外の検査や実装調査を勝手に始めない。

```bash
rg 'リープン|SPECIES_KEY_VEGA_001' docs/wiki/stage61/data/search_index.jsonl
rg 'マスターボール|ITEM_KEY_MASTER_BALL' docs/wiki/stage61/data/search_index.jsonl
```

現行ROM SHA-256: `734541807df91ca6f82211b57e0a56e6af6c1c70ec46b9f89cd6a89b3f701f3b`。新ROMへのWiki更新をユーザーから明示的に依頼された保守作業では、再生成後に一致確認を行います。通常の閲覧質問では実行しません。
