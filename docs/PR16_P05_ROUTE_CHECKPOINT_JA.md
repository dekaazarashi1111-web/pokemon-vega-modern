# PR16 P05実取得のデータ成功と表示不合格 — 2026-09-11

**製品・P05・ショップ画面全体は未合格です。** 現在の残件は `content/modernization/p08_remaining_work.json`、今回の正確な記録は `content/modernization/pr16_p05_route_acceptance.json`。

## 新しい実ROM実行と、合否を分ける境界

run **34568373963**、実行HEAD `cd0f07c9c190b9e5a84f36ef3addd9e18259e3c7`。10プロセス・20コア。Factoryのマップ96/5、実NPC local14 (24,19) に話しかけ、5品ずつの一覧を操作しました。オーダイル・シビルドン・カエンジシ・メガニウム・ドリュウズ・スコヴィランの6種の石の購入、最初のページと後のページでの取消、15BPの不足、リング未所持の拒否を確認しています。

在庫全体・BP・手持ち全600 bytesの非対象変更なし、成功時だけ16BP消費と自動保存、10件すべての通常Start保存・別コアContinueがデータ検査に合格しました。再開後の購入済み除外も9件の解禁済みケースで確認。マップ・リング・BP・claim初期状態は試験fixtureです。石は観測開始後に実受付で取得しますが、リングの通常取得・BP稼ぎ・自然捕獲・取得個体の戦闘を確認したものではありません。観測中の7種類のhost書込みAPIは禁止し、その拒否を検査しています。

**画面原本の確認は不合格です。** メニューの表示中と終了後に背景のタイル崩れがあり、購入だけでなく取消・BP不足でも再現します。一覧を開かないリング未所持の対照画面には同じ崩れがありません。スクリーンショットのハッシュと確認対象は受入JSONの `visual_review` に保存しています。原因は未確定です。データ用runnerのPASSを画面・ショップ全体の合格へ読み替えず、外側は `DATA_PATH_PASS_VISUAL_REJECTED`、`shop_visual_acceptance=false` です。

候補は変更していません。SHA-256 `635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e`、33554432 bytes。旧成功を今回の10件に足していません。

## P05の静的経路診断

run **34567225043**、HEAD `ca9a0489bbd2bd68d84b9f208f42bb9b83025308`。5340 root中5334を読み、6不正rootと1未知命令を明示したまま探索しました。野生表265ヘッダ中header139の釣りinfo参照は未解決です。初回座標ownerのspecies411の地上遭遇候補は1/113と1/118にありますが、これは捕獲成功ではありません。共有変数0x403Aやnative関数の存在だけでCircusの入場と断定していません。実行した対象unit testは16件で、エミュレータ実行は0件です。

## Gitに残した原本と再検査

`content/modernization/pr16_p05_route_evidence/<run>/original.zip` と `actions.json` を保存。受入JSONはZIPのハッシュ・CRC・安全性、Actionsの成功した全stepと実行HEAD、検証コード、raw stdout/process、7書込み拒否を再照合して生成します。原本のデータPASSや画面を編集しません。ROM/saveを新しい原本へ入れていません。

`python3 scripts/pr16_p05_route_checkpoint.py` と `python3 scripts/pr16_refresh_current_view.py` で再検査できます。既存の最終受入/P03忘却の両生成経路にも表示不合格が残ります。保存・再検査は追加の実ROM件数に数えません。

## 次に閉じる作業

ショップ表示の原因修正と画面回帰、自然捕獲および通常取得から戦闘への接続、実Circus受付・入場、残るP03/P07供給経路の原本対応、P08の最終統合とclean ROMから全工程の独立2回生成・配布。Rotom/Happiny/Pichu/進化/共有技の旧成功、P06の内外整合、publicと無料わざメモリー承認は保持します。Stage62・実プレイsave・原本・履歴は変更せず、PR #16は未マージです。
