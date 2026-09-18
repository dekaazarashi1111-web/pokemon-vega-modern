# PR #16 固定再開メモ

> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。
> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。
> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。

## いまの停止点と次の1手

状態0/1の保存callsiteから残存5calleeを新規280命令/614byteで保存。旧8280命令再解読/1231条件再実行/native0。

**次: 次は保存属性0・paletteコピー中継・r8 frame・tile矩形/window資源を明示RAMで結合し、state0/1の帰還・次状態・queue予約・不足時部分writeを検証。新BL/BIOS/DMAは成功stubにしない。今回5callee/旧29命令/旧1231条件/BP/nativeは単独再実行せず、通常story/Ring/live初期化は未受入。**

BP購入成功run34946969126と3勝/取消/Save/Continueを単独再実行しない。Ring正規取得・装備実戦・保存を観測するまでRing受入にしない。policy/Circusやreleaseへscopeを拡大しない。

branch: `codex/modernization-followup-20260908` / PR #16（記録時 open, draft=true）。

証拠のsource HEAD: `627bd6f29c9e087e6284d4179e881b57348807a4`。
限定工程のsource HEAD。完了commit/runはremote ref/Actionsで確認。

## 最短の再開手順

PR#16とbranch refをGitHubから取得し、live HEADを固定して読む。観測headとの差分を対象pathだけ確認。本文にある旧SHAへresetせず、同一repo/branch・未mergeを確認。

まず `AGENTS.md` → この文書 → `content/modernization/pr16_native_supply_resume_20260913.json` を読む。
受入判定・ROM変更前に `content/modernization/pr16_bp_chooser_checkpoint.json` と `content/modernization/p08_remaining_work.json` を照合する。
次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。

- `content/modernization/pr16_ring_message_window_dependencies.json`
- `scripts/pr16_ring_message_window_dependencies.py`
- `content/modernization/pr16_ring_message_window_frontier.json`

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
- external2 0x0806DD1Dの保存28命令/56byteは全u16×2mode分類と局所stack帰還ABIを検証済み。同一入力の再採取/単独ABI再実行をしない。外側callee・保存slot/返却pointer非alias・Ring通常取得の受入へ昇格せず、次は0x081138F9の1根だけ進める。
- external3 0x081138F9の1根byte採取は完了。同一candidateで再採取せず保存byteのABI/副作用を検証する。external1/2とBPは再実行しない。新規未読継続・旧18owner・外側callee帰還/保存slot/返却pointer非alias・Ring通常取得は未証明として保持する。
- external3保存前半32命令/64byteのABIは完了。3条件・正規化引数・20byte frameを保存契約として再利用し、再採取/単独ABI再実行しない。次は未読継続0x08113939だけ。末尾0x08113961・旧18owner・外側帰還/非alias・Ring通常取得は未受入。
- external3継続0x08113939の1根byte採取は完了。同一candidateで再採取せず保存byteのABI/副作用を検証する。external1/2とBPは再実行しない。未読末尾0x08113961・旧18owner・外側callee帰還/保存slot/返却pointer非alias・Ring通常取得は未証明として保持する。
- external3継続20命令/40byteのABIは完了。4書込の順序とcounter/baseの再読取を保存契約として再利用し、再採取/単独ABI再実行しない。次は未読末尾0x08113961だけ。record/counter/base/frame非alias・外側帰還・旧18owner・Ring通常取得は未証明。
- external3末尾0x08113961の1根byte採取は完了。同一candidateで再採取せず保存byteの帰還ABIを検証する。prefix/bodyは保存契約だけで合成し、既読ABI/BPを再実行しない。旧18owner・帰還先/保存frame非alias・Ring通常取得は未証明。
- external3末尾3命令/6byteと保存prefix/bodyの条件付き帰還合成は完了。末尾r0は保存LRで上書きされbodyのindex+1ではない。160単一bit破壊診断はnative観測ではない。同一入力の末尾再採取・先行ABI/BP再実行を避け、callerの実frame/record/global非aliasと旧18ownerだけを進める。
- run35054868301の末尾43testsと条件付き合成は保存原本で成功照合済み。P05所有権テストの旧3件期待をBP受入原本に結び直した。旧failure run35054872496はfailureのまま保持。BP/P03 native、末尾ABI、prefix/bodyを再実行せず実caller非aliasと旧18ownerへ進む。
- 保存external1/2/3とFlagSet callerの契約結合は完了。selector2のexternal3到達域は560..2047/2080..2303、最大frame44byte。新checkerのfixture PASSは実SP/base/LR/割込み状態の観測ではない。旧ABI/受入native/本工程同一fixtureを再実行せず、実caller snapshotとallocation/帰還先証拠、旧18ownerを進める。Ring通常取得は未受入。
- boot FlagSet caller snapshotは保存原本を再利用。同一観測器・同一candidateの無変更再実行をしない。fixture/bootをRing物理受入へ昇格しない。
- selector/record制御変数8件の限定literal参照採取は保存原本を再利用する。既知命令は再decodeせず、未検証のThumb解釈候補を実行可能owner/通常取得へ昇格しない。次は保存したwriter候補からselector1/2の到達条件とrecord割当契約を結合する。
- 保存0x08113984初期化の局所Thumb契約・容量差・別callsiteの制御域alias候補は検証済み。候補再復元/同一初期化ABI/BP/nativeを再実行せず、実callerのpointer/size/limitと0x09126CB4/0x09127060/0x09099E16の実作用・実到達条件を次に照合する。
- selector採取・record初期化と今回closeoutの保存原本を再利用。受入済みnative/BP/既読ABIを再実行しない。
- initializer/外部callee6根のBL・pointer参照と不足byteは保存原本を再利用する。selectorの既存literal採取/initializer ABI/BP/nativeは再実行しない。採取されたcall候補は実到達やRing取得受入を意味しない。
- 保存BCD変換2048vector・I/O wrapper条件モデル・tick/init prefix・veneerは完了。0x09099E16は0x081C9DF9へのtail veneerで、memset効果/帰還保存を証明していない。同じ局所ABI/byte採取を繰り返さず、保存された未読delegateと実到達だけを進める。
- run35082799310のcaller採取20testsとrun35084187651のrole35testsは成功原本/保存commitまで照合済み。今回closeoutを含め保存原本を再利用し、同条件のbyte採取/ABI/nativeを再実行しない。
- 未検索Thumb短分岐/ADR・ARM B/BL/ADR・PC相対literal参照の探索と6delegateの不足byte採取は保存原本を再利用。canonical実行addressに限定した候補探索で、computed pointer/実到達/全caller不存在は未証明。
- branch-frontier採取と7delegateの局所契約は保存原本を再利用。memsetの限定ベクトル、reset、I/O readerの供給bit列モデル、gate、date validatorを通常story/hardware受入へ昇格しない。0x0912C4A8/0x0912C554/0x09099E04とmonth table/間接callerが次の未読境界。
- 今回frontier30testsと7delegate36testsは成功Actions・原artifact・保存commitまで照合済み。新規66tests/限定8191vectorの実装成果を再利用し、同一探索・byte採取・ABI・受入BP/nativeを繰り返さない。
- 未読3delegate/月表の不足byteとmirrored-PC命令候補は保存原本を再利用する。canonical-PC探索、7delegate局所契約、BP/nativeを再実行しない。実caller/pointer/size/LIMITは未証明。
- GPIO2関数/月表11か月/無効monthの表範囲超過/09099E04中継は保存結果を再利用。同じbyte採取、mirrored探索、旧7delegate/BP/nativeを再実行しない。081C85A5の戻値・ABIと閏年suffix、実caller/pointer/size/LIMITは未証明。
- 081C85A5の限定512byte窓は保存結果を再利用。同一candidateから再採取しない。GPIO/月表/既読ABI/mirrored探索/BPは再実行せず、保存命令の剰余・閏年契約へ進む。
- 保存081C85A5の非0除数剰余・中継ABI・二月suffixを再利用。除数0の未読helperや実年offset、caller/pointer/size/LIMITの証明へ昇格しない。同じbyte採取/候補復元/GPIO/月表/BPを単独再実行しない。
- 旧18targetの今回保存命令/境界を再利用。保存nodeへ合流した先や未読calleeを再帰探索しない。cohort内共有node・operand/literal/未知命令/資源上限は受入に昇格しない。BP/GPIO/閏年/候補の同一採取は再実行しない。
- 保存18targetのcallsite結合を再利用。中継先の定数とcallee帰還/SP/保存register仮定を区別する。ROM/native再採取や受入済みBPを単独再実行しない。未解決caller・jump table・calleeを残す。
- 保存callback/cursor/copy2048/checksum/LE32/runtime metadata初期化とvalidator prefixの合成契約を再利用。synthetic frameをlive frame・Ring取得と同一視しない。新規byte採取0、既読ABI/nativeを単独再実行しない。
- 実callsiteからの新規7入口・5要素jump表と合流先を再利用。今回保存したnodeを再採取/再解読しない。定数targetや分岐表をnative到達・全callee ABI・Ring受入に読み替えず、未知/窓外/共有境界を残す。
- 保存pop+cursor復帰、mode全256値、中継先2件、validator version/size/hash/reservedの合成契約を再利用。10090d4以後の新規境界以外を採取せず、既読ABI/BPを単独再実行しない。低level成否とRing通常取得・装備実戦・保存の受入は別。
- 残る4callee/中継先/validator正常継続の有限wave採取は保存原本を再利用。既存nodeと新規共有nodeを再解読せず、未知callee/間接辺/資源境界は未証明で保持。次は保存byteの契約結合だけを進め、BP/nativeや同じ採取を単独再実行しない。
- 445保存命令によるversion1/VACQ正常・CRC拒否、version2初期化、flash4byte書込の合成契約を再利用。既読採取/native/BPを再実行せず、未読6calleeと3data範囲だけを次の有限結合へ渡す。合成I/O書込を実flash操作やstory到達と同一視しない。
- 残る6callee/3data表とtable先の有限採取は今回保存原本を再利用。次はv2正常/実buffer copy/string分岐を合成契約として結合。旧445命令・280単独契約・BP/nativeは再実行しない。
- v2正常/規則境界・v1 owner copyとv2 copyなし・有限string契約は今回原本を再利用。旧採取/単独280契約/BP/nativeを再実行せず、残る6calleeとstring subtype21要素表84byteへ進む。長さ0のcopyは安全なno-opでなく未map停止として保持。native取得とは別の合成契約。
- 未読6callee/string252の21要素84byte表とその有限継続は今回保存原本を再利用。同一採取・既存94契約・BP/nativeを再実行せず、保存nodeでstring253/252とcallee境界を結合する。表の分岐先同定は帰還/SP/実callerやRing正規取得の証明ではない。
- FC全21subtype有限契約・memset0/正長/整列・selector範囲/合成nibble表・null gateは今回原本を再利用。旧94契約/採取/BP/nativeを再実行せず、3callee・1実中継先・未読data133byteへ進む。合成表の値を候補ROM値に、null gate成功を非null帰還やRing取得に読み替えない。
- 3callee/非null中継先/placeholder等133byteと表候補先の有限採取は今回保存原本を再利用。同じ採取・旧716契約・FC/memset/BP/nativeを単独再実行しない。表word候補と保存命令の結合を実callbackの帰還/SPやRing正規取得の証明にしない。
- placeholder14参照/実nibble/16slot task挿入と非nullprefixは保存原本を再利用。正常な有限task列と不正slot255のframe外write診断を混同しない。旧716契約・FC/memset・同じ採取・BP/nativeを単独再実行せず、1callee/1継続と11文字列の限定窓へ進む。
- 未読2入口と11文字列83byteの有限採取は保存原本を再利用する。同じcandidate復元・既読命令再解読・旧795/716契約・BP/nativeを単独再実行しない。保存文字列終端とcallee候補を実callerのbuffer/task境界やRing正規取得へ昇格しない。
- CreateTask保存callerの0..15探索・正常task列/満杯と11実文字列の容量境界・非nullコピーprefixを再利用。特定callerの範囲証明を全live caller/割込み状態やRing正規取得へ昇格しない。同じ採取・旧795/716・task挿入/memset/BP/native単独試験を再実行しない。
- 3callee/VarGet中継先の有限採取を保存原本から再利用する。同じ候補復元、1935既読命令、11文字列、CreateTask caller265契約、旧795/716/BPを単独再実行しない。新callee・table・callbackは未証明境界を明記し、全live frameやRing取得へ昇格しない。
- 保存2107命令による81要素展開・非null caller帰還/32byte保存・resource/callback停止契約を再利用する。11文字列/265caller/旧795/716/BP/nativeを単独再実行しない。非null限定帰還をdispatch callback帰還・全live slot境界やRing取得へ昇格しない。
- 4calleeとVarGetの2継続の有限採取は保存原本を再利用する。既読2107命令・81要素展開・非null帰還・265caller・11文字列・BP/nativeの単独再実行は禁止。未読callee/間接callbackと実allocation条件は未証明のまま、次は保存byteの契約結合へ進む。
- VarGet helper全65536値・保存caller帰還・明示slot不足拒否・callback/resource停止契約を再利用。同じ候補復元/採取/既読2330命令/81要素/非null帰還/265caller/11文字列/BP/nativeを単独再実行しない。special pointer表と拡張/通常変数領域の合成allocationを実callerの有効範囲やRing取得へ昇格しない。
- 保存external1/2/3の7byte graphを現在の2330命令へ再利用結合した。今回2工程の成功Actions/原ZIP/保存commitを照合済み。採取・旧ABI・VarGet全u16/1337帰還・BP/nativeを単独再実行しない。既知nodeへの再結合はselector callerの全帰還や実allocation/Ring取得の証明ではない。
- VarGet selector1/2の全通常256変数・record key/mode・count/limit/capacity境界と外側帰還の新規結合は保存結果を再利用する。旧external ABI/7graph・旧VarGet65536/1337・既読2457命令・81要素/265caller/11文字列・BP/nativeを単独再実行しない。明示合成allocationの帰還を実caller/Ring通常取得へ昇格しない。
- 未読resource 8calleeの有限採取は保存原本を再利用する。既読2457命令/VarGet selector縦結合/旧external ABI/BP/nativeを単独再実行しない。新規calleeや間接辺はstubで補わず、保存命令からresource/callback/出力slotの条件付き帰還とallocationを結合する。
- resource追加3callee/8要素32byte表と表先の有限採取は保存結果を再利用する。既読2850命令・先の8callee・VarGet/旧external ABI/BP/nativeを単独再実行しない。保存table targetを実callback選択・実allocation・Ring通常取得の証明へ昇格しない。
- 保存2970命令のresource属性/queue/転送/bitmap/12byte caller帰還と不足時部分書込は今回原本を再利用する。同じbyte採取/旧VarGet/旧external ABI/BP/nativeを単独再実行しない。queue予約をDMA実行・描画・Ring通常取得と同一視しない。cursor>=128の配列外初回参照、size0再利用、bitmap検索count0/1拒否、実allocation未証明を保持する。
- 固定source-lockのJP symbolと描画owner/ヘッダABI照合を再利用。保存32byte text slotとCFRU36byte TextPrinterの差を保持し、ヘッダだけでlive allocationやRing取得を受入しない。先行resource1752契約・2970命令採取・BP/nativeを単独再実行しない。
- JP text/windowの7入口の有限採取は今回保存nodeを再利用。旧2970命令/1752resource契約/固定JPsource取得/BP/nativeは再実行しない。保存initializerの存在を通常入場・実allocation成功・callback実行と同一視しない。
- 実RunTextPrinters転送先0x09378A43とwindow6callee・dummy template採取は保存原本を再利用。旧3496命令/7入口/旧resource契約/BP/nativeを単独再実行しない。allocatorや間接辺を成功stubへ置換しない。
- heap2入口・実描画本体・復帰と属性10要素表の採取は保存原本を再利用。旧3595命令や既読UI/属性/resource/nativeを単独再実行せず、保存pool/heap/callbackの契約へ進む。
- 保存3918命令のUI pool/heap/実RunTextPrinters有界契約は今回原本を再利用。heap不足/null freeのassert呼出前とsplit初期化前の部分書込を保持する。未読3callee/実gFontsを成功stubにせず、旧byte採取/旧resource/受入済みBP/nativeを単独再実行しない。
- heap split/assert/render thunkの未読3入口採取は今回原本を再利用。旧3918命令・pool/heap契約・旧resource/BP/nativeを単独再実行しない。実gFonts callback table/実allocationは未観測のままで、未読辺を成功stubに置換しない。
- 保存3955命令のheap分割・window連結・実renderの有界契約は今回原本を再利用。heap不足/assertは未読診断callee前、active描画は実gFontsとcallback未結合のまま保持。旧733条件・今回37命令採取・resource/BP/nativeを単独再実行しない。
- gFonts reader隣接の初期化窓と有限literal依存は保存結果を再利用する。同じcandidate復元/採取・旧3955命令/609条件・BP/nativeを単独再実行しない。literal表候補の有限窓を実table長・通常初期化到達・Ring取得へ昇格しない。
- gFonts setterの3保存命令と新規caller literal/table有限採取・描画lookup結合を再利用。同じsetter caller探索/候補復元/byte採取/旧3955命令契約/BP/nativeを単独再実行しない。候補表のoffset lookupを実table全長・live初期化・callback帰還・Ring通常取得へ昇格しない。
- 保存messageのfont2/4/5だけで絞ったcallbackと直接1段、default initializer帰還を再利用。候補表の他offsetを有効fontとして採取しない。同じ復元/採取/初期化契約/旧140条件/BP/nativeを単独再実行しない。callbackの保存命令・分岐表境界をlive初期化/描画完了/Ring通常取得へ昇格しない。
- font2/4/5のstate7分岐表と直接1段を保存。無効state帰還/未map表境界を再利用し、次は保存state/終端/遅延・window書込を契約結合する。既読命令/default初期化/旧font契約/BP/nativeを再実行しない。
- 文字8分岐・選択font2/4/5の字形分岐と待機5calleeの有限byteを再利用。次は明示RAM/狭いstackでstate/終端/遅延/queue結合を検証し、音声globalを暗黙stackゼロで代用しない。既読採取/受入済みfont・BP/nativeは再実行しない。
- 保存text状態/終端/遅延/通常高速描画の明示RAM契約を再利用。音声globalと512byte live stackを分離。未読control24表・字形callee・cursor/audio/BIOS境界を成功stubにしない。今回契約/既読byte採取/旧font初期化/BP/nativeは単独再実行しない。
- control24表と字形/出力/prompt/音声8calleeの有限採取は保存原本を再利用。旧5891命令・627text契約・受入済みfont/BP/nativeは単独再実行しない。次は保存命令のcontrol/prompt/字形を明示RAMで結合し、未読data/音声/BIOSを成功stubにしない。
- 保存control24分岐・色81要素展開・prompt初期化とpayload不足の部分write契約を再利用。字形/音声/BIOS未読境界は成功stubにしない。同じ採取・旧627text契約・font/BP/nativeを単独再実行しない。
- 保存7calleeと字形4文字/font2・4・5、cursor画像/animation、symbolと音声表の限定窓を再利用。旧6534命令・636control/627text契約・font/BP/nativeを単独再実行しない。字形/cursor/scrollと音声/BIOSの実効果は保存命令と明示RAMから結合し、未読辺をstubにしない。
- 字形256byte変換表と音声3calleeの不足採取は保存原本を再利用する。旧6983命令/3212byte・636control/627text・受入済みfont/BP/nativeを単独再実行しない。次は保存字形/cursor/scrollの明示RAM効果を検証し、未読音声/BIOSを成功stubにしない。
- 保存字形4文字/font2・4・5とspaceの展開、透明pixel、clipと通常callbackの明示RAM契約は本原本を再利用。全文字/live allocation/実画面の受入ではない。既読byte・636control/627text・font/BP/nativeを単独再実行しない。
- 保存cursor/scrollのpixel・queue・state2/3/4は本原本を再利用する。4byte旧stack残値の明示条件とfillの隣接nibble効果、speed3..7の進捗0を保持。同じcursor/scroll・1122glyph・636control/627text・font/BP/nativeは単独再実行しない。
- RunTextPrintersの色制御+字形4文字/space有限streamは通常6呼出し・高速1呼出しと終了後無変更を保存原本で再利用。pixel最終像の一致とqueue予約回数の違いを保持。全文法/全caller/実DMA/nativeの受入ではない。同じrenderer・591cursor/scroll・1122glyph・636control/627text・font/BP/nativeは単独再実行しない。
- 保存音声停止/再開/設定とtext callerの限定RAM契約は本原本を再利用。合成音声object/IO byteの変化を実音声やBIOS実行へ昇格しない。未読3callee・song header・BIOS entryをstubにせず、同じaudio/renderer/cursor/glyph/BP/nativeを単独再実行しない。
- 音声未読3callee・BIOS入口・song0/5/291 headerの有限採取は保存原本を再利用。既読7091命令・audio164/renderer/cursor/glyph/BP/nativeは単独再実行しない。SWIを成功stubにせず、track pointerを再生完了やlive音声の受入へ昇格しない。
- 選択曲0/5/291のheader・優先度・track容量・text16の初期化契約と音声末端の部分writeは保存原本を再利用。初期化を再生完了へ、明示IO byteを実DMA/音声へ昇格しない。同じaudio出力/旧164・renderer/cursor/glyph/BP/nativeを単独再実行せず、残る3callee/周波数表とlive callerの未証明境界へ進む。
- 音声末端3入口/周波数15index参照窓の有限採取を保存原本で再利用。既知SWIは未実行BIOS境界であって未読再採取対象ではない。15要素を本来の表長/有効mode全域と断定せず、index0の表前参照を保持。同じ採取・audio342/164・renderer/cursor/glyph/BP/nativeは単独再実行しない。
- 保存除算/音声再開/周波数と有限VCOUNT入力の契約は保存原本を再利用。BIOS11/12を実行済み・未読再採取へ読み替えない。15index参照窓は合法mode一覧ではない。ゼロ除算例外先0x081c7fcdは不足時停止として保持。同じ末端/音声342/164・renderer/cursor/glyph/BP/nativeを単独再実行しない。次は未結合text/live ownerの到達・allocation/callback。
- 混在textの選択3曲・色・4文字・停止/再開は本原本を再利用。通常5呼出し/高速1呼出しの最終画素/音声一致、queue要求4対1を保持。音声初期化後のglyph不足、track pointer不足の部分writeを破棄しない。同じ混在列/音声末端439・342/164・renderer/cursor/glyph/BP/nativeを単独再実行しない。
- run35255462365は49tests/333条件と非force記録が成功した後のexport失敗。原Actions failureを保持し、記録commit a5573a9を独立照合。混在列は再実行しない。分割exportは各member 2MB以下・全体hash照合。次は未結合text/live owner。
- message実callerのslot0/font2/4/5供給と速度delegate一根を保存。同じ採取・混在列333/旧renderer/audio/glyph/BP/nativeを単独再実行しない。次は保存速度byteとmessage callerの設定/不足/slot書込/callback選択を一体検証。
- 保存7309命令によるmessage生成→設定検証→slot0→task割当とfont callback結合は保存原本を再利用。設定byte256値、stack LR由来残留、task満杯/null fontの部分成功を通常story受入へ昇格しない。次は登録task callback08068C31とその上流実到達・window初期化を限定する。本工程/速度採取/混在333/音声/renderer/BP/nativeは単独再実行しない。
- 登録message task08068C31の限定採取と保存caller照合は保存原本を再利用。次は保存taskの状態遷移/終了/不足境界を上流と結合。登録を実行、初期化表をlive初期化へ読み替えない。旧391条件/速度採取/renderer/audio/BP/nativeを単独再実行しない。
- 保存task08068C31の七callee採取は原本を再利用。新規callは再帰採取せず未読境界を保持。次は保存命令で待機/終了/task削除/window分岐/不足を結合。今回採取/前回62命令/旧391条件/BP/nativeは単独再実行しない。
- task終了判定/未読window8calleeとliteral由来frame callbackの採取は保存原本を再利用。次は保存命令だけで上流script/busy・task待機/終了/削除/window不足を結合。今回/旧採取/旧391条件/BP/nativeは単独再実行しない。
- message taskと上流scriptの結合・busy全byte・待機/終了/削除/不足の条件は本原本を再利用。task満杯でもbusy2となる部分成功を正常受入へ昇格しない。今回結合/七callee採取/旧391条件/BP/nativeは単独再実行しない。
- 55tests/1231条件の原本run35301261393と完了5a489a17はこの軽量checkpointから再利用。大きなJSON本文が空なら権限不足/内容不在と推測せず、記載artifactと分割exportをhash照合して読む。今回記録だけで契約/native/byte採取を再実行しない。次はwindow状態0/1の未読境界。
- window属性selector0の一word/選択body・palette0806FB91・frame thunk081C7AE9は保存原本を再利用。次は状態0/1の条件付き効果/帰還/不足を保存命令で検証。今回採取・旧1231条件/391条件/BP/nativeは単独再実行しない。
- 状態0/1の残存5callee採取は本原本とhash付きexportを再利用。次は属性0・palette・r8 frame・queueの明示RAM結合。今回/旧29命令78byte/旧1231条件/BP/nativeは再実行しない。

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

先行run35303089805の原結論と保存証拠、BP run34946969126成功を照合。今回run35303682033は記録時in_progress。action_requiredを成功へ読み替えない。

merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。
