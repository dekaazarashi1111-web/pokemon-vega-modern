# USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME — Factory Trialの100連勝色違い記念枠を実ROMへ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME`
- Queue ID: `USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME`
- Baseline: post-v1.4.0 stage 30 / SHA-256 `e605841d83c6f8e9acd7dbd58b5b4f3d7b262d0274c4c5b4369f0728dc25bf38`
- Output: post-v1.4.0 stage 31

## 目的

`manifests/facility_rewards.csv` のACTIVE `SHINY_MEMORIAL` 100連勝行を、
Factory Master解禁後の一度限り非伝説色違い記念枠として実ROMへ接続する。
受取先、非伝説pool、生成、図鑑・取得台帳、party/PC満杯、保存失敗のtransactionを
既存の取得イベントruntimeと統合する。

## 受入条件

- [x] 100連勝境界、Factory Master gate、claim bit 9をmanifestから一意に生成する。
- [x] 非伝説色違いを一度限り生成し、party/PC・図鑑・取得台帳を原子的に更新する。
- [x] 容量不足と保存失敗ではclaimを消費せず、後続受取を可能にする。
- [x] Stage 30以前のFactory報酬、party復元、通常save／sector 31を回帰させない。
- [x] exact-ROM、allocator、BPS、ログ、タスク単位commitを残す。
