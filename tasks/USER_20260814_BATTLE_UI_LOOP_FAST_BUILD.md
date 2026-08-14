# USER-20260814-BATTLE-UI-LOOP-FAST-BUILD — 戦闘UI・アクタシ初戦ループ・高速差分ビルドを修正する

- Lane: `engine/ui/build/qa`
- Depends on: `USER-20260814-QOL-RELEASE`
- Queue ID: `USER-20260814-BATTLE-UI-LOOP-FAST-BUILD`

## 目的

実機相当の通常戦で確認された、技選択画面にタイプ一致・相性表示が出ない問題と、
アクタシ選択時の最初のライバル戦で無名の特性通知と行動順メッセージが反復する問題を
自然発生経路から修正する。あわせて、検証済み中間成果を再利用する開発用差分ビルドを整備し、
変更確認のたびに全工程を再構築しない運用へ改める。

## 実行

1. Deltaエクスポートは私有原本として不変に扱い、形式を識別できる範囲で再現補助に使う。
2. アクタシを選ぶ通常の初戦を開始し、行動選択から通知発生、battle script復帰まで追跡する。
3. 技選択画面の通常入力経路からtype、STAB、有効度表示とL/Rモードの詳細画面が実際に描画されることを確認する。
4. 変更箇所に必要な後段stageだけを再生成する開発用コマンドを追加し、入力ハッシュと上流成果を検査して再利用する。
5. 完成ROMで自然発生経路を再検証し、再現可能なpatchとROMを生成する。

## 受入条件

- [x] Delta原本を変更・追跡せず、読める場合はROMまたはbattle stateの識別情報を記録する。
- [x] アクタシ選択時の初戦が行動選択後も進み、無名の特性通知や「こうどうがはやくなった！」が反復しない。
- [x] 正常なQuick Claw、Custap、Quick Drawの行動順効果と通知は維持される。
- [x] 通常の技選択操作でtype/STABと抜群、いまひとつ、無効の表示が実damage判定と一致し、等倍・タイプ不一致は元CFRUどおり空欄になる。
- [x] ボタン設定L/RでLを押すと、元CFRUの技名・接触・威力・命中詳細を開閉できる。
- [x] single/double、trainer/wild、および既存のFactory/Raid経路で入力と画面復帰が壊れない。
- [x] 検証済み中間成果を使う差分ビルドが全工程の再生成を避け、同一入力で決定的なROMを短時間に生成する。
- [x] 対象検証、ログ、version履歴、配布用patch/ROMを更新し、タスク単位コミットを作る。

## 完了

対象検証と実測値を記録し、`design/run_log.md` / `design/version_log.md` / `design/current_state.md`を更新する。
`python3 scripts/taskctl.py done USER-20260814-BATTLE-UI-LOOP-FAST-BUILD --summary "..."` 後に
`USER-20260814-BATTLE-UI-LOOP-FAST-BUILD:` で始まるコミットを作る。
