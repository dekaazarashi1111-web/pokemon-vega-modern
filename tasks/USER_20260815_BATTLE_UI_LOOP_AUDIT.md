# USER-20260815-BATTLE-UI-LOOP-AUDIT — 直前修正を再監査して実症状を直す

- Lane: `engine/ui/build/qa`
- Depends on: `USER-20260814-BATTLE-UI-LOOP-FAST-BUILD`
- Queue ID: `USER-20260815-BATTLE-UI-LOOP-AUDIT`

## 目的

直前コミットがユーザー報告の実状態を覆っているかを再監査し、アクタシの初戦ループと
技選択UI未反映を、Delta exportおよび実メニュー経路から特定して修正する。検証済みstageを
再利用し、全chainを再構築せずに識別可能な新ROMを生成する。

## 受入条件

- [x] 直前2コミットの変更と生成ROM hashを監査し、旧ROMとの同一性・テスト漏れを記録する。
- [x] Delta exportを原本不変で読み、アクタシのAbility 64とQuick Draw通知loopを特定する。
- [x] Ability 64の不正indicatorを破棄し、正規Ability 260のQuick Draw通知は維持する。
- [x] 実際の「たたかう→技選択→カーソル移動」でtype/effect adapterを通り、抜群labelとpaletteを描画する。
- [x] fixed CFRUでinline済みだった旧UIが新表示を上書きしない。
- [x] stage 20以前を再利用する差分chainでstage 21〜25、final、BPSを再生成する。
- [x] 32 MiB v1.3.4 ROMを旧ファイルと別名でWindows Downloadsへ配置する。
- [x] 対象テスト、ログ、version履歴を更新し、タスク単位commitを作る。
