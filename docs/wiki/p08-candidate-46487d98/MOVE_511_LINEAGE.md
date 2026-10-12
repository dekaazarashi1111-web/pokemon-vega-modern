# 技511の凍結互換由来

[技511](moves/511.md) / [技1](moves/1.md) / [effect由来](EFFECT_ORIGIN_AUDIT.md)

同じ表示名でも511を1へ統合しません。flagsとZ威力も異なり、MOVE_POUNDのaliasは1のみです。旧effect pointerは保存modelの由来情報であり、現候補の実行先証明ではありません。

```json
{
  "candidate_compiled_handler_execution": "DEFERRED_AUDIT",
  "candidate_fields": {
    "accuracy": 100,
    "effect": 0,
    "flags": 51,
    "power": 40,
    "pp": 35,
    "priority": 0,
    "secondary": 0,
    "split": 0,
    "target": 0,
    "type": 0,
    "z_move_effect": 0,
    "z_move_power": 0
  },
  "candidate_row_sha256": "2d1d6fc18627db2d00dbb3bd6173d7029bf0a908518834f8b4f41bd692a9abcb",
  "canonical_pound_alias_does_not_target_511": true,
  "canonical_pound_id": 1,
  "different_fields_from_canonical_pound": [
    "flags",
    "z_move_power"
  ],
  "full_handler_lineage": "DEFERRED_AUDIT",
  "move_id": 511,
  "move_key": "MOVE_KEY_VEGA_511",
  "native_acceptance": "DEFERRED_AUDIT",
  "policy_binding": {
    "path": "config/move_port.json",
    "sha256": "ded26093f0e5b67443e11ec20691f9a8887e50bd3f693439e311f9a7aac32d72",
    "size": 3752
  },
  "reason_ja": "511は凍結Vega行を保持する互換重複。MOVE_POUNDは1だけへaliasする。元modelのVEGA_ROM_POINTERを記録するが、現候補でその旧pointerを実行するとは主張しない。",
  "saved_original_effect_mapping": {
    "id": 0,
    "mapping_kind": "VEGA_ROM_POINTER",
    "script_symbol": null,
    "symbol": null,
    "vega_pointer": 136030396
  },
  "source_kind": "FROZEN_VEGA_ROW",
  "source_model": {
    "member": "generated/engine/moves/move_port.json",
    "sha256": "0c1e38aac41eb6b96a5fbeb695c0a60bcc15b92e6b5dffb3490e346fa260f442",
    "size": 1252828
  },
  "source_proofs": [
    {
      "end_line": 903,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "3880b373b32bbcd2340243f6aebc1927d1a42b84ca264a45468acdcc8993c0cd",
      "path": "scripts/build_move_port.py",
      "start_line": 501,
      "symbol": "build_move_model",
      "unit_sha256": "a7b7f095ffc4fe7a3a89d2d24a6474782dcfb8a666794b5d0ab2935dd21b3382"
    },
    {
      "end_line": 430,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "3880b373b32bbcd2340243f6aebc1927d1a42b84ca264a45468acdcc8993c0cd",
      "path": "scripts/build_move_port.py",
      "start_line": 413,
      "symbol": "_vega_battle",
      "unit_sha256": "9b8c84b7cdc83cf822351288ca0228be80cc0a67ba7d6877d32c5365634e8782"
    },
    {
      "end_line": 1029,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "3880b373b32bbcd2340243f6aebc1927d1a42b84ca264a45468acdcc8993c0cd",
      "path": "scripts/build_move_port.py",
      "start_line": 906,
      "symbol": "validate_move_model",
      "unit_sha256": "f2fce211fc290c08fc3bd1618577f9f10fb3f99bdf64541afc47606a91b9950b"
    }
  ],
  "source_row_sha256": "1138e2469dc42d18977c66f170c28db0b328ecdfe36098dedc326bc4a1a81516",
  "status": "FROZEN_VEGA_COMPAT_DUPLICATE_BOUND"
}
```
