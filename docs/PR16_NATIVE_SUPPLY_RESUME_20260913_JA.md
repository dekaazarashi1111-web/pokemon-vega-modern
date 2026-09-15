# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

保存済み0x090970F7は70bd=POP {r4-r6,pc}の1命令2byte。helper非0側だけで保存r4/r5/r6とsaved LRからPCを復元し、SPはFlagSet基準-24→-8、callee入口へ戻る。帰還先0x0806DE81、r0返却pointer不変、pointer参照/書込み0、外側8byte frameと保存slotは残る。LR register自体は復元せず0x09097113を保持。既証明prefix/helperと有効不変stackを前提とするsource結合で、native帰還は未観測。未読0x0806DDBD、callee全体/返却pointer非alias/全caller・ownerは未証明。旧18target・BP受入を保持。

**次: 次は未読0x0806DDBDだけを優先し、helper zero側の返却値生成・SP/r4-r6/保存slot復元を限定確認する。今回の非0継続POP、helper全u16、callee prefix、FlagSet/FlagGet、15辺分類、BP受入を再採取/単独再実行しない。旧18targetを削らず、非0側の条件付き帰還をcallee全体・全caller/全owner除外・Ring通常取得へ昇格しない。**

BP購入成功run34946969126と3勝/取消/Save/Continueを単独再実行しない。Ring正規取得・装備実戦・保存を観測するまでRing受入にしない。policy/Circusやreleaseへscopeを拡大しない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `558ed9e28ca9318c2a3d8d9829775850d15f3a2c`。
保存済み非0継続POPの限定ABI結合source HEAD。完了commit/runはremote ref/Actionsで確認。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_ring_nonzero_abi.json`
- `scripts/pr16_ring_nonzero_abi.py`
- `content/modernization/pr16_ring_nonzero_bytes.json`
- `content/modernization/pr16_ring_helper_abi.json`
- `content/modernization/pr16_ring_callee_abi.json`
- `content/modernization/pr16_ring_frame_join.json`

checkは限定source hashと正本間整合性を検査するだけで、GitHubの新runを自動発見しない。Actionsの最新run・実行中runを別途照会し、保存済み最新runより新しければ先に結果を照合・引継ぎへ反映する。

候補/上流source/runner/fixture/契約が同じ結果を再利用。文書だけのcommitではROMを再生成しない。live HEADが違うだけで全回帰しない。

## 正式受入と診断を混同しない

正式BP checkpoint: run `34946969126` / HEAD `0b7497b575a3180a045f2be377386490f192a012`。
取消/元party復元/保存再開と3勝基礎9 BPを保持し、稼得BP通常購入・保存再開を追加受入。

最新scoped受入: run `34946969126` / job `104308573084` / HEAD `0b7497b575a3180a045f2be377386490f192a012`。
照合抄録: `content/modernization/pr16_bp_spending_verified.json`。
2026-09-15: run34946969126/job104308573084で、同一candidateの3勝基礎9 BPに既存反復報酬3 BPが加算され12 BPへ確定。通常QOL供給ショップでかわらずのいしを4 BP購入し、残高12→8、所持0→1、Save counter5→6→7→7、通常Save/fresh Continue後の保持をscoped受入。ROM変更0、成功1process/2fresh cores。次はRing。

通常取得の観測開始後にRing所有bit・inventory・party・PC/LRをhostから設定しない。既存fixtureは正規取得証拠ではない。

## 候補identityと残件

SHA-256 `ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b` / 33554432 bytes / CRC32 `3EB17B36`。同一candidateのBP3勝・稼得・通常購入・保存再開は受入済み。Ring/policy/Circusと最終製品SHAは未受入。

正式physical残件（台帳から照合）:

- `P05_NATIVE_RING_ACQUISITION_PHYSICAL`
- `P05_ORDINARY_POLICY_SELECTION_PHYSICAL`
- `PHYSICAL_CIRCUS_ADMISSION`

P08ゲート:

- `FINAL_NATIVE_ACCEPTANCE`
- `RELEASE_DECISION`

2026-09-15: run34946969126/job104308573084で、同一candidateの3勝基礎9 BPに既存反復報酬3 BPが加算され12 BPへ確定。通常QOL供給ショップでかわらずのいしを4 BP購入し、残高12→8、所持0→1、Save counter5→6→7→7、通常Save/fresh Continue後の保持をscoped受入。ROM変更0、成功1process/2fresh cores。次はRing。

BP通常購入と保存再開は完了。次はRing正規story取得、policy通常UI、Circus実受付/実戦。physical3/P08 gates2完了後に最終候補/変更影響回帰/二重生成/配布判定。

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
- run34854927678の同一playthrough native 3勝・BP 0→9・元party600bytes復元はscoped受入済み。変更影響なしに単独再実行せず、BP購入suffixもrun34946969126で完了。
- run34946969126の通常購入12→8 BP・かわらずのいし0→1・Save/fresh Continueは正式受入。source/候補/契約変更影響なしに再実行しない。失敗run34933733445と34945660762をsuccessに読み替えない。
- Ring source graphと誤入口選択の修正は完了。同一sourceで再scanせず、map97/80 compiled ownerの未観測区間へ進む。source-onlyをRing通常取得や全ROMのgiver不在証明にしない。
- Ring compiled監査の成功原本とsource hashが同じなら再compile/再scanしない。記録された未解決外部ownerだけを進め、受入済みBPを再実行しない。
- run34960361700の34 tests/callstd4/6入口はsource不変なら再実行しない。patch先の未観測実体と未解決辺だけを進める。BP受入原本は不変。
- run34964225479の18 tests・24 graph/366命令は同一source/candidateなら再実行しない。残る18target/15間接辺だけを進める。Ring通常取得受入や全owner不存在へ読み替えない。
- 15間接辺のABI分類12return/2callsite trampoline/1live-frame branchを同一入力で再実行しない。旧18未読targetと新1target、全caller/CFG/stack-integrityの仮定を保持し、Ring受入や全owner不存在へ昇格しない。
- 0x0806DE7Dの1根byte採取は完了。同一candidate/sourceで再採取せず、保存した継続graphを再利用する。継承8byte frame・旧18未読target・全owner未除外を保持し、Ring通常取得の受入へ読み替えない。
- FlagSet継続の継承frame結合は条件付きで完了。opaque callee 0x09097105のreturn/SP/r4/保存slotと返却pointer非aliasは未証明。結合を全owner除外やRing受入へ昇格せず、同一入力で単独再実行しない。
- 0x09097105の限定byte採取は保存済み。保存graphを再利用し、同一candidateから再採取しない。帰還/SP/r4/非alias検証は別工程。
- 0x09097105の10命令/22byteと追加16byte live-frameの限定検証は完了。helper091281D1・非0継続090970F7・0継続0806DDBDは未読。callee return/SP/r4/返却pointer非aliasを受入せず、literal code pointerを返却bufferへ読み替えない。同一prefixを再採取しない。
- 0x091281D1のhelper byte採取は保存済み。同一candidateから再採取せず、保存byteでreturn/stackを限定検証する。
- 0x091281D1の保存29命令/全u16 return・SP/r4-r11/LR/保存slot非変更検証は完了。source不変なら再採取/単独再実行せず0x090970F7へ進む。callee全体帰還/非alias/Ring受入とは区別する。
- 0x090970F7の限定byte採取は保存済み。保存byteを再利用し、同一candidateを再構築/再採取しない。
- 0x090970F7の保存POP1命令2byte・非0側SP/r4-r6/保存slot結合は完了。同一入力を再採取/単独再実行せず未読0x0806DDBDへ進む。callee全体/非alias/Ring受入とは区別。

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

採取run34988999991・helper run34984185105・BP run34946969126成功照合。今回run34990811278は記録時in_progress。failure/action_requiredは原状態を保持し全CI greenを主張しない。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
