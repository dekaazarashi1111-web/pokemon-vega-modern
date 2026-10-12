# 承認案との結合入口

**固定レビュー版 R0** — SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[入口](README.md) · [証拠区分と制限](LIMITATIONS.md) · [提案記入](OWNER_PROPOSALS.md)

ROM数値・文字列は旧候補読取＋5段階非変更範囲の継承。全機能の新native受入ではありません。

この版を基準に、対象ID/stable key/form、現在値、提案後の値、理由、対象ページ、R0の意味hashを指定できます。提出や記入は実装承認ではありません。

`owner_approved_overlay=[]`、承認済みbatch0を保持。次の情報を所有者の明示指示から記録し、依存条件と保存互換を確認してから限定実装します。

```json
{"reference_revision":"R0","reference_semantic_sha256":"data/index.jsonを参照","target_id":null,"stable_key":null,"form_key":null,"before":null,"after":null,"rationale":null,"approval_status":"NOT_APPROVED"}
```

自動の役割タグから採用案や対象種を創作しません。所有者の案待ちだけで後続の保存基盤作業を止めません。
