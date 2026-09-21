# 技effectのsource由来

[Wiki入口](README.md) / [全技](MOVE_INDEX.md)

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38`。effect ID比較ではなく、T04変換器の実命令・query操作を分類します。

現在の固定上流宣言とlocal変換sourceの構造的由来。Git全履歴・候補compiled全callerの証明ではない。T04の新規アダプターと新しいengine opcodeを区別する。

## 集計

```json
{
  "effect_origin_records": 1063,
  "effect_origin_states": {
    "LOCKED_UPSTREAM_EFFECT_DECLARATION": 991,
    "MOVE_NONE_NOT_PLAYABLE": 1,
    "T04_SOURCE_ADAPTER_CLASSIFIED": 70,
    "UNRESOLVED_SOURCE_LINEAGE": 1
  },
  "t04_adapters_with_central_queries": 17,
  "t04_required_source_patch_contracts": 26,
  "t04_script_origins": {
    "PROJECT_COMPOSED_SCRIPT": 5,
    "PROJECT_DYNAMIC_PREPARE_ADAPTER": 3,
    "UPSTREAM_EFFECT_PARAMETER_ADAPTER": 43,
    "UPSTREAM_SCRIPT_DELEGATE": 19
  },
  "t04_source_adapters": 70
}
```

## T04の専用アダプター

| 技 | source由来 | 既存script呼出 | 独自central query |
| --- | --- | --- | --- |
| [292](moves/292.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [355](moves/355.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [356](moves/356.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [357](moves/357.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [358](moves/358.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"RECOIL_ONE_THIRD"&#93; |
| [359](moves/359.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [360](moves/360.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [361](moves/361.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [418](moves/418.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [425](moves/425.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"RECOIL_ONE_THIRD"&#93; |
| [426](moves/426.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [427](moves/427.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;"HIT_EXACTLY_2"&#93; |
| [428](moves/428.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;"SOUND_MOVE"&#93; |
| [429](moves/429.md) | PROJECT_COMPOSED_SCRIPT | &#91;"BS_MOVE_END"&#93; | &#91;&#93; |
| [430](moves/430.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_187_Yawn"&#93; | &#91;&#93; |
| [431](moves/431.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [432](moves/432.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [433](moves/433.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"NO_EVASION_BOOST"&#93; |
| [434](moves/434.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [435](moves/435.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [436](moves/436.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [437](moves/437.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [438](moves/438.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [439](moves/439.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [440](moves/440.md) | PROJECT_COMPOSED_SCRIPT | &#91;"BS_MOVE_END"&#93; | &#91;&#93; |
| [441](moves/441.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [442](moves/442.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [443](moves/443.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [444](moves/444.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [445](moves/445.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_049_SetConfusion"&#93; | &#91;&#93; |
| [446](moves/446.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [447](moves/447.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [448](moves/448.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [449](moves/449.md) | PROJECT_COMPOSED_SCRIPT | &#91;"BS_MOVE_FAINT","BS_MOVE_MISSED"&#93; | &#91;&#93; |
| [450](moves/450.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [451](moves/451.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"HIT_EXACTLY_2"&#93; |
| [452](moves/452.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [453](moves/453.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [454](moves/454.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [455](moves/455.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;"SOUND_MOVE"&#93; |
| [456](moves/456.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [457](moves/457.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [458](moves/458.md) | PROJECT_DYNAMIC_PREPARE_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [459](moves/459.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [460](moves/460.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [461](moves/461.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [462](moves/462.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [463](moves/463.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [464](moves/464.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"WEIGHT_BASED_SPECIAL_POWER"&#93; |
| [465](moves/465.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;"SOUND_MOVE"&#93; |
| [466](moves/466.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [467](moves/467.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_117_Rollout"&#93; | &#91;&#93; |
| [468](moves/468.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [469](moves/469.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [470](moves/470.md) | PROJECT_COMPOSED_SCRIPT | &#91;"BS_MOVE_FAINT","BS_MOVE_MISSED"&#93; | &#91;&#93; |
| [471](moves/471.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"USER_HP_SCALED_POWER"&#93; |
| [472](moves/472.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"FALSE_SWIPE_DAMAGE_FLOOR"&#93; |
| [473](moves/473.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;"SOUND_MOVE"&#93; |
| [474](moves/474.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"DOUBLE_POWER_IF_HIT"&#93; |
| [475](moves/475.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [476](moves/476.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"CRITICAL_STAGE_UP_1"&#93; |
| [477](moves/477.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"SOUND_MOVE"&#93; |
| [478](moves/478.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_055_RaiseUserAcc2"&#93; | &#91;&#93; |
| [479](moves/479.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [480](moves/480.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"HIT_EXACTLY_3"&#93; |
| [481](moves/481.md) | UPSTREAM_EFFECT_PARAMETER_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [482](moves/482.md) | PROJECT_DYNAMIC_PREPARE_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [486](moves/486.md) | PROJECT_COMPOSED_SCRIPT | &#91;"BS_MOVE_FAINT","BS_MOVE_MISSED"&#93; | &#91;&#93; |
| [487](moves/487.md) | PROJECT_DYNAMIC_PREPARE_ADAPTER | &#91;"BS_STANDARD_HIT"&#93; | &#91;&#93; |
| [509](moves/509.md) | UPSTREAM_SCRIPT_DELEGATE | &#91;"BS_STANDARD_HIT"&#93; | &#91;"CRITICAL_STAGE_UP_2"&#93; |

## 未結合・未検証

未結合技: [511]

固定上流のeffect宣言一致は、全handlerが無改変である証拠ではありません。compiled dispatch・move ID分岐・patchの実適用とnative受入は別です。

```json
[
  {
    "end_line": 336,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "1a40a23c851a740aeb4333b15ab4fe7a200f02098b2b79bf9e84bcc88f1f885c",
    "path": "tools/engine/cfru_move_effect_lowering.py",
    "start_line": 271,
    "symbol": "_compile_commands",
    "unit_sha256": "1d4c29c7172208a1fef6463ac5a81df8c068935030388df2568b8d4b47af5912"
  },
  {
    "end_line": 904,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "1a40a23c851a740aeb4333b15ab4fe7a200f02098b2b79bf9e84bcc88f1f885c",
    "path": "tools/engine/cfru_move_effect_lowering.py",
    "start_line": 679,
    "symbol": "_required_patches",
    "unit_sha256": "4cb89074cf5e1c498dd901ea8dc9478de7f4210a4c9d31ad2259e36bc3c01828"
  },
  {
    "end_line": 1045,
    "evidence": "GENERATED_CANONICAL",
    "file_sha256": "1a40a23c851a740aeb4333b15ab4fe7a200f02098b2b79bf9e84bcc88f1f885c",
    "path": "tools/engine/cfru_move_effect_lowering.py",
    "start_line": 943,
    "symbol": "lower_t04_move_effects",
    "unit_sha256": "12f9eadd253422b35524cb1b8e8b14feccc7d37cc31bc8041287653897d9b4a3"
  }
]
```
