# USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME — Factory Trialの49連勝特殊イベントキーを実ROMへ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME`
- Queue ID: `USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME`
- Baseline: post-v1.4.0 stage 29 / SHA-256 `00548aa770dc377eefe671b1825af9a78852374322471eb5e9b1cfb174a644a6`
- Output: post-v1.4.0 stage 30

## 目的

Stage 29のFactory Trial完了wrapperを正本として先に呼び、
`manifests/facility_rewards.csv` のACTIVE `SPECIAL_EVENT` 49連勝行を、
Factory Master解禁後の成功完走へ一度限りの特殊イベントキーとして接続する。
Stage 29までの基本9 BP、初回・連勝credit、反復item/BP、party復元の所有権は変更しない。

## 実行

1. `FACILITY_REWARD_KEY_STREAK_049` をmanifestから決定的catalogへ生成する。
2. Trial完了scriptの`callnative`を、Stage 29完了wrapperを先に呼ぶStage 30 wrapperへ差し替える。
3. 成功完走後、`league_ii_cleared`、Trial streak 49以上、claim bit未設定を満たす場合だけbit 8を設定する。
4. claim更新はpost-Stage 29 ledgerの補償transactionとし、sector 31保存失敗時はStage 29完了後の状態へ戻す。
5. stage 29をhash固定入力にstage 30、incremental/cumulative BPS、allocator・symbol・exact-ROM証跡を生成する。

## 受入条件

- [x] ACTIVE `SPECIAL_EVENT` 49連勝行が、threshold 49・`FACTORY_MASTER`・`CLAIM_KEY_STREAK_049_EVENT`・claim bit 8へ一意に生成される。
- [x] Stage 29完了wrapperを必ず先に呼び、結果9以外では特殊イベントキーを更新しない。
- [x] Factory Master未解禁またはstreak 48以下ではclaim bit 8を設定しない。
- [x] Factory Master解禁済みかつstreak 49以上ではclaim bit 8を一度だけ設定し、後続成功完走で重複transactionを作らない。
- [x] 初回・連勝credit・反復item/BPと同一完走で共存し、Stage 29の結果とparty exact復元を維持する。
- [x] sector 31再読込でclaim bitとtransactionが一致する。
- [x] 保存失敗時はexact post-Stage 29 ledger像へ補償rollbackする。
- [x] stage 30のdeclared span外変更0、ROM allocator overlap 0、RAM overlap 0、incremental/cumulative BPS完全往復がPASSする。
- [x] libmGBA独立2 processで物理binding、Master gate、threshold、catch-up、once抑止、sector 31、exact party復元をPASSする。
- [x] v1.4.0 release tag／配布ROMとstage 27〜29成果は変更せず、post-release stage 30として分離する。
