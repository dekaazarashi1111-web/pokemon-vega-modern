# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

WIP: 次戦限定predicateとhost4回帰はPASS、固定candidateのowner監査run34785149994もSUCCESS。target呼出位置/ABIの確定・runtime接続・修復後native保持検証は未完。追加コード反映2回がOpenAIのツール安全性確認でブロックされたため、以後は解析/接続を停止して記録のみ実施。GitHub権限不足ではない。

既存native診断: 交換確定後から次戦までにparty個体が変化し、交換個体保持は不成立。 38個の同時600byte/個体snapshotを照合。交換確定17345f、次戦action19169f。 PID/OT/species/movesを比較し、次戦active battlerと実partyの一致も検証。frame境界観測でありCPU関数entry/returnの証明ではない。 次戦chooser17389fでは600byte一致。最初の変化は17770f、callback2=0x0800FEC5/script=0x092CF6A5で3個体がゼロ。actionで88byte差・新規3個体を確認。保持修復は未完。

**次: 保存済みWIPとowner監査を再利用し、未接続のtarget呼出位置/ABI照合・最小successor接続・修復後native個体保持検証を完了する。既存host4回帰/owner監査の単独再実行や同じtool-blocked要求の反復は行わず、保持確認前に2/3戦目・BP報酬へ進まない。**

今回の読取専用診断・初勝利・交換の単独再実行はしない。新規修復/報酬ケースへ同一prefixを延長する時だけ使用する。取消Save/Continue等の受入済みケース、P03/P06/P07等は影響なしにつき再実行しない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `48a36caf3361b1d167c302174eb2c4c4121c7508`。
WIPとsource-only owner監査の固定HEAD。latest_native_*と正式受入は以前の原本を維持。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_bp_party_retention_wip.json`
- `overlays/facility_party_retention/facility_party_retention.c`
- `tests/test_pr16_bp_party_retention.py`
- `scripts/pr16_bp_party_retention_owner.py`
- `.github/workflows/pr16-bp-party-retention.yml`
- `content/modernization/pr16_bp_exchange_identity_verified.json`
- `content/modernization/pr16_bp_exchange_identity_evidence/identity.json`
- `content/modernization/pr16_bp_exchange_identity_evidence/native.stderr.txt`
- `scripts/pr16_bp_exchange_identity.py`
- `tools/mgba_pr16_bp_exchange_identity.c`
- `overlays/facility_runtime/facility_runtime.c`
- `scripts/pr16_bp_exchange_successor.py`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34733866168` / HEAD `f01149dfd6848623466fadf611a6599d1f22e1ca`。
受入済みはレンタル取消→元party600bytes/count復元→通常Save→fresh Continueの1ケース。受付special operand 0x2F→0x29の修正で実chooserへ到達。global special表・save layoutを変更していない。

最新診断: run `34774194505` / job `103769160925` / HEAD `e9793dfda49ec3044b662aefd7bb0093182dce3a`。
照合抄録: `content/modernization/pr16_bp_exchange_identity_verified.json`。
交換確定後から次戦までにparty個体が変化し、交換個体保持は不成立。 38個の同時600byte/個体snapshotを照合。交換確定17345f、次戦action19169f。 PID/OT/species/movesを比較し、次戦active battlerと実partyの一致も検証。frame境界観測でありCPU関数entry/returnの証明ではない。 次戦chooser17389fでは600byte一致。最初の変化は17770f、callback2=0x0800FEC5/script=0x092CF6A5で3個体がゼロ。actionで88byte差・新規3個体を確認。保持修復は未完。

開始時fixtureと観測境界後native入力のみを区別し、7 host-write barrier・timeout・判定条件を緩めない。

## 候補identityと残件

SHA-256 `7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd` / 33554432 bytes / CRC32 `0D5D9178`。交換修復済み7f32の今回native診断候補。正式BP受入・最終製品SHAではない。

正式physical残件（台帳から照合）:

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_NATIVE_BP_EARNING_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- `PHYSICAL_CIRCUS_ADMISSION`

P08ゲート:

- `FINAL_NATIVE_ACCEPTANCE`
- `RELEASE_DECISION`

交換確定後から次戦までにparty個体が変化し、交換個体保持は不成立。 38個の同時600byte/個体snapshotを照合。交換確定17345f、次戦action19169f。 PID/OT/species/movesを比較し、次戦active battlerと実partyの一致も検証。frame境界観測でありCPU関数entry/returnの証明ではない。 次戦chooser17389fでは600byte一致。最初の変化は17770f、callback2=0x0800FEC5/script=0x092CF6A5で3個体がゼロ。actionで88byte差・新規3個体を確認。保持修復は未完。 BP稼得/消費、3勝、Save/fresh Continueの新規受入はしていない。

BP、Ringの正規story取得、policy通常UI、Circus実受付/実戦を進める。physical gap完了後に最終SHA/size/CRCを固定し、owner/ROM範囲/runner/fixture/契約の変更影響台帳で継承・代表回帰・完全再実行を選ぶ。最後にclean-ROM独立二重生成・配布patch往復・manifest/backup/rollback/混入検査・release判定。

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

WIP48a36caの8 Actionsは照合時SUCCESS。entry c0dcのPR 2件はaction_required履歴のまま保持。今回owner監査はnative0、runtime保持修復は未完。詳細: content/modernization/pr16_bp_party_retention_wip.json

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
