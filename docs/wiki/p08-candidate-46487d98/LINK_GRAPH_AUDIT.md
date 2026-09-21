# Z関連入口のcompiled構造graph

[Wiki入口](README.md) / [Z split監査](RUNTIME_Z_AUDIT.md)

保存metadataの3入口から到達し得るThumb-1命令を有界に追う。条件分岐は両側、BL先関数へは入らず、BX/POP PC/PC書換/未対応命令で止まる。source同一性・全関数範囲・実行済みは主張しない。

```json
{
  "link_graph_direct_bl_sites": 4,
  "link_graph_limited_seeds": 0,
  "link_graph_nodes": 32,
  "link_graph_overlap_sites": 0,
  "link_graph_seeds": 3,
  "missing_named_link_symbols": 16
}
```

## 保存metadataで名前が確認できた入口

| 入口名 | 現候補address | 到達候補命令 | 直接BL | 停止理由 |
| --- | --- | --- | --- | --- |
| HandleInputChooseMove | 0x9116f90 | 2 | 0 | {"INDIRECT_PC_TRANSFER":1} |
| VegaBattlePolicyCanZ | 0x9126bb4 | 16 | 2 | {"POP_PC_RETURN_OR_INDIRECT":1} |
| VegaBattlePolicyMarkZ | 0x9126be0 | 14 | 2 | {"POP_PC_RETURN_OR_INDIRECT":1} |

## 未保存link表

全offsetsは13,131 symbols、SHA-256 `f9851fb5eea759573d1e4e0b923e69c34c85ddb171fb03321f5b7ce380870523`。linked.oは5,733,212 bytes、SHA-256 `52bbd57a7d2649164c4706ee45dc17ef1f8357862d8dbd79bdcd439c2b0a36fb`。今回調べた保存先に実体なし。再コンパイルや近傍prologueからの命名はしていません。

[各命令・BL先・入力hash・未解決辺](data/link_graph_audit.json)
