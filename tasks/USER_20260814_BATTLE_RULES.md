# USER-20260814-BATTLE-RULES — 状態異常・急所・天候を固定CFRU-JP既定へ統一する

- Lane: `engine/qa`
- Depends on: `USER-20260814-FIRST-BATTLE-LOOP`
- Queue ID: `USER-20260814-BATTLE-RULES`

## 目的

現行releaseでVega処理とCFRU-JP処理のどちらが実際に有効かを実ROMhook単位で確定し、
麻痺を含む状態異常、急所、天候をsource-lock済みCFRU-JPの初期設定へ統一する。

## 実行

1. 麻痺速度補正・行動不能、やけど・毒・猛毒・眠り・凍り、急所倍率/段階、天候継続/補正/終了を監査する。
2. 固定CFRU-JP `e24a16f...` の既定defineとruntimeを期待値の正本にする。
3. Vega fallbackが残る経路をexpected-byte付きでCFRU処理へ接続し、二重適用を拒否する。
4. 通常戦・trainer戦・double・施設・Raidで同じrule ownerを使う。
5. 現在値と採用値を機械可読reportへ記録する。

## 受入条件

- [x] 各ruleについて現行owner、固定CFRU既定値、修正後ownerを証跡化する。
- [x] 麻痺、主要状態異常、急所、主要天候の固定RNG fixtureがCFRU既定値と一致する。
- [x] 同じダメージ・残ターン・状態更新が二重適用されない。
- [x] 通常戦、double、Factory Trial、Raidの対象回帰がPASSする。

## 完了

対象検証とログを更新し、queueをDONEへ変更してタスク単位コミットを作る。
