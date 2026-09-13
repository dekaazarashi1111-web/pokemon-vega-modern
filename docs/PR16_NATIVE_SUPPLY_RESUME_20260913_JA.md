# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

run34749370272/job103703085018はfailure。初回turn3925f後、追加8turn/PP消費8回と瀕死交代2回、11261fでnative敗北outcome2を観測。11405fにCB2_WhiteOutへ移り、11525fでfacility script pointerが0へ。93925fまで元party復元なし、map4/0(8,5)、party3/snapshot1/marker2、BP0/save counter2。FacilityRuntime_AfterBattle帰還・勝利・BP稼得は未観測。

CFRU固定commitの独立復元・fsck/clean検証と19件のsource testsはPASS。WhiteOut参照はinclude/overworld.h:97の宣言1件のみ。旧schema1のowner_resolved=trueは宣言同居による誤判定で不採用。schema2はowner_resolved=false、候補ROM上ownerの固定とnative敗北復帰修復は未完。

**次: 固定候補bffdのCB2_WhiteOut(08055F65)を設定する実callbackと、facility script 092CF669の復帰先をROM bytes・逆アセンブルで固定する。source-only監査の再実行ではなく候補bytesへ進み、安全な最小修復後だけ敗北帰還・元party600bytes/count復元を検証する。**

同一bffd・同一controllerの93925f敗北失敗を再実行しない。WhiteOut所有者とfacility return callback/scriptのcandidate bytesを読取監査してから最小修復する。勝敗/HP/RNGをhost注入せず、復元assertionやtimeoutを緩めない。失敗stdoutが空でPython JSON parse errorになっているが、根本のnative failureはstderr末尾のAfterBattle不達。 run34757633314の固定source監査は完了し再実行しない。header宣言を分岐ownerと扱わず、run34757179781の旧owner=trueを修復根拠へ使わない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `9e435e551598c2b99046c7aaff1bff6da1721da3`。
このHEADはsource-only監査の対象。最新native診断HEAD・正式受入HEADとは異なり、現在branch HEADの代用品ではない。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_bp_loss_return_owner.json`
- `scripts/build_battle_core.py`
- `content/modernization/pr16_bp_battle_return_diagnostic.json`
- `tools/mgba_pr16_bp_battle_return.c`
- `scripts/pr16_bp_battle_return.py`
- `overlays/facility_runtime/facility_runtime.c`
- `scripts/build_facility_runtime.py`
- `.github/workflows/pr16-bp-battle-return.yml`
- `content/modernization/pr16_bp_battle_return_evidence/reward-source-audit.json`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34733866168` / HEAD `f01149dfd6848623466fadf611a6599d1f22e1ca`。
受入済みはレンタル取消→元party600bytes/count復元→通常Save→fresh Continueの1ケース。受付special operand 0x2F→0x29の修正で実chooserへ到達。global special表・save layoutを変更していない。

最新診断: run `34749370272` / job `103703085018` / HEAD `96ad7823a147e1db6ea8f411c77650b27a4f3102`。
照合抄録: `content/modernization/pr16_bp_battle_return_diagnostic.json`。
原本ZIP883756bytes/SHA9fa6bdf3dc7a4ad316788413b61687c90e23882c742ca938388f9e531ad9ed0c、82member/79source/24completion-chain source、生成C、7guard、raw stdout空/process exit1/stderr失敗を照合。新規実戦process1、成功fresh core0。観測抄録は失敗stderrから抽出したものと明記し、成功JSONへ代作しない。

開始時fixtureと観測境界後native入力のみを区別し、7 host-write barrier・timeout・判定条件を緩めない。

## 候補identityと残件

SHA-256 `bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92` / 33554432 bytes / CRC32 `635A3CE5`。開発候補。最終製品SHAではない。

正式physical残件（台帳から照合）:

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_NATIVE_BP_EARNING_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- `PHYSICAL_CIRCUS_ADMISSION`

P08ゲート:

- `FINAL_NATIVE_ACCEPTANCE`
- `RELEASE_DECISION`

1戦敗北は実測済みだが施設へ戻らずsnapshot/marker/レンタルpartyが残存する。交換修正や勝利だけを先に進めて負例を隠さない。Trial reward0はID、基本9BP。manifest/Stage28追加BP3とStage29 repeat1/2の条件を読取照合したが、候補上の全completion chainと最終付与量は未確定。交換operand092CF729/092CF775のsingle-selection ABI修正は敗北復帰の後。初期chooser修正、受入取消/Save/Continueは再実施しない。

BP、Ringの正規story取得、policy通常UI、Circus実受付/実戦を進める。physical gap完了後に最終SHA/size/CRCを固定し、owner/ROM範囲/runner/fixture/契約の変更影響台帳で継承・代表回帰・完全再実行を選ぶ。最後にclean-ROM独立二重生成・配布patch往復・manifest/backup/rollback/混入検査・release判定。

## 再実行・過大主張の禁止

- CFRU固定commitの独立復元・fsck/clean検証と19件のsource testsはPASS。WhiteOut参照はinclude/overworld.h:97の宣言1件のみ。旧schema1のowner_resolved=trueは宣言同居による誤判定で不採用。schema2はowner_resolved=false、候補ROM上ownerの固定とnative敗北復帰修復は未完。 同一固定sourceの再scanや受入済み取消/Save/Continueの再実行は不要。
- run34749370272の敗北→WhiteOut→party未復元はfailure原本で保持。同一sourceで再実行せず、native return修復後の影響区間だけ検証する。
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

BP run34749370272/job103703085018はnative帰還/復元不達でfailure。source13件と7guard、原本再検証は別判定。初期HEADの5 Actionsと前回closeout成功を照合済み。一般CIのpending/failureをこの診断成功へ読み替えず、最終記録commitの全Checks完了も主張しない。 Source-only run34757633314/job103724666041は成功・19tests PASSだがowner未固定を確認した結果でありnative帰還の成功ではない。最終記録commitの全Checks完了は主張しない。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
