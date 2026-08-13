# Symbolic content workspace

`content/**` は数値Species/Move/Item IDを持たない実装正本である。`*_key` は `manifests/**` または同じcontent catalogのsymbolic keyへ解決する。V2受領CSVはreview入力であり、`tools/content/v2_normalize.py` の型・form・意味重複・参照正規化を通すまで直接生成入力にしない。

```bash
python3 scripts/build_content_schema.py build
python3 scripts/build_content_schema.py check
python3 scripts/build_content_schema.py dry-run
python3 scripts/build_content_schema.py emit --resolution path/to/id_resolution.json
```

`dry-run` はlogical mapを許可し、未bindingをreportする。`emit` は全symbolic keyとphysical mapが解決しなければactionable errorで停止する。T11 crosswalkの実bindingとROM emissionはT13が所有するため、T12時点のresolution fixtureは意図的に存在しない。

Kantoは `KANTO_EARLY_ACCESS`、8認定章、`VEGA_HALL_OF_FAME`、`KANTO_LEAGUE`、`KANTO_LEAGUE_CLEAR` を別phaseにする。Lv.68〜100は動的scaleしない任意高難度curveで、早期rowには推奨level、警告、無料帰還safe routeを必須とする。

新規eventは `SIMPLE_EVENT` を既定とし、標準message/list/Yes-No、condition、flag、reward、通常battle、warpだけを使う。専用UI/cutscene/minigame/mapをschema validatorが拒否する。
