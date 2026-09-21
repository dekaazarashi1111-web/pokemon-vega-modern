# 汎用Zの実行時分類監査

[Wiki入口](README.md) / [Z一覧](Z_MOVE_INDEX.md)

候補SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38`。技の元分類、条件付きの変化、候補署名を区別します。

## 分岐別件数

| 分類規則 | 全技行数 |
| --- | --- |
| CANDIDATE_BASE_SPLIT | 783 |
| SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT | 1 |
| STATUS_SENTINEL_NOT_DAMAGE_SPLIT | 275 |
| STAT_STAGE_COMPARISON | 2 |
| TERA_CONDITIONAL_STAT_COMPARISON | 2 |

シェルアームズはZ callerのbank引数が同じため相手比較を使いません。フォトンゲイザー等は能力段階適用後を比較し、同値なら特殊です。Tera条件付きの技は非Tera時に元分類へ戻ります。

| 技 | 規則 | 可能な分類 | 候補Z変換先ID |
| --- | --- | --- | --- |
| [733](moves/733.md) | STAT_STAGE_COMPARISON | &#91;0,1&#93; | &#91;864,865&#93; |
| [788](moves/788.md) | SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT | &#91;1&#93; | &#91;845&#93; |
| [889](moves/889.md) | STAT_STAGE_COMPARISON | &#91;0,1&#93; | &#91;&#93; |
| [1037](moves/1037.md) | TERA_CONDITIONAL_STAT_COMPARISON | &#91;0,1&#93; | &#91;838,839&#93; |
| [1050](moves/1050.md) | TERA_CONDITIONAL_STAT_COMPARISON | &#91;0,1&#93; | &#91;838,839&#93; |

## 短いtable署名の扱い

2技+終端の6byteを2byte境界で検索し、候補内の4byte境界pointer値を別に記録します。pointer値はcallgraphや実行済みの証明ではありません。

```json
{
  "candidate": {
    "crc32": "CC068B4A",
    "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
    "size": 33554432
  },
  "limit_ja": "候補table署名とaligned pointer値を照合するが、命令の逆アセンブルによる全caller同定や全modeのnative受入へ昇格しない。",
  "new_native_runs": 0,
  "old_move_split_enabled_in_locked_inputs": false,
  "physicality_binding": {
    "candidate_move_ids": [
      733,
      889
    ],
    "candidate_native_acceptance": "DEFERRED_AUDIT",
    "compiled_consumer_entry_binding": "DEFERRED_AUDIT",
    "evidence": "EXACT_CANDIDATE_ROM",
    "matches": [],
    "pointer_values_are_not_callgraph_proof": true,
    "signature_sha256": "03bf3b8653d8da52410c6fd510d69c11c2d77168e315618538f9942660171d49",
    "signature_size": 6,
    "status": "NO_CANDIDATE_BYTE_MATCH"
  },
  "physicality_move_keys": [
    "MOVE_KEY_PHOTONGEYSER",
    "MOVE_KEY_LIGHT_THAT_BURNS_THE_SKY"
  ],
  "physicality_source": {
    "blob_sha": "efadafd029731238469d204dbb0705a53a46efcd",
    "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "file_sha256": "1506b69f4a524d21432d670e0c4f21e2a45d102edf06970ec994c11fb03fba8c",
    "path": "assembly/data/move_tables.s",
    "start_line": 1229,
    "text": "gMovesThatChangePhysicality:\n.hword MOVE_PHOTONGEYSER\n.hword MOVE_LIGHT_THAT_BURNS_THE_SKY\n.hword MOVE_TABLES_TERMIN\n"
  },
  "records": 1063,
  "rule_counts": {
    "CANDIDATE_BASE_SPLIT": 783,
    "SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT": 1,
    "STATUS_SENTINEL_NOT_DAMAGE_SPLIT": 275,
    "STAT_STAGE_COMPARISON": 2,
    "TERA_CONDITIONAL_STAT_COMPARISON": 2
  },
  "schema_version": 1,
  "source_proofs": [
    {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 1529,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "558c9a85d067e984c96bf83fb0c652a58df3b0b5fbf63620e4ea694195458ed3",
      "path": "src/battle_util.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 1498,
      "symbol": "CalcMoveSplit",
      "unit_sha256": "00c993929b4add1eabbabbd5b0143529d62fce724d6a4a3d3fa9c383b3ce92ba"
    },
    {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 203,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "578ff365e1b8695303ee62fdc27745d537f1c3d5682053c0b6376a989d0c67b3",
      "path": "src/set_z_effect.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 190,
      "symbol": "GetTypeBasedZMove",
      "unit_sha256": "feaab49200ce21e4fa53d19e16d2ba59051f88c5aeb2a1e3ea0156f68b5cd8c7"
    }
  ]
}
```
