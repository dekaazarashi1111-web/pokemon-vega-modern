# USER-20260815-ECOLOGY-RUNTIME — 外来生態293行を実ROMへ接続する

- Lane: `engine/content/qa/release`
- Depends on: `USER-20260815-RUNTIME-STABILITY`
- Queue ID: `USER-20260815-ECOLOGY-RUNTIME`

## 目的

v1.3.6で未接続だった夜間・大量発生・朝昼／ずつき・釣り・DexNav相当を含め、
トーホク外来生態設計293行を実ROMの遭遇入口へ接続する。emulatorのRTC設定に依存して
確認不能にならないよう、現在modeの確認と手動切替を行えるキーアイテムも追加する。

## 受入条件

- [x] 設計293行が0件保留でruntime tableへ変換され、全method layerを実ROMで走査できる。
- [x] 通常歩行、釣り、朝昼、夜、日替わり大量発生、屋内を含む隠れ遭遇を実入口で生成できる。
- [x] RTC自動modeと、朝昼・夜・群れ・隠れ探索の手動modeを併設する。
- [x] 「せいたいレーダー」を1個目のバッジ報酬と既存save用シオウ補完へ接続する。
- [x] 既存遭遇表、trainer開始、初戦、戦闘HELP/UI、HP表示、Factory/Raidの回帰を維持する。
- [x] 検証済みstageを再利用する高速buildでv1.3.7最終ROMを生成する。
- [x] ログ、version履歴、配布資料を更新し、タスク単位commitを作る。
