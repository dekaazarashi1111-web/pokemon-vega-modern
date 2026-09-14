# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

2026-09-15: run34854927678/job104011896602で同一cedd candidateを1processのままnative 2・3戦目まで勝利。BP 0→9、streak3、pending0、元party600bytes復元をscoped受入。受入済み取消/Save/Continue再実行0。BP消費・Ring/policy/Circus・releaseは未受入。

**次: 同じcandidateで稼得した9 BPを通常BPショップUIから消費し、購入物・残高・通常Save/fresh Continueをnativeに検証する。**

受入済みrun34854927678と取消/Save/Continueを変更影響なしに単独再実行しない。稼得9 BPの通常UI消費、購入物、残高、通常Save/fresh Continueを観測するまでRing/policy/Circusやrelease判定へ進まない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `d9d0dfefcc524b35993eab0f98ae7b6849133644`。
同一cedd candidateの保持済みprefixを変更せず、未観測だったnative 2・3戦目と報酬completionまで延長して正確な9 BP稼得を固定した実装HEAD。今回の変更は証拠・checkpoint・引継ぎ・検証・ログの記録のみ。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_bp_three_win_reward_verified.json`
- `content/modernization/pr16_bp_chooser_checkpoint.json`
- `scripts/pr16_bp_three_win_reward_native.py`
- `scripts/build_bp_shop_runtime.py`
- `manifests/facility_rewards.csv`
- `overlays/factory_reward_runtime/factory_reward_runtime.c`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34854927678` / HEAD `d9d0dfefcc524b35993eab0f98ae7b6849133644`。
正式受入はレンタル取消→元party600bytes/count復元→通常Save→fresh Continueの既存1ケースと、同一cedd candidateでnative 3勝→BP 0から9→元party600bytes復元のscoped 1ケース。BP消費、native exchange単体の正式受入、Ring/policy/Circus、releaseは含まない。

最新scoped受入: run `34854927678` / job `104011896602` / HEAD `d9d0dfefcc524b35993eab0f98ae7b6849133644`。
照合抄録: `content/modernization/pr16_bp_three_win_reward_verified.json`。
run34854927678/job104011896602で同一cedd candidateを1processのまま2・3戦目までnative勝利。BP 0→9、streak3、reward pending 0、snapshot無効化、元party600bytes復元を観測し、P05 native BP稼得gapをscopedに閉じた。受入済み取消/Save/Continue再実行0。BP消費・exchange正式受入・releaseは未受入。

run34854927678の7 host-write barrier、timeout、candidate/source identity、正確な9 BP結果を緩めない。必要な場合は同じprefixをショップ消費まで一続きで延長し、3勝区間だけを単独再実行しない。

## 候補identityと残件

SHA-256 `ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b` / 33554432 bytes / CRC32 `3EB17B36`。保持wrapper接続済みcandidate。同一playthroughのnative 3勝と正確な9 BP稼得までscoped受入済み。BP消費・Ring/policy/Circus・最終製品SHAは未受入。

正式physical残件（台帳から照合）:

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- `PHYSICAL_CIRCUS_ADMISSION`

P08ゲート:

- `FINAL_NATIVE_ACCEPTANCE`
- `RELEASE_DECISION`

run34854927678/job104011896602で同一cedd candidateを1processのまま2・3戦目までnative勝利。BP 0→9、streak3、reward pending 0、snapshot無効化、元party600bytes復元を観測し、P05 native BP稼得gapをscopedに閉じた。受入済み取消/Save/Continue再実行0。BP消費・exchange正式受入・releaseは未受入。

獲得9 BPの通常ショップ消費を閉じ、Ringの正規story取得、policy通常UI、Circus実受付/実戦を進める。physical gap完了後に最終SHA/size/CRCを固定し、owner/ROM範囲/runner/fixture/契約の変更影響台帳で継承・代表回帰・完全再実行を選ぶ。最後にclean-ROM独立二重生成・配布patch往復・manifest/backup/rollback/混入検査・release判定。

## 再実行・過大主張の禁止

- run34762342982の交換ABI source/host検証と2operand修正は完了。9tests・二重限定生成をnative交換/BP受入と混同せず、次は未観測の勝利後区間へ進む。
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
- run34770280751の単体交換＋次戦開始は診断原本を再利用。次戦個体同一性とBP報酬まで受入済みと読まない。
- 個体追跡run34774194505の原本を再利用。追跡完了と個体保持/BP受入を混同しない。
- WIP48a36ca/owner run34785149994を再利用。host predicate PASSはruntime修復やnative保持成功を意味しない。対象コード変更時だけ対応回帰を再実行。
- run34802013676のtarget callsite/ABI限定監査（12tests、cache alias 2件、linked.o byte-identical、predicate 0x090DD51C、player build 0x090DD538、0x090DD2E6再合流）は完了。runtime/保持/BP受入とは混同せず、対象source・candidate・cache契約の変更なしに再実行しない。
- run34825059791の限定runtime接続・交換個体保持（600byte/3個体/次戦action）は完了。同一candidate/sourceで単独再実行せず、run34854927678の3勝9BP受入prefixとして再利用する。
- run34854927678の同一playthrough native 3勝・BP 0→9・元party600bytes復元はscoped受入済み。変更影響なしに単独再実行せず、次は稼得BP消費の未観測suffixへ延長する。

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

実装HEAD d9d0dfefcc524b35993eab0f98ae7b6849133644 の専用run34854927678/job104011896602はsuccess。focused 7 tests、同一candidate、新規process1、受入済みcase再実行0、2/3戦目勝利、BP 0→9、streak3、pending0、元party600bytes復元、7 host-write barrierを確認。BP消費・native exchange正式受入・Ring/policy/Circus・releaseは未受入。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
