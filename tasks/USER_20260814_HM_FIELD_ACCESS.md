# USER-20260814-HM-FIELD-ACCESS — HM所持だけで対応フィールド技を使用可能にする

- Lane: `engine/content/qa`
- Depends on: `USER-20260814-FIRST-BATTLE-LOOP`
- Queue ID: `USER-20260814-HM-FIELD-ACCESS`

## 目的

対応するひでんマシンを入手した時点から、手持ちポケモンへの習得・選択・技枠を必要とせず、
対応フィールド能力をマップ上で常時使用可能にする。

## 実行

1. Vega全field moveのitem、badge、party move、map permission、script gateを監査する。
2. 解禁の正本を「対応HMをバッグに所持」へ統一し、ポケモンの習得有無と適性判定を外す。
3. HM入手前、使用禁止map、対象のない地形、script lock中は従来どおり拒否する。
4. field animation/実行主体は既存UIを再利用し、技を覚えていない個体へ一時的に技を書き込まない。
5. HMは非消費、save/load後もバッグ所持から同じ結果を導出し、Vega story flagを新規流用しない。

## 受入条件

- [x] 全対応HMで入手前FAIL、入手直後PASSを実ROMまたは同一runtime fixtureで確認する。
- [x] 手持ち0体・未習得・習得済みの差でfield利用可否が変わらない。
- [x] 使用禁止map/地形、script lock、HM未所持の安全境界を維持する。
- [x] HMを忘れてもfield能力を失わず、save/load後も同じである。
- [x] Vegaのstory進行、warp、map object、既存HM入手eventを壊さない。

## 完了

対象検証とログを更新し、queueをDONEへ変更してタスク単位コミットを作る。
