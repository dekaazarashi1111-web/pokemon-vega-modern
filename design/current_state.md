# current_state.md

最終更新: 2026-08-27

## 現在地

- マイルストーン: T00〜T18、本編トレーナー再設計V4、実ROM Factory Trialをstage 20へ結合し、初戦の行動順通知防御をstage 21、HM所持field能力をstage 22、固定CFRU-JP battle rule監査をstage 23、技タイプ・有効度UIをstage 24、無料の共通技管理をstage 25へ追加した。v1.3.7でトーホク外来生態293行を実ROMの全遭遇layerへ接続し、v1.3.8で追加Species全体の画像・palette・icon表示とタマゴ／キャタピーID衝突、v1.3.9で6文字Species名のstock UI欠落を修正し、v1.4.0で全コレクション対象の取得経路と201件の取得イベントをstage 26へ結合した。
- USER-20260823-SPECIES-FORM-BACKSPRITE-COMPATで、固定CFRU-JPの全Species/Form・Ability参照を`species_ids.csv`／`ability_ids.csv`生成aliasへ統一した。canonical Ability 312行、Species 1,621行、C/ASM 84ファイルのAbility 4,024参照・Species 8,641参照を監査し、未変換0。source定数、manifest、consumer、indexed tableの変更はfingerprintとfail-closed監査で再buildを要求する。
- Stage48 exact-ROM回帰でHunger Switch 4ターン、Disguise初撃1/8・二撃目通常・終了復元、Battle Bond、Schooling、Zen Mode、Ice Face、Power Construct、Intimidate、Speed BoostをPASSした。表示14種、player back 7種を64×64 OAM／2,048-byte OBJ tile、front/back、palette、icon、healthboxまで検査した。upstream vendor変更は0。
- canonical修正をclean FireRedからStage06〜47へ再生成した現行identityは、Stage06 `32b3e4d7...`、Stage09 `4bc51545...`、Stage42 `cc5b1afd...`、Stage43 `66700e6d...`、Stage44 `432e3052...`、Stage45 `f580f6df...`、Stage46 `35fea920...`、Stage47/48 `b8244d5d...`（CRC32 `CA37AC3D`）。この文書内の旧Stage06〜47 hash記録は各完了時点の履歴であり、現行配布候補はStage48を正とする。
- Stage48は再生成済みStage47とbyte同一で追加ROM変更0。旧不具合Stage47 `fccc882e...`との差分BPSとclean直接BPSを完全往復した。2026-08-24にexact Stage48 ROMだけをiPadへversioned filenameで新規配置し、33,554,432 bytes／SHA-256 `b8244d5d...`一致を確認した。RetroArch起動・save/savestate操作は行っておらず、実プレイ確認は別扱いとする。
- USER-20260824-STAGE48-WORLD-ITEM-RECOVERYでStage45以前から残っていたworld serializer／physical binding／item accessor境界を修正し、Stage49を生成した。T17が捨てていたカントーの一般NPC 688、看護師12、店員15、看板360、ジムごみ箱15をproject所有scriptへ安全に再接続し、FireRed story／hidden item scriptは取り込んでいない。全678 mapを走査し、未監査のROM外pointer 0、local ID重複0。Vega正本の空event 5 mapとmap-script／flag所有zero-script object 62件は既存仕様として分離した。
- T501〜T523を平均levelではなくStage09の物理map-sectionへexact束縛し、95-row／294 candidateの野生overlay表をStage49へ再直列化した。T501=`3/19`、T511=`3/29`、T523=`3/38`。低レベルRaid 6件（Lv.5/12/20/35/45/55）を追加し、既存object枠が満杯の`3/21`だけ足元調査hostとしてobject pressureを増やしていない。
- Focus Sash ID897は40-byte表自体でなくstock `ItemId_GetMystery2`の旧item-count clampが原因だった。Stage49で境界付き0..998 accessorへ差し替え、mGBAでhold effect 39／Mystery2 1、満タン時だけpredicate true、99/100・HP1・未所持false、正式`removeitem`で消費を2 process一致で確認した。trainer 1,302戦／6,490 memberは全command ID、party pointer、level／Species／Move／Item範囲を再監査し、シンイチはID299へ一意に束縛、trainer byte変更0。Stage49は33,554,432 bytes、SHA-256 `780504cda0884bf53ed88f30fce18cbb54985740162210cb4724df0c6570ef5a`。
- 2026-08-24にStage49 exact ROMをiPadへversioned filenameで新規配置し、Stage47のCodex受付前セーブを同名Stage49セーブへ複製した。有効save generation 56、map `96/5`、座標`20/20`をsector監査し、Stage49＋複製セーブの自然ContinueをlibmGBA 2 processでPASSした。ROM／セーブは33,554,432／131,072 bytes、SHA-256 `780504cd...`／`4a83b7d2...`。RetroArch NCIは利用不可だったため実機contentは起動していない。
- USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIRで、Stage49が見た目だけでFireRed objectを一般NPC化していた誤ownerをStage48正本から再構築した。通常item ball 129、hidden item 124、いあいぎり33、いわくだき40、回復12、店員16を別ownerへ束縛し、一律「カントーへようこそ」到達を0にした。ヒスイシティを含む無効script NPC 86体をfinite会話へ接続し、残るscript 0は動的clone／不可視runtime actor 13件だけ。Stage49の未完成低レベルRaid host 6件は撤回した。
- Stage50ではtrainer template 829体のownerを保持し、視線range 2以上の652体を1マス補正した。trainer command 1,302戦／party 1,302／member 6,490、Codex受付map `96/5` local 2、既存story／T20 eventは不変。511番水道`3/29`へland ownerを新設し、方向転換を野生遭遇歩数から除外、最低10歩内の早期乱数を除去した。旧Vegaの重複`(0,0)` wild header 17件は実行時先頭一致後に到達不能なlegacy orphanとして分離記録した。
- `あくのはどう`はROM上20%で、compiled比較は`random % 100 < 20`。mGBA 4,096回の決定標本は821回で、Inner Focusと行動済み無効を維持した。Focus Sashの満タン発動・99/100不発・正式消費、canonical Ability／Species回帰もPASS。Stage50は33,554,432 bytes、SHA-256 `af9bd50194e16fc409a31b6c179ec8c53a15d6961220daf29a0bd38a2b7dc92d`。
- Stage50 ROMをiPadへ旧Stage49と別名で新規配置し、Stage47由来のCodex受付前セーブ（generation 56、map `96/5`、座標`20/20`）を同名セーブへbyte同一複製した。iPad側ROM／saveはSHA-256 `af9bd501...`／`4a83b7d2...`一致。既存ROM、save、savestateは変更しておらず、RetroArch NCI unavailableのためcontent起動は行っていない。
- USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIRで、Stage50の移動時遭遇wrapperがGBAのARM7TDMI（ARMv4T）に存在しないThumb `BLX register`命令`0x4798`を実行していたことを、iPadからbyte同一回収した報告saveの自然Continue＋実歩行で再現した。従来smokeは方向転換側だけを直接callし、実移動経路と2歩目を検査していなかった。ARMv4T互換tail-callへ置換し、既存28-byte wrapper内20 changed byte、宣言外変更0でStage51を生成した。
- Stage47由来の強制進行saveはContinue直後のlive map viewが210 word中1種類だけで、破損地形を保存していた。通常new game→stock warp/load→SaveMapView→2世代saveでCodex受付前saveを再発行し、map view 77種類、framebuffer正常、両save slot、自然Continue、右／左／下の全3経路で2歩以上、overworld callback、script context無効、mGBA warning/error 0を確認した。旧saveをStage51へ付けた場合も左右2歩とwarning 0になり、入力停止がROM原因、描画がsave原因であることを分離した。
- Stage51は33,554,432 bytes、SHA-256 `6cda0c65836fa389c27e18bdcd500df4410348bb2176a85c2ab2fa4d41ed96e4`。正常saveは131,072 bytes、SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`。iPadへ同じstemのversioned ROM／saveとして新規配置し、size／hash一致を確認した。旧Stage49／50、既存save、savestateは不変。
- その後のiPad実プレイにより、Stage51でも視線trainer不発／1マスずれ、通常itemの固定文だけの表示、いあいぎり等field objectの誤会話、話せない一般NPC、ヒスイシティRaid会話後停止、551番水道の草むらで出現0、知恵の洞窟で方向転換または毎歩遭遇が残ることが判明した。Stage51はContinue停止を切り分けた診断用基準であり、world interactionの修正版・配布候補ではない。
- USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIRで全678 map／3,093 object／1,422 BG eventを再監査し、380 event headerを再構築した。trainer 825体を先頭`trainerbattle`へ直結しauthored sightを復元、4体を非runtime actorへ分類した。全party builder共通継続点でenemy countとbattle snapshotを同期し、縦横視線から3体完走・field復帰・撃破flagを実入力でPASSした。通常item 262件は`STD_FIND_ITEM`、hidden 124件は`STD_OBTAIN_ITEM`成功後commitへ戻し、clean sourceのobject owner 469件／BG owner 375件をscript rootごと復元した。
- Stage50/51のglobal wild wrapperと最低歩数patchを撤去してstock cadenceへ戻した。fresh-coreの通常入力10 fixtureを独立2 processで完全一致させ、方向転換32回遭遇0、カントー草むら／知恵の洞窟の通常遭遇、逃走後10歩以上、終了時field復帰を確認した。Stage52はSHA-256 `8e407a1547826c61c6fab7306cfb792ca56d4f2bfac8855b485229028be4f096`で、clean直接／Stage51差分BPS、declared span外0、allocator overlap 0をPASSした。ROMと互換saveはiPadへ旧成果物と別名で配置した。初回実プレイ時はRetroArch起動中のin-memory新規saveが正規save先を上書きしていたため、停止状態で誤saveを退避し、正常な131,072-byte save（SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`）を正規mGBA save先へ復元した。Stage52は後続Stage55に置換された履歴成果であり、iPad承認をrelease gateにはしない。
- Stage52のiPad再検証で、ヒスイ入口`3/2`、506番道路double`3/24`、511番水道`3/29`、知恵の洞窟`1/83`・`1/84`・`1/85`・`1/11`・`1/100`・`3/59`を従来fixtureが外していたことを確定し、Stage52のローカル合格判定を撤回した。Stage53では全13 stock wild-header consumerを拡張265件正本へ統一し、実player objectの完了歩だけstock encounterへ渡す。Codexの通常field常駐pollと共有save workspace使用を明示request時だけへ隔離し、通常doubleの3入力router、trainer flag物理表、enemy party count順序を共通修正した。停止するbattle transition 4はstock transition 8へ正規化し、Continueのあらすじ再生は無効化した。
- Stage53は33,554,432 bytes、SHA-256 `b6ed65b8b7010bf652b55e0314c7202bcfe1bcf8b43c32a2547b1f4961ce6226`。fresh-core自然new game／2世代save／自然Continueから18 fixtureを独立2 processで完全一致、warnings 0でPASSした。縦横trainerと506通常doubleは技選択・勝利・field復帰、ヒスイ2 NPCは有限会話、511番水道と知恵の洞窟6 mapは方向転換32回遭遇0・通常歩行遭遇・逃走後10歩以上を確認した。老人部屋のnative表はムチュールLv.49〜51、デリバードLv.49〜51、アスイーツLv.48〜51、ニューラLv.49〜51、ルージュラLv.51、フリージオLv.49〜50で、ライノスLv.100は表に存在しない。2026-08-25にGBAをiPadのStage52と同じROMフォルダへ`53_world_runtime_e2e_repair.gba`として新規配置した。続いて新規ゲーム側のStage53 saveを退避し、実`savefile_directory`配下のmGBA directoryへ正常な`53_world_runtime_e2e_repair.srm`を配置した。131,072 bytes／SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`、source不変、一時ファイル0をread-back確認済み。配置正本は`docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`とする。Stage53は後続修正で不合格と確定した履歴成果である。
- 2026-08-25の原作Vega資料と参照ROM再照合で、直前のStage53判定を撤回した。原作「ちえのどうくつ」はmap section `131`の`1/36`・`1/37`・`1/38`・`1/73`であり、Stage53が試験した6 mapは全てsection `139`の別map群だった。原作B1FはディグダLv.6〜9、ダンゴロウLv.7〜9、ライノスLv.7〜8、バルキーLv.6〜8で、ユーザー報告のライノスLv.100／毎歩遭遇は異常。前回の`3/2 local 9 (4,16)`も別NPCだったため、Stage53の洞窟・NPC合格を取り消し、配布候補ではない。再開正本は`docs/HANDOFF_STAGE53_WORLD_RUNTIME_REOPEN.md`。
- ユーザー報告で博士NPCを`96/5 local 5 (25,7)`、player `(25,8)`上向きA入力へ確定した。既存Reward Encounters Scientistのscript root `0x093C330C`はnative同期終了時にも無条件で`waitstate`しており、メニューを開けない結果で再開不能になっていた。Stage54ではresult `BUSY`の非同期メニューだけ待ち、同期終了は即releaseする。旧`3/2 local 9`から博士表記・専用会話を削除した。Stage54 ROM SHA-256は`b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`。博士2経路、洞窟北口・南口・B2F往復、B1F/B2F wildを含む20 fixture×独立2 process完全一致、warnings 0、BPS往復、declared span外0をPASSした。Stage54はStage55に置換された履歴成果である。
- Stage54実機で判明した博士と近隣NPCの無表示終了は、event-design復元TALK_OBJECT 15件のsource fallbackを台帳へ記録しながら、runtime dispatcherへdaycare 1件しか設定していなかった共通生成不良だった。Stage55でsource builderとretrofitの両方を全15 fallback必須へ修正し、博士の`BUSY=9`以外の同期result 13種も6種類の可視メッセージへ接続した。全678 map／3,093 objectで接触可能な無効root 0、可視応答契約違反0、博士同期可視root 1。博士同期／メニュー、歩行中の`96/5 local 4`、通常walkerを含む22 fixture×独立2 process完全一致、warnings 0。Stage55 ROM SHA-256は`b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`。正常進行saveとともにWi-Fi SSHでiPadへ別basename配置・read-back済み。2026-08-27のD-028により、ローカル再現可能gateの合格をもってStage55を完了とし、iPad配置・実機プレイ・人手承認はrelease gateに含めない。
- USER-20260825-CHATGPT-PRO-COLLECTION-SUPPLY-PACKETで、バグ修正後に実装する全収集・供給設計をChatGPT Proへ渡す入力ZIPを作成した。canonical Species 1,621、form 388、G-Max 34、Item 999、Raid 256、会話のみNPC候補118を同梱し、既存Raid全行割当、G-Max bit、反復供給、物理ID後決めをvalidatorで固定した。Windows Downloadsへの配置と利用正本は`docs/CHATGPT_PRO_COLLECTION_SUPPLY_PACKET_JA.md`。ROM／save／world runtimeは変更していない。
- T19で35機能を35個の一意なproduction ownerへ接続し、通常のOptions、summary、PSS、bag、field、預かり屋、battle、save導線から操作できるStage 36を生成した。97 expected-byte hook、リリース対象35/35、受入条15/15、mGBA quick/fullの独立2 processをPASSした。Stage 36 SHA-256は `c262fbb121957950f890c7b28ab64b19f9bc8fdf541b543747c39ab1f7c381dd`。
- clean FireRed日本版Rev.0からStage 36への直接BPSとStage 35からの差分BPSは完全往復し、変更67,991 byteのdeclared span外0、allocator/RAM重複0を確認した。Stage 35の1,302 trainer、74 DOUBLE、6,490 member、201 Kanto trainerとgimmick/save cleanupはbyte監査で不変。
- T20で受領済みの実装可能イベント設計を、7 batch・76 event・63 physical placement・326会話としてStage 37へ統合した。80 stateは衝突のないflag `0x13B0..0x13FF`へ割り当て、160 conditionと7 atomic rewardをfield scriptへ一度だけcompileした。58 mapの59 rooted patchをStage 36実ROMからexpected-byte付きで再解決し、未解決host、object上限超過、collision、allocator/RAM/save所有重複は0。
- 既存trainer 1,302戦・6,490 member・74 DOUBLE・201 Kanto、取得イベント201件、QOL 35機能・97 hookを回帰不変に保った。mGBA quick/full独立2 processで7/76 field path、state、condition、reward、即時map transition、save/reloadをwarnings/errors 0でPASSした。Stage 37は33,554,432 bytes、SHA-256 `76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c`。
- clean FireRed日本版Rev.0→Stage 36→Stage 37とclean→Stage 37直接BPSはbyte一致し、34,168 changed byteのdeclared span外0。Stage 36差分BPS / clean直接BPS SHA-256は `56b2eb2583323a76e14878bf4db028690462fc2676f96c676258bda6141cd7d5` / `bb7a417791b2a944a3663cc6d5c69d3b360d5c40f1c01b7bc2b09547826669ce`。
- T21で既存Mirage map `31/1`の受付を通常NPC A入力へ接続し、標準party UIで選ぶ持込3体を永続partyへ書き戻さずLv.100 battle copy化した。7戦×4周をtrainer ID 745〜748のcanonical `trainerbattle 0x5C/mode3`へ接続し、Round 1〜4のNONE／MEGA／Z／選択MEGA・Z・TERA、AI FULL SMART、SPECIAL 6体poolからの決定的3体選出を実戦hookで確認した。
- Mirage専用volatile stateはEWRAM `0x0203EE00..0x0203F098`のexact 664 byte（64-byte header＋600-byte party snapshot）とし、既存UI state `0x0203F101`を含めない。既存40-byte `VegaMirageState`の`current_record[4..7]`だけを8-byte active/badge journalとして予約し、stock save＋sector 31の原子的transaction、保存失敗補償、fresh-core reset復旧、256 badge mask×8退出経路のexact restoreをPASSした。
- Stage 38は33,554,432 bytes、SHA-256 `f66c4823e50d9db86a7c5ef07436558dd4c25c2f41ee3a94e413eadc4a37d941`。7 expected-byte root、16 runtime export、変更8,432 byte、declared span外0、allocator/RAM/save overlap 0。mGBA quick/full独立2 processは受入15/15、warnings/errors 0、result identity `MP38:4:4:5:4:28:256:8:600`で一致し、clean→Stage37→Stage38とclean直接Stage38もbyte一致した。Reward Encounters V2、Move Distribution V4、Factory High Modes V2、Research Economy V1は変更していない。
- T22でMove Distribution V4のlevel-up 28,274、egg 8,219、TM/tutor 0→1追加2,799、form 509、wild/source 1,206をcanonical IDへ解決し、Stage 39の通常consumerへ接続した。Stage 38に残っていたTutor旧20-byte strideはexpected-byte付き1命令adapterで設計固定の16-byte正本へ統一し、既存特殊判定を維持した。Stage 39は33,554,432 bytes、SHA-256 `c6d9d118e329512235e27efd876108d630b827bd8f2a8eb5b2bce63748e3f6dd`。mGBA quick/full独立2 process、BPS往復、clean再構築、T00〜T21回帰、野生適用境界をPASSした。
- T23で独立U16研究ポイント、active play 60分の研究日、6活動、7 rank、23品の交換所、9 physical host、35会話をStage 40へproduction接続した。旧modern save v1の193-byte予約末尾から64-byte ownerだけを割り当て、checksum検証済みv1→v2移行、pending transaction、保存失敗rollbackを実装した。21 physical patch（11 hook、2 veneer、7 map root、取得台帳v2互換1）のdeclared span外変更とROM/RAM/save/map/hook overlapは0。Stage 40は33,554,432 bytes、SHA-256 `b46e28935675198db09f5947e6701918deafb49db27c03343f4b5b2ddaceb488`で、mGBA quick/full独立2 processとclean chain/direct BPS再構築をPASSした。
- T24で4 tier、24 encounter pool、typed credit、BP直接支払い、pending同一個体再戦、10 credit source、56会話をStage 41へproduction接続した。既存2 KiB ledgerのcredit/BP/pending/claimだけを再利用し、戦闘前persist、捕獲時atomic clear、非捕獲・reset無料再戦、保存失敗rollback、報酬戦副作用maskを32 transaction rowで確認した。クチバ共有ScientistとT23 wild-end delegateをexpected-byte付きでrootし、declared span外変更とROM/RAM/save/map/hook overlapは0。Stage 41は33,554,432 bytes、SHA-256 `282ab4af1f4f509c2c4ce40bf77b1881a0b69b05b9cb509708f13735a93cc352`で、mGBA quick/full独立2 processとclean chain/direct BPS再構築をPASSした。
- T25で既存Trialをslot 0のexact delegateとして保ち、24 mode、28 unlock requirement、248 rental、55 opponent profile、16 reward、28会話を通常Factory受付へproduction接続した。7,440-row有限生成matrix、reset/敗北時forfeit exact restore、round境界retire、packed marker/reward pending、49/100 milestoneとT24 creditのatomic transaction、Mirage分離を実ROMで確認した。5 expected-byte rootと24,115 changed byteはdeclared span内で、allocatorおよびROM/RAM/save/UI/hook overlapは0。Stage 42は33,554,432 bytes、SHA-256 `2e3c796b1deff84c83b68fde29c2eddf8672b1870f1ebe3e8308969fafde1068`で、mGBA quick/full独立2 process・受入11/11・warnings/errors 0とclean chain/direct BPS再構築をPASSした。
- T26でStage 42へ512-byte EWRAM予約と256-byte protocol 1.0 mailboxを追加し、Stage 43を生成した。production CLIは任意address操作を公開せず、宣言済み64-byte request spanだけを3分割commitで書く。実iPad RetroArch 1.22.2 / mGBAで`VERSION`、`GET_STATUS`、EWRAM read、mailbox write、sequence 1の`PING/PONG`をPASSした。Stage 43 SHA-256は `4834d42bc28d044e99b2686263808718441f4abe2347353a9eca1592224d8a9c`、CRC32は `40CE01CE`。端末固有IP、credential、container pathは証跡から除外した。GBA link/netplay、save polling、PCからの直接save編集は採用しない。
- T27の実装前契約をStage 43完了identityへ固定した。CLIは判断や理由説明を強制せず、read-only構築catalog、wait、明示actionだけを提供する。プレイヤーのpending move/switch/target/gimmickはCodex commit前にmailboxへ出さず、双方commit後に解決する。Codex対戦中はMega/Z/Dynamax/Terastalをfixed CFRU-JPの適合性・相互作用どおり`UPSTREAM_OPEN`で利用でき、個々の自主縛りは会話側へ残す。
- T27で双方6体提示・3体選出、Lv.50統一／自由、同一持ち物許可／禁止、`UPSTREAM_OPEN` gimmick、公平なpending action非公開、Codexの技・交代・降参をStage 44へproduction接続した。実iPadでtransport、first-turn、複数turn、交代、双方Dynamax、正常resultを完走し、Stage 44 SHA-256は `96820c78d6e43ef82951c23121618aac55f54579d4f196c27d6a24185ed7a256`。
- T28で正常resultに束縛したitem/Pokémon任意報酬、PREPARED/STAGED/COMMITTED journal、不可逆close、通常bag/party/PC API、Codex companion skillをStage 45へ接続した。実iPadの敗北で賞金授受・全滅ワープなしを確認し、指定カイリューを一度だけPCへ付与、UI確認、通常save、再起動、再読込、repeat close無書込までPASSした。Stage 45 SHA-256は `2eedbe64a50664d9077af19920bcffb2cf1953d0a0c2b5e3c419c2b2410b1eb7`、CRC32は `8FFD6131`。61 transaction、mGBA quick/full各16検査、clean chain/direct BPS、ROM/RAM/save/UI/hook重複0、declared span外変更0を確認した。
- T29でWindows canonical catalogを減算しない対戦用templateとして扱い、Codex受付map `96/5`の通常field・runtime `IDLE`・reward window `CLOSED`だけでitem/Pokémonを通常bag／party／PCへ生成するStage 46を追加した。CLIの`bank item`／`bank mon`／`bank batch`は1件ずつT28 journalへcommitし、最初の失敗位置と再開indexを返す。Species `1..1620`、Item `1..998`、1／6／30件batch、再送、満杯停止、別map/UI/script/result拒否、従来報酬、T19 PC一括逃がしをPASSした。protocol contractからROMを発見するため、今後のStage 47以降も固有filenameなしで同じCLI／installerを利用できる。Stage 46 SHA-256は `7941e7b59772b60829aa80a67eea26b982b397851a9e8e02d0e26be17459f44c`、CRC32は `3D8B62B1`。変更7,293 byte、11 hook再束縛、ROM/RAM/save/hook重複とdeclared span外変更は0で、Stage 45既定buildは`2eedbe64...`からbyte不変。
- T30でBox 14のCFRU展開済み80-byte `BoxPokemon`原本をWindows owner-only個体庫へexact移動するStage 47を追加した。`vault deposit`はWindows blob／pendingを先にfsyncしてから1slotずつ通常saveでBox 14から削除し、`vault withdraw`は通常save後だけWindows在庫を減算する。持ち物を含む全bitを再生成せず保持し、ABI fingerprintが一致する今後のROMで再利用できる。Stage 47では預け入れ・引き出し・Windows catalog生成のmap／NPC位置条件を廃止し、PC・会話・戦闘を閉じた任意mapの通常fieldで利用する。対戦後報酬もNPC位置へ依存しない。Stage 47 SHA-256は `fccc882e7b11315a36b146715396d63348b726268e7560a99a55f4ccbad3d3c9`、CRC32は `51C5114B`。
- USER-20260823-STAGE47-VAULT-WITHDRAW-6で実iPadのWindows個体庫から6体をBox 14へ引き出した。通常saveを各個体で完了し、最終Box 14はslot 0〜5の6体、Windows在庫0、pendingなし。ROM identityとStage 47 protocolは不変。
- USER-20260823-STAGE46-LIVE-CATALOG-BATCHで実iPadのStage 46へLv.50 Pokémon 30体とitem 21種をsequence 1〜51で連続commitした。CLI 2.4.1は、物理境界拒否後の同一sequenceを未使用padding saltで安全に再評価し、古い応答をaccepted sequence／rejected countの進行まで無視する。request body更新前に旧commit markerを無効化し、中間payloadへの誤反応も防ぐ。ROM identityとsave ABIは不変。
- ChatGPT Pro返却4 ZIPをGit管理外の読取専用原本として受領した。CRC・安全path・symlink・暗号化・private binary混入は異常0で、共通validatorによりMove 11、Research 12、Reward 10、Factory 13ファイルすべてstatus PASS、open question 0。T22〜T25を `Move -> Research -> Reward -> Factory` の直列DAGとして追加し、各直前Stageで物理値を再監査してStage 39〜42へ順次統合する。
- `Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`をGit管理外の読取専用原本として受領した。ZIP SHA-256は `576847447f0c659c3db639179aa1fa71057b909d8eff5b408ba725ee285fee8e`。Stage 35用生成catalog付きvalidatorで28 arc、76 event、7 batch、326会話、open question 0、warnings/errors 0をPASSし、Stage 36への物理host再解決と実ROM統合をT20の唯一READYとした。
- Trainer Redesign V5を累積54 encounter（50 SINGLE / 4 DOUBLE、54一意party、171 member）へ
  拡張し、Gym1直後のmap-script物理命令1件とmap `3/21`の連続14命令をstage 34へ接続した。
  stage 34 SHA-256は `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`。
- グローバル`FlagGet/Set/Clear`と最適化private party関数はhookしない。trainer専用flag入口、
  公開`BuildTrainerPartySetup`、exact command-data pointer＋kind＋source ID入口だけをwrapする。
  rooted kind-4の物理ID 702とkind-7の物理ID 100は保持し、CFRU引数消費後だけ高IDへ再束縛する。
- exact rebindとtrainer-specific defeat flag mapは29行。再戦は8-byte RematchMap V2 23行を
  command-data address＋physical source IDで引き、共有source 119を物理位置別の1043/1045へ
  分離する。論理alias ref 0/419/424は物理root側へ統合して既存save ownerを一意に保つ。
- v1.4.0はコレクション対象1,206種と到達性に必要な10フォームを監査し、既存野生・進化と
  201取得イベントのいずれかで1,216/1,216を到達可能にした。T17で省略されていたclean
  FireRed由来24 objectを19マップへ元の座標・予算内で復元し、新規設計objectは追加していない。
- 固定捕獲、ギフト、タマゴ、化石復元、進化支援、交換エミュレータ、サービスの7方式を
  共通transaction runtimeへ接続した。捕獲後確定、重複防止、party→PC、全収納満杯、道具rollback、
  reset復旧を実装し、タマゴは受取時claim・孵化時図鑑登録に分離した。通信進化30経路は
  Item 395「リンクケーブル」で必要持ち物を維持した単独ROM進化になる。
- 既存2,048 byte台帳の予約領域へ4 byte整列の240 byte `VACQ` blockを配置し、後続offsetを
  変えずにv1.3.9以前の全zero領域を移行する。個体・party・PC・図鑑は標準save、取得台帳は
  sector 31へ保存し、通常load後の台帳復元、outer/inner CRC、中断transactionを実ROMで確認した。
- v1.4.0 stage 26/finalは32 MiB、SHA-256
  `30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e`。BPS / 9-member ZIP
  SHA-256は `0b69b5de39e29168929f36750049c29f2064f290215112384449f1e4b38f418e` /
  `ca20130634c519fc08049464a21faa88e71f9708b3642af74b3cf8b55f739a1e`。release sourceは
  tag `v1.4.0`で実装コミット`9c3671d617ad5c17b1a09acf317d2ac68d4a9704`へ固定する。
- 外来生態は通常の草むら77、洞窟・屋内31、水上23、いわくだき22、朝昼／ずつき28、
  夜34、夜間水上1、日替わり大量発生29、釣り21、水上／釣り兼用1、隠れ7、
  隠れ／タマゴ11、屋内異常8の293行を、41地点・95 runtime entry・294候補bindingへ生成する。
  保留0、layer mask `0x3F`、通常・釣り・隠れの実生成入口をexact-ROM 2 processで検証する。
- 1個目バッジで「せいたいレーダー」（Item 348）をわざメモリーと同時に渡し、既存saveは
  シオウNPCが不足分だけ補う。modeはRTC自動、朝昼、夜、群れ、隠れ探索。Var `0x51FF`へ保存し、
  RTCのないemulatorや時刻待ちを避けたい場合も手動確認できる。T-E04は2個目バッジ＋いいつりざおへ正規化し、
  生態チケット代替はレーダーの夜固定へ接続した。
- v1.3.8はDPE由来1209行のfront/back/palette resource tagをcanonical IDへ正規化し、
  FireRed/Vega表示関数のSpecies 412上限と全画像・座標・icon参照を1621行へ拡張した。
  タマゴをengine予約ID 412へ戻し、衝突していたキャタピーだけを649へ交換した。ポッポ418、
  キャタピー649、グルトン1484、最大ID1620とタマゴ412の前後画像・palette・iconを実ROMで確認し、
  全1620表示名、タマゴを除く1619種の個体生成、追加1209行の全LZ77/icon pointerを検査した。
- v1.3.9はcanonical 1,621行×11 byte名表を正本にし、6文字名134行を末尾文字＋終端付きの
  8 byte互換表へ変換する。stock直接参照40か所、stride/bound命令48か所、nickname表示の
  native 13 callerとCFRU 3 literal poolをfail-closed監査し、戦闘データ転送4経路だけを
  8 byte境界の6文字copy wrapperへ移行した。エースバーン1288とムゲンダイナ1363は実ROMの
  戦闘メッセージ、HPバー文字列・OBJ tileで6文字を保持し、5文字以下1,487行のbyteは不変。
- v1.3.9は検証済みstage 07以前を再利用し、stage 09→25→finalを545.3秒で再生成した。
  finalは32 MiB、SHA-256 `0f7406c70021adf9778f0e7a9220f4e014feaac73d7e988ba39700a63be97fcd`。
  通常wild/trainer/double、Factory Trial 24 matrix、Raid 5 shield、初戦、HM、戦闘規則/UI、
  わざメモリー、Kanto/QOL-Bを同じ最終stageで再観測した。BPS / 9-member ZIP SHA-256は
  `31b4f83741f53bf20c27a6571b53e156fdb5ee34e9ffbb9ac2c36a5d1f8dae73` /
  `5cb94dd8ebb735cc4c1681ea455b1ca273f26365946ff73a396daf06235001ba`。
- Vega固有種の従来図鑑値と追加種の公式全国番号をhybrid表で分離し、既存命令列のレジスタ副作用を
  保持した。施設Trial、レイド5 shield、最初のライバル戦、HM、戦闘ルール、L詳細、技メモリ、
  QOL統合が同じ最終stageでPASSした。v1.3.8最終ROMは32 MiB、SHA-256
  `51b154c056f5bd83cdff6d9afbe124204d88ab65137d85271480ffce4448a1f2`。検証済み前段を再利用した
  最終成功chainと証跡再発行は合計約12分で、stage 00からの長時間再生成は行っていない。
- v1.3.7最終ROMは検証済みstage 16以前を再利用し、成功したstage 17→finalの累計約23分19秒で
  生成した。32 MiB、SHA-256 `cb8ac173bf8f9e0e4bc51ecd12adc581c6344761955f38766ce7211e2dd5f167`。
  exact-ROM 2 processと同一stage 25のQOL統合で、trainer開始、初戦通知、L詳細、傷薬前後HP、
  Factory/Raid、通常／釣り／隠れ遭遇を再観測した。
- trainer戦開始の黒画面は、Vega Species `0..411`の2-byte packed初期技表と追加Species
  `412..1620`の3-byte初期技表を同じ読み出し経路へ混在させたABI不一致が原因。
  canonical 1,621行は3-byte表へ統一し、Vega既存種の初期化だけは従来処理をbyte単位で保持。
  追加種は専用adapterを通し、有効trainer ID `0..771`の全772件を実party生成から戦闘画面まで自動実行して停止0を確認した。
- トーホク最初の草むらは、論理地点の文字列sortでT024が先に結合される不具合を修正し、
  V2正本のorderでT501を実map `3/19`へ結合した。既存遭遇表を保持したまま5%で8候補を追加抽選し、
  4,096回中238回の追加抽選、8候補全種、実際の`TryGenerateWildMon`から追加Species 583の生成、
  非対象mapへの漏れ0を実ROMで確認した。
- v1.3.6時点の外来生態を再集計し、通常の草むら77、洞窟・屋内31、水上23、
  いわくだき22の計153行が36論理地点・47 runtime entryで実接続済み。夜間34、大量発生29、
  ずつき28、釣り等22、DexNav等18、屋内異常8、夜間水上1の計140行とevent別解禁は専用runtime未接続で、KI-006へscope exclusionとして明記した。
- v1.3.6最終ROMは差分buildで363.6秒（6分04秒）、32 MiB、SHA-256
  `aeaa8724db55aaff5261581b4faead9aaf91b013e0fc9fb04bb9ae5bf701f5e1`。Species ID `1..1620`の生成・名前・
  初期技、有効trainer 772件、初戦、L詳細、Factory/Raid、傷薬前後のHP表示を再検証した。
- 今回提供の `vega-modern-kanto-v1.3.5-verified 2.srm` は131,072 byteの全byte `FF`で、
  ゲーム内saveは含まれていない。そのため該当saveの個別状態は再現できないが、自動戦闘fixtureで
  通常HP、傷薬対象 `8/21`、回復後 `21/21` の数字・ゲージは二重表示なし。再現しないUIへの推測patchは加えていない。
- v1.3.4で「ROM改版間の実行state混入」とした診断を訂正した。提供されたbattery saveと実際の
  「技画面→L→閉じる」経路を固定VBA-M engineで追跡すると、FR由来の`RunHelpSystemCallback`が
  CFRUより先にLを受け取り、旧HELPの画面退避領域がCFRU戦闘EWRAMを上書きして
  `gNewBS=0`にしていた。これが技Type、空欄の特性通知、「こうどうが はやくなった！」の破損を
  同時に起こした根因で、Delta環境、battery save、アクタシのヘドロえき／げきりゅうの効果ではない。
- stage 24は旧HELPがL/Rを検出した地点`0x0813C0AC`だけをexpected-byte付きでhookする。
  戦闘中は旧HELPのopenだけを抑止して同じL edgeをCFRU技詳細へ渡し、fieldではstockの
  `HelpSystem_IsSinglePlayer`判定とHELP動作をそのまま維持する。通常HELP設定とL/R設定の双方で
  接触・威力・命中の詳細を開閉し、`gNewBS`、HELP state、battle controllerが不変であることを確認した。
- v1.3.5最終ROMそのものを固定VBA-M engineへ渡し、L詳細open/close、命中label、
  `gNewBS=0x02017634`の前後一致、HELP state 0、controller `0x0802E1ED`を確認した。
  この時に提供されたv1.3.4用`.srm`は通常のbattery saveとして利用できる。症状発生後の
  savestateだけは再利用しない。後に受領したv1.3.5用`.srm`は全byte `FF`で別物。
- `scripts/build_fast_rom.py --from battle-ui`でstage 23以前を再利用し、stage 24〜25、QOL統合、finalを
  225.3秒（3分45.3秒）で再生成した。v1.3.5最終ROMは32 MiB、SHA-256
  `7db577ce5a2db02c9a33b1d87338be756f42e5cfe0cbad49bac4ff7dada45cc8`。
- ユーザー提供の6 ZIP、3 ROM、IPS、UPSをGit管理外へ取り込み、原本とのSHA-256一致を確認済み。
- 6 ZIPは破損・パストラバーサルなし。プレイブック基盤、競合監査、V1来歴資料、V2二地方設計資料、V3技調整資料、V4本編トレーナー資料を役割別に配置済み。
- V4の141戦・610体を全件canonical ID解決し、既存本編Trainer ID 648件へ実配置した。主要人物62、既存Gym NPC 39、一般・バトルサーチャー547。Mirageと未指定Sphereを保護し、追加event枠のない21戦はcatalog-onlyである。
- V4 AI rankは固定CFRU-JPの既存3段階だけを使用する。rank 1→flags 1、rank 2〜3→flags 3、rank 4〜5→flags 5。stage 19 SHA-256は `cbec85a298bc146b4b12a0edc8ca4d478b6713a5cb1f7db77e7ab1f74da1104a`。
- クチバ（group 96 / map 5）へFactory Trial受付NPCを実配置した。固定CFRU-JP生成器の重複なしLv.50候補6体から既存party UIで3体を選び、single 3v3×3、1・2勝後の任意1体交換、各戦全回復、完走9 BPを実ROMで実行する。完走・敗北・辞退・cancel・保存後復旧は入場前party 600 byteをexact復元し、図鑑はseenだけを更新する。
- Factory ledgerは既存CFRU sector 31へ直接保存し、ROM用2 KiB rollback像をEWRAM `0x0203E400..0x0203EC00`へ配置した。stage 20はT06のhash検証済みoffsetsから施設、rental、trainer、active-state addressを解決し、SHA-256は `d82f280c4d9c6ca6b5268c287c9534c0e556bc9ba2ad2075d027af6a7580d4cd`、中央allocator overlapは0。
- 初戦schedulerはQuick Claw/Custapに加えてQuick Draw indicatorも実Abilityへ再照合する。Deltaと同じアクタシAbility 64への不正indicator注入はQuick Draw script進入0、PP 35→34、双方HP更新でPASSし、正規Ability 260は通知1回・表示Ability 260を維持する。stage 21 SHA-256は `40d0c53e1f624eee2ead523f8b37f3bc30e5695e0e0b0e164658ef78184999f2`、runtime 148 bytes、allocator overlap 0。
- Vegaの実HMは既存Item 339〜346で、CFRU追加別名570〜577とは分離した。stage 22はHM05をフラッシュ、HM08をダイビングとして、バッグ所持だけでfield能力を許可する。badge、手持ち数、習得、適性、技枠を解禁条件から外し、既存map/terrain/follower/script境界とcallbackを維持する。8 HM×手持ち0体／未習得／習得済み、snapshot復元、Surf状態、BPS往復がPASSし、SHA-256は `ce8748a5c725bd523824147571c081254281e6521af204472cfffdf45ca9fa36`、runtimeは408 bytes、allocation overlapは0。
- stage 22の5 stock battle-script root、command table、行動順・end-turn・status hookは固定CFRU-JP `e24a16f...` payloadの単一ownerで、T06から対象15 surfaceがbyte不変だった。legacy battle defineは全て無効で、麻痺1/2・1/4、眠り、凍り1/5、毒1/8、固定sourceの猛毒初回、やけど1/16、急所1.5倍、天候5/8 turn・雨晴れ補正・終了を固定RNG実ROMで確認した。追加patch 0のstage 23はstage 22とbyte-identicalでSHA-256 `ce8748a5c725bd523824147571c081254281e6521af204472cfffdf45ca9fa36`。通常/trainer/double、Factory Trial 24 matrix、Raid 5 shield/終了/cleanupが現行ROMでPASSした。
- stage 24は固定CFRU move menuの実タイプ・有効度分岐、inline owner、戦闘中旧HELP guardを1,200-byte adapterで接続し、`VisualTypeCalc`由来の事前計算結果から抜群・半減・無効・タイプ一致を既存文字列・paletteへ表示する。実カーソル経路、等倍・タイプ不一致空欄、2×以上/0.5×以下/0×、Stellar/Tera Blast、double対象別表示、通常HELP/LR両設定のL詳細、field HELP、wild/trainer/Factory/Raid入力復帰をlibmGBAで確認した。SHA-256は `659e25bd994a10466b981b10a0c775590ec1bf749e2a316e46dadcedbf7ec6f0`、allocation overlapは0。Factory ROM byteは使用していない。
- stage 25はItem 347をだいじなもの「わざメモリー」とし、1個目のバッジ報酬、シオウ、カラスバを共通coreへ接続した。通常Lv.0/1・未来Lv拒否・既知/重複除外、D・Hビル/HOF/ものまねハーブ/空き枠のタマゴ技5条件、最後の1技・PP Up警告・HM・form技、battle/facility/Raid拒否、cancel時mode resetをlibmGBAで確認した。技削除はCFRU `SetMonMoveSlot` を通し、ケルディオの通常form復帰とPP Up段階のslot移動もPASSした。SHA-256は `7db577ce5a2db02c9a33b1d87338be756f42e5cfe0cbad49bac4ff7dada45cc8`、runtimeは2,931 bytes、allocation overlapは0。
- v1.3.5統合fixtureは同じstage 25で初戦3分岐、Kanto往復、Factory選択・交換・sector 31復旧、8 HM、状態異常・急所・天候、通常HELP設定を含む実カーソル技選択UI、わざメモリーを再観測してPASSした。stage 20以後の新規serialized fieldは0。最終ROM SHA-256はstage 25と同じ `7db577ce5a2db02c9a33b1d87338be756f42e5cfe0cbad49bac4ff7dada45cc8`。
- release source revision `c6f15f4ad421d35e33853039fae4ae4fabedb3ec` をローカルannotated tag `v1.3.3` へ固定した。隔離fresh checkoutからT01〜stage 25、final、BPS、9-member ZIPを再構築し、通常worktreeと完全byte一致した。BPS / ZIP SHA-256は `9f99d3663458b7f065de9ab0104eff54562331c0467c25fee3e9983935959c5f` / `aac8894833b5124e8ec82edd166291961c1c3c4c5e7c6a24c3c86fd96e894af5`。
- clean ROMはBPRJ01 Rev.00、CRC32 `3B2056E9`。IPS/UPSから個別生成した参照ROMは提供済み2 ROMとbyte一致。
- 厳密競合結果は775 byte中、同値191、異値584。単純なパッチ結合はNO-GO。
- 上流pinは2026-08-12時点のGitHub既定ブランチHEADへ固定する。
- T01で固定DPE-JP/CFRU-JPをvendor外のWindows ACL保護sandboxから各2回再構築し、全variantのROM・primary blob・offsets一致を確認した。現行tool inventoryを含む再現fingerprintは `893768977db000f14ec7620a4768c425679a3559d8bec75ec58b4bd6a45231e2`。
- DPE base ROMは `eb9434745801c8f82dc1eedbda3445a45bf6d5393290c1cec4e4c6697d3c820c`、CFRU baselineは `140aa67a38046bcbf3d211550d900929039a4e7c41e55572f9503b6f27d71922`、Factory-likeは `494b488735270cc0b384febc1dc5b73f53595905f6fd51aa32f471864f7e61b1`、minimalは `964ee5b785200b018143586351373cf60aeb37df85649173c2c8f1c98e208517`。
- ARM GCC/binutils/newlib、Python、host runner closure、mGBA/libmGBA、Windows PE converter/DLL/bridgeをversion・path・SHA-256で固定した。grit/wav2agb/mid2agbは各2回のfixtureとknown-good canonical hashを通過した。
- Factory実挙動fixtureはBP、参加判定、Battle Mine optionが参照と一致し、trainer選出は差異として分類した。固定CFRU AIの保守的cold合成上限はsingle `2,584,765` cycles、double `6,297,788` cyclesで、warmはそれぞれ `339,772` / `609,210` cycles。
- T02でDPE/CFRUのactive fixed write `6,143`件を実emission spanで再生し、同値write `155`件、許可済みoverlap `156`組を含めてT01の4 ROMとbyte一致した。分類はCFRU `5,127`、PORT `943`、RELOCATE `4`、SAME_TARGET `69`、UNKNOWN `0`。
- Vega ROMをrooted walkし、43 map group / 425 map、132 encounter header、743 trainer、4,665 script nodeを機械可読化した。RAM/save/ID、QOL 14 domain、Factory/Mirage、通貨、CFRU AI ABI/cacheも同じpolicyとvalidatorへ統合した。
- T03でclean ROMへVega IPSをmemory上で再適用し、32 MiBへ `0xFF` 拡張してno-op Thumb moduleをfile offset `0x01200000`へ配置するstage driverを確定した。連続2 buildはbyte一致、出力SHA-256は `fd01903a3507e25ae62377e3549962709ca207d5871b55fd4dcbb57813d5bbaf`、Vega-owned byte差分0、allocator overlap 0、hook/repoint 0件。
- T03 libmGBA smokeは固定title frame、通常new-game入力trace、map `4/0`での移動、128 KiB physical save、第1core破棄後のfresh-core loadをreference/candidateで一致確認した。現行fingerprintは `e5f3134ed04cd8b081bab5a65f8ff86b1341bc789d986d36d0c3a01ad9c6a205`。
- T04でVega Move ID 0〜511を固定し、CFRU identity 441件を対応、未収録551技を512〜1062へappendした。V3現代化61件と独自技70件を構造化し、独自技は70個のcompile済みeffect handlerへ変換した。game charmap名・説明、992 CFRU alias、5 table bridge、178 repointを生成した。
- 同名別技はVega ID 470を「ソウルバイト」、ID 509を「ダークスナイプ」へ変更し、CFRU公式「くらいつく」「ねらいうち」は別append IDに保持した。stage 04 SHA-256は `3adfbc639176b5e2b3f7a9b6beff2da5fcac792562a940bd154b2af5d83bc099`、fingerprintは `dce93866e70a8df720c9b52241a903b5ee836ec1128da4d6e23be41bf2827ff4`。
- T04 smokeは自然field状態からsynthetic wild battleを開始し、技ID33を固定入力で実行してPP `35→34` と敵HP低下をreference/candidate双方で確認した。CFRU battle coreへのadapter runtime bindingは依存T06で行う。
- T05でVega Type `0..17`、Ability `0..77`、Item slot `0..374`を未使用行込みで凍結し、固定CFRU/DPEのType 25、Ability 311、Item 774とTM/HM別名52件をstable keyへ解決した。canonicalはType 25、Ability 312、Item 999で、意味同一161 itemだけをVegaへ対応し、CFRU未対応613 itemとQOL新規11 itemをappendした。
- Ability source 76 `AIRLOCK`はVega canonical 77へaliasし、Vega 76 `そうおん`を保持した。Fairy 23とStellar 24は表示icon、色、25×25相性、特殊規則を完全化し、Stellar runtime bindingをT06へ渡した。VegaのGhost/Dark→Steel半減は明示overrideで維持した。
- 経験アメ5種、育成道具、21 mint、特性道具、王冠、Oval Charm、単能力EV reset用品6種を45 QOL効果・callback・supply keyへ正規化した。ボール27種、進化石12種、進化道具40種、pocket、`unk19`、hold/field/battle用途を直交する契約として保持した。生成Cはhost実行とARM7TDMI Thumb compile、`check`は公開13成果のbyte一致と副作用なしを確認した。ROM配置/repointに加え、Item/Icon 999行とAbility名/説明312行のpositional runtime表再構築・全行照合をT06 hard gateへ渡した。
- T06で固定CFRU-JPのbattle-only hook 955件をexpected-byte付きでstage 04へ統合し、CFRU 774件・PORT 181件、未分類変更0を確定した。Move 1,063、Ability 312、Item/Icon 999、Vega base stat 412、進化1,440行をallocator管理payloadへ配置し、連続2 buildをbyte一致させた。
- 通常wild/trainer、status、priority、double multi-target、switch、faint、EXP、captureを実schedulerで完走した。固定CFRU AI 3 profileとsingle/double 18判断fixture、Factory 24 rule/format、育成QOL、1戦1gimmick、Mirage仮想item、high-difficulty Raidを同じcoreへ接続した。
- Raid partnerの技破損は、Vega packed-u16 learnsetへ不適合なCFRU初期技fallbackが正しいspreadを上書きしていたことを動的traceで確定し、fallbackを無効化した。partner controllerのcommand上限を修正し、Raid 5/5 shield、自然捕獲、full-party PC 80-byte ABI、Raid後wild/trainer、turn-limit終了と一時flag cleanupを検証した。
- T06 stage fingerprintは `5dcedeba8c93e42b2dbde1d3a5ac0d9df1898b12ea2a30fb43ecd42d732f6de0`、ROM SHA-256は `61a525502e758f927c8b7af15babce87e6c6280ca279ae6c5014778234df2591`。対象135 tests、build/check、独立read-only監査は全PASSし、blocking/P1はない。
- T07でVega Species `0..411`を固定し、DPE定義済み1415 IDのうち206件（NONE sentinelを含む）をVegaへalias、欠落Species/form 1209件を`412..1620`へappendした。DPE予約hole `252..276`は生成対象外とし、FireRed/Vegaのタマゴ予約ID 412を維持するためキャタピーだけを649へ交換した。
- canonical 1621行のBaseStatsでDPE Ability/ItemをT05 IDへ変換し、file offset `0x01600000`へ配置した。T06 canonical rootのaligned参照105件をrepointし、Vega prefix 412行はbyte一致。現行stage 07 SHA-256は `6c0a7cff328835e2eef0ee3bc8daae099b2ab22ba6b58c11de8e674e1da31ad8`。
- 全行にofficial判定、canonical全国番号、review stateを付け、公式全国番号1〜1025と209 multi-form群を検証した。公式捕獲数は全国番号distinctで数えるためform重複で100種条件を水増ししない。既存trainer/wild/script/gift/evolution参照は全て解決し、先頭の通常追加種トランセルcanonical ID 413を実party memoryへ2 processで生成した。
- T08でT02のlive RAM/save ownerを統合し、CFRU sector 30/31 payloadのEWRAM `0x0203D000..0x0203D800`へ2,048-byte version 1 ledgerを割り当てた。magic/version/size/FNV-1a checksumと予約領域検査をfail-closedにし、既存Vega saveはsector checksum検証後だけ一回性migrationへ進める。
- Kanto渡航・訪問・殿堂入り・認定章・地方別heal/return anchor・League I/II・地方別NORMAL/RESEARCH profile、125共有捕獲/Raid stateをVega badge/HM/story flagと分離した。早期渡航は`0x0824 && 0x114B`または殿堂入りからmonotonicに付与する。
- Factoryはreset unsafeな348-byte/3体backupを廃止し、6×100 byte exact party snapshot、BP、24 mode streak、once reward、unlock、markerを原子的に保存する。typed encounter creditと完全なpending encounterも同じpersist-before-battle transactionにし、flash失敗、reset、二重課金・二重報酬をfocused C fixtureで検証した。
- `natureMint`、Hyper Training、Tera typeは80-byte BoxPokemon ABI内を正本とし、最大5個のタマゴqueueも個体byteをFIFO保存する。arcade coinは既存暗号化u16を再利用し、Factory BPは新規u16、research pointはearn hook不在のためstorageなしのDEFERとした。
- T09でVega 412行のfront/back、palette、coords、icon、footprint、鳴き声、Dexをlossless prefixで保ち、DPE追加1209行をcanonical順に統合した。追加行のLZ77 4,836ポインタ、icon 1,209ポインタを全検査し、NULLの内部補助IDは境界内default assetへ固定した。全6484 resource tag、画像関数上限、全aligned表示root、icon palette境界、全国図鑑変換をruntime化し、T06進化runtime root 38参照も新表へrepointした。現行stage 09 SHA-256は `df5463eac2e5d5afc4449f0e9177d8542da65a9713f9c365957e068e1f835849`、ROM末尾残量は158,344 byte。
- T06進化prefixとDPE進化を1621×16行ABIに統合し、Species/Move/Item参照をcanonical IDへ変換した。V2進化553行は意味重複43行を除いて510行に正規化し、from/to form keyと数値National Dexを付与した。level-up 1209行とegg 3,362値のMove IDを変換し、TM/HM・tutorを16-byte行で固定した。
- 現代式孵化はかわらずの石・あかいいと・power系・両親技・共通level技・ball/特性/おこう/メタモン/異親ID6回/地域form、5個FIFO、party/PC満杯保留、3孵化mode、compact IV/EV、無料技思い出し契約、公式100種またはquestのOval Charmと18固定RNG caseへ固定した。
- T10で追加オコリザル445、ふんどのこぶし1027、まけんき129、ウタンのみ669、技習得進化method 26を選び、stage 09のlibmGBA 2 process生成と継続save fixtureを通した。wild/trainer/capture/level/move/ability/item/evolution/Dex/save/restart/loadを同一fixtureで検証し、release debug giftはOFFに固定した。
- `config/feature_matrix.csv`でTEXT_SPEED=INSTANT、HATCH_MODE=FAST、ダッシュ37.5%・自転車62.5%の固定course短縮、QOL-A全release既定値を固定した。tile event各1回、text control順、共通数量UI、アメ、孵化/王冠/mint/特性/IV-EV/egg queueを同一saveで検証した。
- Factory Lv.50 single 3v3×3、交換/BP/全exit復元、credit報酬遭遇、3 AI profile、TM reuse license、Mirage仮想item、Tohoku overlayのbyte同値fallback、NORMAL/RESEARCH save、4-star Raid cleanupをhost Cで統合検証した。engine manifest schemaはv1でfreezeした。
- T12で進行13 phase、map/encounter/trainer/QOL供給/event/facility/通貨/credit/Raidをraw IDなしsymbolic schemaへ固定した。V2付属59検査を元CSVから59/59再計算し、受領原本の意味重複23行・小数National ID 205行・不足救済道具4件は正規化前FAIL、正規化後PASSにした。541系統二地方coverage、125共有捕獲key、8 gym rewardをcanonical CSVへ昇格した。
- T13でT11 physical mapとT12 symbolic contentをbuild-modeでbindし、`0x0824 && 0x114B` の直前/直後から殿堂入り・全国図鑑なしのクチバ往復を固定した。アーシア初回便、シオウ再訪便、クチバ無料帰還、到着時heal/whiteout anchor、船上戦4結果を検証した。
- クチバ初期安全導線7 mapは強制戦闘・field move・支払い0。ジムは認定章2個と3端末電圧puzzle、Vega badge書込み0にし、6候補Factory TrialとT08 persist-before-battle遭遇NPCを同じ縦切りへ接続した。
- T14で本土256 physical mapをINCLUDE 252、Route11 clean BPRJ REBUILD 1、未使用孤立house DEFER 3へ確定した。253 operational mapはクチバ起点で全到達し、V2 47地点を全て保持する。
- 全warp/connectionをKANTO namespaceへ変換し、未解決参照、Vega map誤接続、physical/local ID重複、欠損tileset、予期しない一方通行を0にした。T14の局所見積り329,866 bytesはT09 future tailと衝突するため実ROM配置に使わず、T16以降は全ownerを中央allocatorでintegration_modulesへ再配置する。
- T15で39-node進行DAGを固定し、早期認定章1〜4とHOF後の5〜8、League I→II→Finalを分離した。全253 mapに到達gateがあり、全Kanto stateから無料帰還でき、Kanto側のVega badge/HM/story書込みは0。
- QOL 35境界、Factory Trial/Standard/Full/Master、地方強豪3段階、Research/TM/HA DexNav/競技品/UB・Paradox/Raidを直前/直後fixtureへ固定した。Research rank、二地方共鳴、共有特殊捕獲、permit/return stateは独立ownerで、開発terminalはrelease無効。
- T16でTohoku 49 / Kanto 47論理地点を物理mapへ一意にbindし、Kanto 541系統、二地方RESEARCH 1,082行、125特殊種×2地方Raid 250行をsymbolic manifestへ生成した。Tohoku NORMALは全既存slotのbyte同値fallbackを保持する。
- Kanto Gym 48体・League 30体、Tohoku登録済み強豪再戦48体、3 AI profile、3段階再戦、Factory/Mirage、BP価格、進化道具、QOL供給を進行境界つきで完全化した。Kantoは `FIXED_HIGH_LEVEL_OPTIONAL` Lv.68〜100で、全体動的scaleは0。
- T09/T14領域衝突は、T03/T04/T09/T16の全allocationを単一reportへ統合し、T16 payload 77,092 bytesをintegration_modulesの `0x0120AC24`へexpected-FF付きで配置して解消した。stage 16 SHA-256は `22c7f2e6021d2f65dd5fab63bab49fa515b5dd495338183d3b369567e533dd4c`、allocation overlapは0。
- カントーLv.68〜100は任意固定高難度、警告・安全帰還必須とし、早期招待/調査pass/進行別会話/船上戦をSIMPLE_EVENTへ正規化した。Factory/Mirage owner分離、AI 3 profile、NORMAL/RESEARCH直交、供給tier、DEFERRED調査point、persist-before-battle encounter、Raid捕獲/報酬state分離をvalidatorとnegative fixtureで固定した。T13 physical map bindingなしのemitはfail-closedする。
- T17でstage 16から253 Kanto map、180 layout、51 tileset、133 wild header、29 trainer/174 party row、8 gym＋四天王/Champion 13 eventを実ROMへserializeした。既存map/layout/wild rootと24 trainer table参照をexpected-byte付きでrepointし、中央allocation overlap 0のstage 17 SHA-256 `bf3dcc979edcfd6f0c9892f236c2e4873155fceda267c43239bfc9be45cb279e`を生成した。
- 自然new-gameのVega fieldからKantoへ渡航し、描画・移動・無条件帰還、QOL-B Thumb probe、先頭gym/最終Championのobject→script→trainer→6体party graphをlibmGBA 2 processで通した。253/253 mapの往復到達、殿堂入り前後各200往復、125共有捕獲、34 event×7分岐、20 facility mode、3 AI profileを決定論fixtureで固定し、release blocker 0とした。
- T18でstage 17から32 MiB最終ROMとclean FireRed日本版Rev.0用BPSを生成し、BPS CRCと完全往復、BPRJ header、中央allocation、9-member決定論ZIP、ROM/save/元patch/private path不在をfail-closedにした。最終ROM SHA-256は `dc77691bb2f2bfb1965803707f937c03c73dfc96605cfb7358ba35821f865997`。
- source revision `a98b991dbd8742b8f51a611f8d30dc714044400a` を `v1.0.0` へtag付けし、隔離Git worktree＋読み取り専用私有入力からT01〜T17、final ROM、BPS、ZIPを完全再構築して現成果とbyte一致させた。release BPS / ZIP SHA-256は `a20a85a5501e134b36020c0b8b169958c1ef1876d26914d725ffeecceaf7c9e4` / `eb11865e3817f4d4ead53f10288a8c31ffa818e6f3e8c8c26c3d9164c7985cf6`。
- T00成果としてportableな `state/source-lock.json`、preflight、参照ROM、exact auditを生成済み。同一条件の2回目quickstartでcache reuseを確認済み。
- `VEGA_CFRU_DPE_統合設計_V2_二地方生態版` をactive review資料に切替済み。V1は来歴保存専用。
- T11で本土256 physical mapsをoutdoor 38 / dungeon 96 / indoor 122へ確定し、新規group 96〜98へ全IDを予約した。180 unique layoutの179件をclean日本版BPRJでbyte照合し、V2の47論理地点から全physical map・layout・tileset・warp/connection・script/text依存へのcrosswalkを生成した。
- クチバ民家1を新規 `KANTO_INDOOR_VERMILION_CITY_HOUSE1` (`98/0`)へcanonical importした。11x9 blockdata/collision/elevation、tileset、border、漁師NPC座標、warp座標を保持し、未取込先warpは安全terminalへremap、原作の釣り竿flag/varと英語textは日本語local flavor stubへ置換した。round-trip structural diffは0。
- 早期渡航の条件は、シオウ3個目バッジの完了flag `0x0824` と、アーシア島D・Hビル初回攻略完了flag `0x114B` のANDを一回性latchへ写す。`0x114B`を含むVega所有高位flagはwhitelist移行し、旧bitmap/varsの一括copyは禁止する。早期は認定章進行0〜4の範囲、Vega殿堂入り後は後半認定章・カントーリーグ・最終共鳴を解禁する。
- 育成・操作QOLをrelease scopeへ追加済み。文章は既定即時表示、ダッシュは25%以上、自転車は50%以上の移動時間短縮を目標にする。現代式孵化、経験アメ、SV式Hyper Training、IV/EV表示、全体学習装置、タマゴPC転送はT10、PC検索・一括操作、field PC、タマゴバスケット、自動戦闘は最初のカントー縦切りを待たせずT17回帰前に統合する。
- UIと追加eventは最小実装に固定した。新規full-screen UIや長いcutsceneを作らず、既存画面・標準menu・既存NPC/端末・短いflag/reward scriptを再利用する。
- Trainer AIは固定済みCFRU-JP `src/Battle_AI/**` と既定knowledge modelを移植する。本編は一律scaleせず、一般trainer・boss・野生を進行別profileと実測したmap/batch単位の横強化で調整する。League I→II→Finalを明示flagで順番に解禁し、現行Lv.100 leagueはKanto League＋Sphere完結後のFinalへ移す。
- Trainer ChangeKit 01〜06の全1,302戦をpost-v1.4.0 stage 35へ最終統合した。
  1,302一意party／6,490 member、1,228 SINGLE／74 DOUBLE、再戦227、Mega 86／Zワザ111／
  ダイマックス4／テラスタル67をserializer・runtime・AI・cleanupへ接続した。
  flag命令誤認51行と共有command追加20行は元命令非破壊の71 Archive consumerへ正規化し、
  Kanto 188新規戦のうち3競合は同mapの安全tileへ決定的に再配置した。
  clean FireRed日本版Rev.0起点のexact BPS chainと直接BPS往復はmGBA quick/fullとともにPASSし、
  stage 35 SHA-256は`2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180`。

- v1.4.0最終ROMを入力に、クチバFactory map `96/5`へBPショップNPC local 3を追加したpost-release stage 27を生成した。ACTIVE `BP_SHOP` 18行、Trial共通BP、5件ページmenu、通常save＋sector 31、補償rollbackを接続し、output SHA-256は `c1266a414fcb80b5d3754adec1158effd0326aa8d8d75a8365a0fa0363b5e0b1`。v1.4.0 tag／配布ROMは不変。
- post-v1.4.0 stage 28で、Factory Trial完了scriptの`callnative`を既存`FacilityRuntime_Complete`先行wrapperへ接続した。基本9 BP、連勝更新、party exact復元、sector 31保存を保持し、初回XS×5・S×2・追加3 BP、連勝3/7/14/21の4 encounter creditをclaim bit付きで実装した。stage 28 SHA-256は `268b1f8e309f4e877c2aa77256abb81056a03e99044659d5956ede0fe271989a`。
- post-v1.4.0 stage 29で、stage 28完了wrapperを先に呼ぶ反復報酬wrapperを接続した。初回claim完了済みの成功完走だけを対象に、stock RNGでオレンのみ×1＋1 BPまたはハイパーボール×1＋2 BPを付与する。bag満杯時は基本9 BPを保持し、反復item／追加BPだけを見送る。stage 29 SHA-256は `00548aa770dc377eefe671b1825af9a78852374322471eb5e9b1cfb174a644a6`。
- post-v1.4.0 stage 30で、stage 29完了wrapperを先に呼ぶ49連勝特殊event wrapperを接続した。Factory Masterを現行save ABIの`league_ii_cleared`へ写像し、完了後Trial streak 49以上で`CLAIM_KEY_STREAK_049_EVENT`のclaim bit 8を一度だけsector 31へ確定する。Stage 29の反復item/BP、基本9 BP、party exact復元を維持し、stage 30 SHA-256は `e605841d83c6f8e9acd7dbd58b5b4f3d7b262d0274c4c5b4369f0728dc25bf38`。
- post-v1.4.0 stage 31で、stage 30完了wrapperを先に呼ぶ100連勝色違い記念wrapperを接続した。Factory Master解禁、Trial streak 100以上、claim bit 9未設定をgateに、special event catalogを除外した137種からLv.50色違いをparty優先・満杯時PCへ一度だけ配布する。generated National／取得台帳bit表、PREPARED/STAGED journal、個体markerで図鑑・collection・claimを原子的に確定し、保存失敗とjournal喪失から再試行／復旧する。stage 31 SHA-256は `3a962877175d837ddb18d446182e6a63f5b72247567b93b0cc8982c74f1c8703`。

## 次の正本タスク

`design/tasks_next.md` を正とする。現時点で正本IN_PROGRESSはない。iPad配置は直接依頼がある場合だけ行い、実機プレイ・人手承認は今後もtask完了／release／READY判定に含めない。

- USER-20260827-STAGE56-TEST-READY-SAVE: DONE。Codex受付前、博士のポケモン／図鑑／ランニングシューズ取得済み、badge 8件による全個体服従、Lv.100ミュウツー先頭の標準profileを通常save APIから決定的に生成した。save SHA-256は`bdc4eea8dacf093734be6fcaa26eb55351126bbe39654d156f61829a3b90a5f7`。Stage56 ROM／同名saveをlive iPad配置先へ原子的に配置し、read-back byte一致、既存Stage55不変、一時ファイル0を確認した。
- USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION: DONE。検証済み返却ZIPの388 form、34 G-Max、999 Item、14 host、292 Raid pool、217 rewardをStage55完了baselineからStage56へproduction統合した。Stage56 SHA-256は`9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`。mGBA quick／full、Stage55自然入力22 fixture×独立2 process、clean 3経路、BPS往復、owner overlap監査をPASSした。iPadは任意配置であり、今回の安全終了不可による未配置は合否を左右しない。
- USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR: DONE。Stage55の22 fresh-core fixture×独立2 process、全map owner監査、BPS往復、declared span外0、allocator overlap 0、warnings 0をローカル完了gateとした。Stage55 ROM／saveのiPad配置は既存の任意証跡として保持する。

- USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT: DONE。全Species/Form/Ability canonical監査、フォーム特性、64×64背面画像、Stage48、2系統BPS、下流Stage42〜47回帰を完成した。
- T30: DONE。任意mapで使えるBox 14⇔Windows exact個体庫、通常save、Stage 47、実iPad 6体depositを完成した。
- T29: DONE。NPC前IDLEのWindows対戦カタログ、通常収納、1件単位batch停止・再開、Stage 46を完成した。
- T28: DONE。対戦後の任意item/Pokémon報酬、exactly-once save、Codex companion skill、iPad実戦完走をStage 45で完成した。
- T27: DONE。双方6体提示・3体選出、対戦規則、gimmick、公平なpending action非公開、Codex行動をStage 44へproduction接続した。
- T26: DONE。Stage 43のversioned mailbox、安全な`vega-codex-battle` CLI、実iPad RetroArch/mGBAのNCI EWRAM read/write・PING/PONG、mGBA quick/full、clean chain/direct BPSをPASSした。
- T25: DONE。Factory High Modes V2の24 mode、248 rental、55 profile、16 rewardを既存Trial不変でStage 42へ接続し、mGBA quick/full、7,440-row有限生成matrix、clean rebuildをPASSした。
- T24: DONE。Reward Encounters V2の4 tier、24 pool、typed credit/BP、pending同一個体再戦、10 source、ScientistをStage 41へ接続し、mGBA quick/full、32 transaction、clean rebuildをPASSした。
- T23: DONE。Research Economy V1の独立通貨・6活動・7 rank・23 shop・9 host・35会話、modern save v2 migrationをStage 40へ接続し、mGBA quick/full、clean rebuild、既存取得台帳v2回帰をPASSした。
- T22: DONE。Move Distribution V4の全canonical行をStage 39へcompileし、level-up、egg、TM/tutor、form、わざメモリー、預かり屋、孵化、野生生成のproduction consumer、mGBA quick/full、clean rebuildをPASSした。
- T21: DONE。既存Mirage map `31/1`へ持込3体・Lv.100・7戦×4周・round別gimmick・仮想item・独立記録/saveをproduction接続し、全退出時のbadge exact restore、Factory/後続4領域との非干渉、Stage 38、mGBA quick/full、clean rebuildをPASSした。
- T20: DONE。76 event / 63 placement / 80 state / 326 dialogue / 7 batchをStage 37の通常入力・保存・既存trainer/acquisition/QOL serviceへ接続し、mGBA quick/fullとclean rebuildをPASSした。
- T19: DONE。QOL 35機能を実BoxPokemon/PSS/menu/daycare/battle/saveと供給導線へ接続し、Stage 36の実ROM入力、fault injection、save/reload、clean rebuildをPASSした。ChatGPT Proのイベント設計との所有境界は変更していない。
- USER-20260817-BP-SHOP-RUNTIME: DONE。Factory map 96/5へ18品目のmanifest-backed BPショップを物理接続し、通常save／sector 31、成功購入、再読込、残高不足、bag満杯、未解禁をstage 27 exact-ROM 2 processで検証した。
- USER-20260818-FACTORY-REWARD-RUNTIME: DONE。libmGBA独立2 processで初回12 BP、credit catch-up、反復重複なし、bag満杯時の基本9 BP維持とbonus繰越、通常save item再読込、sector 31 ledger一致、全完了時party exact復元を確認した。declared span外変更0、ROM/RAM overlap 0、incremental/cumulative BPS往復はPASS。fresh全体監査とv1.4.0再releaseは実施していない。
- USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME: DONE。ACTIVE `TRIAL_REPEAT` 2行を反復完走へ接続し、初回非対象、+1 BP／オレン、+2 BP／ハイパーボール、連勝credit共存、bag満杯時の基本9 BP維持、通常save／sector 31再読込、party exact復元をlibmGBA独立2 processで確認した。stage 29のdeclared span外変更0、ROM/RAM overlap 0、BPS往復はPASS。fresh全体監査とv1.4.0再releaseは実施していない。
- USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME: DONE。ACTIVE `SPECIAL_EVENT` 49連勝行をFactory Master gate、claim bit 8へ接続し、未解禁、streak 48、60連勝catch-up、once抑止、sector 31再読込、Stage 29反復報酬共存、party exact復元をlibmGBA独立2 processで確認した。stage 30のdeclared span外変更0、ROM/RAM overlap 0、BPS往復はPASS。fresh全体監査とv1.4.0再releaseは実施していない。
- USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME: DONE。ACTIVE `SHINY_MEMORIAL` 100連勝行をFactory Master gate、claim bit 9、137種poolへ接続し、party／PC配布、強制色違い、図鑑・取得台帳、once抑止、全収納満杯再試行、PREPARED/STAGED復旧、通常save／sector 31失敗復旧、Stage 30共存をlibmGBA独立2 processで確認した。stage 31のdeclared span外変更0、ROM/RAM overlap 0、BPS往復はPASS。fresh全体監査とv1.4.0再releaseは実施していない。
- USER-20260816-ACQUISITION-EVENTS: DONE。1,206種＋10フォームの取得経路、201イベント、24 host、
  7方式の共通transaction、240 byte取得台帳、孵化時登録、通常save／sector 31復元をstage 26で検証した。
- USER-20260815-SPECIES-NAME-LENGTH: DONE。canonical 11 byte名を正本に、旧6 byte名前表を読む40経路を8 byte互換ABIへ移行し、6文字名134行を全UIで欠けなく表示する。
- USER-20260814-FIRST-BATTLE-LOOP: DONE。残留Quick Claw/Custap indicatorをhold effect再検証で破棄し、stage 21の実ROM回帰を通した。
- USER-20260814-HM-FIELD-ACCESS: DONE。Vega既存HM所持を正本にし、手持ち・習得・badgeから分離したstage 22の実ROM境界を通した。
- USER-20260814-BATTLE-RULES: DONE。現行ownerが単一CFRU payloadであることをsource/hook/固定RNGで確定し、zero-patch stage 23と全mode回帰を通した。
- USER-20260814-BATTLE-UI: DONE。固定CFRUの実タイプ・有効度・STAB表示をstage 24へ接続し、通常/Factory/Raidを同じownerと判定へ統一した。
- USER-20260814-MOVE-MEMORY: DONE。だいじなものと既存NPCが共用する無料の技思い出し・技忘れ・段階解禁タマゴ技をstage 25へ結合した。
- USER-20260814-QOL-RELEASE: DONE。同一stage 25の全QOL/Factory/Kanto統合スモーク、BPS往復、archive安全監査、日本語文書、`v1.3.3` tagged fresh checkoutのfinal/BPS/ZIP byte一致がPASSした。

- T01: DONE。固定toolchain、隔離build、baseline/Factory-like/minimal、Factory/AI実fixture、再生成可能なreportをfingerprint付きで確定した。
- T02: DONE。config-aware fixed-write、RAM/SaveBlock/ID、Vega map/encounter/trainer/script graph、早期解禁flag、QOL/施設/AIをUNKNOWN 0で確定した。アーシア港はplayer込みobject上限16のため、新規静的NPCを追加しない。
- T03: DONE。clean ROMからVegaを再適用し、32 MiB拡張、named allocator、expected-byte assertion、no-op Thumb module、title/new-game/movement/save/fresh-core load smokeを決定的buildへ統合した。
- T04: DONE。Vega Move ID 0〜511、V3調整、CFRU追加551技を1063技modelとstage 04へ統合した。
- T05: DONE。Vega既存Type/Ability/Itemを凍結し、CFRU/DPE alias、Fairy/Stellar、育成/QOL itemを決定的な配置前modelへ統合した。
- T06: DONE。固定CFRU battle core、canonical runtime表、育成QOL、Factory、AI、gimmick、Mirage、Raidをstage 04へ統合し、実schedulerと決定的publish gateを通過した。
- T07: DONE。Vega Species 0〜411を固定し、DPE alias/追加Species/formを1621行canonical modelとstage 07へ統合し、追加Speciesの実party生成を通過した。
- T08: DONE。live RAM overlap 0の配置、2 KiB versioned ledger、旧Vega一回性migration、Factory/遭遇/Raid transaction、QOL/二地方stateを実装し、focused 5 testsと決定的report checkを通過した。
- T09: DONE。Vega/DPEのgraphics・cry・Dex・evolution・learnsetを1621行canonical tableとstage 09へ統合し、現代式孵化/QOL境界を固定fixtureで検証した。
- T10: DONE。stage 09の追加要素とQOL-A、Factory/報酬遭遇/AI/TM/Mirage/Research/Raidを継続save vertical sliceで通した。
- T11: DONE。256本土map、3安全group、47論理地点crosswalk、clean raw照合、クチバ民家1のstory-safe canonical import/round-tripを通過した。
- T12: DONE。V2正規化、symbolic content schema、dry-run/physical emit境界、59検査、negative fixtureを通過した。
- T13: DONE。中盤flagからのクチバ恒久往復、安全導線、physical binding、認定章ジム、Factory Trial、遭遇transactionを通過した。
- T14: DONE。本土256 mapを253 operationalへimportし、全到達・参照・namespace・allocation gateを通過した。
- T15: DONE。早期/HOF後の二段階進行、QOL/Factory/再戦/League/Research/Raid境界を通過した。
- T16: DONE。二地方encounter/trainer/item/facility/Raid manifest、NORMAL保護、物理binding、中央allocator、stage 16 ROMを通過した。
- T17: DONE。Kanto map/wild/trainer/progressionとQOL-Bをstage 17へ実配置し、libmGBA exact-ROM、二地方state、施設/AI/QOL回帰を通過した。
- T18: DONE。v1.0.0最終ROM、BPS、決定論ZIP、release文書を生成し、隔離fresh checkoutからの完全byte再現を通過した。
- USER-20260814-TRAINER-V4: DONE。V4本編trainerをstage 19へ実配置し、v1.1.0 release導線へ接続した。
- USER-20260814-FACILITY-RUNTIME: DONE。クチバFactory Trialの受付・候補6→選択3・3連戦・勝利後交換・BP・sector 31保存・exact復元をstage 20へ実配置し、v1.2.0 release導線へ接続した。
- USER-20260814-FIRST-BATTLE-LOOP: DONE。hold effect再検証をT06 sourceへ統合し、stage 21はsource統合済みをzero-patchで確認する。初戦3分岐・不正indicator注入・正規優先効果3種・BPS往復を現行stage 21で検証した。
- USER-20260814-HM-FIELD-ACCESS: DONE。stage 21へVega HM Item 339〜346を正本とするruntimeと8 callback guardを結合し、party非依存・Surf状態・保存相当復元・BPS往復をstage 22で検証した。
- USER-20260814-BATTLE-RULES: DONE。stage 22のCFRU rule owner/defaultを監査し、麻痺・主要状態・急所・天候、単一適用、通常/double/Factory/Raidをzero-patch stage 23で検証した。
- USER-20260814-BATTLE-UI: DONE。stage 23へ固定CFRU source相当の技タイプ・有効度・STAB adapterを結合し、表示区分・Stellar・canonical名・全battle modeをstage 24で検証した。
- USER-20260814-MOVE-MEMORY: DONE。stage 24へItem/NPC共通の無料技管理coreを結合し、通常/タマゴ候補、技忘れ、CFRU form連動、context復帰をstage 25で検証した。
- USER-20260816-ACQUISITION-EVENTS: DONE。stage 25を入力に全取得経路、201イベント、24 host object、
  7方式runtime、240 byte取得台帳を結合し、stage 26の実ROMとv1.4.0 releaseで検証した。

ARM toolchain、asset converter、mGBA/libmGBAはT01で導入・固定済み。入力、参照ROM、上流commitは一致し、ブロッカーはない。

WSLではrepository全体の標準verifyを実行しない。変更対象とtask acceptanceに必要なgateだけを選び、重複検査を避ける。旧 `scripts/verify_wsl.sh` は削除済み。

全体wave、終了条件、最初の動作成果は `MASTER_PLAN.md`、現在の自動導出結果は `make plan` を参照する。

## 固定済み方針

- Vega本編を母体とし、Factory UPSは参照専用にする。
- Vega Move ID 0〜511と既存Species IDを固定する。
- 追加IDはmanifestから生成する。
- カントーは別名前空間の高難度地方として復活させ、Vega本編中盤から任意訪問可能にする。
- カントー本土とトーホクは連絡船で双方向移動可能にする。ナナシマはV2本体のscope外。
- カントーのLv.68〜100帯は動的に下げない。初回警告、強制戦闘なしの安全導線、無条件の無料帰還を必須にする。
- V2の統合設計CSVはreview状態であり、進化重複、フォームキー、ID型、道具参照を修正するまで実装正本にしない。
- 育成・操作QOLの正本は `docs/QOL_POLICY.md` とし、添付内の未確定案はジャッジ最初から、タマゴIV表示、SV式王冠、預かりタマゴ5個queue、無料技思い出しとして固定する。

## 再開時の確認先

1. `AGENTS.md`
2. このファイル
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. READYになった `tasks/T*.md`

入力詳細は `design/import_inventory.md`、資料評価は `design/import_review.md`、採択済み判断は `design/decisions.md` を参照する。
