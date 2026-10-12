# 機械可読データと再生成

**固定レビュー版 R0** — SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[入口](README.md) · [証拠区分と制限](LIMITATIONS.md) · [提案記入](OWNER_PROPOSALS.md)

ROM数値・文字列は旧候補読取＋5段階非変更範囲の継承。全機能の新native受入ではありません。

[data/index.json](data/index.json) に入力HEAD・候補・全入力hash・意味hash・出力hashを固定。[種族要約](data/species.jsonl)、[技逆引き](data/moves.jsonl)、[特性逆引き](data/abilities.jsonl)、[機構](data/mechanics.json)、[現役経路参照](data/active_sources.json) を提供します。全経路・条件の元JSONは候補固定のIssue19ディレクトリに保持し、R0 manifestでbyteを束縛します。

```bash
python3 -B scripts/pr16_wiki_r0_build.py check
```

checkは入力・全生成byte・ファイル集合・リンク・mtimeを照合し、書き込みません。buildは別R0出力だけを生成し、同一内容の再書込みをしません。公開後のR0を調整版へ上書きせず次のreview revisionを別途作ります。
