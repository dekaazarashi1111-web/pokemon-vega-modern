# Manifests

これらのCSVは、安定IDとトーホク／カントー二地方コンテンツの実装正本である。生成コードはsymbolic keyからこれらを解決し、生成物を手編集しない。

`design/imported/**` はreview入力であり正本ではない。V2データはT12で型・フォーム・重複・参照を正規化した後にだけ昇格する。

Run:

```bash
python3 scripts/validate_manifests.py
```

bootstrap中はheaderのみの空ファイルを許容し、各タスクで段階的に埋める。

`move_ids.csv` はT04の `scripts/build_move_port.py` が生成するMove ID正本で、0〜511はVega固定、512〜1062はCFRU-JP appendです。手編集せず、`make moves` / `make moves-check` と `scripts/validate_manifests.py` で更新・検査します。
