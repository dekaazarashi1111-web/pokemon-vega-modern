# USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR — Stage 51のworld runtimeを実入力E2Eで再構築する

- Status: `IN_PROGRESS`（`STAGE54_LOCAL_PASS_AWAITING_IPAD`。Stage 53の誤fixtureは不合格のまま保持し、Stage 54で正しい洞窟4 mapと`96/5 local 5`博士NPCを再検証。iPad実プレイ承認待ち）
- Lane: `map/interaction/trainer/item/field-object/wild/qa/release`
- Depends on: `USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIR`、`T16`、`T17`、`T20`、`T26`〜`T30`
- Queue ID: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR`
- Baseline: Stage 51 / ROM SHA-256 `6cda0c65836fa389c27e18bdcd500df4410348bb2176a85c2ab2fa4d41ed96e4`
- Baseline save: SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`
- Baseline commit: `86846ca`
- iPad mGBA save配置正本: `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`
- 再開用引き継ぎ: `docs/HANDOFF_STAGE53_WORLD_RUNTIME_REOPEN.md`

## 現在の判定

Stage 51はContinue直後のillegal opcodeと強制進行save由来のmap view破損を修正した診断用基準であり、world interactionの修正版または配布候補ではない。ユーザーによるiPad実プレイで、次の不具合が残っていることを確認したため、Stage 49〜51で使った静的pointer監査や関数直呼びsmokeだけを完了根拠にしてはならない。

1. map上で目が合うtrainer NPCが戦闘を開始しない。視線判定が1マスずれる例もある。
2. 通常item ballは固有item名を表示せず「どうぐを ひろった！」だけになり、いあいぎりの木など一部field objectも誤った会話へ入る。
3. 対戦NPC以外にもA入力で話せない一般NPCが残る。ヒスイシティの「手軽なレイドです」と表示するNPCはmessage後に進行不能になる。
4. ユーザー報告の551番水道の草むらでは野生が一切出現しない。
5. 知恵の洞窟では方向転換または1歩ごとに野生が再出現し、逃走後も抜け出せない場合がある。

Stage 52のiPad実プレイでも、ヒスイシティ506番道路入口側の話せないNPC、博士NPCの会話freeze、506番道路入口の視線double戦で技選択後に進まない症状、551番水道の出現0、知恵の洞窟の毎歩遭遇とライノスLv.100を確認した。従来E2Eはヒスイを`3/5`、知恵の洞窟を`3/59`、水道を`96/12`としており、正しい物理mapを通していなかったためStage 52のローカルPASSは無効とする。以後は問題saveに依存せず、fresh mGBA coreの自然new game／Continueと通常キー入力から再現する。

2026-08-25の原作Vega攻略資料と2018-02-23版参照ROMの再照合により、Stage 53の物理map再同定も誤りだったことを確定した。原作「ちえのどうくつ」はmap section `131`の`1/36`、`1/37`、`1/38`、`1/73`である。Stage 53が試験した`1/83`、`1/84`、`1/85`、`1/11`、`1/100`、`3/59`は全てmap section `139`の別map群であり、そのnative表と18 fixtureは知恵の洞窟の合格証跡にならない。原作B1F `1/73`のland rateは`7`で、ディグダLv.6〜9、ダンゴロウLv.7〜9、ライノスLv.7〜8、バルキーLv.6〜8が正本である。したがってライノスという種族自体は正常だが、Lv.100および毎歩遭遇は正常ではない。

ユーザー報告により、博士NPCは`96/5 local 5 (25,7)`、プレイヤー`(25,8)`上向きA入力で確定した。既存script root `0x093C330C`はReward Encounters V2 Scientistを呼び、nativeが未解放等で同期終了しても無条件に`waitstate`へ入るため再開通知が来ず停止していた。Stage 54ではresult `BUSY`の非同期メニューだけ`waitstate`し、同期終了は即releaseする。前回の`3/2 local 9 (4,16)`は別NPCなので博士表記と専用会話を削除し、汎用finite dialogueへ戻した。506番道路double戦`3/24`と「551番水道」→511番水道`3/29`の同定は、実際の通常プレイ導線とruntime map/local IDを取得してから確定し、名称だけで代入しない。

Stage 54はStage 51から独立生成し、ROM SHA-256 `b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`。博士の同期終了と進行済みメニューBキャンセル、正しい洞窟の北口・南口・B2F往復、B1F/B2F wild cadenceを含む20 fixtureを独立2 processで完全一致、warnings 0でPASSした。Stage 53は不合格成果物として上書き・再配布せず、Stage 54もiPad承認までは非release候補とする。

## 確認済みのデータと、未確認の実行導線

- 通常item ballは、Stage 50生成物に126本のcustom scriptと保持されたstock 3本があり、計129 object分のitem設定が存在する。126本には77種類の実item IDが入っている。hidden itemも124件あり、現行manifestには12種類のitem IDがある。したがって「item自体が未設定」ではない。
- 現行custom item scriptは`additem`後に固定文「どうぐを ひろった！」を表示する独自処理で、FireRed既存の`finditem`／`STD_FIND_ITEM`が行うitem名・TM/HM技名・pocket・fanfare・bag満杯・object除去の一連処理を迂回している。これは仕様不足ではなく、既存汎用処理を使わなかった実装不良として扱う。
- trainer command 1,302件、party 1,302件、member 6,490体は定義済みである。手持ち未設計ではない。Stage 50の監査は829 trainer templateのStage 48 script pointer保持とrange変更、1,302件のcommand／party表を別々に確認しただけで、可視NPCから正しい`trainerbattle`へのrootと「視線→接近→戦闘」を実行していない。
- 一般NPCの前回修正はzero／無効pointerと判定した86体だけを汎用finite会話へ置換した。実際のA入力、条件分岐、message完了、script解放を全NPCで検証していないため、話せないNPCと停止scriptを見逃している。
- wildの前回修正はglobalな移動状態と最低歩数へのpatchであり、map header、terrain、stock encounter cadence、逃走後状態を通常歩行から通していない。ユーザー実プレイ結果を正とし、現行hookを正常と仮定しない。

## 実装範囲

### A. 通常item・hidden item・field object

- 129通常item ballと124 hidden itemを、設定済みitem IDを失わず、FireRed既存の`finditem`／`STD_FIND_ITEM`または完全に同等の共通transactionへ戻す。
- 実入力でitem名、個数、TM/HM技名、取得pocket、fanfare、bagへの実追加、取得flag、通常item ballのobject消去を確認する。
- bag満杯ではitem／flag／objectを変更せず、空きを作った後に再取得できること、取得済みobjectから重複取得できないことを確認する。
- いあいぎり33件、いわくだき40件、回復12件、店員16件、看板、足元調査、Raid hostをobject外見ではなく物理event ownerから再分類する。いあいぎりの木などを一般会話やitem scriptへ接続しない。
- 既存のVega story event、T20 event、Codex受付、Factory、取得イベントを上書きしない。

### B. map上trainer

- 829 trainer templateそれぞれについて、可視objectのmap/local ID、movement type、向き、視線range、script root、trainer command ID、party IDを単一の機械可読台帳で結ぶ。到達不能または非runtimeの行は理由を明記し、単にpointerが非zeroという理由で合格にしない。
- authored rangeを一律`-1`する処理を撤回し、stockの座標系と障害物判定に合わせて縦横の視線距離を再構築する。
- playerが視線へ入る通常歩行から、発見icon／停止、trainer接近、会話、正しいpartyによるbattle開始、勝敗後のfield復帰、再戦抑止または再戦仕様まで実行する。
- トーホク／カントー、縦／横、range 1／2以上、障害物あり、double、再戦対象を含む代表fixtureを置き、全829件のroot監査と組み合わせる。
- 定義済み1,302 party／6,490 memberを保持し、未到達party、誤trainerへの共有、範囲外IDを0にする。

### C. 対戦以外の会話NPC

- 全678 mapの可視かつ接触可能objectを列挙し、隣接tileから向きを合わせたA入力でscriptが開始するか、有限時間でmessage／選択肢／移動／battle等の意図した結果へ進み、field入力へ戻るかを監査する。
- ヒスイシティの既知の話せない一般NPCと、`96/5 local 5 (25,7)`で「手軽なレイドです」等の報酬メニューを開く博士NPCを必須fixtureにする。博士はplayer `(25,8)`上向きA入力から同期終了と非同期メニュー終了の双方を回帰する。ユーザーが報告した他の話せない一般NPCもmap/local IDへ固定して回帰対象に加える。
- authored dialogueまたは既存service/event ownerを復元し、固有設計があるNPCを「カントーへようこそ」等の汎用placeholderへ置換して完了扱いにしない。
- 動的clone、不可視actor、map script所有objectは「話せないNPC」と混同せず、生成元とinteraction可否を台帳に明記する。

### D. 野生遭遇

- Stage 50/51の移動wrapperと最低歩数patchをstock処理と比較し、方向転換、tile進入、terrain、map wild header、encounter counter、乱数、repel、逃走後graceのownerを再構築する。症状別の追加global hookで継ぎ足さない。
- ユーザー報告の551番水道について名称から物理map/headerを再同定し、対象草むらのbehavior byteとland tableを確認する。通常入力の決定的な十分長い歩行で0件ではなく出現し、草むら外や未定義mapへ漏れないことを確認する。
- 知恵の洞窟を物理map/headerへ固定し、方向転換だけでは出現しないこと、逃走直後または毎歩の確定出現にならないこと、十分な歩数で洞窟から離脱できることを確認する。
- 草むら、洞窟、水上、釣り、いわくだき、追加生態overlayについて、stock rateとmap固有tableを破壊していないことを回帰する。

### E. 戦闘・save・既存機能の回帰

- `あくのはどう`のひるみ率20%を固定RNGと通常battle入力の両方で確認し、Inner Focus、行動済み、追加効果無効の境界を保つ。
- Focus Sash、Species/Form/Ability、HM field access、Codex対戦受付、Factory、Raid、T20 event、通常save／Continueを回帰する。
- 旧Stage 49／50／51 ROM、save、savestateを上書きしない。修正版候補は全gate通過後だけStage 52以降の別名で生成・配置する。

## 必須の検証方法

- libmGBAの関数直呼び、ROM byte、非zero pointer、table件数だけでは合格にしない。fresh coreの自然new gameまたは自然ContinueからGBAキー入力で対象へ到達し、通常のA入力／歩行／視線／message advance／battle遷移を通す。
- 各実入力fixtureは少なくとも独立2 processで同じ結果を再現し、入力列、開始save hash、map/local ID、座標、終了状態、warning/errorを証跡化する。direct-call監査は補助証跡としてのみ使う。
- 必須fixtureは、縦横の視線trainer、通常item ball、hidden item、いあいぎりの木、ヒスイシティ一般NPC、停止Raid会話、551番水道の草むら、知恵の洞窟の方向転換／歩行／逃走後離脱とする。
- 既知地点だけでなく、全object／headerを機械監査し、代表fixtureでruntimeを実証する。ユーザー報告地点だけ直して他mapへ同じ欠陥を残さない。
- ユーザーによるiPad実プレイ確認が終わるまでtaskをDONEまたは配布候補扱いにしない。実機候補を置く前にローカルE2Eを全て通す。

## 完了条件

- [x] Stage 51を非release基準として固定し、再現save／入力trace／失敗oracleを作る。
- [x] 通常item／hidden itemが設定済みitemを既存汎用取得flowで正しく渡し、全transaction境界をPASSする。
- [x] 全field objectのowner台帳が完成し、いあいぎり等の誤会話rootが0になる。
- [ ] 全trainer objectから正しい1,302 command／partyへのrootが成立し、ユーザー報告地点を含む代表的な視線戦（通常doubleを含む）を実入力で完走する。
- [ ] 全接触可能な非trainer NPCが実入力で応答し、意図した有限script後にfield操作へ戻る。
- [ ] 551番水道の草むらと正しい知恵の洞窟`1/36`・`1/37`・`1/38`・`1/73`を含むwild cadence・species・levelが通常歩行・方向転換・逃走後の各境界で正しい。
- [x] Dark Pulse、Focus Sash、battle、HM、Codex、Factory、Raid、T20、save／Continue回帰がPASSする。
- [x] clean FireRed日本版Rev.0起点の再生成、差分／直接BPS往復、allocator／ROM／RAM／save overlap、declared span外変更0をPASSする。
- [ ] Stage 52以降を旧成果物と別名でiPadへ配置し、ユーザーの実プレイで既知症状の解消を確認する。
- [ ] `design/run_log.md`、`design/version_log.md`、`design/current_state.md`、task状態を更新し、完了commitを作る。

## 非完了条件

- static pointerや件数だけが合っている。
- script関数を直接呼ぶsmokeだけが通る。
- item名を固定文へ差し替えただけ、trainer rangeを一律補正しただけ、wildの最低歩数だけを変更しただけである。
- 一般NPCへ汎用placeholder会話を付けただけで、元のownerや進行を確認していない。
- ローカルsmokeだけでStage番号を進め、iPad実プレイ前に「修正済み」とする。
