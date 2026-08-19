# USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION — Trainer ChangeKit 01〜06最終統合

- Lane: `content/engine/map/save/qa/release`
- Depends on: `USER-TRAINER-V5-STAGE33-TOHOKU-BATCH03`
- Queue ID: `USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION`
- Baseline: post-v1.4.0 stage 34 / SHA-256 `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`
- Status: `DONE`

## 目的

AUTHORING_KITとTask 01〜06を検証・統合し、全trainer encounter、party/member、会話、報酬、
物理binding、再戦、DOUBLE、Mega／Zワザ／ダイマックス／テラスタルをclean ROMへ接続する。

## 自動解決した入力矛盾

- 公式原本でTask 05 validatorが`ENC_TOHOKU_REF_1012`のformat不整合によりFAILする。
- Tohoku 1,101行中51行は`trainerbattle`でなくtrainer flag命令で、対応する実戦闘は別行が所有済み。
- 1,050実参照は1,030 command addressしか持たず、固有party一対一契約と矛盾する。
- Kanto 3戦がStage 34取得イベントの同一object／座標と競合する。
- Kanto会話本文は現行charmapでencode不能で、承認済み正規化本文またはrenderer入力がない。

詳細は`reports/TRAINER_CHANGEKIT_FINAL_INPUT_BLOCKER_20260819.md`を正とする。

## 再開条件

- [x] 51行は同一identityの固有再戦／Trainer Archive consumerへ昇格し、元flag命令を上書きしない。
- [x] 共有commandは正規physical ownerを1件に固定し、余剰partyを固有再戦／Trainer Archive consumerへ接続する。
- [x] 受領原本を不変とし、Task 05補正working copyを再manifest化した全7validatorがPASSする。
- [x] Kanto競合3件は取得hostを保持し、同mapの最近傍安全tileへ決定的に再配置して再監査する。
- [x] Kanto会話は現行1-byte charmapへかな正規化し、対応表とwidth検証を残す。

## 完了条件

- [x] 全正本data、serializer、runtime、event consumerを統合する。
- [x] clean FireRed日本版Rev.0からROMを再構築する。
- [x] focused、coverage、rematch/save、DOUBLE、gimmick、mGBA quick/fullをPASSする。
- [x] ログ・version・commit・完全版ZIPを作り、fresh展開検証をPASSする。
