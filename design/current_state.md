# current_state.md

最終更新: 2026-08-14

## 現在地

- マイルストーン: Gate A・T10完了。統合engineとQOL-Aの継続save vertical sliceがPASSし、Kanto大量content取込み前のengine gateまで到達。
- ユーザー提供の5 ZIP、3 ROM、IPS、UPSをGit管理外へ取り込み、原本とのSHA-256一致を確認済み。
- 5 ZIPは破損・パストラバーサルなし。プレイブック基盤、競合監査、V1来歴資料、V2二地方設計資料、V3技調整資料を役割別に配置済み。
- clean ROMはBPRJ01 Rev.00、CRC32 `3B2056E9`。IPS/UPSから個別生成した参照ROMは提供済み2 ROMとbyte一致。
- 厳密競合結果は775 byte中、同値191、異値584。単純なパッチ結合はNO-GO。
- 上流pinは2026-08-12時点のGitHub既定ブランチHEADへ固定する。
- T01で固定DPE-JP/CFRU-JPをvendor外のWindows ACL保護sandboxから各2回再構築し、全variantのROM・primary blob・offsets一致を確認した。再現fingerprintは `feb30b4f3b3f6324260af767096293c4fc6de79c8cf32334d720e13767a77633`。
- DPE base ROMは `eb9434745801c8f82dc1eedbda3445a45bf6d5393290c1cec4e4c6697d3c820c`、CFRU baselineは `140aa67a38046bcbf3d211550d900929039a4e7c41e55572f9503b6f27d71922`、Factory-likeは `494b488735270cc0b384febc1dc5b73f53595905f6fd51aa32f471864f7e61b1`、minimalは `964ee5b785200b018143586351373cf60aeb37df85649173c2c8f1c98e208517`。
- ARM GCC/binutils/newlib、Python、host runner closure、mGBA/libmGBA、Windows PE converter/DLL/bridgeをversion・path・SHA-256で固定した。grit/wav2agb/mid2agbは各2回のfixtureとknown-good canonical hashを通過した。
- Factory実挙動fixtureはBP、参加判定、Battle Mine optionが参照と一致し、trainer選出は差異として分類した。固定CFRU AIの保守的cold合成上限はsingle `2,584,765` cycles、double `6,297,788` cyclesで、warmはそれぞれ `339,772` / `609,210` cycles。
- T02でDPE/CFRUのactive fixed write `6,143`件を実emission spanで再生し、同値write `155`件、許可済みoverlap `156`組を含めてT01の4 ROMとbyte一致した。分類はCFRU `5,127`、PORT `943`、RELOCATE `4`、SAME_TARGET `69`、UNKNOWN `0`。
- Vega ROMをrooted walkし、43 map group / 425 map、132 encounter header、743 trainer、4,665 script nodeを機械可読化した。RAM/save/ID、QOL 14 domain、Factory/Mirage、通貨、CFRU AI ABI/cacheも同じpolicyとvalidatorへ統合した。
- T03でclean ROMへVega IPSをmemory上で再適用し、32 MiBへ `0xFF` 拡張してno-op Thumb moduleをfile offset `0x01200000`へ配置するstage driverを確定した。連続2 buildはbyte一致、出力SHA-256は `fd01903a3507e25ae62377e3549962709ca207d5871b55fd4dcbb57813d5bbaf`、Vega-owned byte差分0、allocator overlap 0、hook/repoint 0件。
- T03 libmGBA smokeは固定title frame、通常new-game入力trace、map `4/0`での移動、128 KiB physical save、第1core破棄後のfresh-core loadをreference/candidateで一致確認した。T04入口追加後の現行fingerprintは `e82de050dfac119d373a9784c111a1f770ce469ce5ec22a5473bf03c9e13c03c`。
- T04でVega Move ID 0〜511を固定し、CFRU identity 441件を対応、未収録551技を512〜1062へappendした。V3現代化61件と独自技70件を構造化し、独自技は70個のcompile済みeffect handlerへ変換した。game charmap名・説明、992 CFRU alias、5 table bridge、178 repointを生成した。
- 同名別技はVega ID 470を「ソウルバイト」、ID 509を「ダークスナイプ」へ変更し、CFRU公式「くらいつく」「ねらいうち」は別append IDに保持した。stage 04 SHA-256は `3adfbc639176b5e2b3f7a9b6beff2da5fcac792562a940bd154b2af5d83bc099`、fingerprintは `726abc638bdd5ba2a9e6b96963da5fc2db01de50f2c4cf3e0daef83b220e58ac`。
- T04 smokeは自然field状態からsynthetic wild battleを開始し、技ID33を固定入力で実行してPP `35→34` と敵HP低下をreference/candidate双方で確認した。CFRU battle coreへのadapter runtime bindingは依存T06で行う。
- T05でVega Type `0..17`、Ability `0..77`、Item slot `0..374`を未使用行込みで凍結し、固定CFRU/DPEのType 25、Ability 311、Item 774とTM/HM別名52件をstable keyへ解決した。canonicalはType 25、Ability 312、Item 999で、意味同一161 itemだけをVegaへ対応し、CFRU未対応613 itemとQOL新規11 itemをappendした。
- Ability source 76 `AIRLOCK`はVega canonical 77へaliasし、Vega 76 `そうおん`を保持した。Fairy 23とStellar 24は表示icon、色、25×25相性、特殊規則を完全化し、Stellar runtime bindingをT06へ渡した。VegaのGhost/Dark→Steel半減は明示overrideで維持した。
- 経験アメ5種、育成道具、21 mint、特性道具、王冠、Oval Charm、単能力EV reset用品6種を45 QOL効果・callback・supply keyへ正規化した。ボール27種、進化石12種、進化道具40種、pocket、`unk19`、hold/field/battle用途を直交する契約として保持した。生成Cはhost実行とARM7TDMI Thumb compile、`check`は公開13成果のbyte一致と副作用なしを確認した。ROM配置/repointに加え、Item/Icon 999行とAbility名/説明312行のpositional runtime表再構築・全行照合をT06 hard gateへ渡した。
- T06で固定CFRU-JPのbattle-only hook 955件をexpected-byte付きでstage 04へ統合し、CFRU 774件・PORT 181件、未分類変更0を確定した。Move 1,063、Ability 312、Item/Icon 999、Vega base stat 412、進化1,440行をallocator管理payloadへ配置し、連続2 buildをbyte一致させた。
- 通常wild/trainer、status、priority、double multi-target、switch、faint、EXP、captureを実schedulerで完走した。固定CFRU AI 3 profileとsingle/double 18判断fixture、Factory 24 rule/format、育成QOL、1戦1gimmick、Mirage仮想item、high-difficulty Raidを同じcoreへ接続した。
- Raid partnerの技破損は、Vega packed-u16 learnsetへ不適合なCFRU初期技fallbackが正しいspreadを上書きしていたことを動的traceで確定し、fallbackを無効化した。partner controllerのcommand上限を修正し、Raid 5/5 shield、自然捕獲、full-party PC 80-byte ABI、Raid後wild/trainer、turn-limit終了と一時flag cleanupを検証した。
- T06 stage fingerprintは `58417b356175a6e291f6fc194f5ac2e2335c9fbb76e2167db001714f75713a59`、ROM SHA-256は `c0deba02342ccb64558243c897728aea878cc669fb5d458c7543b70a4d9d4f05`。対象135 tests、build/check、独立read-only監査は全PASSし、blocking/P1はない。
- T07でVega Species `0..411`を固定し、DPE定義済み1415 IDのうち206件（NONE sentinelを含む）をVegaへalias、欠落Species/form 1209件を`412..1620`へappendした。DPE予約hole `252..276`は生成対象外とした。
- canonical 1621行のBaseStatsでDPE Ability/ItemをT05 IDへ変換し、file offset `0x01600000`へ配置した。T06 canonical rootのaligned参照105件をrepointし、Vega prefix 412行はbyte一致。stage 07 SHA-256は `3c24e8eb6c8f5ca10e272f1aa6c7daa375741b9061a012385661fba81652f7b8`、fingerprintは `be3931a374adfb902b6add1193adc07925491196b4a335fb17fd396199872188`。
- 全行にofficial判定、canonical全国番号、review stateを付け、公式全国番号1〜1025と209 multi-form群を検証した。公式捕獲数は全国番号distinctで数えるためform重複で100種条件を水増ししない。既存trainer/wild/script/gift/evolution参照は全て解決し、追加キャタピーcanonical ID 412を実party memoryへ2 processで生成した。
- T08でT02のlive RAM/save ownerを統合し、CFRU sector 30/31 payloadのEWRAM `0x0203D000..0x0203D800`へ2,048-byte version 1 ledgerを割り当てた。magic/version/size/FNV-1a checksumと予約領域検査をfail-closedにし、既存Vega saveはsector checksum検証後だけ一回性migrationへ進める。
- Kanto渡航・訪問・殿堂入り・認定章・地方別heal/return anchor・League I/II・地方別NORMAL/RESEARCH profile、125共有捕獲/Raid stateをVega badge/HM/story flagと分離した。早期渡航は`0x0824 && 0x114B`または殿堂入りからmonotonicに付与する。
- Factoryはreset unsafeな348-byte/3体backupを廃止し、6×100 byte exact party snapshot、BP、24 mode streak、once reward、unlock、markerを原子的に保存する。typed encounter creditと完全なpending encounterも同じpersist-before-battle transactionにし、flash失敗、reset、二重課金・二重報酬をfocused C fixtureで検証した。
- `natureMint`、Hyper Training、Tera typeは80-byte BoxPokemon ABI内を正本とし、最大5個のタマゴqueueも個体byteをFIFO保存する。arcade coinは既存暗号化u16を再利用し、Factory BPは新規u16、research pointはearn hook不在のためstorageなしのDEFERとした。
- T09でVega 412行のfront/back、palette、coords、icon、footprint、鳴き声、Dexをlossless prefixで保ち、DPE追加1209行をcanonical順に統合した。追加行のLZ77 4,836ポインタ、icon 1,209ポインタを全検査し、NULLの内部補助IDは境界内default assetへ固定した。T06進化runtime root 38参照も新表へrepointした。stage 09 SHA-256は `9dfd7caf04cdda4c0b4b559ce842a53341667c1f4e5af298348a55c655230345`、ROM末尾残量は210,548 byte。
- T06進化prefixとDPE進化を1621×16行ABIに統合し、Species/Move/Item参照をcanonical IDへ変換した。V2進化553行は意味重複43行を除いて510行に正規化し、from/to form keyと数値National Dexを付与した。level-up 1209行とegg 3,362値のMove IDを変換し、TM/HM・tutorを16-byte行で固定した。
- 現代式孵化はかわらずの石・あかいいと・power系・両親技・共通level技・ball/特性/おこう/メタモン/異親ID6回/地域form、5個FIFO、party/PC満杯保留、3孵化mode、compact IV/EV、無料技思い出し契約、公式100種またはquestのOval Charmと18固定RNG caseへ固定した。
- T10で追加オコリザル445、ふんどのこぶし1027、まけんき129、ウタンのみ669、技習得進化method 26を選び、stage 09のlibmGBA 2 process生成と継続save fixtureを通した。wild/trainer/capture/level/move/ability/item/evolution/Dex/save/restart/loadを同一fixtureで検証し、release debug giftはOFFに固定した。
- `config/feature_matrix.csv`でTEXT_SPEED=INSTANT、HATCH_MODE=FAST、ダッシュ37.5%・自転車62.5%の固定course短縮、QOL-A全release既定値を固定した。tile event各1回、text control順、共通数量UI、アメ、孵化/王冠/mint/特性/IV-EV/egg queueを同一saveで検証した。
- Factory Lv.50 single 3v3×3、交換/BP/全exit復元、credit報酬遭遇、3 AI profile、TM reuse license、Mirage仮想item、Tohoku overlayのbyte同値fallback、NORMAL/RESEARCH save、4-star Raid cleanupをhost Cで統合検証した。engine manifest schemaはv1でfreezeした。
- T00成果としてportableな `state/source-lock.json`、preflight、参照ROM、exact auditを生成済み。同一条件の2回目quickstartでcache reuseを確認済み。
- `VEGA_CFRU_DPE_統合設計_V2_二地方生態版` をactive review資料に切替済み。V1は来歴保存専用。
- T11で本土256 physical mapsをoutdoor 38 / dungeon 96 / indoor 122へ確定し、新規group 96〜98へ全IDを予約した。180 unique layoutの179件をclean日本版BPRJでbyte照合し、V2の47論理地点から全physical map・layout・tileset・warp/connection・script/text依存へのcrosswalkを生成した。
- クチバ民家1を新規 `KANTO_INDOOR_VERMILION_CITY_HOUSE1` (`98/0`)へcanonical importした。11x9 blockdata/collision/elevation、tileset、border、漁師NPC座標、warp座標を保持し、未取込先warpは安全terminalへremap、原作の釣り竿flag/varと英語textは日本語local flavor stubへ置換した。round-trip structural diffは0。
- 早期渡航の条件は、シオウ3個目バッジの完了flag `0x0824` と、アーシア島D・Hビル初回攻略完了flag `0x114B` のANDを一回性latchへ写す。`0x114B`を含むVega所有高位flagはwhitelist移行し、旧bitmap/varsの一括copyは禁止する。早期は認定章進行0〜4の範囲、Vega殿堂入り後は後半認定章・カントーリーグ・最終共鳴を解禁する。
- 育成・操作QOLをrelease scopeへ追加済み。文章は既定即時表示、ダッシュは25%以上、自転車は50%以上の移動時間短縮を目標にする。現代式孵化、経験アメ、SV式Hyper Training、IV/EV表示、全体学習装置、タマゴPC転送はT10、PC検索・一括操作、field PC、タマゴバスケット、自動戦闘は最初のカントー縦切りを待たせずT17回帰前に統合する。
- UIと追加eventは最小実装に固定した。新規full-screen UIや長いcutsceneを作らず、既存画面・標準menu・既存NPC/端末・短いflag/reward scriptを再利用する。
- Trainer AIは固定済みCFRU-JP `src/Battle_AI/**` と既定knowledge modelを移植する。本編は一律scaleせず、一般trainer・boss・野生を進行別profileと実測したmap/batch単位の横強化で調整する。League I→II→Finalを明示flagで順番に解禁し、現行Lv.100 leagueはKanto League＋Sphere完結後のFinalへ移す。
- ブロッカーなし。

## 次の正本タスク

`design/tasks_next.md` と `python3 scripts/taskctl.py next` を正とする。T11完了後は依存DAGに従いT12を統合する。

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
- T12: 数値IDを待たず、V2正規化、symbolic schema、validator fixtureを並列準備する。

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
