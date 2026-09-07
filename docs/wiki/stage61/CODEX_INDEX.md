# Codex用 Stage61 Wiki索引

プレイ中の閲覧質問では、このWikiだけを読み、生成・検査・ROM照合・実装調査へ脱線しません。`make stage61-wiki`、`make stage61-wiki-check`、テスト、ROM hash計算、generator・source・config・report・Git履歴の調査は絶対に実行しません。ユーザーが再生成、検査、修正、実装根拠の確認を明示的に依頼した場合だけ、別の保守作業として行います。

1. 「今バッジ何個」「次はどこ」「今の到達範囲でおすすめ」は [STORY_PROGRESSION.md](STORY_PROGRESSION.md) で区間を確定する。バッジ数が曖昧なら、直前のボス名・現在地・所持HMも照合する。
2. ジムリーダー、四天王、ライバル、D・H団などの手持ち・技は [MAJOR_BATTLES.md](MAJOR_BATTLES.md) でbattle IDまたは名前を検索する。
3. 伝説・幻・UB・パラドックスの固定捕獲は [LEGENDARY_ENCOUNTERS.md](LEGENDARY_ENCOUNTERS.md) で名前を検索する。場所、解禁、レベル、遭遇時技、証拠状態を一緒に読む。
4. 出現場所・条件は [WILD_ENCOUNTERS.md](WILD_ENCOUNTERS.md) 内で場所名を検索する。通常野生、生態オーバーレイ、Raidの順に該当箇所だけ読む。
5. 名前・key・IDは `docs/wiki/stage61/data/search_index.jsonl` で検索し、`page`で示されたMarkdownだけを読む。
6. Wikiに答えがない、または記述が矛盾する場合は、その不足を明示して回答を止める。閲覧依頼の最中にWiki外の検査や実装調査を勝手に始めない。

## 進行地点つき質問の解釈

- 「2個目のジムに勝ったところ」なら進行ガイドのS02を現在区間とする。
- 候補ポケモンは、それ以前の区間＋S02で既に通過したとユーザーが述べた場所に限定して探す。
- 次のボス対策ならS02の主要戦リンクと、次のS03へ進むための道順を読む。
- カントー早期渡航は解禁済みでも固定高レベルの任意ルートなので、通常の本編おすすめへ自動的に混ぜない。

```bash
rg 'リープン|SPECIES_KEY_VEGA_001' docs/wiki/stage61/data/search_index.jsonl
rg 'マスターボール|ITEM_KEY_MASTER_BALL' docs/wiki/stage61/data/search_index.jsonl
rg '2個目のジム|VEGA_BADGE_2|ナギナタ' docs/wiki/stage61/data/search_index.jsonl
rg 'ミュウツー|CHAMPION_GINNO' docs/wiki/stage61/data/search_index.jsonl
```

Stage61固定スナップショットSHA-256: `734541807df91ca6f82211b57e0a56e6af6c1c70ec46b9f89cd6a89b3f701f3b`。新ROMへのWiki更新をユーザーから明示的に依頼された保守作業では、別versionのWikiとして再生成後に一致確認を行います。通常の閲覧質問では実行しません。
