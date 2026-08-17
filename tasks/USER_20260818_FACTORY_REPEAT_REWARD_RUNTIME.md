# USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME — Factory Trialの反復報酬を実ROMへ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-20260818-FACTORY-REWARD-RUNTIME`
- Queue ID: `USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME`
- Baseline: post-v1.4.0 stage 28 / SHA-256 `268b1f8e309f4e877c2aa77256abb81056a03e99044659d5956ede0fe271989a`
- Output: stage 29 SHA-256 `00548aa770dc377eefe671b1825af9a78852374322471eb5e9b1cfb174a644a6`

## 目的

Stage 28のFactory Trial完了wrapperを正本として先に呼び、
`manifests/facility_rewards.csv` に残るACTIVE `TRIAL_REPEAT` 2行だけを
反復完走時の追加報酬として実ROMへ接続する。初回報酬、連勝credit、party復元、
基本9 BP、既存save transactionの所有権はStage 28へ残す。

## 実行

1. `TRIAL_REPEAT` 2行をmanifestとitem ID表から決定的catalogへ生成する。
2. Trial完了scriptの`callnative`だけを、Stage 28完了wrapperを先に呼ぶStage 29 wrapperへ差し替える。
3. 呼出前に初回報酬claim 3 bitが完了済みだった成功完走だけを反復対象とし、stock RNGで2候補を抽選する。
4. item追加と追加BPを同一補償transactionにし、bag満杯または保存失敗時はStage 28完了後の状態へ戻す。
5. stage 28をhash固定入力にstage 29、incremental/cumulative BPS、allocator・symbol・exact-ROM証跡を生成する。

## 受入条件

- [x] ACTIVE `TRIAL_REPEAT` 2/2行が、オレンのみ×1＋1 BP、ハイパーボール×1＋2 BPへ一意に生成される。
- [x] Stage 28完了wrapperを必ず先に呼び、結果9以外では反復報酬を付与しない。
- [x] 初回完走では反復RNGを消費せず、Stage 28の初回item・追加3 BP・連勝creditだけを付与する。
- [x] 2つのRNG分岐で基本9 BPにそれぞれ追加1/2 BPと対応item 1個を付与する。
- [x] 連勝credit付与と反復報酬が同一完走で共存し、初回item・creditを重複付与しない。
- [x] 抽選itemを追加できない場合は基本9 BPを維持し、反復追加BPだけを付与しない。
- [x] 通常save再読込で反復item、sector 31再読込でBP・claim・creditが一致する。
- [x] 保存失敗時はStage 28完了後のledger像とbagへ補償rollbackする。
- [x] stage 29のdeclared span外変更0、ROM allocator overlap 0、RAM overlap 0、incremental/cumulative BPS完全往復がPASSする。
- [x] libmGBA独立2 processで物理binding、初回非対象、両抽選、連勝共存、bag満杯、通常save、sector 31、exact party復元をPASSする。
- [x] v1.4.0 release tag／配布ROMとstage 27・28成果は変更せず、post-release stage 29として分離する。

## 完了

`make factory-repeat-reward-runtime`でexact-ROM 2 processを含む生成を行い、
`make factory-repeat-reward-runtime-check`で固定生成物を再計算照合する。完了証跡は
`reports/generated/factory_repeat_reward_runtime.md`、stage metadata、
`design/run_log.md`、`design/version_log.md`へ記録した。
