# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

run34741232621で実行動3260f→技メニュー3412f→技選択3413f→PP24から23へ減少3430f→次action callback3925fを観測。技247、敵HP167→139・自HP171→119、BP0、元party600bytes/Save counter2不変。初回turn診断は成功。勝利・施設帰還・BP獲得/消費は未観測。

**次: 実行動callback復帰3925fから1戦のnative勝敗・FacilityRuntime_AfterBattle帰還へ延長する。後発completion wrapperの加算条件と交換2か所のsingle-selection ABIを確認し、未観測区間に必要な範囲だけ修正する。**

3260f到達だけ、または初回turn3925fだけの同一診断を繰り返さず次の未観測区間へ進む。command12は描画より早いため実command14遷移まで観測。reward ID0を0BP扱いしない。最初の不一致をframe/callback/run/job付きで保持する。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `2d396337a11fc9735fd6828a20537429c13b42c6`。
これは証拠/sourceを照合した時点のHEADであり、このファイルを含む最新commitのSHAではない。各セッションでbranchの最新HEADを取得し、この旧SHAへresetしない。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_bp_progress_diagnostic.json`
- `tools/mgba_pr16_bp_battle_progress.c`
- `scripts/pr16_bp_battle_progress.py`
- `overlays/facility_runtime/facility_runtime.c`
- `config/factory_high_modes_v2.json`
- `.github/workflows/pr16-bp-battle-progress.yml`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34733866168` / HEAD `f01149dfd6848623466fadf611a6599d1f22e1ca`。
受入済みはレンタル取消→元party600bytes/count復元→通常Save→fresh Continueの1ケース。受付special operand 0x2F→0x29の修正で実chooserへ到達。global special表・save layoutを変更していない。

最新診断: run `34741232621` / job `103681167660` / HEAD `88e043592f07c80d1e4f582320bb955243986711`。
照合抄録: `content/modernization/pr16_bp_progress_diagnostic.json`。
原本ZIP786377bytes/SHA3deea9de7c0bf3eb154ab71de460a33e70a20e9d65c106a4d5bebbdf46c98e3e、76member/74source/10completion-chain source・生成controller・7guard・stdout/processを照合。fresh core1、3925frames、warning0。実行済み2試行(失敗1/成功1)。受入済み取消/Save/Continueの単独再実行0、原本再照合emulator0。

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

Trial reward0は報酬IDで0BPではない。正本と候補headerは3戦・基本9BP。実完了先093C42C9→092DE351→092DDCE9を追跡したがStage29以降を含む全wrapper加算/最終付与量は未確定。交換operand092CF729/092CF775はspecial2F→080CBF8D(7047)とwaitstateのまま。初期chooser092CF629の修正は再実施しない。3勝、初回/繰返し/負例、通常Save/fresh Continue、獲得BP消費は別途正式受入。

BP、Ringの正規story取得、policy通常UI、Circus実受付/実戦を進める。physical gap完了後に最終SHA/size/CRCを固定し、owner/ROM範囲/runner/fixture/契約の変更影響台帳で継承・代表回帰・完全再実行を選ぶ。最後にclean-ROM独立二重生成・配布patch往復・manifest/backup/rollback/混入検査・release判定。

## 再実行・過大主張の禁止

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

native34741232621/job103681167660は成功し原本とGit sourceを照合。一般CI/Stage79の状態はhead別Actions一覧に分離。実行中/action_required/failureを成功へ読み替えず、この記録commitの全Checks完了は主張しない。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
