# current_state.md

最終更新: 2026-08-14

## 現在地

- マイルストーン: T00〜T18、本編トレーナー再設計V4、実ROM Factory Trialをstage 20へ結合し、初戦の行動順通知防御をstage 21、HM所持field能力をstage 22、固定CFRU-JP battle rule監査をstage 23、技タイプ・有効度UIをstage 24、無料の共通技管理をstage 25へ追加した。fresh rebuildで検出した来歴・再配置・tool inventory・可変計測値依存を修正したv1.3.3 sourceで、tagged sourceの最終fresh rebuildを残す。
- ユーザー提供の6 ZIP、3 ROM、IPS、UPSをGit管理外へ取り込み、原本とのSHA-256一致を確認済み。
- 6 ZIPは破損・パストラバーサルなし。プレイブック基盤、競合監査、V1来歴資料、V2二地方設計資料、V3技調整資料、V4本編トレーナー資料を役割別に配置済み。
- V4の141戦・610体を全件canonical ID解決し、既存本編Trainer ID 648件へ実配置した。主要人物62、既存Gym NPC 39、一般・バトルサーチャー547。Mirageと未指定Sphereを保護し、追加event枠のない21戦はcatalog-onlyである。
- V4 AI rankは固定CFRU-JPの既存3段階だけを使用する。rank 1→flags 1、rank 2〜3→flags 3、rank 4〜5→flags 5。stage 19 SHA-256は `cbec85a298bc146b4b12a0edc8ca4d478b6713a5cb1f7db77e7ab1f74da1104a`。
- クチバ（group 96 / map 5）へFactory Trial受付NPCを実配置した。固定CFRU-JP生成器の重複なしLv.50候補6体から既存party UIで3体を選び、single 3v3×3、1・2勝後の任意1体交換、各戦全回復、完走9 BPを実ROMで実行する。完走・敗北・辞退・cancel・保存後復旧は入場前party 600 byteをexact復元し、図鑑はseenだけを更新する。
- Factory ledgerは既存CFRU sector 31へ直接保存し、ROM用2 KiB rollback像をEWRAM `0x0203E400..0x0203EC00`へ配置した。stage 20はT06のhash検証済みoffsetsから施設、rental、trainer、active-state addressを解決し、SHA-256は `d82f280c4d9c6ca6b5268c287c9534c0e556bc9ba2ad2075d027af6a7580d4cd`、中央allocator overlapは0。
- 初戦の相手リープンはItem ID 0 / hold effect 0で正常だが、行動順schedulerが残留Quick Claw/Custap indicatorを再検証せず通知へ進むと、Item 0名の「？？？？？？？？」を反復して行動が止まることを命令単位fault injectionで再現した。通知直前のhold effect 26/96再検証はT06 sourceへ統合し、stage 21は統合済みの場合をzero-patchとして確認する。3御三家、正規Quick Claw/Custap/Quick Draw、clean ROMからのBPS完全往復がPASSし、SHA-256はstage 20と同じ `d82f280c4d9c6ca6b5268c287c9534c0e556bc9ba2ad2075d027af6a7580d4cd`。新規allocationは0。
- Vegaの実HMは既存Item 339〜346で、CFRU追加別名570〜577とは分離した。stage 22はHM05をフラッシュ、HM08をダイビングとして、バッグ所持だけでfield能力を許可する。badge、手持ち数、習得、適性、技枠を解禁条件から外し、既存map/terrain/follower/script境界とcallbackを維持する。8 HM×手持ち0体／未習得／習得済み、snapshot復元、Surf状態、BPS往復がPASSし、SHA-256は `18e31dee11f88060fcc81acbec58cada265ac715dc1c9398061afa2f16684407`、runtimeは408 bytes、allocation overlapは0。
- stage 22の5 stock battle-script root、command table、行動順・end-turn・status hookは固定CFRU-JP `e24a16f...` payloadの単一ownerで、T06から対象15 surfaceがbyte不変だった。legacy battle defineは全て無効で、麻痺1/2・1/4、眠り、凍り1/5、毒1/8、固定sourceの猛毒初回、やけど1/16、急所1.5倍、天候5/8 turn・雨晴れ補正・終了を固定RNG実ROMで確認した。追加patch 0のstage 23はstage 22とbyte-identicalでSHA-256 `18e31dee11f88060fcc81acbec58cada265ac715dc1c9398061afa2f16684407`。通常/trainer/double、Factory Trial 24 matrix、Raid 5 shield/終了/cleanupが現行ROMでPASSした。
- stage 24は固定CFRU move menuの実タイプ・有効度分岐を956-byte adapterで接続し、`VisualTypeCalc`由来の事前計算結果から抜群・半減・無効・タイプ一致を既存文字列・paletteへ表示する。1×/2×以上/0.5×以下/0×、Stellar/Tera Blast、double対象別表示、wild/trainer/Factory/Raid入力復帰、実使用canonical名をlibmGBAで確認した。SHA-256は `b7cb44552185b6478563b67d928dbeb1f50c62f77f7cd8b88059cb0a0661c4bb`、allocation overlapは0。Factory ROM byteは使用していない。
- stage 25はItem 347をだいじなもの「わざメモリー」とし、1個目のバッジ報酬、シオウ、カラスバを共通coreへ接続した。通常Lv.0/1・未来Lv拒否・既知/重複除外、D・Hビル/HOF/ものまねハーブ/空き枠のタマゴ技5条件、最後の1技・PP Up警告・HM・form技、battle/facility/Raid拒否、cancel時mode resetをlibmGBAで確認した。技削除はCFRU `SetMonMoveSlot` を通し、ケルディオの通常form復帰とPP Up段階のslot移動もPASSした。SHA-256は `13eab962d4de4149e463e5120b683302a0ed18170cecca6fa71341aba0479d07`、runtimeは2,931 bytes、allocation overlapは0。
- v1.3.3統合fixtureは同じstage 25で初戦3分岐、Kanto往復、Factory選択・交換・sector 31復旧、8 HM、状態異常・急所・天候、技選択UI、わざメモリーを再観測してPASSした。stage 20以後の新規serialized fieldは0。最終ROM SHA-256はstage 25と同じ `13eab962d4de4149e463e5120b683302a0ed18170cecca6fa71341aba0479d07`。
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
- T07でVega Species `0..411`を固定し、DPE定義済み1415 IDのうち206件（NONE sentinelを含む）をVegaへalias、欠落Species/form 1209件を`412..1620`へappendした。DPE予約hole `252..276`は生成対象外とした。
- canonical 1621行のBaseStatsでDPE Ability/ItemをT05 IDへ変換し、file offset `0x01600000`へ配置した。T06 canonical rootのaligned参照105件をrepointし、Vega prefix 412行はbyte一致。stage 07 SHA-256は `8634e053e4204311b38fb90e8ae3a0da112f2ebd50739763af931800b785252f`、fingerprintは `a29e55ed812ef7f233bd496a1cab6715aaff813511dce5604e4193a64689f74d`。
- 全行にofficial判定、canonical全国番号、review stateを付け、公式全国番号1〜1025と209 multi-form群を検証した。公式捕獲数は全国番号distinctで数えるためform重複で100種条件を水増ししない。既存trainer/wild/script/gift/evolution参照は全て解決し、追加キャタピーcanonical ID 412を実party memoryへ2 processで生成した。
- T08でT02のlive RAM/save ownerを統合し、CFRU sector 30/31 payloadのEWRAM `0x0203D000..0x0203D800`へ2,048-byte version 1 ledgerを割り当てた。magic/version/size/FNV-1a checksumと予約領域検査をfail-closedにし、既存Vega saveはsector checksum検証後だけ一回性migrationへ進める。
- Kanto渡航・訪問・殿堂入り・認定章・地方別heal/return anchor・League I/II・地方別NORMAL/RESEARCH profile、125共有捕獲/Raid stateをVega badge/HM/story flagと分離した。早期渡航は`0x0824 && 0x114B`または殿堂入りからmonotonicに付与する。
- Factoryはreset unsafeな348-byte/3体backupを廃止し、6×100 byte exact party snapshot、BP、24 mode streak、once reward、unlock、markerを原子的に保存する。typed encounter creditと完全なpending encounterも同じpersist-before-battle transactionにし、flash失敗、reset、二重課金・二重報酬をfocused C fixtureで検証した。
- `natureMint`、Hyper Training、Tera typeは80-byte BoxPokemon ABI内を正本とし、最大5個のタマゴqueueも個体byteをFIFO保存する。arcade coinは既存暗号化u16を再利用し、Factory BPは新規u16、research pointはearn hook不在のためstorageなしのDEFERとした。
- T09でVega 412行のfront/back、palette、coords、icon、footprint、鳴き声、Dexをlossless prefixで保ち、DPE追加1209行をcanonical順に統合した。追加行のLZ77 4,836ポインタ、icon 1,209ポインタを全検査し、NULLの内部補助IDは境界内default assetへ固定した。T06進化runtime root 38参照も新表へrepointした。stage 09 SHA-256は `af086a3772c5e6868e68a8d8c0be14a1cb1ae7bd69f70621908583f5153f03ad`、ROM末尾残量は210,548 byte。
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
- ブロッカーなし。

## 次の正本タスク

`design/tasks_next.md` を正とする。T00〜T18は全て完了し、2026-08-14追加のユーザー直接タスクを順次進める。

- USER-20260814-FIRST-BATTLE-LOOP: DONE。残留Quick Claw/Custap indicatorをhold effect再検証で破棄し、stage 21の実ROM回帰を通した。
- USER-20260814-HM-FIELD-ACCESS: DONE。Vega既存HM所持を正本にし、手持ち・習得・badgeから分離したstage 22の実ROM境界を通した。
- USER-20260814-BATTLE-RULES: DONE。現行ownerが単一CFRU payloadであることをsource/hook/固定RNGで確定し、zero-patch stage 23と全mode回帰を通した。
- USER-20260814-BATTLE-UI: DONE。固定CFRUの実タイプ・有効度・STAB表示をstage 24へ接続し、通常/Factory/Raidを同じownerと判定へ統一した。
- USER-20260814-MOVE-MEMORY: DONE。だいじなものと既存NPCが共用する無料の技思い出し・技忘れ・段階解禁タマゴ技をstage 25へ結合した。
- USER-20260814-QOL-RELEASE: IN_PROGRESS。同一stage 25の全QOL/Factory/Kanto統合スモークはPASS。v1.3.2 freshはstage 23まで同一ROMを再構築後、T06の可変な実行時間を含むJSON全体SHA pinで停止した。安定UI ABI契約へ修正したv1.3.3 sourceをtag固定して最終fresh rebuildを行う。

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
