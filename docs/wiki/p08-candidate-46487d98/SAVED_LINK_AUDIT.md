# 保存ELFの全body照合と名前付きcallee

[Wiki入口](README.md) / [技511](MOVE_511_LINEAGE.md)

保存ELFの宣言extent全byteと現候補を比較。一致したbodyだけに保存名を結合し、BL先も全body一致を要求する。条件分岐は構造上の両側で、実到達・間接辺・source/macros一致・native受入は別。差分bodyを旧関数と同一と断定しない。

```json
{
  "frozen_compatibility_move_lineages": 1,
  "saved_elf_direct_call_sites": 94,
  "saved_elf_exact_function_graphs": 17,
  "saved_elf_exact_named_call_sites": 21,
  "saved_elf_requested_symbols": 31,
  "saved_elf_target_states": {
    "CANDIDATE_BODY_DIFFERS": 9,
    "EXACT_CANDIDATE_SYMBOL_BODY": 17,
    "MISSING_SAVED_SYMBOL": 2,
    "SYMBOL_WITHOUT_PROVEN_EXTENT": 3
  }
}
```

## 31対象の同一性

| 保存symbol | 状態 | address | bytes |
| --- | --- | --- | --- |
| CalcMoveSplit | EXACT_CANDIDATE_SYMBOL_BODY | 0x90d6408 | 240 |
| CanUseZMove | CANDIDATE_BODY_DIFFERS | 0x912c2c8 | 300 |
| CreateBoxMon | CANDIDATE_BODY_DIFFERS | 0x90d8e18 | 1152 |
| CreateEgg | EXACT_CANDIDATE_SYMBOL_BODY | 0x90eab80 | 208 |
| CreateMon | SYMBOL_WITHOUT_PROVEN_EXTENT | 未結合 | extentなし |
| CreateWildMon | CANDIDATE_BODY_DIFFERS | 0x9132a78 | 588 |
| DetermineEggAbility | MISSING_SAVED_SYMBOL | 未結合 | extentなし |
| FieldUseFunc_AbilityCapsule | EXACT_CANDIDATE_SYMBOL_BODY | 0x9123730 | 28 |
| GetAbility1 | CANDIDATE_BODY_DIFFERS | 0x913135c | 16 |
| GetAbility2 | CANDIDATE_BODY_DIFFERS | 0x913136c | 16 |
| GetBoxMonAbility | MISSING_SAVED_SYMBOL | 未結合 | extentなし |
| GetHiddenAbility | CANDIDATE_BODY_DIFFERS | 0x913137c | 16 |
| GetMonAbility | CANDIDATE_BODY_DIFFERS | 0x90da23c | 96 |
| GetSpecialZMove | EXACT_CANDIDATE_SYMBOL_BODY | 0x912c190 | 60 |
| GetTypeBasedZMove | EXACT_CANDIDATE_SYMBOL_BODY | 0x912c0fc | 148 |
| GiveBoxMonInitialMoveset | EXACT_CANDIDATE_SYMBOL_BODY | 0x91145f0 | 168 |
| GiveEggFromDaycare | CANDIDATE_BODY_DIFFERS | 0x90eac50 | 2288 |
| GiveMoveToBoxMon | EXACT_CANDIDATE_SYMBOL_BODY | 0x9114538 | 184 |
| HandleInputChooseMove | CANDIDATE_BODY_DIFFERS | 0x9116f90 | 4508 |
| ItemUseCB_AbilityCapsule | EXACT_CANDIDATE_SYMBOL_BODY | 0x91214b0 | 348 |
| ReplaceWithZMoveRuntime | EXACT_CANDIDATE_SYMBOL_BODY | 0x912c3f4 | 176 |
| ScriptGiveMon | EXACT_CANDIDATE_SYMBOL_BODY | 0x90dd02c | 340 |
| SetZEffect | EXACT_CANDIDATE_SYMBOL_BODY | 0x912bec4 | 568 |
| Task_ChangeAbility | EXACT_CANDIDATE_SYMBOL_BODY | 0x91213a4 | 268 |
| Task_HandleAbilityChangeYesNoInput | EXACT_CANDIDATE_SYMBOL_BODY | 0x9121354 | 80 |
| VegaBattlePolicyCanZ | EXACT_CANDIDATE_SYMBOL_BODY | 0x9126bb4 | 44 |
| VegaBattlePolicyMarkZ | EXACT_CANDIDATE_SYMBOL_BODY | 0x9126be0 | 40 |
| VegaMoveEffectPrepare | EXACT_CANDIDATE_SYMBOL_BODY | 0x9131e24 | 160 |
| VegaResolveMoveEffectScript | EXACT_CANDIDATE_SYMBOL_BODY | 0x9131928 | 612 |
| gBattleScriptsForMoveEffects | SYMBOL_WITHOUT_PROVEN_EXTENT | 未結合 | extentなし |
| gMovesThatChangePhysicality | SYMBOL_WITHOUT_PROVEN_EXTENT | 未結合 | extentなし |

## 名前付き直接BL（全body一致calleeだけ）

| caller | site | target | 一致callee |
| --- | --- | --- | --- |
| CalcMoveSplit | 0x90d6418 | 0x9130f38 | &#91;"CheckTableForMove"&#93; |
| CalcMoveSplit | 0x90d64b4 | 0x9130674 | &#91;"TeraTypeActive"&#93; |
| CreateEgg | 0x90eac2c | 0x9131060 | &#91;"HealMon"&#93; |
| GetTypeBasedZMove | 0x912c13a | 0x90d6408 | &#91;"CalcMoveSplit"&#93; |
| GetTypeBasedZMove | 0x912c154 | 0x90e6234 | &#91;"GetMoveTypeSpecial"&#93; |
| GetTypeBasedZMove | 0x912c164 | 0x90d6408 | &#91;"CalcMoveSplit"&#93; |
| GetTypeBasedZMove | 0x912c16e | 0x90d6408 | &#91;"CalcMoveSplit"&#93; |
| GiveBoxMonInitialMoveset | 0x9114666 | 0x9114538 | &#91;"GiveMoveToBoxMon"&#93; |
| ReplaceWithZMoveRuntime | 0x912c41c | 0x90f1894 | &#91;"IsDynamaxed"&#93; |
| ReplaceWithZMoveRuntime | 0x912c460 | 0x90f3114 | &#91;"IsRaidBattle"&#93; |
| ReplaceWithZMoveRuntime | 0x912c478 | 0x90f19a4 | &#91;"GetMaxMoveByMove"&#93; |
| ReplaceWithZMoveRuntime | 0x912c486 | 0x90f35f8 | &#91;"IsRaidBossUsingRegularMove"&#93; |
| ScriptGiveMon | 0x90dd088 | 0x9131060 | &#91;"HealMon"&#93; |
| ScriptGiveMon | 0x90dd08e | 0x90de638 | &#91;"GiveMonToPlayer"&#93; |
| ScriptGiveMon | 0x90dd130 | 0x90d8910 | &#91;"GiveMonNatureAndAbility"&#93; |
| ScriptGiveMon | 0x90dd140 | 0x9131100 | &#91;"SetMonPokedexFlags"&#93; |
| SetZEffect | 0x912bef4 | 0x90d4698 | &#91;"IsOfType"&#93; |
| SetZEffect | 0x912bf16 | 0x912ce54 | &#91;"ChangeStatBuffs"&#93; |
| VegaBattlePolicyCanZ | 0x9126bd2 | 0x910f030 | &#91;"cfru_integration_mechanic_can_use"&#93; |
| VegaBattlePolicyMarkZ | 0x9126bfa | 0x910f058 | &#91;"cfru_integration_mechanic_try_use"&#93; |
| VegaMoveEffectPrepare | 0x9131e4c | 0x9099e04 | &#91;"__aeabi_uidivmod"&#93; |

## 残件

CanUseZMoveとHandleInputChooseMove、種族accessor、CreateBoxMon/CreateWildMon/GiveEggFromDaycareは旧bodyとの差分を別途追跡します。DetermineEggAbilityは独立symbolがなく、inline化と断定しません。全handler・間接辺・通常初回供給/使用の実行受入は未完です。

[全命令graph・不一致・原本hash・取得受入](data/saved_link_audit.json)

```json
{
  "artifact_id": 10624750708,
  "artifact_sha256": "7169bb41d334d783ff860dd7df2565958ce7fc8d525aca23896f0c305213e198",
  "conclusion": "success",
  "failed_predecessor": 35566920479,
  "failure_ja": "保存ELFのsymbol表読取上限で停止。大規模有界表と切詰め拒否2試験を追加し修正。",
  "job": 106231970424,
  "report_sha256": "60d57ca066646e46e82594cd7404ae7bfd5041af7451e2cdc40d612c18045a77",
  "run": 35567438143,
  "source_body_equivalence_not_claimed": true,
  "unit_tests": 40
}
```
