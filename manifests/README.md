# Manifests

これらのCSVは、安定IDとトーホク／カントー二地方コンテンツの実装正本である。生成コードはsymbolic keyからこれらを解決し、生成物を手編集しない。

`design/imported/**` はreview入力であり正本ではない。V2データはT12で型・フォーム・重複・参照を正規化した後にだけ昇格する。

Run:

```bash
python3 scripts/validate_manifests.py
```

bootstrap中はheaderのみの空ファイルを許容し、各タスクで段階的に埋める。
