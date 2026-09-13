# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

WhiteOut設定元をbffdのCB2_EndTrainerBattle内0807FC50→0807FC5C→SetMainCallback2で固定し、1か所のcallback pointerと180bytesの施設限定shimを実装。候補fcda1507/CRC A15FAF9D。run34759726061/job103730310536のnative processはexit0、11261fで敗北、11405fで09FF4681、11444fでAfterBattle call後、11464fで元party復元、11516fで受付前idle。元600bytes/count1、marker/snapshot/pending/streak0、BP0/save counter2、入力barrier7・警告0。

原Actions/Pythonは終了済みscript pointer0を拒否してfailure/FAIL。原本は変更せず、exact field callback08055E75・AfterBattle進行・復元・idleの全遷移を必須にしたsource-only再検証を完了。新規emulator再実行0。敗北帰還修復は完了、勝利・交換・BP稼得/消費は未受入。

**次: 修復候補fcdaの既存AfterBattle復帰後に残る交換用単体選択ABIを、facility script 092CF729/092CF775と選択結果の読取先から固定し、最小修正する。今回完了の敗北帰還を再実行せず、変更影響のある交換経路からnative勝利・3勝BP稼得へ進む。**

同一fcdaの敗北帰還、同一bffdの旧敗北失敗、完了済みsource監査・ROM byte採取は再実行しない。交換ABIの変更が既存帰還/party復元へ影響する場合だけ影響区間を明記して再検証する。勝敗・HP・PP・RNGのhost注入、復元assertionやtimeoutの緩和は禁止。原Actions failureは保存し、source-only判定と混同しない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `dfe293f57b009e04274c5eb67dbb9c4e6cae74ec`。
上記はnative実行ソースHEAD。source-only再検証HEADとrunは最新証拠JSONに別記。記録commit自身のSHAを追記する無限更新はしない。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_bp_loss_return_verified.json`
- `content/modernization/pr16_bp_candidate_return_audit.json`
- `content/modernization/pr16_bp_loss_return_evidence/successor-compile-1-runtime-disassembly.txt.json`
- `scripts/pr16_bp_loss_return_successor.py`
- `overlays/facility_loss_return/facility_loss_return.c`
- `scripts/pr16_bp_loss_return_evidence.py`
- `scripts/build_facility_runtime.py`
- `overlays/facility_runtime/facility_runtime.c`
- `scripts/pr16_bp_trial_route.py`
- `content/modernization/pr16_bp_battle_return_evidence/reward-source-audit.json`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34733866168` / HEAD `f01149dfd6848623466fadf611a6599d1f22e1ca`。
受入済みはレンタル取消→元party600bytes/count復元→通常Save→fresh Continueの1ケース。受付special operand 0x2F→0x29の修正で実chooserへ到達。global special表・save layoutを変更していない。

最新診断: run `34759726061` / job `103730310536` / HEAD `dfe293f57b009e04274c5eb67dbb9c4e6cae74ec`。
照合抄録: `content/modernization/pr16_bp_loss_return_verified.json`。
WhiteOut設定元をbffdのCB2_EndTrainerBattle内0807FC50→0807FC5C→SetMainCallback2で固定し、1か所のcallback pointerと180bytesの施設限定shimを実装。候補fcda1507/CRC A15FAF9D。run34759726061/job103730310536のnative processはexit0、11261fで敗北、11405fで09FF4681、11444fでAfterBattle call後、11464fで元party復元、11516fで受付前idle。元600bytes/count1、marker/snapshot/pending/streak0、BP0/save counter2、入力barrier7・警告0。

原Actions/Pythonは終了済みscript pointer0を拒否してfailure/FAIL。原本は変更せず、exact field callback08055E75・AfterBattle進行・復元・idleの全遷移を必須にしたsource-only再検証を完了。新規emulator再実行0。敗北帰還修復は完了、勝利・交換・BP稼得/消費は未受入。

開始時fixtureと観測境界後native入力のみを区別し、7 host-write barrier・timeout・判定条件を緩めない。

## 候補identityと残件

SHA-256 `fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879` / 33554432 bytes / CRC32 `A15FAF9D`。敗北帰還修復を検証した開発候補。取消/Save/Continue正式受入は従来bffd上の証拠であり、全候補regressionや最終製品SHAへの昇格ではない。

正式physical残件（台帳から照合）:

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_NATIVE_BP_EARNING_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- `PHYSICAL_CIRCUS_ADMISSION`

P08ゲート:

- `FINAL_NATIVE_ACCEPTANCE`
- `RELEASE_DECISION`

1戦敗北→施設受付前idle→元party600bytes/count1復元はfcdaで検証完了。次は交換operand092CF729/092CF775のsingle-selection ABI。Trial reward0はID、基本9BP。manifest/Stage28追加BP3とStage29 repeat1/2の条件は既存読取証拠を再利用するが、候補上の勝利・全completion chain・最終付与量は未受入。初期chooser、取消/Save/Continueと今回の敗北帰還を変更影響なしに再実施しない。

BP、Ringの正規story取得、policy通常UI、Circus実受付/実戦を進める。physical gap完了後に最終SHA/size/CRCを固定し、owner/ROM範囲/runner/fixture/契約の変更影響台帳で継承・代表回帰・完全再実行を選ぶ。最後にclean-ROM独立二重生成・配布patch往復・manifest/backup/rollback/混入検査・release判定。

## 再実行・過大主張の禁止

- run34759726061のnative敗北帰還は原stdout/traceの再検証で完了。原Actions failureをsuccessへ改作しない。同一fcda敗北/同一bffd失敗/完了source監査/候補byte採取を再実行しない。取消・Save・Continue受入原本は無変更。
- 履歴: run34757633314の固定CFRU source監査は19tests PASS、宣言1件のみでsource側ownerは未解決だった。旧schema1 owner=trueは不採用のまま保持。その後run34758866475のcandidate bytesで実分岐を特定し、今回のnative敗北帰還修復を完了。固定source再scan・byte採取・受入取消/Save/Continueは繰り返さない。
- run34749370272の旧bffd敗北→WhiteOut→party未復元はfailure原本で保持。その修復影響区間はrun34759726061のfcda native原本とsource-only判定で検証済み。同一条件を再実行しない。
- 取消・元party600bytes復元・通常Save/fresh Continueの受入を変更影響なしに再実行しない。
- special 0x2F→0x29の最初のchooser原因調査と3体選択診断を、同一入力で単独再実行しない。次の停止点まで延長する。
- run34739491272の2回目確定→5D→battle struct→敵3体→実action到達を変更影響なしに単独再実行しない。次の未観測区間へ延長する。
- run34741232621の技選択・PP消費・次action callback3925fは、source影響なしに単独再実行しない。失敗run34741024241はfailureのまま保持する。
- P03 fixed-form5件、generic FORM、P06、P07ほか完了済み領域は変更影響台帳で必要性が出るまで再オープンしない。
- CircusのF0はbacksprite table誤読。decoder追加やraw403A直接書込みを入場証拠にしない。
- Ring未発見を不存在と断定せず、fixtureやtrainer-authored policyを通常供給/UI受入へ読み替えない。
- ROM/save/private入力/credentialを新規追加しない。既存公開方針と過去guard失敗は保持し、秘密情報の検査を無効化しない。

## 次セッションへ残す更新手順

正本receipt/台帳を必要時だけ更新→このJSONの観測/受入/次の1手を更新→python3 scripts/pr16_resume.py render→checkとfocused tests→両ログへ追記→同一commitで保存する。

```bash
python3 scripts/pr16_resume.py render
python3 scripts/pr16_resume.py check
python3 -m unittest discover -s tests -p test_pr16_resume.py -v
```

`check`は読取専用。hashの変更だけで証拠を追認しない。対象sourceが変わった場合は適用範囲を再評価する。
push直前にbranch HEADを再取得する。進んでいれば差分を再照合してから統合し、force pushや他セッションの変更上書きをしない。

実行したこと、観測できたこと、正式受入、未完、次の1手、run/job、検証結果を分離して記録。実行中runがあればID/対象HEAD/次の確認を記録し、完了を推測しない。

## 履歴の位置づけ

履歴は根拠が必要な箇所だけ読む。PR本文・日付・一般キュー・会話の記憶から最新停止点を上書きしない。

- `docs/PR16_BP_TRIAL_RESUME_20260913_JA.md`
- `docs/PR16_NATIVE_SUPPLY_RESUME_20260912_JA.md`
- `content/modernization/pr16_native_supply_handoff.json`
- `PR body`

PR本文は更新失敗の履歴があり、再開入口に使わない。受付取消checkpointの `next` も受入時点の履歴であり、次の作業順はこの文書を優先する。

## Checks・releaseの境界

native HEADdfeのActionsを再照合。専用run34759726061はPython終了状態検査のfalse negativeでfailure、raw nativeはexit0/PASS。新規source-only検証は別runであり、原失敗の取消・全Checks成功・BP受入とは主張しない。記録commitのChecksはpush後に別照合。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
