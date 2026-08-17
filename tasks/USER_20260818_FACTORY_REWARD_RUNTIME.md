# USER-20260818-FACTORY-REWARD-RUNTIME — Factory Trialの初回・連勝報酬を実ROMへ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-20260814-FACILITY-RUNTIME`, `USER-20260817-BP-SHOP-RUNTIME`
- Queue ID: `USER-20260818-FACTORY-REWARD-RUNTIME`
- Baseline: post-v1.4.0 stage 27 / SHA-256 `c1266a414fcb80b5d3754adec1158effd0326aa8d8d75a8365a0fa0363b5e0b1`
- Output: stage 28 SHA-256 `268b1f8e309f4e877c2aa77256abb81056a03e99044659d5956ede0fe271989a`

## 目的

Factory Trialの既存完了処理を正本として保持したまま、
`manifests/facility_rewards.csv` のACTIVE初回報酬3件と連勝報酬4件を
実ROMのsave transactionへ接続する。基本9 BP、連勝更新、party復元、sector 31保存は
既存runtimeへ所有させ、追加報酬だけを薄いwrapperで確定する。

## 実行

1. Trial初回のExp Candy XS×5、Exp Candy S×2、追加3 BPと、連勝3/7/14/21の4 creditをmanifestから決定的に生成する。
2. Factory Trial完了scriptの`callnative`だけを、既存`FacilityRuntime_Complete`を先に呼ぶwrapperへ差し替える。
3. 基本完了が9を返した場合だけ追加報酬を処理し、claim bitでitem、BP、creditの重複を抑止する。
4. 通常save→sector 31の順に確定し、失敗時はpost-base ledger像と追加itemを補償rollbackする。
5. stage 27をhash固定入力にstage 28、incremental/cumulative BPS、allocator・symbol・exact-ROM証跡を生成する。

## 受入条件

- [x] ACTIVE対象7/7行が実item ID、BP量、credit種別、claim bitへ一意に生成される。
- [x] 既存完了処理がwrapperより先に呼ばれ、party復元、連勝、基本9 BP、sector 31の所有権を維持する。
- [x] 初回完走は基本9 BPに加えてXS×5、S×2、3 BPを付与し、連勝3のHABITAT creditを1回だけ付与する。
- [x] 連勝7/14/21への到達時にTYPE/RARE/RANDOM creditを各1回だけcatch-up付与する。
- [x] 反復完走は基本9 BPだけを反復し、初回item、追加3 BP、4 creditを重複付与しない。
- [x] bag満杯は基本完了を取り消さず、追加報酬claimを未設定のまま後続完走へ繰り越す。
- [x] 初回itemは通常save再読込、BP・claim・creditはsector 31再読込後も一致する。
- [x] stage 28のdeclared span外変更0、ROM allocator overlap 0、RAM overlap 0、incremental/cumulative BPS完全往復がPASSする。
- [x] libmGBA独立2 processで物理binding、初回、catch-up、反復、bag満杯、通常save、sector 31、exact party復元をPASSする。
- [x] v1.4.0 release tag／配布ROMとstage 27成果は変更せず、post-release stage 28として分離する。

## 完了

`make factory-reward-runtime` / `make factory-reward-runtime-check`を再現入口とする。
完了証跡は`reports/generated/factory_reward_runtime.md`、stage metadata、
`design/run_log.md`、`design/version_log.md`へ記録する。
