# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

未読外部callee0x0806DD1Dの1根だけ28命令/56byteを採取保存。external1の5工程と既読rootのdecode/ABI/BP再実行0。先行run35049978307の成功を原Actionsで照合。副作用・帰還・保存slot/返却pointer非aliasは未証明。

**次: 次は保存済みpr16_ring_external2_bytes.jsonの命令だけで0x0806DD1DのABI・副作用を検証する。同一候補から再採取せず、未読継続が出れば保存frontierに従う。0x081138F9・旧18owner・Ring通常取得・policy/Circus・P08最終判定は未完。**

BP購入成功run34946969126と3勝/取消/Save/Continueを単独再実行しない。Ring正規取得・装備実戦・保存を観測するまでRing受入にしない。policy/Circusやreleaseへscopeを拡大しない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `ff04f0764d8a78174b8bd21a0bc3a9c7ead349e3`。
限定工程のsource HEAD。完了commit/runはremote ref/Actionsで確認。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_ring_external2_bytes.json`
- `scripts/pr16_ring_external2_bytes.py`
- `content/modernization/pr16_ring_external1_exit_abi.json`

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
- 0x0806DDBDの限定byte採取は保存済み。同一candidateを再構築/再採取せず、保存byteでABI検証する。
- 保存zero54命令/114byteの採取・限定モデルは完了。次の採取は新規未読targetのみ。仮想call契約を実帰還や保存slot不変へ昇格しない。
- 0x0806DE3Dの共通末尾1根は採取保存済み。同一candidateを復元/再採取せず、保存byteのABI検証へ進む。
- 共通末尾0x0806DE3Dの保存6命令/12byteの限定ABIは完了。再採取/単独再実行せず、新規未読0x0806DE63へ進む。局所store/POP/return0をcallee全体の保存/帰還証明へ昇格しない。
- 0x0806DE63帰還末尾1根は採取保存済み。同一candidateで再採取せず保存byteだけでABIを検証する。既読prefix/BP再実行0を保持。
- 保存末尾0x0806DE63の3命令は条件付き局所ABI検証済み。再採取・単独再実行しない。全callee帰還/保存slot不変/非aliasは未証明。
- 0x0806DE51高域分岐は採取済み。同一candidateの再採取をせず保存byteのABIへ進む。保存共通末尾/帰還末尾/既受入BPは再実行しない。
- 高域0x0806DE51の保存8命令は算術ABI検証済み。再採取・既読ABIの単独再実行をせず、次は外部callee0x08113889を1根だけ進める。
- 外部callee0x08113889の限定byteは保存済み。同一candidateから再採取せず保存graphのABIを検証する。他callee/旧18targetを解決済みへ変えない。
- 0x08113889の保存prefix ABIは完了。再採取/単独ABI再実行をせず、未読0x081138C9/0x081138F1のみを進める。局所stack書込を全副作用なし/帰還/owner除外に昇格しない。
- 0x081138C9の1根継続byteは保存済み。prefix/継続を再採取せず保存継続ABIへ。0x081138F1末尾、他callee、旧18ownerの未証明範囲を保持する。
- external1保存継続18命令のpointer/条件付きcounter STRHは検証済み。再採取・単独ABI再実行をせず末尾0x081138F1へ。counter/返却pointerの保存slot非aliasと格納域サイズは未証明。
- external1帰還末尾0x081138F1のbyteは採取保存済み。再採取せず保存末尾ABIだけを検証し、prefix/継続は保存結果を再利用する。全帰還/保存slot非alias/owner除外は未受入。
- 本セッションのexternal1 prefix ABI/継続採取・ABI/末尾採取・ABIの5工程は完了。保存証拠と原Actions/commitを再利用し単独再実行しない。次は0x0806DD1Dの1根。全callee帰還・counter/返却pointer非alias・Ring通常取得は未受入。
- 外部callee0x0806DD1Dの限定byte採取は完了。保存graphだけでABIと副作用を検証し、同一candidateから再採取しない。external1の5工程・BPを再実行せず、0x081138F9・旧18owner・保存slot/返却pointer非alias・Ring通常取得は未証明のまま保持する。

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

先行run35049978307の原結論と保存証拠、BP run34946969126成功を照合。今回run35050675969は記録時in_progress。action_requiredを成功へ読み替えない。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
