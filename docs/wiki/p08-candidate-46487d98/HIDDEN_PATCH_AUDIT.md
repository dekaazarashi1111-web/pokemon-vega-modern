# 夢特性パッチの適用条件と供給source

[Wiki入口](README.md) / [夢特性一覧](HIDDEN_ABILITY_INDEX.md)

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38`。固定consumerと現candidate slot・local供給sourceの対応。現在の個体の有効特性はGetMonAbilityで決まる。供給/使用callerのcompiled対応・実到達/保存/Continueを受入したものではない。

## 条件

同じ特性IDなら通常slotでも効果なしです。隠れflagを持つかだけでは判定しません。取消・効果なしでは消費せず、承諾後だけ隠れflagを立てて1個消費します。

## 供給

供給定義は **32 BP**。道具ROMの価格field **20000** とは別です。通常sourceの解禁はベガ殿堂入りledgerまたは8個目badge flag。`HIDDEN_ABILITY_DEXNAV_UNLOCKED`という名前だけからDexNavの捕獲条件を追加しません。test_modeを通常供給証拠に使いません。

```json
{
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
}
```

## 全Speciesのslot判定

```json
{
  "hidden_patch_records": 1671,
  "hidden_patch_states": {
    "DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN": 847,
    "NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID": 57,
    "NO_HIDDEN_ABILITY_ASSIGNED": 767
  }
}
```
| Species | 通常1/2 | 隠れID | 適用条件（source分類） |
| --- | --- | --- | --- |
| [0](pokemon/0.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1](pokemon/1.md) | &#91;65,47&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [2](pokemon/2.md) | &#91;65,47&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [3](pokemon/3.md) | &#91;65,47&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [4](pokemon/4.md) | &#91;66,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [5](pokemon/5.md) | &#91;66,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [6](pokemon/6.md) | &#91;66,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [7](pokemon/7.md) | &#91;67,64&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [8](pokemon/8.md) | &#91;67,64&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [9](pokemon/9.md) | &#91;67,64&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [10](pokemon/10.md) | &#91;62,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [11](pokemon/11.md) | &#91;62,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [12](pokemon/12.md) | &#91;62,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [13](pokemon/13.md) | &#91;62,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [14](pokemon/14.md) | &#91;48,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [15](pokemon/15.md) | &#91;48,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [16](pokemon/16.md) | &#91;71,8&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [17](pokemon/17.md) | &#91;71,8&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [18](pokemon/18.md) | &#91;32,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [19](pokemon/19.md) | &#91;32,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [20](pokemon/20.md) | &#91;32,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [21](pokemon/21.md) | &#91;29,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [22](pokemon/22.md) | &#91;29,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [23](pokemon/23.md) | &#91;29,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [24](pokemon/24.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [25](pokemon/25.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [26](pokemon/26.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [27](pokemon/27.md) | &#91;9,56&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [28](pokemon/28.md) | &#91;5,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [29](pokemon/29.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [30](pokemon/30.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [31](pokemon/31.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [32](pokemon/32.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [33](pokemon/33.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [34](pokemon/34.md) | &#91;38,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [35](pokemon/35.md) | &#91;33,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [36](pokemon/36.md) | &#91;33,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [37](pokemon/37.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [38](pokemon/38.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [39](pokemon/39.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [40](pokemon/40.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [41](pokemon/41.md) | &#91;75,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [42](pokemon/42.md) | &#91;75,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [43](pokemon/43.md) | &#91;50,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [44](pokemon/44.md) | &#91;50,30&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [45](pokemon/45.md) | &#91;22,17&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [46](pokemon/46.md) | &#91;62,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [47](pokemon/47.md) | &#91;7,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [48](pokemon/48.md) | &#91;51,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [49](pokemon/49.md) | &#91;22,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [50](pokemon/50.md) | &#91;22,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [51](pokemon/51.md) | &#91;22,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [52](pokemon/52.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [53](pokemon/53.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [54](pokemon/54.md) | &#91;39,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [55](pokemon/55.md) | &#91;39,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [56](pokemon/56.md) | &#91;26,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [57](pokemon/57.md) | &#91;26,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [58](pokemon/58.md) | &#91;42,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [59](pokemon/59.md) | &#91;42,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [60](pokemon/60.md) | &#91;42,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [61](pokemon/61.md) | &#91;30,35&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [62](pokemon/62.md) | &#91;30,35&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [63](pokemon/63.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [64](pokemon/64.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [65](pokemon/65.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [66](pokemon/66.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [67](pokemon/67.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [68](pokemon/68.md) | &#91;22,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [69](pokemon/69.md) | &#91;22,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [70](pokemon/70.md) | &#91;22,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [71](pokemon/71.md) | &#91;31,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [72](pokemon/72.md) | &#91;31,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [73](pokemon/73.md) | &#91;31,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [74](pokemon/74.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [75](pokemon/75.md) | &#91;36,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [76](pokemon/76.md) | &#91;36,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [77](pokemon/77.md) | &#91;36,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [78](pokemon/78.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [79](pokemon/79.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [80](pokemon/80.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [81](pokemon/81.md) | &#91;5,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [82](pokemon/82.md) | &#91;5,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [83](pokemon/83.md) | &#91;11,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [84](pokemon/84.md) | &#91;11,30&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [85](pokemon/85.md) | &#91;47,43&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [86](pokemon/86.md) | &#91;47,43&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [87](pokemon/87.md) | &#91;26,46&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [88](pokemon/88.md) | &#91;26,46&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [89](pokemon/89.md) | &#91;69,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [90](pokemon/90.md) | &#91;69,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [91](pokemon/91.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [92](pokemon/92.md) | &#91;47,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [93](pokemon/93.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [94](pokemon/94.md) | &#91;49,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [95](pokemon/95.md) | &#91;49,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [96](pokemon/96.md) | &#91;26,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [97](pokemon/97.md) | &#91;51,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [98](pokemon/98.md) | &#91;51,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [99](pokemon/99.md) | &#91;7,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [100](pokemon/100.md) | &#91;7,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [101](pokemon/101.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [102](pokemon/102.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [103](pokemon/103.md) | &#91;11,33&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [104](pokemon/104.md) | &#91;11,33&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [105](pokemon/105.md) | &#91;28,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [106](pokemon/106.md) | &#91;1,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [107](pokemon/107.md) | &#91;1,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [108](pokemon/108.md) | &#91;1,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [109](pokemon/109.md) | &#91;15,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [110](pokemon/110.md) | &#91;15,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [111](pokemon/111.md) | &#91;28,46&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [112](pokemon/112.md) | &#91;9,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [113](pokemon/113.md) | &#91;9,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [114](pokemon/114.md) | &#91;9,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [115](pokemon/115.md) | &#91;49,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [116](pokemon/116.md) | &#91;49,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [117](pokemon/117.md) | &#91;49,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [118](pokemon/118.md) | &#91;48,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [119](pokemon/119.md) | &#91;21,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [120](pokemon/120.md) | &#91;21,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [121](pokemon/121.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [122](pokemon/122.md) | &#91;9,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [123](pokemon/123.md) | &#91;69,46&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [124](pokemon/124.md) | &#91;62,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [125](pokemon/125.md) | &#91;61,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [126](pokemon/126.md) | &#91;45,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [127](pokemon/127.md) | &#91;29,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [128](pokemon/128.md) | &#91;29,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [129](pokemon/129.md) | &#91;29,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [130](pokemon/130.md) | &#91;8,24&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [131](pokemon/131.md) | &#91;8,24&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [132](pokemon/132.md) | &#91;8,24&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [133](pokemon/133.md) | &#91;69,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [134](pokemon/134.md) | &#91;69,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [135](pokemon/135.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [136](pokemon/136.md) | &#91;46,73&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [137](pokemon/137.md) | &#91;46,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [138](pokemon/138.md) | &#91;46,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [139](pokemon/139.md) | &#91;46,10&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [140](pokemon/140.md) | &#91;46,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [141](pokemon/141.md) | &#91;46,11&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [142](pokemon/142.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [143](pokemon/143.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [144](pokemon/144.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [145](pokemon/145.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [146](pokemon/146.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [147](pokemon/147.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [148](pokemon/148.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [149](pokemon/149.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [150](pokemon/150.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [151](pokemon/151.md) | &#91;28,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [152](pokemon/152.md) | &#91;65,34&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [153](pokemon/153.md) | &#91;65,34&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [154](pokemon/154.md) | &#91;65,34&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [155](pokemon/155.md) | &#91;66,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [156](pokemon/156.md) | &#91;66,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [157](pokemon/157.md) | &#91;66,18&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [158](pokemon/158.md) | &#91;67,44&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [159](pokemon/159.md) | &#91;67,44&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [160](pokemon/160.md) | &#91;67,44&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [161](pokemon/161.md) | &#91;65,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [162](pokemon/162.md) | &#91;65,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [163](pokemon/163.md) | &#91;65,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [164](pokemon/164.md) | &#91;66,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [165](pokemon/165.md) | &#91;66,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [166](pokemon/166.md) | &#91;66,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [167](pokemon/167.md) | &#91;67,33&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [168](pokemon/168.md) | &#91;67,33&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [169](pokemon/169.md) | &#91;67,33&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [170](pokemon/170.md) | &#91;48,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [171](pokemon/171.md) | &#91;48,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [172](pokemon/172.md) | &#91;48,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [173](pokemon/173.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [174](pokemon/174.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [175](pokemon/175.md) | &#91;50,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [176](pokemon/176.md) | &#91;10,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [177](pokemon/177.md) | &#91;28,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [178](pokemon/178.md) | &#91;26,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [179](pokemon/179.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [180](pokemon/180.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [181](pokemon/181.md) | &#91;50,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [182](pokemon/182.md) | &#91;50,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [183](pokemon/183.md) | &#91;7,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [184](pokemon/184.md) | &#91;12,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [185](pokemon/185.md) | &#91;12,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [186](pokemon/186.md) | &#91;12,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [187](pokemon/187.md) | &#91;53,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [188](pokemon/188.md) | &#91;53,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [189](pokemon/189.md) | &#91;53,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [190](pokemon/190.md) | &#91;30,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [191](pokemon/191.md) | &#91;14,19&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [192](pokemon/192.md) | &#91;14,19&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [193](pokemon/193.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [194](pokemon/194.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [195](pokemon/195.md) | &#91;20,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [196](pokemon/196.md) | &#91;20,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [197](pokemon/197.md) | &#91;20,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [198](pokemon/198.md) | &#91;68,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [199](pokemon/199.md) | &#91;68,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [200](pokemon/200.md) | &#91;68,48&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [201](pokemon/201.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [202](pokemon/202.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [203](pokemon/203.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [204](pokemon/204.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [205](pokemon/205.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [206](pokemon/206.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [207](pokemon/207.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [208](pokemon/208.md) | &#91;64,61&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [209](pokemon/209.md) | &#91;64,61&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [210](pokemon/210.md) | &#91;55,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [211](pokemon/211.md) | &#91;21,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [212](pokemon/212.md) | &#91;64,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [213](pokemon/213.md) | &#91;64,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [214](pokemon/214.md) | &#91;17,29&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [215](pokemon/215.md) | &#91;18,28&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [216](pokemon/216.md) | &#91;18,28&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [217](pokemon/217.md) | &#91;49,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [218](pokemon/218.md) | &#91;49,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [219](pokemon/219.md) | &#91;37,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [220](pokemon/220.md) | &#91;131,120&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [221](pokemon/221.md) | &#91;26,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [222](pokemon/222.md) | &#91;26,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [223](pokemon/223.md) | &#91;43,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [224](pokemon/224.md) | &#91;43,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [225](pokemon/225.md) | &#91;43,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [226](pokemon/226.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [227](pokemon/227.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [228](pokemon/228.md) | &#91;43,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [229](pokemon/229.md) | &#91;43,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [230](pokemon/230.md) | &#91;43,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [231](pokemon/231.md) | &#91;52,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [232](pokemon/232.md) | &#91;52,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [233](pokemon/233.md) | &#91;73,20&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [234](pokemon/234.md) | &#91;26,20&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [235](pokemon/235.md) | &#91;56,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [236](pokemon/236.md) | &#91;41,64&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [237](pokemon/237.md) | &#91;7,14&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [238](pokemon/238.md) | &#91;69,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [239](pokemon/239.md) | &#91;8,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [240](pokemon/240.md) | &#91;2,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [241](pokemon/241.md) | &#91;2,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [242](pokemon/242.md) | &#91;70,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [243](pokemon/243.md) | &#91;70,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [244](pokemon/244.md) | &#91;77,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [245](pokemon/245.md) | &#91;77,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [246](pokemon/246.md) | &#91;8,71&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [247](pokemon/247.md) | &#91;39,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [248](pokemon/248.md) | &#91;46,46&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [249](pokemon/249.md) | &#91;27,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [250](pokemon/250.md) | &#91;27,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [251](pokemon/251.md) | &#91;20,7&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [252](pokemon/252.md) | &#91;65,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [253](pokemon/253.md) | &#91;66,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [254](pokemon/254.md) | &#91;67,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [255](pokemon/255.md) | &#91;68,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [256](pokemon/256.md) | &#91;9,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [257](pokemon/257.md) | &#91;14,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [258](pokemon/258.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [259](pokemon/259.md) | &#91;74,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [260](pokemon/260.md) | &#91;37,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [261](pokemon/261.md) | &#91;3,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [262](pokemon/262.md) | &#91;18,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [263](pokemon/263.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [264](pokemon/264.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [265](pokemon/265.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [266](pokemon/266.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [267](pokemon/267.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [268](pokemon/268.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [269](pokemon/269.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [270](pokemon/270.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [271](pokemon/271.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [272](pokemon/272.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [273](pokemon/273.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [274](pokemon/274.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [275](pokemon/275.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [276](pokemon/276.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [277](pokemon/277.md) | &#91;22,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [278](pokemon/278.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [279](pokemon/279.md) | &#91;51,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [280](pokemon/280.md) | &#91;52,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [281](pokemon/281.md) | &#91;52,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [282](pokemon/282.md) | &#91;68,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [283](pokemon/283.md) | &#91;68,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [284](pokemon/284.md) | &#91;52,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [285](pokemon/285.md) | &#91;52,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [286](pokemon/286.md) | &#91;22,61&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [287](pokemon/287.md) | &#91;22,61&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [288](pokemon/288.md) | &#91;22,61&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [289](pokemon/289.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [290](pokemon/290.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [291](pokemon/291.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [292](pokemon/292.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [293](pokemon/293.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [294](pokemon/294.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [295](pokemon/295.md) | &#91;20,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [296](pokemon/296.md) | &#91;20,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [297](pokemon/297.md) | &#91;68,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [298](pokemon/298.md) | &#91;68,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [299](pokemon/299.md) | &#91;14,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [300](pokemon/300.md) | &#91;14,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [301](pokemon/301.md) | &#91;14,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [302](pokemon/302.md) | &#91;3,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [303](pokemon/303.md) | &#91;25,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [304](pokemon/304.md) | &#91;41,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [305](pokemon/305.md) | &#91;41,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [306](pokemon/306.md) | &#91;37,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [307](pokemon/307.md) | &#91;8,31&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [308](pokemon/308.md) | &#91;20,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [309](pokemon/309.md) | &#91;33,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [310](pokemon/310.md) | &#91;33,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [311](pokemon/311.md) | &#91;33,63&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [312](pokemon/312.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [313](pokemon/313.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [314](pokemon/314.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [315](pokemon/315.md) | &#91;28,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [316](pokemon/316.md) | &#91;28,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [317](pokemon/317.md) | &#91;5,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [318](pokemon/318.md) | &#91;8,11&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [319](pokemon/319.md) | &#91;8,11&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [320](pokemon/320.md) | &#91;11,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [321](pokemon/321.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [322](pokemon/322.md) | &#91;28,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [323](pokemon/323.md) | &#91;33,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [324](pokemon/324.md) | &#91;11,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [325](pokemon/325.md) | &#91;34,20&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [326](pokemon/326.md) | &#91;27,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [327](pokemon/327.md) | &#91;27,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [328](pokemon/328.md) | &#91;8,69&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [329](pokemon/329.md) | &#91;22,55&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [330](pokemon/330.md) | &#91;4,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [331](pokemon/331.md) | &#91;4,51&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [332](pokemon/332.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [333](pokemon/333.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [334](pokemon/334.md) | &#91;68,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [335](pokemon/335.md) | &#91;7,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [336](pokemon/336.md) | &#91;41,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [337](pokemon/337.md) | &#91;8,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [338](pokemon/338.md) | &#91;34,35&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [339](pokemon/339.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [340](pokemon/340.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [341](pokemon/341.md) | &#91;32,50&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [342](pokemon/342.md) | &#91;32,20&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [343](pokemon/343.md) | &#91;51,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [344](pokemon/344.md) | &#91;17,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [345](pokemon/345.md) | &#91;28,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [346](pokemon/346.md) | &#91;73,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [347](pokemon/347.md) | &#91;73,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [348](pokemon/348.md) | &#91;33,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [349](pokemon/349.md) | &#91;33,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [350](pokemon/350.md) | &#91;24,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [351](pokemon/351.md) | &#91;47,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [352](pokemon/352.md) | &#91;9,7&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [353](pokemon/353.md) | &#91;34,9&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [354](pokemon/354.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [355](pokemon/355.md) | &#91;39,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [356](pokemon/356.md) | &#91;33,56&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [357](pokemon/357.md) | &#91;8,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [358](pokemon/358.md) | &#91;28,15&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [359](pokemon/359.md) | &#91;57,58&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [360](pokemon/360.md) | &#91;37,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [361](pokemon/361.md) | &#91;24,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [362](pokemon/362.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [363](pokemon/363.md) | &#91;69,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [364](pokemon/364.md) | &#91;30,32&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [365](pokemon/365.md) | &#91;30,32&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [366](pokemon/366.md) | &#91;30,32&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [367](pokemon/367.md) | &#91;69,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [368](pokemon/368.md) | &#91;69,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [369](pokemon/369.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [370](pokemon/370.md) | &#91;8,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [371](pokemon/371.md) | &#91;8,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [372](pokemon/372.md) | &#91;8,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [373](pokemon/373.md) | &#91;74,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [374](pokemon/374.md) | &#91;61,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [375](pokemon/375.md) | &#91;61,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [376](pokemon/376.md) | &#91;55,72&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [377](pokemon/377.md) | &#91;5,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [378](pokemon/378.md) | &#91;24,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [379](pokemon/379.md) | &#91;57,58&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [380](pokemon/380.md) | &#91;57,58&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [381](pokemon/381.md) | &#91;34,20&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [382](pokemon/382.md) | &#91;28,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [383](pokemon/383.md) | &#91;4,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [384](pokemon/384.md) | &#91;6,56&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [385](pokemon/385.md) | &#91;59,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [386](pokemon/386.md) | &#91;14,71&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [387](pokemon/387.md) | &#91;14,71&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [388](pokemon/388.md) | &#91;22,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [389](pokemon/389.md) | &#91;22,5&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [390](pokemon/390.md) | &#91;69,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [391](pokemon/391.md) | &#91;20,12&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [392](pokemon/392.md) | &#91;18,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [393](pokemon/393.md) | &#91;18,53&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [394](pokemon/394.md) | &#91;33,63&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [395](pokemon/395.md) | &#91;39,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [396](pokemon/396.md) | &#91;39,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [397](pokemon/397.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [398](pokemon/398.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [399](pokemon/399.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [400](pokemon/400.md) | &#91;15,28&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [401](pokemon/401.md) | &#91;15,28&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [402](pokemon/402.md) | &#91;18,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [403](pokemon/403.md) | &#91;18,49&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [404](pokemon/404.md) | &#91;30,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [405](pokemon/405.md) | &#91;30,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [406](pokemon/406.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [407](pokemon/407.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [408](pokemon/408.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [409](pokemon/409.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [410](pokemon/410.md) | &#91;63,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [411](pokemon/411.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [412](pokemon/412.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [413](pokemon/413.md) | &#91;61,0&#93; | 61 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [414](pokemon/414.md) | &#91;14,0&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [415](pokemon/415.md) | &#91;19,0&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [416](pokemon/416.md) | &#91;61,0&#93; | 61 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [417](pokemon/417.md) | &#91;68,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [418](pokemon/418.md) | &#91;51,78&#93; | 146 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [419](pokemon/419.md) | &#91;51,78&#93; | 146 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [420](pokemon/420.md) | &#91;51,78&#93; | 146 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [421](pokemon/421.md) | &#91;50,62&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [422](pokemon/422.md) | &#91;50,62&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [423](pokemon/423.md) | &#91;51,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [424](pokemon/424.md) | &#91;51,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [425](pokemon/425.md) | &#91;56,99&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [426](pokemon/426.md) | &#91;56,99&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [427](pokemon/427.md) | &#91;18,0&#93; | 70 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [428](pokemon/428.md) | &#91;18,0&#93; | 70 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [429](pokemon/429.md) | &#91;56,173&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [430](pokemon/430.md) | &#91;56,173&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [431](pokemon/431.md) | &#91;39,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [432](pokemon/432.md) | &#91;39,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [433](pokemon/433.md) | &#91;34,0&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [434](pokemon/434.md) | &#91;34,0&#93; | 1 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [435](pokemon/435.md) | &#91;34,0&#93; | 27 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [436](pokemon/436.md) | &#91;27,88&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [437](pokemon/437.md) | &#91;27,88&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [438](pokemon/438.md) | &#91;14,111&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [439](pokemon/439.md) | &#91;19,111&#93; | 148 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [440](pokemon/440.md) | &#91;53,102&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [441](pokemon/441.md) | &#91;7,102&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [442](pokemon/442.md) | &#91;6,13&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [443](pokemon/443.md) | &#91;6,13&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [444](pokemon/444.md) | &#91;72,84&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [445](pokemon/445.md) | &#91;72,84&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [446](pokemon/446.md) | &#91;22,18&#93; | 155 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [447](pokemon/447.md) | &#91;22,18&#93; | 155 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [448](pokemon/448.md) | &#91;11,6&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [449](pokemon/449.md) | &#91;11,6&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [450](pokemon/450.md) | &#91;11,6&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [451](pokemon/451.md) | &#91;28,39&#93; | 99 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [452](pokemon/452.md) | &#91;28,39&#93; | 99 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [453](pokemon/453.md) | &#91;28,39&#93; | 99 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [454](pokemon/454.md) | &#91;62,100&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [455](pokemon/455.md) | &#91;62,100&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [456](pokemon/456.md) | &#91;62,100&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [457](pokemon/457.md) | &#91;34,0&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [458](pokemon/458.md) | &#91;34,0&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [459](pokemon/459.md) | &#91;34,0&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [460](pokemon/460.md) | &#91;50,18&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [461](pokemon/461.md) | &#91;50,18&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [462](pokemon/462.md) | &#91;12,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [463](pokemon/463.md) | &#91;12,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [464](pokemon/464.md) | &#91;50,48&#93; | 78 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [465](pokemon/465.md) | &#91;50,48&#93; | 78 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [466](pokemon/466.md) | &#91;47,94&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [467](pokemon/467.md) | &#91;47,94&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [468](pokemon/468.md) | &#91;1,60&#93; | 144 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [469](pokemon/469.md) | &#91;1,60&#93; | 144 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [470](pokemon/470.md) | &#91;69,5&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [471](pokemon/471.md) | &#91;15,109&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [472](pokemon/472.md) | &#91;15,109&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [473](pokemon/473.md) | &#91;69,31&#93; | 4 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [474](pokemon/474.md) | &#91;69,31&#93; | 4 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [475](pokemon/475.md) | &#91;34,103&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [476](pokemon/476.md) | &#91;33,98&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [477](pokemon/477.md) | &#91;38,98&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [478](pokemon/478.md) | &#91;33,41&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [479](pokemon/479.md) | &#91;33,41&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [480](pokemon/480.md) | &#91;43,112&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [481](pokemon/481.md) | &#91;33,0&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [482](pokemon/482.md) | &#91;22,0&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [483](pokemon/483.md) | &#91;50,92&#93; | 108 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [484](pokemon/484.md) | &#91;11,11&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [485](pokemon/485.md) | &#91;10,10&#93; | 96 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [486](pokemon/486.md) | &#91;18,18&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [487](pokemon/487.md) | &#91;33,75&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [488](pokemon/488.md) | &#91;33,75&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [489](pokemon/489.md) | &#91;33,4&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [490](pokemon/490.md) | &#91;33,4&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [491](pokemon/491.md) | &#91;17,47&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [492](pokemon/492.md) | &#91;61,0&#93; | 63 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [493](pokemon/493.md) | &#91;61,0&#93; | 63 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [494](pokemon/494.md) | &#91;39,0&#93; | 137 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [495](pokemon/495.md) | &#91;65,0&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [496](pokemon/496.md) | &#91;65,0&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [497](pokemon/497.md) | &#91;65,0&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [498](pokemon/498.md) | &#91;66,0&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [499](pokemon/499.md) | &#91;66,0&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [500](pokemon/500.md) | &#91;66,0&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [501](pokemon/501.md) | &#91;67,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [502](pokemon/502.md) | &#91;67,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [503](pokemon/503.md) | &#91;67,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [504](pokemon/504.md) | &#91;50,51&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [505](pokemon/505.md) | &#91;50,51&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [506](pokemon/506.md) | &#91;39,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [507](pokemon/507.md) | &#91;10,35&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [508](pokemon/508.md) | &#91;10,35&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [509](pokemon/509.md) | &#91;56,99&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [510](pokemon/510.md) | &#91;56,173&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [511](pokemon/511.md) | &#91;28,48&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [512](pokemon/512.md) | &#91;28,48&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [513](pokemon/513.md) | &#91;9,0&#93; | 57 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [514](pokemon/514.md) | &#91;9,0&#93; | 57 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [515](pokemon/515.md) | &#91;9,0&#93; | 57 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [516](pokemon/516.md) | &#91;34,0&#93; | 132 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [517](pokemon/517.md) | &#91;47,37&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [518](pokemon/518.md) | &#91;47,37&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [519](pokemon/519.md) | &#91;5,69&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [520](pokemon/520.md) | &#91;11,6&#93; | 2 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [521](pokemon/521.md) | &#91;34,103&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [522](pokemon/522.md) | &#91;34,103&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [523](pokemon/523.md) | &#91;34,103&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [524](pokemon/524.md) | &#91;50,53&#93; | 93 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [525](pokemon/525.md) | &#91;34,95&#93; | 48 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [526](pokemon/526.md) | &#91;34,95&#93; | 48 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [527](pokemon/527.md) | &#91;3,14&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [528](pokemon/528.md) | &#91;6,11&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [529](pokemon/529.md) | &#91;6,11&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [530](pokemon/530.md) | &#91;28,28&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [531](pokemon/531.md) | &#91;28,28&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [532](pokemon/532.md) | &#91;12,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [533](pokemon/533.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [534](pokemon/534.md) | &#91;23,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [535](pokemon/535.md) | &#91;52,8&#93; | 17 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [536](pokemon/536.md) | &#91;69,5&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [537](pokemon/537.md) | &#91;22,50&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [538](pokemon/538.md) | &#91;22,96&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [539](pokemon/539.md) | &#91;38,33&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [540](pokemon/540.md) | &#91;68,62&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [541](pokemon/541.md) | &#91;53,96&#93; | 119 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [542](pokemon/542.md) | &#91;62,96&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [543](pokemon/543.md) | &#91;40,49&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [544](pokemon/544.md) | &#91;40,49&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [545](pokemon/545.md) | &#91;55,30&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [546](pokemon/546.md) | &#91;33,11&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [547](pokemon/547.md) | &#91;33,98&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [548](pokemon/548.md) | &#91;53,0&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [549](pokemon/549.md) | &#91;5,0&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [550](pokemon/550.md) | &#91;22,120&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [551](pokemon/551.md) | &#91;20,102&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [552](pokemon/552.md) | &#91;30,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [553](pokemon/553.md) | &#91;65,0&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [554](pokemon/554.md) | &#91;65,0&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [555](pokemon/555.md) | &#91;65,0&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [556](pokemon/556.md) | &#91;66,0&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [557](pokemon/557.md) | &#91;66,0&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [558](pokemon/558.md) | &#91;66,0&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [559](pokemon/559.md) | &#91;67,0&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [560](pokemon/560.md) | &#91;67,0&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [561](pokemon/561.md) | &#91;67,0&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [562](pokemon/562.md) | &#91;50,96&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [563](pokemon/563.md) | &#91;22,96&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [564](pokemon/564.md) | &#91;53,83&#93; | 96 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [565](pokemon/565.md) | &#91;53,83&#93; | 96 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [566](pokemon/566.md) | &#91;19,0&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [567](pokemon/567.md) | &#91;61,0&#93; | 61 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [568](pokemon/568.md) | &#91;68,0&#93; | 80 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [569](pokemon/569.md) | &#91;61,0&#93; | 61 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [570](pokemon/570.md) | &#91;19,0&#93; | 14 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [571](pokemon/571.md) | &#91;33,44&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [572](pokemon/572.md) | &#91;33,44&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [573](pokemon/573.md) | &#91;33,44&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [574](pokemon/574.md) | &#91;34,48&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [575](pokemon/575.md) | &#91;34,48&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [576](pokemon/576.md) | &#91;34,275&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [577](pokemon/577.md) | &#91;51,94&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [578](pokemon/578.md) | &#91;51,2&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [579](pokemon/579.md) | &#91;33,0&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [580](pokemon/580.md) | &#91;22,0&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [581](pokemon/581.md) | &#91;41,12&#93; | 46 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [582](pokemon/582.md) | &#91;41,12&#93; | 46 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [583](pokemon/583.md) | &#91;56,97&#93; | 148 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [584](pokemon/584.md) | &#91;56,97&#93; | 148 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [585](pokemon/585.md) | &#91;16,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [586](pokemon/586.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [587](pokemon/587.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [588](pokemon/588.md) | &#91;5,42&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [589](pokemon/589.md) | &#91;12,108&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [590](pokemon/590.md) | &#91;12,108&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [591](pokemon/591.md) | &#91;52,75&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [592](pokemon/592.md) | &#91;52,75&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [593](pokemon/593.md) | &#91;33,12&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [594](pokemon/594.md) | &#91;63,173&#93; | 56 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [595](pokemon/595.md) | &#91;24,0&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [596](pokemon/596.md) | &#91;24,0&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [597](pokemon/597.md) | &#91;52,71&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [598](pokemon/598.md) | &#91;26,26&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [599](pokemon/599.md) | &#91;26,26&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [600](pokemon/600.md) | &#91;47,62&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [601](pokemon/601.md) | &#91;47,62&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [602](pokemon/602.md) | &#91;9,31&#93; | 58 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [603](pokemon/603.md) | &#91;9,31&#93; | 58 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [604](pokemon/604.md) | &#91;12,87&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [605](pokemon/605.md) | &#91;40,117&#93; | 84 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [606](pokemon/606.md) | &#91;39,116&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [607](pokemon/607.md) | &#91;39,116&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [608](pokemon/608.md) | &#91;47,37&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [609](pokemon/609.md) | &#91;47,20&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [610](pokemon/610.md) | &#91;47,20&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [611](pokemon/611.md) | &#91;57,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [612](pokemon/612.md) | &#91;58,0&#93; | 10 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [613](pokemon/613.md) | &#91;74,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [614](pokemon/614.md) | &#91;74,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [615](pokemon/615.md) | &#91;30,0&#93; | 13 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [616](pokemon/616.md) | &#91;30,0&#93; | 13 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [617](pokemon/617.md) | &#91;23,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [618](pokemon/618.md) | &#91;30,38&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [619](pokemon/619.md) | &#91;54,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [620](pokemon/620.md) | &#91;72,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [621](pokemon/621.md) | &#91;54,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [622](pokemon/622.md) | &#91;64,60&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [623](pokemon/623.md) | &#91;64,60&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [624](pokemon/624.md) | &#91;75,0&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [625](pokemon/625.md) | &#91;33,0&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [626](pokemon/626.md) | &#91;33,0&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [627](pokemon/627.md) | &#91;61,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [628](pokemon/628.md) | &#91;17,0&#93; | 138 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [629](pokemon/629.md) | &#91;5,69&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [630](pokemon/630.md) | &#91;5,69&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [631](pokemon/631.md) | &#91;5,69&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [632](pokemon/632.md) | &#91;59,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [633](pokemon/633.md) | &#91;35,68&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [634](pokemon/634.md) | &#91;12,111&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [635](pokemon/635.md) | &#91;4,0&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [636](pokemon/636.md) | &#91;4,0&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [637](pokemon/637.md) | &#91;69,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [638](pokemon/638.md) | &#91;69,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [639](pokemon/639.md) | &#91;22,0&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [640](pokemon/640.md) | &#91;29,0&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [641](pokemon/641.md) | &#91;29,0&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [642](pokemon/642.md) | &#91;29,0&#93; | 136 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [643](pokemon/643.md) | &#91;2,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [644](pokemon/644.md) | &#91;70,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [645](pokemon/645.md) | &#91;77,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [646](pokemon/646.md) | &#91;32,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [647](pokemon/647.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [648](pokemon/648.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [649](pokemon/649.md) | &#91;19,0&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [650](pokemon/650.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [651](pokemon/651.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [652](pokemon/652.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [653](pokemon/653.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [654](pokemon/654.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [655](pokemon/655.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [656](pokemon/656.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [657](pokemon/657.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [658](pokemon/658.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [659](pokemon/659.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [660](pokemon/660.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [661](pokemon/661.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [662](pokemon/662.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [663](pokemon/663.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [664](pokemon/664.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [665](pokemon/665.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [666](pokemon/666.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [667](pokemon/667.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [668](pokemon/668.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [669](pokemon/669.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [670](pokemon/670.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [671](pokemon/671.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [672](pokemon/672.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [673](pokemon/673.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [674](pokemon/674.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [675](pokemon/675.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [676](pokemon/676.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [677](pokemon/677.md) | &#91;65,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [678](pokemon/678.md) | &#91;65,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [679](pokemon/679.md) | &#91;65,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [680](pokemon/680.md) | &#91;66,0&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [681](pokemon/681.md) | &#91;66,0&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [682](pokemon/682.md) | &#91;66,0&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [683](pokemon/683.md) | &#91;67,0&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [684](pokemon/684.md) | &#91;67,0&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [685](pokemon/685.md) | &#91;67,0&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [686](pokemon/686.md) | &#91;51,0&#93; | 121 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [687](pokemon/687.md) | &#91;22,0&#93; | 121 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [688](pokemon/688.md) | &#91;22,0&#93; | 121 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [689](pokemon/689.md) | &#91;87,110&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [690](pokemon/690.md) | &#91;87,110&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [691](pokemon/691.md) | &#91;61,0&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [692](pokemon/692.md) | &#91;68,0&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [693](pokemon/693.md) | &#91;80,22&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [694](pokemon/694.md) | &#91;80,22&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [695](pokemon/695.md) | &#91;80,22&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [696](pokemon/696.md) | &#91;30,38&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [697](pokemon/697.md) | &#91;30,38&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [698](pokemon/698.md) | &#91;105,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [699](pokemon/699.md) | &#91;105,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [700](pokemon/700.md) | &#91;5,0&#93; | 43 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [701](pokemon/701.md) | &#91;5,0&#93; | 43 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [702](pokemon/702.md) | &#91;61,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [703](pokemon/703.md) | &#91;108,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [704](pokemon/704.md) | &#91;68,0&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [705](pokemon/705.md) | &#91;119,0&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [706](pokemon/706.md) | &#91;46,0&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [707](pokemon/707.md) | &#91;34,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [708](pokemon/708.md) | &#91;123,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [709](pokemon/709.md) | &#91;60,115&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [710](pokemon/710.md) | &#91;60,115&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [711](pokemon/711.md) | &#91;102,53&#93; | 93 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [712](pokemon/712.md) | &#91;107,85&#93; | 139 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [713](pokemon/713.md) | &#91;107,85&#93; | 139 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [714](pokemon/714.md) | &#91;50,104&#93; | 7 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [715](pokemon/715.md) | &#91;56,104&#93; | 7 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [716](pokemon/716.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [717](pokemon/717.md) | &#91;7,20&#93; | 51 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [718](pokemon/718.md) | &#91;47,20&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [719](pokemon/719.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [720](pokemon/720.md) | &#91;1,107&#93; | 51 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [721](pokemon/721.md) | &#91;1,107&#93; | 51 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [722](pokemon/722.md) | &#91;26,86&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [723](pokemon/723.md) | &#91;26,86&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [724](pokemon/724.md) | &#91;5,69&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [725](pokemon/725.md) | &#91;43,112&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [726](pokemon/726.md) | &#91;46,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [727](pokemon/727.md) | &#91;53,47&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [728](pokemon/728.md) | &#91;45,0&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [729](pokemon/729.md) | &#91;45,0&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [730](pokemon/730.md) | &#91;108,88&#93; | 144 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [731](pokemon/731.md) | &#91;108,88&#93; | 144 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [732](pokemon/732.md) | &#91;33,115&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [733](pokemon/733.md) | &#91;33,115&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [734](pokemon/734.md) | &#91;33,11&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [735](pokemon/735.md) | &#91;34,103&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [736](pokemon/736.md) | &#91;3,111&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [737](pokemon/737.md) | &#91;103,103&#93; | 34 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [738](pokemon/738.md) | &#91;82,82&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [739](pokemon/739.md) | &#91;52,8&#93; | 91 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [740](pokemon/740.md) | &#91;5,42&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [741](pokemon/741.md) | &#91;82,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [742](pokemon/742.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [743](pokemon/743.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [744](pokemon/744.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [745](pokemon/745.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [746](pokemon/746.md) | &#91;113,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [747](pokemon/747.md) | &#91;46,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [748](pokemon/748.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [749](pokemon/749.md) | &#91;30,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [750](pokemon/750.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [751](pokemon/751.md) | &#91;163,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [752](pokemon/752.md) | &#91;65,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [753](pokemon/753.md) | &#91;65,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [754](pokemon/754.md) | &#91;65,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [755](pokemon/755.md) | &#91;66,0&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [756](pokemon/756.md) | &#91;66,0&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [757](pokemon/757.md) | &#91;66,0&#93; | 121 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [758](pokemon/758.md) | &#91;67,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [759](pokemon/759.md) | &#91;67,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [760](pokemon/760.md) | &#91;67,0&#93; | 75 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [761](pokemon/761.md) | &#91;50,51&#93; | 149 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [762](pokemon/762.md) | &#91;35,51&#93; | 149 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [763](pokemon/763.md) | &#91;72,53&#93; | 50 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [764](pokemon/764.md) | &#91;22,147&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [765](pokemon/765.md) | &#91;22,147&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [766](pokemon/766.md) | &#91;7,85&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [767](pokemon/767.md) | &#91;7,85&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [768](pokemon/768.md) | &#91;83,0&#93; | 65 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [769](pokemon/769.md) | &#91;83,0&#93; | 65 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [770](pokemon/770.md) | &#91;83,0&#93; | 66 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [771](pokemon/771.md) | &#91;83,0&#93; | 66 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [772](pokemon/772.md) | &#91;83,0&#93; | 67 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [773](pokemon/773.md) | &#91;83,0&#93; | 67 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [774](pokemon/774.md) | &#91;109,28&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [775](pokemon/775.md) | &#91;109,28&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [776](pokemon/776.md) | &#91;146,106&#93; | 80 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [777](pokemon/777.md) | &#91;146,106&#93; | 80 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [778](pokemon/778.md) | &#91;146,106&#93; | 80 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [779](pokemon/779.md) | &#91;31,79&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [780](pokemon/780.md) | &#91;31,79&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [781](pokemon/781.md) | &#91;5,134&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [782](pokemon/782.md) | &#91;5,134&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [783](pokemon/783.md) | &#91;5,45&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [784](pokemon/784.md) | &#91;110,104&#93; | 87 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [785](pokemon/785.md) | &#91;110,104&#93; | 87 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [786](pokemon/786.md) | &#91;147,160&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [787](pokemon/787.md) | &#91;147,160&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [788](pokemon/788.md) | &#91;132,145&#93; | 104 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [789](pokemon/789.md) | &#91;62,126&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [790](pokemon/790.md) | &#91;62,126&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [791](pokemon/791.md) | &#91;62,126&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [792](pokemon/792.md) | &#91;33,94&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [793](pokemon/793.md) | &#91;33,94&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [794](pokemon/794.md) | &#91;33,144&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [795](pokemon/795.md) | &#91;62,39&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [796](pokemon/796.md) | &#91;5,39&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [797](pokemon/797.md) | &#91;68,34&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [798](pokemon/798.md) | &#91;103,34&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [799](pokemon/799.md) | &#91;68,34&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [800](pokemon/800.md) | &#91;38,68&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [801](pokemon/801.md) | &#91;38,68&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [802](pokemon/802.md) | &#91;38,68&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [803](pokemon/803.md) | &#91;159,152&#93; | 34 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [804](pokemon/804.md) | &#91;159,152&#93; | 34 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [805](pokemon/805.md) | &#91;121,92&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [806](pokemon/806.md) | &#91;55,0&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [807](pokemon/807.md) | &#91;126,0&#93; | 162 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [808](pokemon/808.md) | &#91;11,34&#93; | 115 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [809](pokemon/809.md) | &#91;148,99&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [810](pokemon/810.md) | &#91;153,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [811](pokemon/811.md) | &#91;153,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [812](pokemon/812.md) | &#91;117,5&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [813](pokemon/813.md) | &#91;117,5&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [814](pokemon/814.md) | &#91;130,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [815](pokemon/815.md) | &#91;130,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [816](pokemon/816.md) | &#91;1,60&#93; | 107 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [817](pokemon/817.md) | &#91;1,134&#93; | 107 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [818](pokemon/818.md) | &#91;150,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [819](pokemon/819.md) | &#91;150,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [820](pokemon/820.md) | &#91;56,102&#93; | 93 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [821](pokemon/821.md) | &#91;56,102&#93; | 93 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [822](pokemon/822.md) | &#91;120,173&#93; | 23 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [823](pokemon/823.md) | &#91;120,173&#93; | 23 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [824](pokemon/824.md) | &#91;120,173&#93; | 23 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [825](pokemon/825.md) | &#91;143,99&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [826](pokemon/826.md) | &#91;143,99&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [827](pokemon/827.md) | &#91;143,99&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [828](pokemon/828.md) | &#91;51,146&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [829](pokemon/829.md) | &#91;51,146&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [830](pokemon/830.md) | &#91;116,82&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [831](pokemon/831.md) | &#91;116,82&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [832](pokemon/832.md) | &#91;116,118&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [833](pokemon/833.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [834](pokemon/834.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [835](pokemon/835.md) | &#91;9,0&#93; | 79 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [836](pokemon/836.md) | &#91;68,61&#93; | 100 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [837](pokemon/837.md) | &#91;68,75&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [838](pokemon/838.md) | &#91;27,0&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [839](pokemon/839.md) | &#91;27,0&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [840](pokemon/840.md) | &#91;11,131&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [841](pokemon/841.md) | &#91;11,131&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [842](pokemon/842.md) | &#91;132,94&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [843](pokemon/843.md) | &#91;141,28&#93; | 149 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [844](pokemon/844.md) | &#91;141,28&#93; | 149 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [845](pokemon/845.md) | &#91;18,49&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [846](pokemon/846.md) | &#91;18,49&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [847](pokemon/847.md) | &#91;18,49&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [848](pokemon/848.md) | &#91;80,105&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [849](pokemon/849.md) | &#91;80,105&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [850](pokemon/850.md) | &#91;80,105&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [851](pokemon/851.md) | &#91;82,203&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [852](pokemon/852.md) | &#91;82,203&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [853](pokemon/853.md) | &#91;94,75&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [854](pokemon/854.md) | &#91;94,60&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [855](pokemon/855.md) | &#91;24,126&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [856](pokemon/856.md) | &#91;90,104&#93; | 100 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [857](pokemon/857.md) | &#91;90,104&#93; | 100 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [858](pokemon/858.md) | &#91;129,39&#93; | 46 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [859](pokemon/859.md) | &#91;129,39&#93; | 46 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [860](pokemon/860.md) | &#91;121,158&#93; | 43 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [861](pokemon/861.md) | &#91;51,126&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [862](pokemon/862.md) | &#91;51,126&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [863](pokemon/863.md) | &#91;146,143&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [864](pokemon/864.md) | &#91;146,143&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [865](pokemon/865.md) | &#91;83,18&#93; | 73 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [866](pokemon/866.md) | &#91;68,55&#93; | 54 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [867](pokemon/867.md) | &#91;55,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [868](pokemon/868.md) | &#91;55,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [869](pokemon/869.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [870](pokemon/870.md) | &#91;49,0&#93; | 68 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [871](pokemon/871.md) | &#91;49,0&#93; | 68 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [872](pokemon/872.md) | &#91;155,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [873](pokemon/873.md) | &#91;155,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [874](pokemon/874.md) | &#91;155,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [875](pokemon/875.md) | &#91;159,0&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [876](pokemon/876.md) | &#91;159,0&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [877](pokemon/877.md) | &#91;164,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [878](pokemon/878.md) | &#91;165,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [879](pokemon/879.md) | &#91;160,0&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [880](pokemon/880.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [881](pokemon/881.md) | &#91;155,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [882](pokemon/882.md) | &#91;32,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [883](pokemon/883.md) | &#91;89,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [884](pokemon/884.md) | &#91;146,106&#93; | 80 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [885](pokemon/885.md) | &#91;11,131&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [886](pokemon/886.md) | &#91;11,131&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [887](pokemon/887.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [888](pokemon/888.md) | &#91;61,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [889](pokemon/889.md) | &#91;61,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [890](pokemon/890.md) | &#91;108,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [891](pokemon/891.md) | &#91;108,0&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [892](pokemon/892.md) | &#91;60,115&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [893](pokemon/893.md) | &#91;60,115&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [894](pokemon/894.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [895](pokemon/895.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [896](pokemon/896.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [897](pokemon/897.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [898](pokemon/898.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [899](pokemon/899.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [900](pokemon/900.md) | &#91;32,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [901](pokemon/901.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [902](pokemon/902.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [903](pokemon/903.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [904](pokemon/904.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [905](pokemon/905.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [906](pokemon/906.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [907](pokemon/907.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [908](pokemon/908.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [909](pokemon/909.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [910](pokemon/910.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [911](pokemon/911.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [912](pokemon/912.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [913](pokemon/913.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [914](pokemon/914.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [915](pokemon/915.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [916](pokemon/916.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [917](pokemon/917.md) | &#91;69,92&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [918](pokemon/918.md) | &#91;162,0&#93; | 162 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [919](pokemon/919.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [920](pokemon/920.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [921](pokemon/921.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [922](pokemon/922.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [923](pokemon/923.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [924](pokemon/924.md) | &#91;34,158&#93; | 32 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [925](pokemon/925.md) | &#91;45,0&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [926](pokemon/926.md) | &#91;45,0&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [927](pokemon/927.md) | &#91;32,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [928](pokemon/928.md) | &#91;89,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [929](pokemon/929.md) | &#91;89,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [930](pokemon/930.md) | &#91;89,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [931](pokemon/931.md) | &#91;89,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [932](pokemon/932.md) | &#91;123,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [933](pokemon/933.md) | &#91;165,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [934](pokemon/934.md) | &#91;164,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [935](pokemon/935.md) | &#91;145,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [936](pokemon/936.md) | &#91;10,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [937](pokemon/937.md) | &#91;22,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [938](pokemon/938.md) | &#91;155,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [939](pokemon/939.md) | &#91;65,0&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [940](pokemon/940.md) | &#91;65,0&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [941](pokemon/941.md) | &#91;65,0&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [942](pokemon/942.md) | &#91;66,0&#93; | 171 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [943](pokemon/943.md) | &#91;66,0&#93; | 171 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [944](pokemon/944.md) | &#91;66,0&#93; | 171 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [945](pokemon/945.md) | &#91;67,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [946](pokemon/946.md) | &#91;67,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [947](pokemon/947.md) | &#91;67,211&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [948](pokemon/948.md) | &#91;53,168&#93; | 37 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [949](pokemon/949.md) | &#91;53,168&#93; | 37 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [950](pokemon/950.md) | &#91;146,0&#93; | 178 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [951](pokemon/951.md) | &#91;49,0&#93; | 178 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [952](pokemon/952.md) | &#91;49,0&#93; | 178 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [953](pokemon/953.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [954](pokemon/954.md) | &#91;61,61&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [955](pokemon/955.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [956](pokemon/956.md) | &#91;80,128&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [957](pokemon/957.md) | &#91;80,128&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [958](pokemon/958.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [959](pokemon/959.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [960](pokemon/960.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [961](pokemon/961.md) | &#91;158,0&#93; | 180 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [962](pokemon/962.md) | &#91;158,0&#93; | 180 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [963](pokemon/963.md) | &#91;90,105&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [964](pokemon/964.md) | &#91;90,105&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [965](pokemon/965.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [966](pokemon/966.md) | &#91;51,152&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [967](pokemon/967.md) | &#91;51,152&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [968](pokemon/968.md) | &#91;100,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [969](pokemon/969.md) | &#91;100,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [970](pokemon/970.md) | &#91;177,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [971](pokemon/971.md) | &#91;132,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [972](pokemon/972.md) | &#91;132,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [973](pokemon/973.md) | &#91;176,0&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [974](pokemon/974.md) | &#91;176,0&#93; | 85 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [975](pokemon/975.md) | &#91;127,21&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [976](pokemon/976.md) | &#91;127,21&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [977](pokemon/977.md) | &#91;182,98&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [978](pokemon/978.md) | &#91;182,98&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [979](pokemon/979.md) | &#91;38,144&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [980](pokemon/980.md) | &#91;38,144&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [981](pokemon/981.md) | &#91;179,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [982](pokemon/982.md) | &#91;179,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [983](pokemon/983.md) | &#91;88,8&#93; | 95 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [984](pokemon/984.md) | &#91;88,8&#93; | 95 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [985](pokemon/985.md) | &#91;174,0&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [986](pokemon/986.md) | &#91;174,0&#93; | 69 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [987](pokemon/987.md) | &#91;175,0&#93; | 118 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [988](pokemon/988.md) | &#91;175,0&#93; | 118 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [989](pokemon/989.md) | &#91;56,56&#93; | 183 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [990](pokemon/990.md) | &#91;7,85&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [991](pokemon/991.md) | &#91;168,53&#93; | 57 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [992](pokemon/992.md) | &#91;29,0&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [993](pokemon/993.md) | &#91;158,94&#93; | 184 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [994](pokemon/994.md) | &#91;158,94&#93; | 184 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [995](pokemon/995.md) | &#91;158,94&#93; | 184 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [996](pokemon/996.md) | &#91;159,0&#93; | 171 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [997](pokemon/997.md) | &#91;30,120&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [998](pokemon/998.md) | &#91;30,120&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [999](pokemon/999.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1000](pokemon/1000.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1001](pokemon/1001.md) | &#91;20,116&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1002](pokemon/1002.md) | &#91;20,116&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1003](pokemon/1003.md) | &#91;120,152&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1004](pokemon/1004.md) | &#91;120,152&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1005](pokemon/1005.md) | &#91;188,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1006](pokemon/1006.md) | &#91;187,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1007](pokemon/1007.md) | &#91;189,0&#93; | 212 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1008](pokemon/1008.md) | &#91;29,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1009](pokemon/1009.md) | &#91;171,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1010](pokemon/1010.md) | &#91;171,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1011](pokemon/1011.md) | &#91;11,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1012](pokemon/1012.md) | &#91;80,128&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1013](pokemon/1013.md) | &#91;51,152&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1014](pokemon/1014.md) | &#91;177,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1015](pokemon/1015.md) | &#91;122,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1016](pokemon/1016.md) | &#91;189,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1017](pokemon/1017.md) | &#91;189,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1018](pokemon/1018.md) | &#91;189,0&#93; | 212 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1019](pokemon/1019.md) | &#91;212,0&#93; | 212 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1020](pokemon/1020.md) | &#91;211,211&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1021](pokemon/1021.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1022](pokemon/1022.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1023](pokemon/1023.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1024](pokemon/1024.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1025](pokemon/1025.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1026](pokemon/1026.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1027](pokemon/1027.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1028](pokemon/1028.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1029](pokemon/1029.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1030](pokemon/1030.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1031](pokemon/1031.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1032](pokemon/1032.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1033](pokemon/1033.md) | &#91;167,0&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1034](pokemon/1034.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1035](pokemon/1035.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1036](pokemon/1036.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1037](pokemon/1037.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1038](pokemon/1038.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1039](pokemon/1039.md) | &#91;53,120&#93; | 15 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1040](pokemon/1040.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1041](pokemon/1041.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1042](pokemon/1042.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1043](pokemon/1043.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1044](pokemon/1044.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1045](pokemon/1045.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1046](pokemon/1046.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1047](pokemon/1047.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1048](pokemon/1048.md) | &#91;170,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1049](pokemon/1049.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1050](pokemon/1050.md) | &#91;47,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1051](pokemon/1051.md) | &#91;182,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1052](pokemon/1052.md) | &#91;70,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1053](pokemon/1053.md) | &#91;179,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1054](pokemon/1054.md) | &#91;92,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1055](pokemon/1055.md) | &#91;100,100&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1056](pokemon/1056.md) | &#91;36,36&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1057](pokemon/1057.md) | &#91;75,75&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1058](pokemon/1058.md) | &#91;23,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1059](pokemon/1059.md) | &#91;186,186&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1060](pokemon/1060.md) | &#91;185,185&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1061](pokemon/1061.md) | &#91;105,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1062](pokemon/1062.md) | &#91;182,182&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1063](pokemon/1063.md) | &#91;81,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1064](pokemon/1064.md) | &#91;15,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1065](pokemon/1065.md) | &#91;105,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1066](pokemon/1066.md) | &#91;160,160&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1067](pokemon/1067.md) | &#91;102,102&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1068](pokemon/1068.md) | &#91;93,93&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1069](pokemon/1069.md) | &#91;95,95&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1070](pokemon/1070.md) | &#91;45,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1071](pokemon/1071.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1072](pokemon/1072.md) | &#91;3,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1073](pokemon/1073.md) | &#91;33,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1074](pokemon/1074.md) | &#91;183,183&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1075](pokemon/1075.md) | &#91;157,157&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1076](pokemon/1076.md) | &#91;37,37&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1077](pokemon/1077.md) | &#91;112,112&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1078](pokemon/1078.md) | &#91;74,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1079](pokemon/1079.md) | &#91;22,22&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1080](pokemon/1080.md) | &#91;174,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1081](pokemon/1081.md) | &#91;126,126&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1082](pokemon/1082.md) | &#91;183,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1083](pokemon/1083.md) | &#91;159,159&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1084](pokemon/1084.md) | &#91;157,157&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1085](pokemon/1085.md) | &#91;175,175&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1086](pokemon/1086.md) | &#91;185,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1087](pokemon/1087.md) | &#91;182,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1088](pokemon/1088.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1089](pokemon/1089.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1090](pokemon/1090.md) | &#91;191,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1091](pokemon/1091.md) | &#91;190,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1092](pokemon/1092.md) | &#91;192,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1093](pokemon/1093.md) | &#91;114,114&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1094](pokemon/1094.md) | &#91;160,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1095](pokemon/1095.md) | &#91;92,92&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1096](pokemon/1096.md) | &#91;118,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1097](pokemon/1097.md) | &#91;39,39&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1098](pokemon/1098.md) | &#91;132,132&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1099](pokemon/1099.md) | &#91;157,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1100](pokemon/1100.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1101](pokemon/1101.md) | &#91;0,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1102](pokemon/1102.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1103](pokemon/1103.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1104](pokemon/1104.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1105](pokemon/1105.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1106](pokemon/1106.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1107](pokemon/1107.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1108](pokemon/1108.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1109](pokemon/1109.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1110](pokemon/1110.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1111](pokemon/1111.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1112](pokemon/1112.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1113](pokemon/1113.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1114](pokemon/1114.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1115](pokemon/1115.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1116](pokemon/1116.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1117](pokemon/1117.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1118](pokemon/1118.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1119](pokemon/1119.md) | &#91;19,14&#93; | 133 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1120](pokemon/1120.md) | &#91;65,0&#93; | 204 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1121](pokemon/1121.md) | &#91;65,0&#93; | 204 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1122](pokemon/1122.md) | &#91;65,0&#93; | 204 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1123](pokemon/1123.md) | &#91;66,0&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1124](pokemon/1124.md) | &#91;66,0&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1125](pokemon/1125.md) | &#91;66,0&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1126](pokemon/1126.md) | &#91;67,0&#93; | 205 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1127](pokemon/1127.md) | &#91;67,0&#93; | 205 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1128](pokemon/1128.md) | &#91;67,0&#93; | 205 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1129](pokemon/1129.md) | &#91;51,93&#93; | 53 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1130](pokemon/1130.md) | &#91;51,93&#93; | 53 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1131](pokemon/1131.md) | &#91;51,93&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1132](pokemon/1132.md) | &#91;199,174&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1133](pokemon/1133.md) | &#91;199,174&#93; | 92 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1134](pokemon/1134.md) | &#91;68,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1135](pokemon/1135.md) | &#91;218,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1136](pokemon/1136.md) | &#91;26,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1137](pokemon/1137.md) | &#91;52,90&#93; | 84 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1138](pokemon/1138.md) | &#91;52,90&#93; | 84 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1139](pokemon/1139.md) | &#91;217,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1140](pokemon/1140.md) | &#91;119,19&#93; | 176 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1141](pokemon/1141.md) | &#91;119,19&#93; | 176 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1142](pokemon/1142.md) | &#91;51,72&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1143](pokemon/1143.md) | &#91;51,147&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1144](pokemon/1144.md) | &#91;209,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1145](pokemon/1145.md) | &#91;197,7&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1146](pokemon/1146.md) | &#91;197,7&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1147](pokemon/1147.md) | &#91;20,193&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1148](pokemon/1148.md) | &#91;20,193&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1149](pokemon/1149.md) | &#91;200,0&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1150](pokemon/1150.md) | &#91;200,0&#93; | 11 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1151](pokemon/1151.md) | &#91;103,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1152](pokemon/1152.md) | &#91;103,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1153](pokemon/1153.md) | &#91;35,27&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1154](pokemon/1154.md) | &#91;35,27&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1155](pokemon/1155.md) | &#91;213,0&#93; | 12 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1156](pokemon/1156.md) | &#91;213,0&#93; | 12 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1157](pokemon/1157.md) | &#91;219,104&#93; | 56 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1158](pokemon/1158.md) | &#91;219,104&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1159](pokemon/1159.md) | &#91;103,12&#93; | 176 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1160](pokemon/1160.md) | &#91;103,12&#93; | 176 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1161](pokemon/1161.md) | &#91;103,215&#93; | 176 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1162](pokemon/1162.md) | &#91;167,206&#93; | 30 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1163](pokemon/1163.md) | &#91;39,141&#93; | 181 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1164](pokemon/1164.md) | &#91;223,0&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1165](pokemon/1165.md) | &#91;194,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1166](pokemon/1166.md) | &#91;195,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1167](pokemon/1167.md) | &#91;196,0&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1168](pokemon/1168.md) | &#91;196,0&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1169](pokemon/1169.md) | &#91;216,0&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1170](pokemon/1170.md) | &#91;4,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1171](pokemon/1171.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1172](pokemon/1172.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1173](pokemon/1173.md) | &#91;214,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1174](pokemon/1174.md) | &#91;75,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1175](pokemon/1175.md) | &#91;161,31&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1176](pokemon/1176.md) | &#91;210,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1177](pokemon/1177.md) | &#91;220,174&#93; | 148 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1178](pokemon/1178.md) | &#91;202,158&#93; | 13 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1179](pokemon/1179.md) | &#91;201,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1180](pokemon/1180.md) | &#91;172,43&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1181](pokemon/1181.md) | &#91;172,43&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1182](pokemon/1182.md) | &#91;172,43&#93; | 143 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1183](pokemon/1183.md) | &#91;227,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1184](pokemon/1184.md) | &#91;228,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1185](pokemon/1185.md) | &#91;230,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1186](pokemon/1186.md) | &#91;229,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1187](pokemon/1187.md) | &#91;110,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1188](pokemon/1188.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1189](pokemon/1189.md) | &#91;231,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1190](pokemon/1190.md) | &#91;232,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1191](pokemon/1191.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1192](pokemon/1192.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1193](pokemon/1193.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1194](pokemon/1194.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1195](pokemon/1195.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1196](pokemon/1196.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1197](pokemon/1197.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1198](pokemon/1198.md) | &#91;233,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1199](pokemon/1199.md) | &#91;221,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1200](pokemon/1200.md) | &#91;102,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1201](pokemon/1201.md) | &#91;83,55&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1202](pokemon/1202.md) | &#91;83,55&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1203](pokemon/1203.md) | &#91;208,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1204](pokemon/1204.md) | &#91;82,0&#93; | 203 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1205](pokemon/1205.md) | &#91;82,0&#93; | 203 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1206](pokemon/1206.md) | &#91;82,0&#93; | 118 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1207](pokemon/1207.md) | &#91;82,0&#93; | 118 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1208](pokemon/1208.md) | &#91;8,222&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1209](pokemon/1209.md) | &#91;8,222&#93; | 160 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1210](pokemon/1210.md) | &#91;53,102&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1211](pokemon/1211.md) | &#91;170,102&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1212](pokemon/1212.md) | &#91;42,5&#93; | 207 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1213](pokemon/1213.md) | &#91;42,5&#93; | 207 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1214](pokemon/1214.md) | &#91;42,5&#93; | 207 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1215](pokemon/1215.md) | &#91;144,83&#93; | 224 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1216](pokemon/1216.md) | &#91;144,83&#93; | 224 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1217](pokemon/1217.md) | &#91;34,0&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1218](pokemon/1218.md) | &#91;120,0&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1219](pokemon/1219.md) | &#91;69,31&#93; | 4 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1220](pokemon/1220.md) | &#91;131,31&#93; | 69 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1221](pokemon/1221.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1222](pokemon/1222.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1223](pokemon/1223.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1224](pokemon/1224.md) | &#91;217,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1225](pokemon/1225.md) | &#91;217,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1226](pokemon/1226.md) | &#91;217,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1227](pokemon/1227.md) | &#91;51,72&#93; | 100 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1228](pokemon/1228.md) | &#91;209,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1229](pokemon/1229.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1230](pokemon/1230.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1231](pokemon/1231.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1232](pokemon/1232.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1233](pokemon/1233.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1234](pokemon/1234.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1235](pokemon/1235.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1236](pokemon/1236.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1237](pokemon/1237.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1238](pokemon/1238.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1239](pokemon/1239.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1240](pokemon/1240.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1241](pokemon/1241.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1242](pokemon/1242.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1243](pokemon/1243.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1244](pokemon/1244.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1245](pokemon/1245.md) | &#91;226,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1246](pokemon/1246.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1247](pokemon/1247.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1248](pokemon/1248.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1249](pokemon/1249.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1250](pokemon/1250.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1251](pokemon/1251.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1252](pokemon/1252.md) | &#91;198,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1253](pokemon/1253.md) | &#91;210,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1254](pokemon/1254.md) | &#91;221,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1255](pokemon/1255.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1256](pokemon/1256.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1257](pokemon/1257.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1258](pokemon/1258.md) | &#91;225,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1259](pokemon/1259.md) | &#91;10,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1260](pokemon/1260.md) | &#91;233,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1261](pokemon/1261.md) | &#91;233,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1262](pokemon/1262.md) | &#91;234,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1263](pokemon/1263.md) | &#91;182,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1264](pokemon/1264.md) | &#91;42,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1265](pokemon/1265.md) | &#91;90,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1266](pokemon/1266.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1267](pokemon/1267.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1268](pokemon/1268.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1269](pokemon/1269.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1270](pokemon/1270.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1271](pokemon/1271.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1272](pokemon/1272.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1273](pokemon/1273.md) | &#91;31,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1274](pokemon/1274.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1275](pokemon/1275.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1276](pokemon/1276.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1277](pokemon/1277.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1278](pokemon/1278.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1279](pokemon/1279.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1280](pokemon/1280.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1281](pokemon/1281.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1282](pokemon/1282.md) | &#91;188,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1283](pokemon/1283.md) | &#91;65,0&#93; | 230 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1284](pokemon/1284.md) | &#91;65,0&#93; | 230 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1285](pokemon/1285.md) | &#91;65,0&#93; | 230 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1286](pokemon/1286.md) | &#91;66,0&#93; | 237 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1287](pokemon/1287.md) | &#91;66,0&#93; | 237 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1288](pokemon/1288.md) | &#91;66,0&#93; | 237 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1289](pokemon/1289.md) | &#91;67,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1290](pokemon/1290.md) | &#91;67,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1291](pokemon/1291.md) | &#91;67,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1292](pokemon/1292.md) | &#91;168,0&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1293](pokemon/1293.md) | &#91;168,0&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1294](pokemon/1294.md) | &#91;51,128&#93; | 146 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1295](pokemon/1295.md) | &#91;51,128&#93; | 146 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1296](pokemon/1296.md) | &#91;46,128&#93; | 241 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1297](pokemon/1297.md) | &#91;68,14&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1298](pokemon/1298.md) | &#91;68,14&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1299](pokemon/1299.md) | &#91;68,120&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1300](pokemon/1300.md) | &#91;50,85&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1301](pokemon/1301.md) | &#91;50,85&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1302](pokemon/1302.md) | &#91;239,145&#93; | 27 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1303](pokemon/1303.md) | &#91;239,145&#93; | 27 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1304](pokemon/1304.md) | &#91;219,50&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1305](pokemon/1305.md) | &#91;219,81&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1306](pokemon/1306.md) | &#91;174,75&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1307](pokemon/1307.md) | &#91;174,75&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1308](pokemon/1308.md) | &#91;238,0&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1309](pokemon/1309.md) | &#91;174,0&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1310](pokemon/1310.md) | &#91;244,86&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1311](pokemon/1311.md) | &#91;244,49&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1312](pokemon/1312.md) | &#91;244,49&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1313](pokemon/1313.md) | &#91;248,83&#93; | 172 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1314](pokemon/1314.md) | &#91;248,83&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1315](pokemon/1315.md) | &#91;248,83&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1316](pokemon/1316.md) | &#91;246,61&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1317](pokemon/1317.md) | &#91;246,61&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1318](pokemon/1318.md) | &#91;242,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1319](pokemon/1319.md) | &#91;33,0&#93; | 240 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1320](pokemon/1320.md) | &#91;33,0&#93; | 240 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1321](pokemon/1321.md) | &#91;156,9&#93; | 104 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1322](pokemon/1322.md) | &#91;245,57&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1323](pokemon/1323.md) | &#91;18,73&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1324](pokemon/1324.md) | &#91;18,73&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1325](pokemon/1325.md) | &#91;7,0&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1326](pokemon/1326.md) | &#91;7,0&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1327](pokemon/1327.md) | &#91;134,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1328](pokemon/1328.md) | &#91;134,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1329](pokemon/1329.md) | &#91;132,108&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1330](pokemon/1330.md) | &#91;132,108&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1331](pokemon/1331.md) | &#91;132,108&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1332](pokemon/1332.md) | &#91;159,120&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1333](pokemon/1333.md) | &#91;159,120&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1334](pokemon/1334.md) | &#91;159,120&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1335](pokemon/1335.md) | &#91;121,62&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1336](pokemon/1336.md) | &#91;4,182&#93; | 253 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1337](pokemon/1337.md) | &#91;134,0&#93; | 254 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1338](pokemon/1338.md) | &#91;81,0&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1339](pokemon/1339.md) | &#91;78,252&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1340](pokemon/1340.md) | &#91;255,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1341](pokemon/1341.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1342](pokemon/1342.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1343](pokemon/1343.md) | &#91;4,0&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1344](pokemon/1344.md) | &#91;31,0&#93; | 227 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1345](pokemon/1345.md) | &#91;19,0&#93; | 247 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1346](pokemon/1346.md) | &#91;19,0&#93; | 247 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1347](pokemon/1347.md) | &#91;250,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1348](pokemon/1348.md) | &#91;249,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1349](pokemon/1349.md) | &#91;39,28&#93; | 228 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1350](pokemon/1350.md) | &#91;259,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1351](pokemon/1351.md) | &#91;126,0&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1352](pokemon/1352.md) | &#91;126,0&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1353](pokemon/1353.md) | &#91;10,55&#93; | 147 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1354](pokemon/1354.md) | &#91;10,9&#93; | 203 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1355](pokemon/1355.md) | &#91;11,174&#93; | 147 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1356](pokemon/1356.md) | &#91;11,116&#93; | 203 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1357](pokemon/1357.md) | &#91;136,135&#93; | 243 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1358](pokemon/1358.md) | &#91;29,152&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1359](pokemon/1359.md) | &#91;29,152&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1360](pokemon/1360.md) | &#91;29,152&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1361](pokemon/1361.md) | &#91;235,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1362](pokemon/1362.md) | &#91;236,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1363](pokemon/1363.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1364](pokemon/1364.md) | &#91;39,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1365](pokemon/1365.md) | &#91;261,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1366](pokemon/1366.md) | &#91;103,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1367](pokemon/1367.md) | &#91;263,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1368](pokemon/1368.md) | &#91;264,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1369](pokemon/1369.md) | &#91;265,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1370](pokemon/1370.md) | &#91;266,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1371](pokemon/1371.md) | &#91;128,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1372](pokemon/1372.md) | &#91;242,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1373](pokemon/1373.md) | &#91;242,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1374](pokemon/1374.md) | &#91;245,58&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1375](pokemon/1375.md) | &#91;134,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1376](pokemon/1376.md) | &#91;134,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1377](pokemon/1377.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1378](pokemon/1378.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1379](pokemon/1379.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1380](pokemon/1380.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1381](pokemon/1381.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1382](pokemon/1382.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1383](pokemon/1383.md) | &#91;249,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1384](pokemon/1384.md) | &#91;20,28&#93; | 228 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1385](pokemon/1385.md) | &#91;259,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1386](pokemon/1386.md) | &#91;235,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1387](pokemon/1387.md) | &#91;236,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1388](pokemon/1388.md) | &#91;46,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1389](pokemon/1389.md) | &#91;261,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1390](pokemon/1390.md) | &#91;103,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1391](pokemon/1391.md) | &#91;267,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1392](pokemon/1392.md) | &#91;268,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1393](pokemon/1393.md) | &#91;53,182&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1394](pokemon/1394.md) | &#91;50,258&#93; | 108 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1395](pokemon/1395.md) | &#91;50,258&#93; | 108 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1396](pokemon/1396.md) | &#91;83,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1397](pokemon/1397.md) | &#91;260,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1398](pokemon/1398.md) | &#91;81,0&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1399](pokemon/1399.md) | &#91;26,257&#93; | 1 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1400](pokemon/1400.md) | &#91;26,257&#93; | 229 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1401](pokemon/1401.md) | &#91;72,252&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1402](pokemon/1402.md) | &#91;173,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1403](pokemon/1403.md) | &#91;129,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1404](pokemon/1404.md) | &#91;202,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1405](pokemon/1405.md) | &#91;262,20&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1406](pokemon/1406.md) | &#91;134,0&#93; | 131 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1407](pokemon/1407.md) | &#91;53,83&#93; | 96 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1408](pokemon/1408.md) | &#91;53,83&#93; | 96 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1409](pokemon/1409.md) | &#91;43,112&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1410](pokemon/1410.md) | &#91;55,0&#93; | 39 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1411](pokemon/1411.md) | &#91;256,0&#93; | 162 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1412](pokemon/1412.md) | &#91;162,0&#93; | 162 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1413](pokemon/1413.md) | &#91;255,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1414](pokemon/1414.md) | &#91;251,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1415](pokemon/1415.md) | &#91;22,18&#93; | 69 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1416](pokemon/1416.md) | &#91;22,18&#93; | 69 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1417](pokemon/1417.md) | &#91;43,9&#93; | 107 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1418](pokemon/1418.md) | &#91;43,9&#93; | 107 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1419](pokemon/1419.md) | &#91;66,0&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1420](pokemon/1420.md) | &#91;38,33&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1421](pokemon/1421.md) | &#91;39,51&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1422](pokemon/1422.md) | &#91;67,0&#93; | 293 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1423](pokemon/1423.md) | &#91;34,55&#93; | 103 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1424](pokemon/1424.md) | &#91;156,92&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1425](pokemon/1425.md) | &#91;150,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1426](pokemon/1426.md) | &#91;150,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1427](pokemon/1427.md) | &#91;51,126&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1428](pokemon/1428.md) | &#91;158,75&#93; | 184 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1429](pokemon/1429.md) | &#91;158,75&#93; | 184 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1430](pokemon/1430.md) | &#91;174,116&#93; | 5 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1431](pokemon/1431.md) | &#91;65,0&#93; | 114 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1432](pokemon/1432.md) | &#91;22,120&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1433](pokemon/1433.md) | &#91;68,126&#93; | 293 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1434](pokemon/1434.md) | &#91;62,172&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1435](pokemon/1435.md) | &#91;33,92&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1436](pokemon/1436.md) | &#91;33,92&#93; | 105 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1437](pokemon/1437.md) | &#91;46,85&#93; | 144 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1438](pokemon/1438.md) | &#91;38,33&#93; | 22 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1439](pokemon/1439.md) | &#91;56,0&#93; | 127 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1440](pokemon/1440.md) | &#91;143,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1441](pokemon/1441.md) | &#91;65,0&#93; | 34 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1442](pokemon/1442.md) | &#91;66,0&#93; | 95 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1443](pokemon/1443.md) | &#91;67,0&#93; | 44 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1444](pokemon/1444.md) | &#91;14,0&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1445](pokemon/1445.md) | &#91;9,0&#93; | 31 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1446](pokemon/1446.md) | &#91;53,102&#93; | 128 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1447](pokemon/1447.md) | &#91;62,100&#93; | 81 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1448](pokemon/1448.md) | &#91;131,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1449](pokemon/1449.md) | &#91;52,75&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1450](pokemon/1450.md) | &#91;11,75&#93; | 94 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1451](pokemon/1451.md) | &#91;50,92&#93; | 108 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1452](pokemon/1452.md) | &#91;17,47&#93; | 83 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1453](pokemon/1453.md) | &#91;1,134&#93; | 107 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1454](pokemon/1454.md) | &#91;90,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1455](pokemon/1455.md) | &#91;65,0&#93; | 230 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1456](pokemon/1456.md) | &#91;66,0&#93; | 237 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1457](pokemon/1457.md) | &#91;67,0&#93; | 98 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1458](pokemon/1458.md) | &#91;46,128&#93; | 241 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1459](pokemon/1459.md) | &#91;68,120&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1460](pokemon/1460.md) | &#91;174,75&#93; | 33 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1461](pokemon/1461.md) | &#91;244,49&#93; | 18 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1462](pokemon/1462.md) | &#91;248,83&#93; | 55 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1463](pokemon/1463.md) | &#91;248,83&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1464](pokemon/1464.md) | &#91;246,61&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1465](pokemon/1465.md) | &#91;245,57&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1466](pokemon/1466.md) | &#91;245,58&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1467](pokemon/1467.md) | &#91;18,73&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1468](pokemon/1468.md) | &#91;132,108&#93; | 157 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1469](pokemon/1469.md) | &#91;159,120&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1470](pokemon/1470.md) | &#91;176,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1471](pokemon/1471.md) | &#91;126,0&#93; | 135 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1472](pokemon/1472.md) | &#91;136,135&#93; | 243 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1473](pokemon/1473.md) | &#91;261,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1474](pokemon/1474.md) | &#91;261,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1475](pokemon/1475.md) | &#91;65,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1476](pokemon/1476.md) | &#91;65,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1477](pokemon/1477.md) | &#91;65,0&#93; | 169 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1478](pokemon/1478.md) | &#91;66,0&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1479](pokemon/1479.md) | &#91;66,0&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1480](pokemon/1480.md) | &#91;66,0&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1481](pokemon/1481.md) | &#91;67,0&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1482](pokemon/1482.md) | &#91;67,0&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1483](pokemon/1483.md) | &#91;67,0&#93; | 154 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1484](pokemon/1484.md) | &#91;166,83&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1485](pokemon/1485.md) | &#91;269,83&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1486](pokemon/1486.md) | &#91;166,83&#93; | 47 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1487](pokemon/1487.md) | &#91;15,0&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1488](pokemon/1488.md) | &#91;15,0&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1489](pokemon/1489.md) | &#91;68,0&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1490](pokemon/1490.md) | &#91;68,0&#93; | 111 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1491](pokemon/1491.md) | &#91;9,30&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1492](pokemon/1492.md) | &#91;10,30&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1493](pokemon/1493.md) | &#91;10,30&#93; | 90 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1494](pokemon/1494.md) | &#91;50,53&#93; | 20 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1495](pokemon/1495.md) | &#91;133,168&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1496](pokemon/1496.md) | &#91;133,168&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1497](pokemon/1497.md) | &#91;20,0&#93; | 104 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1498](pokemon/1498.md) | &#91;274,0&#93; | 166 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1499](pokemon/1499.md) | &#91;48,0&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1500](pokemon/1500.md) | &#91;48,0&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1501](pokemon/1501.md) | &#91;270,0&#93; | 140 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1502](pokemon/1502.md) | &#91;22,55&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1503](pokemon/1503.md) | &#91;22,55&#93; | 62 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1504](pokemon/1504.md) | &#91;22,55&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1505](pokemon/1505.md) | &#91;22,55&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1506](pokemon/1506.md) | &#91;273,5&#93; | 29 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1507](pokemon/1507.md) | &#91;273,5&#93; | 29 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1508](pokemon/1508.md) | &#91;273,5&#93; | 29 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1509](pokemon/1509.md) | &#91;18,0&#93; | 49 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1510](pokemon/1510.md) | &#91;18,0&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1511](pokemon/1511.md) | &#91;18,0&#93; | 134 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1512](pokemon/1512.md) | &#91;20,9&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1513](pokemon/1513.md) | &#91;281,9&#93; | 6 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1514](pokemon/1514.md) | &#91;278,10&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1515](pokemon/1515.md) | &#91;278,10&#93; | 173 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1516](pokemon/1516.md) | &#91;22,50&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1517](pokemon/1517.md) | &#91;22,276&#93; | 199 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1518](pokemon/1518.md) | &#91;85,125&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1519](pokemon/1519.md) | &#91;85,144&#93; | 159 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1520](pokemon/1520.md) | &#91;275,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1521](pokemon/1521.md) | &#91;275,0&#93; | 152 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1522](pokemon/1522.md) | &#91;299,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1523](pokemon/1523.md) | &#91;299,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1524](pokemon/1524.md) | &#91;272,75&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1525](pokemon/1525.md) | &#91;34,15&#93; | 104 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1526](pokemon/1526.md) | &#91;34,15&#93; | 142 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1527](pokemon/1527.md) | &#91;14,0&#93; | 61 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1528](pokemon/1528.md) | &#91;28,0&#93; | 141 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1529](pokemon/1529.md) | &#91;108,120&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1530](pokemon/1530.md) | &#91;291,120&#93; | 3 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1531](pokemon/1531.md) | &#91;105,20&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1532](pokemon/1532.md) | &#91;105,20&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1533](pokemon/1533.md) | &#91;105,20&#93; | 125 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1534](pokemon/1534.md) | &#91;184,156&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1535](pokemon/1535.md) | &#91;184,156&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1536](pokemon/1536.md) | &#91;146,51&#93; | 277 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1537](pokemon/1537.md) | &#91;41,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1538](pokemon/1538.md) | &#91;279,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1539](pokemon/1539.md) | &#91;279,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1540](pokemon/1540.md) | &#91;143,0&#93; | 113 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1541](pokemon/1541.md) | &#91;143,0&#93; | 112 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1542](pokemon/1542.md) | &#91;61,0&#93; | 145 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1543](pokemon/1543.md) | &#91;298,0&#93; | 8 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1544](pokemon/1544.md) | &#91;296,0&#93; | 213 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1545](pokemon/1545.md) | &#91;296,0&#93; | 213 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1546](pokemon/1546.md) | &#91;53,0&#93; | 219 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1547](pokemon/1547.md) | &#91;147,0&#93; | 219 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1548](pokemon/1548.md) | &#91;114,78&#93; | 295 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1549](pokemon/1549.md) | &#91;47,82&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1550](pokemon/1550.md) | &#91;47,203&#93; | 126 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1551](pokemon/1551.md) | &#91;105,0&#93; | 293 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1552](pokemon/1552.md) | &#91;110,12&#93; | 41 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1553](pokemon/1553.md) | &#91;280,0&#93; | 115 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1554](pokemon/1554.md) | &#91;280,0&#93; | 115 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1555](pokemon/1555.md) | &#91;280,0&#93; | 115 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1556](pokemon/1556.md) | &#91;72,39&#93; | 129 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1557](pokemon/1557.md) | &#91;38,11&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1558](pokemon/1558.md) | &#91;292,297&#93; | 158 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1559](pokemon/1559.md) | &#91;32,50&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1560](pokemon/1560.md) | &#91;32,50&#93; | 156 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1561](pokemon/1561.md) | &#91;129,294&#93; | 46 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1562](pokemon/1562.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1563](pokemon/1563.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1564](pokemon/1564.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1565](pokemon/1565.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1566](pokemon/1566.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1567](pokemon/1567.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1568](pokemon/1568.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1569](pokemon/1569.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1570](pokemon/1570.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1571](pokemon/1571.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1572](pokemon/1572.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1573](pokemon/1573.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1574](pokemon/1574.md) | &#91;271,0&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1575](pokemon/1575.md) | &#91;271,0&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1576](pokemon/1576.md) | &#91;271,0&#93; | 116 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1577](pokemon/1577.md) | &#91;156,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1578](pokemon/1578.md) | &#91;50,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1579](pokemon/1579.md) | &#91;284,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1580](pokemon/1580.md) | &#91;287,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1581](pokemon/1581.md) | &#91;286,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1582](pokemon/1582.md) | &#91;285,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1583](pokemon/1583.md) | &#91;288,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1584](pokemon/1584.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1585](pokemon/1585.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1586](pokemon/1586.md) | &#91;289,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1587](pokemon/1587.md) | &#91;290,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1588](pokemon/1588.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1589](pokemon/1589.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1590](pokemon/1590.md) | &#91;22,84&#93; | 292 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1591](pokemon/1591.md) | &#91;22,84&#93; | 292 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1592](pokemon/1592.md) | &#91;22,84&#93; | 292 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1593](pokemon/1593.md) | &#91;38,11&#93; | 110 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1594](pokemon/1594.md) | &#91;301,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1595](pokemon/1595.md) | &#91;307,83&#93; | 60 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1596](pokemon/1596.md) | &#91;300,0&#93; | 86 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1597](pokemon/1597.md) | &#91;300,0&#93; | 86 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1598](pokemon/1598.md) | &#91;300,0&#93; | 86 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1599](pokemon/1599.md) | &#91;300,0&#93; | 86 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1600](pokemon/1600.md) | &#91;306,0&#93; | 276 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1601](pokemon/1601.md) | &#91;306,0&#93; | 120 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1602](pokemon/1602.md) | &#91;306,0&#93; | 102 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1603](pokemon/1603.md) | &#91;129,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1604](pokemon/1604.md) | &#91;11,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1605](pokemon/1605.md) | &#91;105,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1606](pokemon/1606.md) | &#91;5,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1607](pokemon/1607.md) | &#91;302,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1608](pokemon/1608.md) | &#91;304,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1609](pokemon/1609.md) | &#91;303,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1610](pokemon/1610.md) | &#91;305,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1611](pokemon/1611.md) | &#91;193,5&#93; | 243 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1612](pokemon/1612.md) | &#91;307,145&#93; | 60 | DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN |
| [1613](pokemon/1613.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1614](pokemon/1614.md) | &#91;282,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1615](pokemon/1615.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1616](pokemon/1616.md) | &#91;283,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1617](pokemon/1617.md) | &#91;308,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1618](pokemon/1618.md) | &#91;309,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1619](pokemon/1619.md) | &#91;310,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1620](pokemon/1620.md) | &#91;311,0&#93; | 0 | NO_HIDDEN_ABILITY_ASSIGNED |
| [1621](pokemon/1621.md) | &#91;157,157&#93; | 157 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1622](pokemon/1622.md) | &#91;182,182&#93; | 182 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1623](pokemon/1623.md) | &#91;271,271&#93; | 271 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1624](pokemon/1624.md) | &#91;152,152&#93; | 152 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1625](pokemon/1625.md) | &#91;172,172&#93; | 172 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1626](pokemon/1626.md) | &#91;26,26&#93; | 26 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1627](pokemon/1627.md) | &#91;157,157&#93; | 157 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1628](pokemon/1628.md) | &#91;90,90&#93; | 90 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1629](pokemon/1629.md) | &#91;124,124&#93; | 124 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1630](pokemon/1630.md) | &#91;26,26&#93; | 26 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1631](pokemon/1631.md) | &#91;145,145&#93; | 145 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1632](pokemon/1632.md) | &#91;137,137&#93; | 137 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1633](pokemon/1633.md) | &#91;202,202&#93; | 202 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1634](pokemon/1634.md) | &#91;313,313&#93; | 313 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1635](pokemon/1635.md) | &#91;105,105&#93; | 105 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1636](pokemon/1636.md) | &#91;316,316&#93; | 316 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1637](pokemon/1637.md) | &#91;129,129&#93; | 129 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1638](pokemon/1638.md) | &#91;312,312&#93; | 312 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1639](pokemon/1639.md) | &#91;188,188&#93; | 188 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1640](pokemon/1640.md) | &#91;118,118&#93; | 118 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1641](pokemon/1641.md) | &#91;8,8&#93; | 8 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1642](pokemon/1642.md) | &#91;92,92&#93; | 92 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1643](pokemon/1643.md) | &#91;195,195&#93; | 195 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1644](pokemon/1644.md) | &#91;261,261&#93; | 261 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1645](pokemon/1645.md) | &#91;169,169&#93; | 169 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1646](pokemon/1646.md) | &#91;100,100&#93; | 100 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1647](pokemon/1647.md) | &#91;18,18&#93; | 18 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1648](pokemon/1648.md) | &#91;81,81&#93; | 81 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1649](pokemon/1649.md) | &#91;221,221&#93; | 221 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1650](pokemon/1650.md) | &#91;221,221&#93; | 221 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1651](pokemon/1651.md) | &#91;127,127&#93; | 127 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1652](pokemon/1652.md) | &#91;315,315&#93; | 315 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1653](pokemon/1653.md) | &#91;36,36&#93; | 36 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1654](pokemon/1654.md) | &#91;36,36&#93; | 36 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1655](pokemon/1655.md) | &#91;314,314&#93; | 314 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1656](pokemon/1656.md) | &#91;227,227&#93; | 227 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1657](pokemon/1657.md) | &#91;100,100&#93; | 100 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1658](pokemon/1658.md) | &#91;75,75&#93; | 75 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1659](pokemon/1659.md) | &#91;317,317&#93; | 317 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1660](pokemon/1660.md) | &#91;22,22&#93; | 22 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1661](pokemon/1661.md) | &#91;243,243&#93; | 243 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1662](pokemon/1662.md) | &#91;127,127&#93; | 127 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1663](pokemon/1663.md) | &#91;37,37&#93; | 37 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1664](pokemon/1664.md) | &#91;115,115&#93; | 115 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1665](pokemon/1665.md) | &#91;115,115&#93; | 115 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1666](pokemon/1666.md) | &#91;115,115&#93; | 115 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1667](pokemon/1667.md) | &#91;216,216&#93; | 216 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1668](pokemon/1668.md) | &#91;10,10&#93; | 10 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1669](pokemon/1669.md) | &#91;189,189&#93; | 189 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |
| [1670](pokemon/1670.md) | &#91;20,20&#93; | 20 | NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID |

## 原文と未受入境界

```json
{
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
}
```

[保存ELFの全body照合・名前付きcallee・未解決差分](SAVED_LINK_AUDIT.md)
