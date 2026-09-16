# PR #16 P05 通常リング・BP・戦闘モード供給の有限化checkpoint

このcheckpointは静的な入口候補台帳です。エミュレータ実行や通常プレイ受入の成功報告ではありません。
既存のシビルドナイト購入→装備→自然戦闘→保存成功をやり直したり、取り消したりしません。

## 残る実操作sub-gap

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_NATIVE_BP_EARNING_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`

## 候補根の機械抽出

### リング通常取得

保持match: 120 / implementation: 111 / anchor: 4

- `scripts/pr16_gear_originals.py:83` score=14 — `prior.fields(report,dict(status='PASS',schema_version=2,candidate=display.CANDIDATE,actual_new_processes=4,successful_fresh_cores=9,failures=[],old_runs_relabelled=0,purchased_gear_to_battle_accepted=True,initial_map_party_ring_bp_policy_ar`
- `scripts/pr16_purchased_gear.py:33` score=14 — `initial_map_party_ring_bp_policy_are_fixtures=True,ring_bp_natural_acquisition_accepted=False,`
- `scripts/pr16_purchased_gear.py:75` score=14 — `initial_map_party_ring_bp_policy_are_fixtures=True,no_post_observation_host_writes=True,`
- `scripts/pr16_purchased_gear.py:165` score=14 — `purchased_gear_to_battle_accepted=not failures,initial_map_party_ring_bp_policy_are_fixtures=True,`
- `scripts/pr16_gear_screen_checkpoint.py:46` score=9 — `prior.fields(report,dict(schema_version=2,status='PASS',scope=native.SCOPE,candidate=display.CANDIDATE,actual_new_processes=4,successful_fresh_cores=9,failures=[],guard_checks=prior.GUARDS,purchased_gear_to_battle_accepted=True,initial_map_`
- `scripts/pr16_gear_screen_checkpoint.py:76` score=9 — `purchased_gear_to_battle_accepted=True,initial_map_party_ring_bp_policy_are_fixtures=True,`
- `scripts/pr16_natural_capture_checkpoint.py:112` score=9 — `row.update(reason_ja='同一ショップ修正版で洞窟2経路の自然歩行→シビルドン捕獲→通常保存→別コア再開は2件4コア成功。開始位置・先頭個体・ボールはfixture。石の実購入・表示・保存の既存成功も保持。通常取得から戦闘への接続、リング/BP/ボールの通常入手は未受入',`
- `scripts/pr16_p05_native_supply_evidence_map.py:60` score=9 — `"reuse purchased-stone success as proof of ring acquisition",`

### BP通常獲得

保持match: 120 / implementation: 120 / anchor: 25

- `scripts/build_bp_shop_runtime.py:225` score=17 — `_fail(f"BP shop reward contract differs: {reward.get('reward_key')}")`
- `scripts/build_codex_battle_rewards.py:1292` score=17 — `subprocess.SubprocessError, CodexBattleRewardsBuildError) as error:`
- `scripts/build_factory_repeat_reward_runtime.py:202` score=17 — `points = ", ".join(f"{row['battle_points']}u" for row in rewards)`
- `scripts/build_factory_repeat_reward_runtime.py:217` score=17 — `static const uint16_t gFactoryRepeatRewardBattlePoints[FACTORY_REPEAT_REWARD_COUNT] = {{`
- `scripts/build_factory_repeat_reward_runtime.py:387` score=17 — `"purpose": "Factory Trial repeat item/BP reward wrapper",`
- `scripts/build_factory_repeat_reward_runtime.py:565` score=17 — `"repeat_rewards_1_and_2_bp": [row["battle_points"] for row in catalog["rewards"]] == [1, 2],`
- `scripts/build_factory_repeat_reward_runtime.py:679` score=17 — `- ACTIVE `TRIAL_REPEAT` 2行をstock `Random()`で抽選し、`{rewards[0]['item_key']}`×1＋{rewards[0]['battle_points']} BP、`{rewards[1]['item_key']}`×1＋{rewards[1]['battle_points']} BPを接続した。`
- `scripts/build_factory_reward_runtime.py:275` score=17 — `bp = selected["FACILITY_REWARD_KEY_TRIAL_BP"]`

### 戦闘許可モード通常選択

保持match: 120 / implementation: 120 / anchor: 1

- `scripts/pr16_apply_gear_policy_boundary.py:27` score=14 — `s=s[:a]+''' /* A configured NEXT-battle policy lives in volatile RAM, not the save.`
- `scripts/pr16_gear_screen_checkpoint.py:77` score=11 — `ring_bp_natural_acquisition_accepted=False,ordinary_policy_selection_accepted=False,all_six_gear_routes_accepted=False,full_p05_acceptance=False,release_ready=False)`
- `scripts/pr16_p05_native_supply_evidence_map.py:37` score=11 — `"policy_selection": "P05_ORDINARY_POLICY_SELECTION_PHYSICAL",`
- `scripts/pr16_p05_native_supply_evidence_map.py:88` score=11 — `"claim controller/scheduler fixture coverage as ordinary policy selection",`
- `scripts/pr16_p05_native_supply_evidence_map.py:262` score=11 — `purchased_acceptance["ordinary_policy_selection_accepted"] is False,`
- `scripts/pr16_p05_native_supply_evidence_map.py:290` score=11 — `need(row["ordinary_policy_selection_required"] is True, "policy was prematurely closed")`
- `scripts/pr16_p05_native_supply_evidence_map.py:323` score=11 — `"P05_ORDINARY_POLICY_SELECTION_PHYSICAL": "戦闘許可モード通常選択",`
- `scripts/pr16_purchased_gear_checkpoint.py:73` score=11 — `purchased_gear_to_battle_accepted=True,ring_bp_natural_acquisition_accepted=False,ordinary_policy_selection_accepted=False,all_six_species_gear_routes_accepted=False,full_p05_acceptance=False,release_ready=False)`

## 境界

- `PHYSICAL_CIRCUS_ADMISSION` は別残件のままです。
- Circusフラグの直接書込みで代替しません。
- 冷Continue後に試験側から許可policyを再注入しません。
- 通常戦闘を一律にメガ許可へ変更しません。
- この台帳から実入口を選び、各sub-gapの通常操作・保存境界だけを次の受入で閉じます。

source commit: `cec56d0aff5a336367b2e6ae4d4b816f6cd80362`
candidate SHA-256: `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`
