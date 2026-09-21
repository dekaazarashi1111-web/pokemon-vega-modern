# 固定consumerと候補tableの対応

[Wiki入口](README.md) / [Z一覧](Z_MOVE_INDEX.md) / [隠れ特性一覧](HIDDEN_ABILITY_INDEX.md)

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38`。静的な対応付けであり、新規native受入ではありません。

## 汎用Zのtype・物理/特殊対応

専用クリスタルの条件不一致では汎用へfallbackしない。道具type一致は元技tableのtype。動的typeの変換と混同しない。候補独自のVegaBattlePolicyCanZ gateも先行する。

| type ID | 分類ID | 変換先 | stable key | 候補クリスタルID |
| --- | --- | --- | --- | --- |
| 0 | 0 | [838](moves/838.md) | MOVE_KEY_BREAKNECK_BLITZ_P | &#91;794&#93; |
| 0 | 1 | [839](moves/839.md) | MOVE_KEY_BREAKNECK_BLITZ_S | &#91;794&#93; |
| 1 | 0 | [840](moves/840.md) | MOVE_KEY_ALL_OUT_PUMMELING_P | &#91;795&#93; |
| 1 | 1 | [841](moves/841.md) | MOVE_KEY_ALL_OUT_PUMMELING_S | &#91;795&#93; |
| 2 | 0 | [842](moves/842.md) | MOVE_KEY_SUPERSONIC_SKYSTRIKE_P | &#91;796&#93; |
| 2 | 1 | [843](moves/843.md) | MOVE_KEY_SUPERSONIC_SKYSTRIKE_S | &#91;796&#93; |
| 3 | 0 | [844](moves/844.md) | MOVE_KEY_ACID_DOWNPOUR_P | &#91;797&#93; |
| 3 | 1 | [845](moves/845.md) | MOVE_KEY_ACID_DOWNPOUR_S | &#91;797&#93; |
| 4 | 0 | [846](moves/846.md) | MOVE_KEY_TECTONIC_RAGE_P | &#91;798&#93; |
| 4 | 1 | [847](moves/847.md) | MOVE_KEY_TECTONIC_RAGE_S | &#91;798&#93; |
| 5 | 0 | [848](moves/848.md) | MOVE_KEY_CONTINENTAL_CRUSH_P | &#91;799&#93; |
| 5 | 1 | [849](moves/849.md) | MOVE_KEY_CONTINENTAL_CRUSH_S | &#91;799&#93; |
| 6 | 0 | [850](moves/850.md) | MOVE_KEY_SAVAGE_SPIN_OUT_P | &#91;800&#93; |
| 6 | 1 | [851](moves/851.md) | MOVE_KEY_SAVAGE_SPIN_OUT_S | &#91;800&#93; |
| 7 | 0 | [852](moves/852.md) | MOVE_KEY_NEVER_ENDING_NIGHTMARE_P | &#91;801&#93; |
| 7 | 1 | [853](moves/853.md) | MOVE_KEY_NEVER_ENDING_NIGHTMARE_S | &#91;801&#93; |
| 8 | 0 | [854](moves/854.md) | MOVE_KEY_CORKSCREW_CRASH_P | &#91;802&#93; |
| 8 | 1 | [855](moves/855.md) | MOVE_KEY_CORKSCREW_CRASH_S | &#91;802&#93; |
| 10 | 0 | [856](moves/856.md) | MOVE_KEY_INFERNO_OVERDRIVE_P | &#91;803&#93; |
| 10 | 1 | [857](moves/857.md) | MOVE_KEY_INFERNO_OVERDRIVE_S | &#91;803&#93; |
| 11 | 0 | [858](moves/858.md) | MOVE_KEY_HYDRO_VORTEX_P | &#91;804&#93; |
| 11 | 1 | [859](moves/859.md) | MOVE_KEY_HYDRO_VORTEX_S | &#91;804&#93; |
| 12 | 0 | [860](moves/860.md) | MOVE_KEY_BLOOM_DOOM_P | &#91;805&#93; |
| 12 | 1 | [861](moves/861.md) | MOVE_KEY_BLOOM_DOOM_S | &#91;805&#93; |
| 13 | 0 | [862](moves/862.md) | MOVE_KEY_GIGAVOLT_HAVOC_P | &#91;806&#93; |
| 13 | 1 | [863](moves/863.md) | MOVE_KEY_GIGAVOLT_HAVOC_S | &#91;806&#93; |
| 14 | 0 | [864](moves/864.md) | MOVE_KEY_SHATTERED_PSYCHE_P | &#91;807&#93; |
| 14 | 1 | [865](moves/865.md) | MOVE_KEY_SHATTERED_PSYCHE_S | &#91;807&#93; |
| 15 | 0 | [866](moves/866.md) | MOVE_KEY_SUBZERO_SLAMMER_P | &#91;808&#93; |
| 15 | 1 | [867](moves/867.md) | MOVE_KEY_SUBZERO_SLAMMER_S | &#91;808&#93; |
| 16 | 0 | [868](moves/868.md) | MOVE_KEY_DEVASTATING_DRAKE_P | &#91;809&#93; |
| 16 | 1 | [869](moves/869.md) | MOVE_KEY_DEVASTATING_DRAKE_S | &#91;809&#93; |
| 17 | 0 | [870](moves/870.md) | MOVE_KEY_BLACK_HOLE_ECLIPSE_P | &#91;810&#93; |
| 17 | 1 | [871](moves/871.md) | MOVE_KEY_BLACK_HOLE_ECLIPSE_S | &#91;810&#93; |
| 23 | 0 | [872](moves/872.md) | MOVE_KEY_TWINKLE_TACKLE_P | &#91;811&#93; |
| 23 | 1 | [873](moves/873.md) | MOVE_KEY_TWINKLE_TACKLE_S | &#91;811&#93; |

## Z変化技の追加効果

0xFFFFは元技を維持する返り値であり、技ID65535へのリンクではありません。Max/G-Max共用欄の数値をこの表へ混ぜません。

| effect ID | key | 効果 |
| --- | --- | --- |
| 0 | Z_EFFECT_NONE | 追加効果なし |
| 1 | Z_EFFECT_RESET_STATS | 使用者の下がった能力段階を標準値へ戻す |
| 2 | Z_EFFECT_ALL_STATS_UP_1 | 使用者の攻撃・防御・特攻・特防・素早さを各1段階上げる（命中・回避を除く） |
| 3 | Z_EFFECT_BOOST_CRITS | 使用者へきあいだめ状態を付与 |
| 4 | Z_EFFECT_FOLLOW_ME | 使用者をこのターンの攻撃誘導先に設定 |
| 5 | Z_EFFECT_CURSE | 使用者がゴーストタイプならHP全回復、それ以外は攻撃1段階上昇 |
| 6 | Z_EFFECT_RECOVER_HP | 使用者のHPを最大値まで回復 |
| 7 | Z_EFFECT_RESTORE_REPLACEMENT_HP | 次に交代で入る味方を回復する予約を設定 |
| 8 | Z_EFFECT_ATK_UP_1 | 使用者の攻撃を1段階上げる |
| 9 | Z_EFFECT_DEF_UP_1 | 使用者の防御を1段階上げる |
| 10 | Z_EFFECT_SPD_UP_1 | 使用者の素早さを1段階上げる |
| 11 | Z_EFFECT_SPATK_UP_1 | 使用者の特攻を1段階上げる |
| 12 | Z_EFFECT_SPDEF_UP_1 | 使用者の特防を1段階上げる |
| 13 | Z_EFFECT_ACC_UP_1 | 使用者の命中を1段階上げる |
| 14 | Z_EFFECT_EVSN_UP_1 | 使用者の回避を1段階上げる |
| 15 | Z_EFFECT_ATK_UP_2 | 使用者の攻撃を2段階上げる |
| 16 | Z_EFFECT_DEF_UP_2 | 使用者の防御を2段階上げる |
| 17 | Z_EFFECT_SPD_UP_2 | 使用者の素早さを2段階上げる |
| 18 | Z_EFFECT_SPATK_UP_2 | 使用者の特攻を2段階上げる |
| 19 | Z_EFFECT_SPDEF_UP_2 | 使用者の特防を2段階上げる |
| 20 | Z_EFFECT_ACC_UP_2 | 使用者の命中を2段階上げる |
| 21 | Z_EFFECT_EVSN_UP_2 | 使用者の回避を2段階上げる |
| 22 | Z_EFFECT_ATK_UP_3 | 使用者の攻撃を3段階上げる |
| 23 | Z_EFFECT_DEF_UP_3 | 使用者の防御を3段階上げる |
| 24 | Z_EFFECT_SPD_UP_3 | 使用者の素早さを3段階上げる |
| 25 | Z_EFFECT_SPATK_UP_3 | 使用者の特攻を3段階上げる |
| 26 | Z_EFFECT_SPDEF_UP_3 | 使用者の特防を3段階上げる |
| 27 | Z_EFFECT_ACC_UP_3 | 使用者の命中を3段階上げる |
| 28 | Z_EFFECT_EVSN_UP_3 | 使用者の回避を3段階上げる |

## 夢特性の条件付きsource規則

初回入手経路と、既に隠れ特性の親を持つ場合の継承を分離します。上流のraid生成処理と本プロジェクトのcollection poolは同じ入口とは限りません。

```json
{
  "breeding": {
    "consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 650,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "3533614a49b2025a299c6446b6fb303b2eeccd76dfc102dc8197097a1023fe5a",
      "path": "src/daycare.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 627,
      "symbol": "DetermineEggAbility",
      "unit_sha256": "99437dc3de3725af26be47fb75082c3bd3e4107e3591e02b31c6cf7fe2882ff8"
    },
    "current_project_daycare_caller": "DEFERRED_AUDIT",
    "ditto_mother_uses_father": true,
    "is_first_supply": false,
    "percent": 60,
    "requires_hidden_parent": true,
    "status": "UPSTREAM_CONDITIONAL_INHERITANCE"
  },
  "dexnav": {
    "consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 1435,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "8049836072f5f3469cb134ade1d864ab0c2241f6162930ba76028d8b3d1dbd17",
      "path": "src/dexnav.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 1362,
      "symbol": "DexNavGenerateHiddenAbility",
      "unit_sha256": "b196642f3804ee477b009a2c5bcd62853b904871d5296b2d488761935c0868dc"
    },
    "current_project_entry_and_config": "DEFERRED_AUDIT",
    "requires_previously_caught": true,
    "status": "UPSTREAM_SEARCH_LEVEL_AND_CAUGHT_GATED"
  },
  "patch": {
    "cancel_and_no_effect_do_not_consume": true,
    "compiled_patch_and_species_accessors": "DEFERRED_AUDIT",
    "confirm_consumes_one": true,
    "confirm_sets_hidden_flag": true,
    "current_ability_compared_not_only_hidden_flag": true,
    "item_supply": {
      "bp_shop_cost": 32,
      "candidate_field_callback_binding": "DEFERRED_AUDIT",
      "eighth_badge_flag": "0x827",
      "exact_hold_effect_parameter": 1,
      "field_callback_declaration": "FieldUseFunc_AbilityCapsule",
      "input_runtime_binding_label_not_current_acceptance": "T06_RUNTIME_BIND_PENDING",
      "item_id": 943,
      "item_key": "ITEM_KEY_ABILITY_PATCH",
      "normal_unlock": "VEGA_HALL_OF_FAME_OR_EIGHTH_BADGE_FLAG",
      "quantity": 1,
      "rom_price_field": 20000,
      "secondary_source_declared_not_caller_proof": "RAID_REWARD",
      "shop_to_bag_to_patch_native": "DEFERRED_AUDIT",
      "source_proofs": [
        {
          "end_line": 498,
          "evidence": "GENERATED_CANONICAL",
          "file_sha256": "14c27f895b9ae8d1b3d9d077ce49999fc17a1422a83e8ddb87657c66ebab06d3",
          "path": "overlays/collection_supply_v1/collection_supply_v1.c",
          "start_line": 452,
          "symbol": "unlock_satisfied",
          "unit_sha256": "9ee3ea108f07089d544cec16ac10369cb1fda597ef948fb353c1f95c2b979874"
        },
        {
          "end_line": 582,
          "evidence": "GENERATED_CANONICAL",
          "file_sha256": "14c27f895b9ae8d1b3d9d077ce49999fc17a1422a83e8ddb87657c66ebab06d3",
          "path": "overlays/collection_supply_v1/collection_supply_v1.c",
          "start_line": 573,
          "symbol": "source_currency",
          "unit_sha256": "067bd5b3f7573345df8ee9ec2b23779379457c3e157a285e52b4af20c866b912"
        },
        {
          "end_line": 834,
          "evidence": "GENERATED_CANONICAL",
          "file_sha256": "14c27f895b9ae8d1b3d9d077ce49999fc17a1422a83e8ddb87657c66ebab06d3",
          "path": "overlays/collection_supply_v1/collection_supply_v1.c",
          "start_line": 758,
          "symbol": "acquire_item",
          "unit_sha256": "ff30dfe35edf7a8cb8c06b6cb2812647517b26d7891e617a1bfd1ac5f6bf48ab"
        },
        {
          "end_line": 1334,
          "evidence": "GENERATED_CANONICAL",
          "file_sha256": "14c27f895b9ae8d1b3d9d077ce49999fc17a1422a83e8ddb87657c66ebab06d3",
          "path": "overlays/collection_supply_v1/collection_supply_v1.c",
          "start_line": 1291,
          "symbol": "eligible_at",
          "unit_sha256": "8d545521734bbbabe59a3997e0e2923ed31f3e520e3b69e485f53ac0efb83fe4"
        }
      ],
      "test_mode_excluded": true,
      "unlock_name": "HIDDEN_ABILITY_DEXNAV_UNLOCKED"
    },
    "new_native_runs": 0,
    "source_proofs": [
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2467,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2463,
        "symbol": "FieldUseFunc_AbilityCapsule",
        "unit_sha256": "1de2bdb5cb0b7907edfc16329ed0ff3d18eed9fb1bf17ef234b19015927eaa3d"
      },
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2493,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2471,
        "symbol": "ItemUseCB_AbilityCapsule",
        "unit_sha256": "7fc5915d3a58de246c5113115fa3eaf4d6edf281a229bcb43edf7b09b27ffba4"
      },
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2535,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2495,
        "symbol": "GetAbilityCapsuleNewAbility",
        "unit_sha256": "5c5b3dc7b4b842a8b7932e4797098013b2a0db219ebc240b05a3904fe7407b9d"
      },
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2544,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2537,
        "symbol": "Task_OfferAbilityChange",
        "unit_sha256": "e074b4cb30aaa73a54981503b94a912de7699f5d8b9e233e1f2bf308969d8661"
      },
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2560,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2546,
        "symbol": "Task_HandleAbilityChangeYesNoInput",
        "unit_sha256": "704fc029a44aa2442562a0d53205c14c8e686bfffeb04daa904a8974f6986a61"
      },
      {
        "candidate_native_acceptance": "DEFERRED_AUDIT",
        "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        "end_line": 2588,
        "evidence": "GENERATED_CANONICAL",
        "file_sha256": "6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59",
        "path": "src/party_menu.c",
        "repository": "kapibarasan000/CFRU-JP",
        "start_line": 2562,
        "symbol": "Task_ChangeAbility",
        "unit_sha256": "b20ac3a5d4ef4b15eb9e68081e566f3573dd1ad1d3fca903be5235469924752d"
      }
    ],
    "status": "SOURCE_CONDITION_JOINED_TO_CANDIDATE_SLOTS",
    "unbound_extra_conditions_disabled_by_project_profile": true
  },
  "raid": {
    "collection_pool_does_not_prove_this_caller": true,
    "consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 428,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "a2e57daf75961a550faa034e7f668443b519787d289044e5e0a32d3c933a6249",
      "path": "src/wild_encounter.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 381,
      "symbol": "sp117_CreateRaidMon",
      "unit_sha256": "2181a29dbcca1262e9238ed73ed118c2508ad394f1fd93aae670b853bbd61833"
    },
    "forced_hidden_or_random_all_percent": 50,
    "species_policy_consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 2122,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "165a51cf016a690a17c8fa981cb65db67e1ea853ad0a92a6ec374bbd6843c490",
      "path": "src/dynamax.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 2103,
      "symbol": "GetRaidSpeciesAbilityNum",
      "unit_sha256": "1c05afa062d0856a9c6941ec4f0fff9eca2fdc11e7ad74c727efef16ab78ee5e"
    },
    "status": "UPSTREAM_RAID_TABLE_POLICY_NOT_COLLECTION_POOL_POLICY"
  },
  "script_gift": {
    "consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 3936,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "ac81e3a9a8c7a58105573e6ee2abf62a4b22922e88c6c7d3a1ecdc6c9431e824",
      "path": "src/build_pokemon.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 3844,
      "symbol": "ScriptGiveMon",
      "unit_sha256": "fc06ba1ffb91ef0c8759fe2becfc3bb24a4d406f84c42492b95469e5e8499e5f"
    },
    "species_specific_flag_setter": "SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES",
    "status": "UPSTREAM_FLAG_GATED_AND_FLAG_CLEARED"
  },
  "wild": {
    "consumer": {
      "candidate_native_acceptance": "DEFERRED_AUDIT",
      "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
      "end_line": 379,
      "evidence": "GENERATED_CANONICAL",
      "file_sha256": "a2e57daf75961a550faa034e7f668443b519787d289044e5e0a32d3c933a6249",
      "path": "src/wild_encounter.c",
      "repository": "kapibarasan000/CFRU-JP",
      "start_line": 289,
      "symbol": "CreateWildMon",
      "unit_sha256": "3836954ce303e44723007ac772cd808fd0ed5dd13be9a62f9dfb2eb3cf8813a8"
    },
    "flag_number_in_upstream_not_project_assignment": 2319,
    "flag_symbol": "FLAG_HIDDEN_ABILITY",
    "species_specific_flag_setter": "SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES",
    "status": "UPSTREAM_FLAG_GATED_NOT_UNIVERSAL_RATE"
  }
}
```

## 根拠と残件

```json
[
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
  },
  {
    "candidate_native_acceptance": "DEFERRED_AUDIT",
    "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "end_line": 227,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "578ff365e1b8695303ee62fdc27745d537f1c3d5682053c0b6376a989d0c67b3",
    "path": "src/set_z_effect.c",
    "repository": "kapibarasan000/CFRU-JP",
    "start_line": 205,
    "symbol": "GetSpecialZMove",
    "unit_sha256": "0801bb9c17bd4c205a11fc74ba1dd6b75a62a5f70c41aa0900a9ce7b2d6a50ba"
  },
  {
    "candidate_native_acceptance": "DEFERRED_AUDIT",
    "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "end_line": 306,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "578ff365e1b8695303ee62fdc27745d537f1c3d5682053c0b6376a989d0c67b3",
    "path": "src/set_z_effect.c",
    "repository": "kapibarasan000/CFRU-JP",
    "start_line": 259,
    "symbol": "CanUseZMove",
    "unit_sha256": "e1760477b18bad1660db676aab77f73286a6518e1860d21291b82301c78d4016"
  },
  {
    "candidate_native_acceptance": "DEFERRED_AUDIT",
    "commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "end_line": 188,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "578ff365e1b8695303ee62fdc27745d537f1c3d5682053c0b6376a989d0c67b3",
    "path": "src/set_z_effect.c",
    "repository": "kapibarasan000/CFRU-JP",
    "start_line": 67,
    "symbol": "SetZEffect",
    "unit_sha256": "4f38a10b358d59928ee74b3375bf90ed57ae3f158ed63565d491dcc180d69b02"
  },
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
    "end_line": 124,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "885c2ae9fa78d145eec1eca4333104b6fdd90a1d5afbbe191e0bc3398e740922",
    "path": "src/item.c",
    "repository": "kapibarasan000/CFRU-JP",
    "start_line": 121,
    "symbol": "IsTypeZCrystal",
    "unit_sha256": "0ba7c2c66a4a3f768985d07ce587b4b33fa0930be214e01c46004a3a2fdfdc84"
  }
]
```

```json
{
  "issue18_complete": false,
  "new_native_runs": 0,
  "remaining_work_ja": [
    "追加野生95行・collection配布18/Floette1・collection raid292を現候補level表の初期技source規則に結合済み。残りは全通常野生header/既存story配布、現compiled初期化caller・マクロ、生成後form変更/custom技。条件付き計算を実生成技受入にしない。",
    "汎用Zのsplit/候補表に加え保存metadataの3入口からThumb-1構造graphを抽出済み。残りはCanUseZMove/GetTypeBasedZMove/CalcMoveSplitの名前付きcallee結合・間接辺。既存offsets.ini/linked.oの固定hashはlink_graph_auditに記録。再build/nativeなしに名前を推測しない。",
    "夢特性パッチは全1671slotの適用条件とBP供給source/解禁を分類済み。残りは現候補のcompiled field callback・種族accessor・通常初回供給caller・育て屋の対応。source分類を実入手/使用受入にしない。",
    "T04全70アダプターのsource由来を分類済み。残りは未結合技[511]の由来、上流宣言技のlocal patch/全handler履歴、候補compiled dispatch対応。source分類をnative受入にしない。"
  ],
  "schema_version": 1,
  "summary": {
    "creation_declared_routes": 311,
    "creation_profile_species": 470,
    "creation_profile_states": {
      "SOURCE_RULE_APPLIED_TO_CANDIDATE_ROWS": 4776
    },
    "creation_profiles": 4776,
    "creation_route_kinds": {
      "COLLECTION_RAID": 292,
      "FIXED_GIFT": 4,
      "RESEARCH_EGG": 15
    },
    "effect_origin_records": 1063,
    "effect_origin_states": {
      "LOCKED_UPSTREAM_EFFECT_DECLARATION": 991,
      "MOVE_NONE_NOT_PLAYABLE": 1,
      "T04_SOURCE_ADAPTER_CLASSIFIED": 70,
      "UNRESOLVED_SOURCE_LINEAGE": 1
    },
    "generic_z_records": 1063,
    "generic_z_states": {
      "DAMAGE_MOVE_SOURCE_RULE": 633,
      "INTERNAL_Z_MAX_ROW_NOT_ORDINARY_BASE_MOVE": 156,
      "MOVE_NONE_NOT_A_BASE_MOVE": 1,
      "STATUS_MOVE_WITH_ADDITIONAL_EFFECT": 273
    },
    "hidden_patch_records": 1671,
    "hidden_patch_states": {
      "DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN": 847,
      "NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID": 57,
      "NO_HIDDEN_ABILITY_ASSIGNED": 767
    },
    "hidden_slot_records": 1671,
    "link_graph_direct_bl_sites": 4,
    "link_graph_limited_seeds": 0,
    "link_graph_nodes": 32,
    "link_graph_overlap_sites": 0,
    "link_graph_seeds": 3,
    "missing_named_link_symbols": 16,
    "physicality_candidate_table_matches": 1,
    "runtime_z_records": 1063,
    "runtime_z_rules": {
      "CANDIDATE_BASE_SPLIT": 783,
      "SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT": 1,
      "STATUS_SENTINEL_NOT_DAMAGE_SPLIT": 275,
      "STAT_STAGE_COMPARISON": 2,
      "TERA_CONDITIONAL_STAT_COMPARISON": 2
    },
    "t04_adapters_with_central_queries": 17,
    "t04_required_source_patch_contracts": 26,
    "t04_script_origins": {
      "PROJECT_COMPOSED_SCRIPT": 5,
      "PROJECT_DYNAMIC_PREPARE_ADAPTER": 3,
      "UPSTREAM_EFFECT_PARAMETER_ADAPTER": 43,
      "UPSTREAM_SCRIPT_DELEGATE": 19
    },
    "t04_source_adapters": 70,
    "type_split_mappings": 36,
    "wild_overlay_entries": 95,
    "wild_overlay_slots": 294,
    "z_status_effects": 29
  }
}
```

[汎用Zの実行時split・候補table監査](RUNTIME_Z_AUDIT.md)
