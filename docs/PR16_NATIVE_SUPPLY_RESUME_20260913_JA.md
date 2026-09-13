# PR #16 再開点 — 2026-09-13 JST

## 今回の新規受入

**BP party chooserの製品側不具合を修正し、レンタル取消→通常Save→fresh Continueを1ケース・2 fresh coresで受入。BP獲得自体は未受入。**

正本: `content/modernization/pr16_bp_chooser_checkpoint.json` / `content/modernization/pr16_bp_chooser_receipt.json`。旧20260912 handoffは履歴として保持する。

- ROM: `bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92` / 33554432 bytes / CRC32 `635A3CE5`。最終製品SHAではない。
- native原本: run 34733866168 / job 103661602964 / HEAD `f01149dfd6848623466fadf611a6599d1f22e1ca`。
- artifact 10310735119 / 704616 bytes / SHA-256 `3d4be68d90ba9537bc337b3ab4521cea84bd2dbc924b56ab14d9ce2c74e4cf1f`。
- 実受付→Trial→6体候補→実chooser→B→「たいせんを やめますか？」→native「はい」→元party600 bytes/count完全復元、snapshot/marker/pending消去、BP0/Bag不変→通常Save counter2→3→旧core破棄→別coreでContinue。開始map/進行/party/Factory ledgerは明示されたfixtureで、観測境界後は7 host-write barrierの下でnative入力のみ。

## 確定した原因と修正境界

実df8 ROM special表0x08163068の0x2Fは0x080CBF8D（bx lr）。その直後のwaitstateがScriptContextを停止するが再開役が存在しない。0x29は0x080A160D→InitChooseHalfPartyForBattleである。受付scriptの0x092CF629にあるU16 operandを2f00→2900へ変更（実差分1 byte）。global special表・過去buildレシピ・save layoutは変更していない。

run34733429516はこの修正により実chooserへ到達したが、取消確認にBだけを送って失敗した。失敗を改称せず、次runでnative Aを1回追加した。fixture/timeout/復元判定は緩和していない。元のC controllerとPython契約はhash固定で保持し、生成時の差分を全てartifactに記録。

## 重複しない再開順

次は**3体選択→実battle launcher/selected-order bridge→3勝9BP**。build_facility_runtimeのbattle/exchange specialも実ROM bindingを確認してから進める。勝利・初回/繰返し・敗北/未完走/取消/不正選択/2勝以下・通常Save/fresh Continue・新しく得たBPのshop消費は未受入。取消受入の再実行は変更影響がある場合だけ。

その後Ringのstory giver、policyの通常UI、Circus施設番号3の実受付/warp/実戦を閉じる。F0はbacksprite table誤読でありdecoder追加不要。完了済みfixed-form5件/P03/P07ほかは再オープンしない。

## 最終化と証拠境界

正式残件はphysical4件＋P08ゲート2件。全製品修正後に最終SHA/size/CRCを固定し、旧ケース・旧/新SHA・owner・ROM範囲・runner/fixture/契約差分による継承/代表回帰/完全再実行台帳を作る。今回の2回の同一operand適用はclean-ROM独立二重生成ではない。clean-ROM二重生成、clean patch往復、配布manifest/backup/rollback/混入検査、release受入は未完。

開始時HEAD f344はChecks5成功/1失敗。新native成功はその失敗を全緑へ書き換えない。後続HEADのChecksは別に確認する。PR本文更新は接続ツールの安全チェックで拒否され未反映。この文書とJSONを現行再開点とする。

public状態・既存tracked originals・歴史的guard FAILは保持。新しいROM/save/private input/credentialを混入させない。merge/active baseline切替/draft解除/release公開は行っていない。
