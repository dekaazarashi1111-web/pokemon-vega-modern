# T24 — Integrate Reward Encounters V2

- Lane: `content/engine/save/maps/qa`
- Depends on: `T23`

## 目的

ChatGPT Pro返却済みのReward Encounters V2を、T23のStage 40へproduction統合する。
4 tier、24 encounter pool、typed credit、BP直接支払い、pending再戦、10 credit source、
Scientist NPCを実battle/saveへ接続し、Stage 41でreset耐性のある報酬遭遇を成立させる。

## 固定入力

### baseline

- T23の正規出力 `build/stages/40_research_economy_v1.gba` とmetadata。
- identityはT23完了commitとmetadataに記録されたsize/hashを正とする。
- T23がDONEかつworktreeがその完了commitを含むことを確認してから開始する。
- Stage 37設計catalogの物理値はStage 40から再解決する。

### 返却済み設計

- 原本: `userfile/imports/Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `b293c9f9c65eaf7acf4a6c5707163460b095d761283dc821d920801b38262195`
- ZIP size: 19,169 bytes、10 entries
- validation fingerprint: `823664fd0f53a88014f361ba592838084ad660101a724e416f3ddffb507a42df`
- validator結果: PASS、open question 0、warning/error 0
- canonical rows: services 4、encounter pool 24、credit economy 10、dialogue 56、batch 5
- validator: `templates/chatgpt_pro_design_packets/tools/validate_submission.py`
- packet root: `dist/chatgpt_pro_design_packets/unpacked/Pokemon-Vega_CHATGPT-PRO_REWARD-ENCOUNTERS-V2_INPUT_20260820/`

## 固定仕様

- tierは `RANDOM / HABITAT / TYPE / RARE` の4つ。typed credit costは各1、BP直払いは
  `8 / 15 / 25 / 50`。playerは1回のtransactionでcreditかBPのどちらか一方だけを選ぶ。
- poolは各tier 6種、計24種。全行を一意にし、禁止Species/form/進行破壊をvalidatorで拒否する。
- 通常入口は `KANTO_OUTDOOR_VERMILION_CITY` の共有Scientist、
  `OBJHOST::KANTO_OUTDOOR_VERMILION_CITY::007`。Stage 40のobject占有・collisionを再監査する。
- encounter生成後、戦闘開始前に同じ個体をpendingとして永続化する。逃走、敗北、reset後は
  同じgenerated monへ無料で再戦でき、再抽選・再課金しない。
- 捕獲成功時にpendingを原子的にclearする。party/box満杯は支払い前に検査し、失敗時にcredit/BPを減らさない。
- 報酬遭遇battleはEXP、EV、賞金、drop、DexNav、研究ポイント、Raid、Factory副作用を無効にする。
  通常捕獲・図鑑登録は既存ownerへ委ね、特殊な個体ownerを新設しない。
- credit source 10件を固定する。Factory 3/7/14/21 milestoneは各一度限り、釣り新規捕獲、
  T23生態研究捕獲、BP voucher 4種を設計どおり接続する。
- credit、BP、pending、claimを同一transaction ledgerで扱い、save失敗やresetで二重付与・消失を起こさない。
- dialogue 56、batch 5をstable keyでcompileする。

## 実行

1. T23 Stage 40、ZIP、private guardのidentityを確認する。
2. 共通validatorをpacket rootと展開結果に対して再実行し、fingerprintと全row countを照合する。
3. 現行currency/save/battle/capture/Factory/研究hookとVermilion hostをrooted監査する。
4. 4 service、24 pool、10 source、56 dialogue、5 batchをcanonical dataへ正規化する。
5. typed credit、BP選択、pending mon、claim、atomic capture transactionを実装する。
6. Scientistの通常入力と10 source hookへ接続し、battle-local副作用maskを適用する。
7. expected-byte付き差分でStage 41を生成し、shared owner overlapを検査する。
8. focused test、全tier/支払/退出/save matrix、mGBA、clean rebuild、BPS往復を検証する。

## 必須成果物

- `content/reward_encounters_v2/**`
- `config/reward_encounters_v2.json`
- `overlays/reward_encounters_v2/**`
- `scripts/build_reward_encounters_v2.py`
- `scripts/rebuild_reward_encounters_v2_from_clean.py`
- `tools/mgba_reward_encounters_v2_smoke.c`
- `tests/test_reward_encounters_v2.py`
- `reports/generated/reward_encounters_v2_{audit,coverage}.json`
- `build/stages/41_reward_encounters_v2.gba`（Git管理外）
- Stage 40→41 BPS、clean→Stage 41 BPS、mGBA、save/reset、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T23 Stage 40とZIP identityが一致し、private原本を変更・追跡しない。
- [ ] 4 service、24 pool、10 source、56 dialogue、5 batchを欠落・重複0でcompileする。
- [ ] 4 tierのtyped credit cost 1とBP 8/15/25/50がexactで、一度に片方だけ支払う。
- [ ] party/box満杯、残高不足、cancel、保存失敗で支払い・pending・claimが変化しない。
- [ ] 生成個体を戦闘前に永続化し、逃走・敗北・reset後に同じ個体へ無料再戦できる。
- [ ] 捕獲成功時だけpendingがclearされ、再抽選・二重課金・個体複製が0。
- [ ] EXP/EV/賞金/drop/DexNav/研究/Raid/Factoryのbattle副作用が0で、通常図鑑登録は維持する。
- [ ] 10 credit sourceが各条件・once/repeatabilityどおりに発火し、Factory/T23 transactionを汚染しない。
- [ ] Scientistの通常field入力から全serviceへ到達でき、host/collision/object競合が0。
- [ ] T00〜T23、QOL、event、Mirage、Research、Factory/Raidの回帰がPASSする。
- [ ] changed byte declared span、ROM/RAM/save/map/hook overlap 0、clean rebuild/BPS/mGBAがPASSする。

## 禁止する完了判定

- pendingをRAMだけに置く、resetで再抽選する、支払い後に容量検査する実装をしない。
- creditとBPを同時消費または自動変換しない。
- host fixture、battle-local helper、CSVだけでDONEにしない。

## 完了

1. task固有build/check、全transaction matrix、mGBA、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T24 --summary "Reward Encounters V2をStage41へproduction統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T24:`で始まるcommitを作る。pushしない。
