# PR #16 P05 通常リング・BP・戦闘モード供給 source/evidence 対応checkpoint

このcheckpointは、前段の静的matchを実装scope・既存receipt・次のrunner契約へ縮約したものです。
通常プレイ受入の成功ではなく、エミュレータ実行数は0です。

## リング通常取得

- gap: `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- preferred source: `scripts/pr16_gear_originals.py:83`
- scope: `verify`
- fixture-only source: `false`
- nonfixture candidates: 8
- disposition: 既存receiptは隣接成功またはfixture境界であり、通常供給の代替にはしない。

### 次runnerの必須操作

- reach the authored ring supplier through normal map/event interaction
- accept the ring through the real give-item/flag transaction
- save normally, discard the emulator core, and Continue on a fresh core
- verify the same obtained ring state without writing inventory or flags

### 禁止する短絡

- preinstall the ring before observation
- write the ownership flag or bag slot directly
- reuse purchased-stone success as proof of ring acquisition

## BP通常獲得

- gap: `P05_NATIVE_BP_EARNING_PHYSICAL`
- preferred source: `scripts/build_bp_shop_runtime.py:225`
- scope: `_catalog_outputs`
- fixture-only source: `false`
- nonfixture candidates: 12
- disposition: 既存receiptは隣接成功またはfixture境界であり、通常供給の代替にはしない。

### 次runnerの必須操作

- enter the authored BP-awarding activity through its real reception/menu
- finish the required battle or result path
- observe the real reward transaction increase BP
- save normally and verify the balance after cold Continue

### 禁止する短絡

- seed the earned BP after observation
- prove only that a BP shop can spend a fixture balance
- call the reward helper without the ordinary facility/result path

## 戦闘許可モード通常選択

- gap: `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- preferred source: `scripts/pr16_apply_gear_policy_boundary.py:27`
- scope: `main`
- fixture-only source: `false`
- nonfixture candidates: 9
- disposition: 既存receiptは隣接成功またはfixture境界であり、通常供給の代替にはしない。

### 次runnerの必須操作

- reach the authored mode/policy selector through its real reception or menu
- choose an accepted battle mode through controller input
- enter the corresponding battle without a test-side policy write
- demonstrate the documented cold-Continue boundary and reselect normally when required

### 禁止する短絡

- globally enable Mega in all battles
- restore the transient policy from the test after cold Continue
- claim controller/scheduler fixture coverage as ordinary policy selection

## 保持する境界

- 購入石→装備→自然戦闘→保存の成功は保持し、再実行対象に戻さない。
- Circus実受付は別残件であり、この3経路の証拠へ混ぜない。
- 後継最終候補への証拠移送はP08で行う。

source commit: `6d3d153e4fcbe34c2e785fa264f1a6cb415dab06`
candidate SHA-256: `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`
