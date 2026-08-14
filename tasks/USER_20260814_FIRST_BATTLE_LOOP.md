# USER-20260814-FIRST-BATTLE-LOOP — 初戦の行動順メッセージ無限ループを修正する

- Lane: `engine/qa`
- Depends on: `v1.2.0 stage 20`
- Queue ID: `USER-20260814-FIRST-BATTLE-LOOP`

## 目的

主人公がアクタシを選んだ場合のハクジ研究所・最初のライバル戦で、相手リープンの
「？？？？？？？？で こうどうが はやくなった！」が行動選択後に無限反復して進行不能になる
不具合を、実ROMのbattle schedulerまで追跡して修正する。

## 実行

1. stage 20、Trainer ID 327、Species ID 1、Item ID 0、Ability ID 65の実データを固定して再現する。
2. Quick Claw / Custap / Quick Drawの行動順indicator、battle script復帰、item/ability表示のどこで状態が再生成されるかを動的traceする。
3. 原因箇所をsource生成またはstage 21の最小runtime overlayで修正し、入力ROMや既存stageを上書きしない。
4. アクタシ・ファマー・リープンの3分岐すべてで初戦を進行させる。
5. 正常なQuick Claw、Custap、Quick Drawは1ターンにつき必要回数だけ通知され、行動順効果自体は維持する。
6. 重い全再構築は行わず、v1.2.0固定成果を再利用した対象stageと実ROM回帰だけを実行する。

## 受入条件

- [x] アクタシ選択時の初戦が1ターン以上進み、同一通知が無限反復しない。
- [x] Item ID 0のリープンでitem発動通知と「？？？？？？？？」が表示されない。
- [x] 3御三家分岐で技選択、行動、HP/PP更新、次ターン入力まで到達する。
- [x] Quick Claw / Custap / Quick Drawの正規fixtureは通知1回以下で効果を維持する。
- [x] stage、allocation、実ROM smoke、release patch往復が決定的にPASSする。

## 完了

対象検証、`design/run_log.md` / `design/version_log.md`、`design/current_state.md`を更新し、
`python3 scripts/taskctl.py done USER-20260814-FIRST-BATTLE-LOOP --summary "..."` 後に
`USER-20260814-FIRST-BATTLE-LOOP:` で始まるコミットを作る。
