# メガ登録行の監査

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38`。

[Wiki入口](README.md) / [正逆対応済みメガ](MEGA_INDEX.md)

method254 + itemの存在だけで、別メガ形態や正逆対応を受入しません。次の自己参照行は候補に存在する事実を保持しつつ、メガ一覧・メガ資産一覧・形態数から除外します。consumerの実挙動は未監査です。

| base / target | raw item | 区分 | 逆変換 | native |
| --- | --- | --- | --- | --- |
| [157: リザードン](pokemon/157.md) | [534: わざマシン15](items/534.md) | LEGACY_SELF_REFERENCE_WITHOUT_REVERSE | False | DEFERRED_AUDIT |

```json
{
  "forward_reverse_verified": 76,
  "game_data_changed": false,
  "raw_rows": 77,
  "unverified_legacy_rows": 1
}
```

[raw監査データ](data/mega_mapping_anomalies.json) に元の登録・asset hashを保存します。
