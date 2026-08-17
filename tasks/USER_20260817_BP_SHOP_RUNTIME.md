# USER-20260817-BP-SHOP-RUNTIME — クチバFactoryのBPショップを実ROMへ物理接続する

- Lane: `content/engine/save/maps/qa`
- Depends on: `USER-20260814-FACILITY-RUNTIME`, `USER-20260816-ACQUISITION-EVENTS`
- Queue ID: `USER-20260817-BP-SHOP-RUNTIME`
- Baseline: v1.4.0 / final SHA-256 `30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e`
- Output: stage 27 SHA-256 `c1266a414fcb80b5d3754adec1158effd0326aa8d8d75a8365a0fa0363b5e0b1`

## 目的

Factory Trialで獲得済みのBPを使う18品目のショップを、既存クチバFactory mapへ
物理NPCとして接続する。manifestを価格・item・解禁条件の正本とし、通常saveと
sector 31を跨ぐ購入transactionを失敗時に片側状態を残さない形で実装する。

## 実行

1. `manifests/qol_rewards.csv` のACTIVE `BP_SHOP` 18行を `item_ids.csv` と結合し、C headerと検証用JSONを決定的に生成する。
2. 既存のFactory Trial NPCをbyte-preserving cloneし、map `96/5` のlocal ID 3、座標 `(22,19)`へショップNPCを追加する。
3. 既存ページ式menuを再利用し、残高、5件単位のページ、解禁、購入結果をscript ABIへ接続する。
4. item追加→BP減算→通常save→sector 31の順に確定し、保存失敗時はitemとBPを補償rollbackする。
5. stage 26相当のv1.4.0最終ROMをhash固定入力にstage 27とBPSを生成し、変更span、allocator、実ROM購入・再読込・失敗系を検証する。

## 受入条件

- [x] ACTIVE `BP_SHOP` 18/18行が一意な実item ID、BP価格、表示文字列、解禁signalへ生成される。
- [x] Factory mapのobject数が2→3になり、既存2 objectとmap scriptsはbyte不変である。
- [x] 新NPCが実scriptからruntimeのpaged menuを開き、Trialと同じ`factory.battle_points`を表示・消費する。
- [x] 未解禁、残高不足、bag満杯は通常save／sector 31／BP／bagを変更せず終了する。
- [x] 成功購入はitemとBPを双方永続化し、通常save再読込とsector 31再読込後も一致する。
- [x] 通常saveまたはsector 31確定失敗時にitem追加とBP減算を補償rollbackする実装を持つ。
- [x] stage 27のdeclared span外変更0、ROM allocator overlap 0、RAM overlap 0、BPS完全往復がPASSする。
- [x] libmGBA独立2 processでphysical NPC、11種の解禁mapping、成功、再読込、残高不足、bag満杯、未解禁をPASSする。
- [x] v1.4.0 release tag／配布ROMは変更せず、post-release stage 27と差分BPSとして分離する。

## 完了

`make bp-shop-runtime` / `make bp-shop-runtime-check`を再現入口とする。
完了証跡は`reports/generated/bp_shop_runtime.md`、stage metadata、
`design/run_log.md`、`design/version_log.md`へ記録する。
