# USER-20260816-ACQUISITION-EVENTS — 全コレクション対象の入手方法と取得イベントを実ROMへ統合する

- Lane: `content/engine/save/maps/qa/release`
- Depends on: `T18`, `USER-20260815-SPECIES-NAME-LENGTH`
- Queue ID: `USER-20260816-ACQUISITION-EVENTS`
- Baseline: v1.3.9 / commit `fb2dba1` / stage 25 SHA-256 `0f7406c70021adf9778f0e7a9220f4e014feaac73d7e988ba39700a63be97fcd`
- User package: `Pokemon-Vega_Acquisition-Design_20260815.zip` / SHA-256 `d96e26b571855c89f112674853165359273564b771f2be5bf29d63b80adfb6ed`

## 目的

ユーザー提供の取得設計パッケージをv1.3.9の実ROM ABIに適合させ、
1,206種のコレクション対象と10種の有効化フォームに対する入手経路を、
野生・進化・ギフト・タマゴ・復元・固有捕獲イベントとして遊べる形で完成させる。

## 実行

1. 受領ZIPを`userfile/imports/**`の読み取り専用原本とし、ハッシュ・安全性・v1.3.7前提と現行v1.3.9の差を監査する。
2. 201取得イベント、24個のclean FireRed由来host object、解禁、コレクションledger、会話と検証ケースを再生可能な正本へ取り込む。
3. 取得transaction、捕獲後確定、中断復帰、セーブ移行、party/PC満員、再受取防止を実ROM adapterで実装する。
4. 内部管理Speciesの野生混入を構造解析で修正し、交換進化はリンクケーブル代替へ安全に変換する。
5. stage 25を入力にstage 26を生成し、実map object・実戦闘・save/reload・到達性・BPS往復を検証してreleaseを更新する。

## 受入条件

- [x] パッケージ正本の1,206種と10有効化フォームが全て少なくとも1つの到達可能な取得経路を持つ。
- [x] 201イベントを24個の既存設計hostへ結合する。T17で省略されたclean FireRed由来objectだけを復元再利用し、新規設計objectを増やさず、元のobject予算とpointerを実ROMから再検証する。
- [x] 固有捕獲は捕獲成功時のみclaimされ、撃破・逃走・リセットで失われず、捕獲済みの複製を禁止する。
- [x] ギフト・タマゴ・化石復元はparty/PCと入力道具をpreflightし、失敗時に渡し済み・消費済みの片側状態を残さない。
- [x] 現行2 KiBセーブ台帳の予約領域に版管理240 byte acquisition blockを割当て、新規・旧save・中断transactionを移行できる。
- [x] 内部Species ID 282の野生2件は公式ストライクID 255へ修正され、その他の野生テーブルbyteは不変である。
- [x] 交換進化30経路がリンクケーブルと必要持ち物のルールを保った通常プレイ進化になる。
- [x] コンテンツ生成・negative test・2,035 exact case・野生sanitize・host graph・allocator overlap・決定性・BPS往復がPASSする。
- [x] libmGBAで解禁前/後、取得、捕獲後確定、save/reload、中断復帰、party満員を実ROM確認する。
- [x] release、日本語配布資料、ログ、version履歴、task状態を同期し、タスク単位commitを作る。

## 完了

受入条件を全て実測して`design/run_log.md` / `design/version_log.md` /
`design/current_state.md`へ記録し、`design/tasks_next.md`の本タスクだけを`[>]`から`[x]`へ変更する。
`USER-20260816-ACQUISITION-EVENTS:`で始まるcommitを作る。
