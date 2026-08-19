# USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION — Trainer ChangeKit 01〜06最終統合

- Lane: `content/engine/map/save/qa/release`
- Depends on: `USER-TRAINER-V5-STAGE33-TOHOKU-BATCH03`
- Queue ID: `USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION`
- Baseline: post-v1.4.0 stage 34 / SHA-256 `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`
- Status: `BLOCKED_INPUT_DESIGN`

## 目的

AUTHORING_KITとTask 01〜06を検証・統合し、全trainer encounter、party/member、会話、報酬、
物理binding、再戦、DOUBLE、Mega／Zワザ／ダイマックス／テラスタルをclean ROMへ接続する。

## ブロック理由

- 公式原本でTask 05 validatorが`ENC_TOHOKU_REF_1012`のformat不整合によりFAILする。
- Tohoku 1,101行中51行は`trainerbattle`でなくtrainer flag命令で、対応する実戦闘は別行が所有済み。
- 1,050実参照は1,030 command addressしか持たず、固有party一対一契約と矛盾する。
- Kanto 3戦がStage 34取得イベントの同一object／座標と競合する。
- Kanto会話本文は現行charmapでencode不能で、承認済み正規化本文またはrenderer入力がない。

詳細は`reports/TRAINER_CHANGEKIT_FINAL_INPUT_BLOCKER_20260819.md`を正とする。

## 再開条件

- [ ] 51行の除外または新規物理戦仕様が確定している。
- [ ] 共有commandのdedupeまたはcaller-aware dispatch仕様が確定している。
- [ ] Task 05を含む全validatorが公式原本に対してPASSする。
- [ ] Kanto競合3件の代替配置とcollision／sightline証跡がある。
- [ ] Kanto会話の実装可能な正本本文がある。

## 完了条件

- [ ] 全正本data、serializer、runtime、event consumerを統合する。
- [ ] clean FireRed日本版Rev.0からROMを再構築する。
- [ ] focused、coverage、rematch/save、DOUBLE、gimmick、mGBA quick/fullをPASSする。
- [ ] ログ・version・commit・完全版ZIPを作り、fresh展開検証をPASSする。

