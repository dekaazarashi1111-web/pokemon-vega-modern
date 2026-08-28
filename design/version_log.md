# version_log.md (append-only)

フォーマット例:

## 2025-01-01T00:00:00Z
- Version: v1.0.0
- Commit: <hash or ->
- Task: <id or -> / <title>
- Summary:
  - 変更点を2〜4行で
- Verify: <command> <PASS|FAIL>

## 2026-08-12T07:18:12Z

- Version: `bootstrap-0.1.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T00` / 受領資料・再現基盤統合
- Summary:
  - 受領したROM・パッチ・ZIPをGit管理外で不変保管し、参照ROMのbyte一致と775 byteの厳密競合監査を再現した。
  - プレイブック、監査、統合設計を役割別に統合し、セッション再開入口とT00〜T18の正本キューを整備した。
  - CFRU-JP、DPE-JP、pokefireredを2026-08-12時点のGitHub最新HEADへ固定し、安全なquickstartと検証基盤を追加した。
- Verify: `bash scripts/verify_wsl.sh` PASS

## 2026-08-12T12:12:25Z

- Version: `design-v2-dual-region-0.2.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260812-V2-DUAL-REGION` / V2切替えと二地方実現性評価
- Summary:
  - V2二地方生態版の不変受領資料を追加し、V1を来歴保存へ切り替えた。
  - clean FireRed日本版からカントー本土を新規名前空間へ復元し、トーホクと双方向に往復する方針を固定した。
  - 256 physical map候補、180 unique layoutsの初期監査とV2意味課題をタスクゲートへ反映した。
- Verify: `bash scripts/verify_wsl.sh` PASS

## 2026-08-12T12:41:58Z

- Version: `design-early-kanto-0.3.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260812-EARLY-KANTO` / Vegaクリア前のカントー早期アクセス設計
- Summary:
  - シオウ3個目バッジとアーシア島D・Hビル攻略後から、殿堂入り前でもカントーへ任意渡航できる二段階進行を採用した。
  - Lv.68〜100固定帯、初回警告、強制戦闘なしの安全導線、無料常時帰還、地方別state/anchor分離を受入条件にした。
  - V2の殿堂入り前提は原本不変のまま正規化層でoverrideし、T02/T08/T12〜T17と36件のsmoke matrixへ反映した。
- Verify: `bash scripts/verify_wsl.sh` PASS

## 2026-08-12T13:20:37Z

- Version: `roadmap-fast-execution-0.4.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260812-FAST-ROADMAP` / 高速実行ロードマップ整理
- Summary:
  - T00〜T18を準備wave、固定正本統合順、成果基準、critical path、ボトルネックへ整理した。
  - taskctlへRESUME/PRIMARY/PARALLEL_PREP、wave、統合順の自動表示と誤順開始拒否を追加した。
  - DAG、キュー、各タスク仕様、INDEX、MASTER_PLANのdriftを自動検出し、直近T01のtoolchain/隔離build手順を具体化した。
- Verify: `bash scripts/verify_wsl.sh` PASS（42 tests）

## 2026-08-12T14:03:43Z

- Version: `design-qol-fast-minimal-ui-0.5.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260812-QOL-FAST-MINIMAL-UI` / 現代育成・高速操作QOL追加
- Summary:
  - 現代孵化、経験アメ、育成値UI/道具、全体学習装置、タマゴ/PC/自動戦闘QOLを既存T01〜T18へ割り当てた。
  - 既定即時文章、ダッシュ25%以上・自転車50%以上の高速化と49件のsmoke条件を固定した。
  - UIは既存画面のcompact adapter、eventは短い `SIMPLE_EVENT` に限定し、QOL-Bが最初のカントー縦切りを待たせない順序にした。
  - READY先頭順を助言化し、検証重複を削減しつつ最終stage/private guard/commitを含むGit完了手順へ統一した。
- Verify: `bash scripts/verify_wsl.sh` PASS（42 tests）

## 2026-08-12T23:22:49+09:00

- Version: `design-battle-factory-0.6.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260812-BATTLE-FACTORY` / Battle Factoryと施設外ランダム捕獲NPC追加
- Summary:
  - 固定CFRU sourceからのRental Factory移植、4段階解禁、BP/shop、Mirage分離、元party完全復元を既存T01〜T18へ割り当てた。
  - クチバ港の簡易受付と建物外NPCを採用し、新規大型map/full-screen UIなしでランダム捕獲戦を即時開始する仕様を固定した。
  - 支払い済み個体のatomic saveと同一個体retryを定義し、smoke matrixを57件へ拡張した。
- Verify: `bash scripts/verify_wsl.sh` PASS（42 tests）

## 2026-08-13T00:07:01+09:00

- Version: `design-trainer-ai-balance-0.7.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260813-TRAINER-AI-BALANCE` / 固定CFRU-JP AIとトレーナー難易度設計追加
- Summary:
  - 固定CFRU-JP AIの3 profile、trainer育成値、single/double、gimmick、cache/RNG/performanceを既存T01〜T18へ割り当てた。
  - Vega本編の横強化、初回boss/league、Tohoku再戦と3段階league、NORMAL/RESEARCH、Sphere、Mirageを機械検証可能な仕様へした。
  - TM再利用と固定CFRU Raidによる簡易高難度Raidを既存UI前提で追加し、smoke matrixを67件へ拡張した。
- Verify: `bash scripts/verify_wsl.sh` PASS（42 tests）

## 2026-08-13T04:21:11+09:00

- Version: `upstream-repro-0.8.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T01` / 固定DPE-JP/CFRU-JP上流ビルド再現
- Summary:
  - ARM/host/mGBA/Windows converter toolchainを完全fingerprint化し、vendor外のACL保護sandboxからDPEとCFRU 3 profileを各2回再構築した。
  - ROM/blob/offsetsの再現性、固定挿入領域と予約領域、hidden insert失敗、private cleanup、cache/report identityを自動gateにした。
  - Factory参照との4カテゴリ実挙動比較と、固定CFRU AIのsingle/double cold/warm ARM cycle fixtureを実測し、QOL/Factory/AIの機械可読inventoryと再生成reportを確定した。
  - T02で使うfixed output hash、symbol/fixture provenance、Save/flag/Factory監査入口を固定した。
- Verify: `make upstream-toolcheck`, `make upstream-repro`, report削除相当からのbyte同一再生成、`bash scripts/verify_wsl.sh` PASS（87 tests）

## 2026-08-13T04:26:37+09:00

- Version: `wsl-targeted-checks-0.8.1`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260813-REMOVE-WSL-VERIFY` / WSL全体標準verifyの廃止
- Summary:
  - `scripts/verify_wsl.sh` を削除し、WSLのall-in-one検証経路を廃止した。
  - 運用・入口・全taskの完了手順を、変更対象とtask acceptanceに必要な最小gateだけを実行する方針へ統一した。
- Verify: active実行参照0、`git diff --check` PASS。repository全体verifyは未実行。

## 2026-08-13T05:33:08+09:00

- Version: `exact-compatibility-audit-0.9.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T02` / Exact ROM/RAM/save/ID audit
- Summary:
  - DPE/CFRU fixed write 6,143件をactive configと実emission spanで再生し、T01の4成果とbyte一致、UNKNOWN 0、許可overlap 156組を確定した。
  - Vegaの425 map、132 encounter、743 trainer、4,665 script nodeと、早期渡航flag、RAM/save/ID、QOL、Factory/Mirage、通貨、AI状態を機械可読化した。
  - 11監査成果を決定的生成し、入力identity、byte一致、意味契約、分類根拠、code context/disassemblyをfail-closedで再検証できるようにした。
- Verify: focused 56 tests、`make t02-check`、py_compile、独立read-only再レビュー PASS。WSL全体verifyは未実行。

## 2026-08-13T06:16:46+09:00

- Version: `vega-module-harness-0.10.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T03` / Create rebuildable Vega module harness
- Summary:
  - clean+Vega IPSから32 MiB ROMを再構築するstage driver、named allocator、expected-byte assertionを追加した。
  - hook 0件の34-byte no-op Thumb moduleを拡張領域へ配置し、Vega-owned byteを完全保持した。
  - title/new game/map movement/save/fresh-core loadをlibmGBAでreference/candidate一致確認し、連続2 buildをbyte一致させた。
- Verify: `make harness`, `make harness-check`, focused 27 tests、独立read-only再レビュー PASS。WSL全体verifyは未実行。

## 2026-08-13T07:42:09+09:00

- Version: `move-port-0.11.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T04` / Port Vega Move IDs into CFRU model
- Summary:
  - Vega Move ID 0〜511を固定し、CFRU追加551技を512〜1062へappendした1,063技manifestとstage 04を生成した。
  - V3現代化61件・独自技70件を構造化してcompile済みeffect adapterへ変換し、同名別技2件を「ソウルバイト」「ダークスナイプ」へ改名した。
  - game charmap表、992 alias、44,032-byte bridge、178 pointer repointを生成し、実wild battleで技実行とPP消費・HP低下を確認した。
- Verify: focused 38 tests、`make harness-check`、`make moves-check`、manifest/import検査、生成C compile、独立read-only監査 PASS。WSL全体verifyは未実行。

## 2026-08-13T09:24:03+09:00

- Version: `id-spaces-0.12.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T05` / Unify Type Ability Item ID spaces
- Summary:
  - Vega既存IDを固定し、Type 25、Ability 312、Item 999のstable manifest/modelを決定的に生成した。
  - 意味同一Item 161件、CFRU append 613件、QOL append 11件を明示rangeへ配置し、827 source alias、ball 27、進化石12、進化道具40を解決した。
  - Fairy/Stellar表示・相性と45 QOL効果を完全化し、T06のcanonical positional runtime表再構築hard gateを機械可読化した。
- Verify: focused 61 tests、manifest validator、T05 build/check、host/ARM compile、T03/T04 check、独立read-only監査 PASS。WSL全体verifyは未実行。

## 2026-08-13T21:33:01+09:00

- Version: `battle-core-0.13.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T06` / Port CFRU battle core
- Summary:
  - 固定CFRU-JPのbattle-only hook 955件とcanonical runtime表をstage 04へ統合し、未分類変更0の32 MiB stageを決定的に生成した。
  - 通常戦・主要戦闘経路、3段階AI、Factory、育成QOL、相互排他gimmick、Mirage、high-difficulty Raidを実schedulerへ接続した。
  - Raid partner moves、controller上限、自然入力・捕獲・PC ABI・終了cleanupを修正し、5/5 shieldからRaid後通常戦とturn-limitまで完走させた。
- Verify: T06 build/check、focused 135 tests、3本のlibmGBA runner各2 process、独立read-only監査 PASS。fingerprint `58417b356175a6e291f6fc194f5ac2e2335c9fbb76e2167db001714f75713a59`、ROM SHA-256 `c0deba02342ccb64558243c897728aea878cc669fb5d458c7543b70a4d9d4f05`。WSL全体verifyは未実行。

## 2026-08-14T02:44:24+09:00

- Version: `species-port-0.14.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T07` / Vega IDを固定してDPE Speciesを移植する
- Summary:
  - Vega Species 0〜411を固定し、DPE identity 206件と追加Species/form 1209件を1621行canonical manifestへ統合した。
  - T05 canonical Ability/Itemへ変換したBaseStatsをDPE領域へ配置し、T06 root 105件をrepointしたstage 07を決定的生成した。
  - 公式全国番号1〜1025とform共有番号を完全化し、form重複なしの100種捕獲countと追加Speciesの実party生成を検証した。
- Verify: T07 build/check、focused 27 tests、manifest validator、生成C compile、libmGBA 2 process PASS。fingerprint `be3931a374adfb902b6add1193adc07925491196b4a335fb17fd396199872188`、ROM SHA-256 `3c24e8eb6c8f5ca10e272f1aa6c7daa375741b9061a012385661fba81652f7b8`。WSL全体verifyは未実行。

## 2026-08-14T03:01:22+09:00

- Version: `save-compatibility-0.15.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T08` / RAMとSaveBlock互換性を解決する
- Summary:
  - live overlap 0のRAM/save台帳と、sector 30/31内2 KiBのversioned checksum ledgerを実装した。
  - 旧Vega一回性migration、二地方/QOL/図鑑/共有捕獲/Raid stateをbadge/HM/storyから分離した。
  - Factory exact party、BP/rewardとpending encounterをflash確定前transactionにし、Mirage/仮想item ownerを分離した。
- Verify: `make save-layout-check`、focused 5 tests、host C `-Wall -Wextra -Werror` compile、py_compile PASS。report SHA-256 `aad1a0f63eebf0bfc52ee5a18b883153a2d8e05baf8cc1b4161d0df0aa304a1e`。WSL全体verifyは未実行。

## 2026-08-14T03:23:05+09:00

- Version: `species-surface-0.16.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T09` / graphics・cry・Dex・進化・learnsetを統合する
- Summary:
  - Vega固定412行のSpecies assetをlosslessに保ち、DPE追加1209行を含む1621行canonical surfaceをstage 09へ配置した。
  - 進化・level/egg/TM/HM/tutorのSpecies/Move/Item IDを変換し、V2進化553行を意味重複なし510行へ正規化した。
  - Vega/全国Dex集計を分離し、現代式孵化、5個queue、party/box満杯、compact IV/EV、3孵化mode、Oval Charmを固定fixtureで実装・検証した。
- Verify: `make species-surface-check`、focused 20 tests、host C `-Wall -Wextra -Werror`、py_compile、`git diff --check` PASS。ROM SHA-256 `9dfd7caf04cdda4c0b4b559ce842a53341667c1f4e5af298348a55c655230345`。WSL全体verifyは未実行。

## 2026-08-14T03:37:45+09:00

- Version: `engine-slice-0.17.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T10` / engine vertical sliceを完成させる
- Summary:
  - stage 09の追加Species/Move/Ability/Item/進化をlibmGBAと継続save fixtureで通し、release debug accessを無効に固定した。
  - QOL-Aのrelease既定値、高速移動・即時文章・共通数量UI・アメ・育成/save境界を15-feature matrixへ固定した。
  - Factory、報酬遭遇、3 AI profile、TM license、Mirage、Tohoku overlay/Research、Raidを既存UI契約で統合検証した。
- Verify: `make engine-slice-check`、focused 17 tests、libmGBA 2 process、release/debug host C compile、py_compile PASS。metadata SHA-256 `b69b17f446b6f0e924d40e21f51e69382fcbf7036fca1bd2587582b49a7558ad`。WSL全体verifyは未実行。

## 2026-08-14T03:45:51+09:00

- Version: `kanto-importer-0.18.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T11` / Kanto map importerを構築する
- Summary:
  - 本土256 mapを3個の安全な新規groupへ予約し、180 layoutのclean BPRJ raw照合とV2 47地点crosswalkを生成した。
  - クチバ民家1の地形・collision・tileset・NPC/warp座標をcanonical importし、未取込warpを安全terminalへ再接続した。
  - 原作global story stateと英語textを除外し、名前空間化したlocal stub、決定的build/check、structural round-tripを固定した。
- Verify: importer build/check、focused 5 tests、manifest validator PASS。256/180/179/47件、ID重複0、story-state非混入、round-trip byte一致を確認した。WSL全体verifyは未実行。

## 2026-08-14T04:00:35+09:00

- Version: `content-schema-0.19.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T12` / symbolic content schemaとgeneratorを構築する
- Summary:
  - 二地方の進行/map/encounter/trainer/QOL/event/facility/currency/Raidをraw IDなしsymbolic schemaへ統合した。
  - V2 59検査を独立再計算し、raw意味課題を正規化前に拒否して541 family・125共有捕獲・8 gym rewardを昇格した。
  - optional Lv.68〜100、SIMPLE_EVENT、供給tier、AI/gimmick、transaction、Raid反復性とT13 physical binding境界をfail-closedにした。
- Verify: content build/check、focused 5 tests・17 negative/valid fixture、JSON schema、py_compile、resolutionなしemit期待FAIL、完全resolution emit PASS。report SHA-256 `3f2278ea269d405403196950a6f482b1079059bf95ca3c3fdbfe94e18838d58c`。WSL全体verifyは未実行。

## 2026-08-14T04:11:12+09:00

- Version: `vermilion-slice-0.20.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T13` / クチバのpostgame vertical sliceを作る
- Summary:
  - 中盤2 flagからの恒久渡航、3つの無料往復edge、到着時Kanto anchorをT08 save runtimeへ接続した。
  - クチバ安全導線7 mapをphysical bindし、認定章ジム、Factory Trial、建物外遭遇transactionを統合した。
  - 解禁境界、船上戦4結果、save失敗rollback、whiteout、puzzle/rewardを決定的fixtureへ固定した。
- Verify: Vermilion build/check、focused 13 tests、host C compile/run、py_compile、diff check PASS。report SHA-256 `3ec549e6b407a98dc613ceadf9d588de219514524ce6e7eff0fc05d61ed82b60`。WSL全体verifyは未実行。

## 2026-08-14T04:16:29+09:00

- Version: `kanto-maps-0.21.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T14` / 選定した全カントーマップをimportする
- Summary:
  - 本土256 mapを253 operational・3 intentional DEFERへ確定し、全mapをKANTO namespaceへcanonical変換した。
  - クチバ起点の全到達、47 logical地点、warp/connection/ID/tileset/one-way validatorを通した。
  - 180 layoutとmetadataを329,866 bytesへdedupeし、future tail overlap 0を固定した。
- Verify: full Kanto build/check、focused 12 tests、py_compile、diff check PASS。connectivity SHA-256 `af6510aeec2aa5bbeafea5c0150c792fe3fe281d1902ea99c95f33b22e54aa9a`。WSL全体verifyは未実行。

## 2026-08-14T04:25:47+09:00

- Version: `kanto-progression-0.22.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T15` / postgame解禁とジム進行を実装する
- Summary:
  - 早期認定章1〜4とHOF後5〜8、Kanto League、League I→II→Finalを39-node DAGへ分離した。
  - 35 QOL境界、Factory 4 tier、地方強豪3段階、Research/TM/DexNav/競技品/UB・Paradox/Raidを状態fixtureへ固定した。
  - 全253 map gate、恒久無料帰還、Vega進行非干渉、owner分離、release shortcut無効を機械検査した。
- Verify: progression/content/T13/T14/engine build-check、focused unittest、py_compile、diff check PASS。report SHA-256 `928a02d56dca147a64f7aa03601060c4bbf767a8d68a98b94145c9e1c30b03cb`。WSL全体verifyは未実行。

## 2026-08-14T05:20:17+09:00

- Version: `content-population-0.23.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T16` / 二地方のencounter・trainer・item・施設contentを本配置する
- Summary:
  - 96論理地点、541系統×2地方、125共有捕獲key、Gym/League/再戦、Factory/Mirage、QOL/進化道具をsymbolic manifestへ完全化した。
  - Tohoku NORMALをbyte保護し、Kantoを `FIXED_HIGH_LEVEL_OPTIONAL` Lv.68〜100、警告・安全帰還・動的scaleなしへ固定した。
  - T09/T14の衝突配置を中央allocatorで解消し、T16 payloadをintegration_modulesへ配置した32 MiB stage 16を生成した。
- Verify: T12/T15/T16 build/check、manifest validator、focused 17 tests、py_compile、diff check PASS。ROM SHA-256 `5c56b86da56b2a15d9e75bad8a85db83e1c63e6a7814e265b996ce07d50660b5`、allocation overlap 0。WSL全体verifyは未実行。

## 2026-08-14T06:54:10+09:00

- Version: `regression-rc-0.24.0`
- Commit: `-`（本エントリを含むコミット）
- Task: `T17` / 本編・engine・Kantoの回帰試験を通す
- Summary:
  - Kanto 253 mapと実asset/wild root、QOL-B、29 trainer/174 party row、8 gym＋League eventを中央allocator管理のstage 17へ統合した。
  - 自然new-gameからKanto描画・移動・往復、QOL-B、trainer/progression pointer graphをlibmGBA 2 processで実行した。
  - 400地方往復、125共有捕獲、34 event分岐、20 facility mode、3 AI profileを決定論fixtureとmanual checkpointへ固定した。
- Verify: `make regression-check`、manifest validator、focused 4 tests、py_compile、diff check PASS。ROM SHA-256 `dc77691bb2f2bfb1965803707f937c03c73dfc96605cfb7358ba35821f865997`、allocation overlap 0。WSL全体verifyは未実行。

## 2026-08-14T09:23:50+09:00

- Version: `v1.0.0`
- Commit: `-`（本エントリを含むコミット。release source tagは`a98b991dbd8742b8f51a611f8d30dc714044400a`）
- Task: `T18` / 再現可能なrelease pipelineを完成させる
- Summary:
  - 32 MiB最終ROM、clean FireRed日本版Rev.0用BPS、9-member決定論ZIP、完全な日本語利用説明・credits・save互換性文書を生成した。
  - BPS完全往復、archive禁止物、source/input/toolchain pin、QOL/Factory/AI契約をrelease gateへ固定した。
  - tagged sourceの隔離fresh checkoutからT01〜T17、final/BPS/ZIPを完全再構築し、byte一致させた。
- Verify: `make release-fresh-check`, `make verify-release`, focused 47 tests、T17 check、manifest/task graph/private guard、diff check PASS。final ROM/BPS/ZIP SHA-256 `dc77691bb2f2bfb1965803707f937c03c73dfc96605cfb7358ba35821f865997` / `a20a85a5501e134b36020c0b8b169958c1ef1876d26914d725ffeecceaf7c9e4` / `eb11865e3817f4d4ead53f10288a8c31ffa818e6f3e8c8c26c3d9164c7985cf6`。

## 2026-08-14T10:37:50+09:00

- Version: `v1.1.0`
- Commit: `d2a3aeaa3f9510be0451b09f0c6fee71b4675a4c`（release source tag。完了ログは本エントリを含むコミット）
- Task: `USER-20260814-TRAINER-V4` / ユーザー提供V4でVega本編トレーナーを再設計する
- Summary:
  - V4の141戦・610体をcanonical IDへ全件解決し、既存本編Trainer ID 648件の編成・レベル・道具・技・IV下限・trainer itemをstage 19へ実配置した。
  - AI rankを固定CFRU-JPのBasic / Semi Smart / Full Smartへ対応し、独自AIを追加せず、名前・class・double battleおよびMirage／未指定Sphereを維持した。
  - 追加event枠のない21戦と通常ABI外の性格・特性・EV・gimmick triggerは検証済み台帳として保持し、誤った既存戦への接続を拒否した。
  - v1.1.0最終ROM、clean FireRed日本版Rev.0用BPS、9-member決定論ZIPを生成し、tagged fresh checkoutでもbyte一致させた。
- Verify: `make trainer-rebalance-check`, focused 11 tests、py_compile、`make final`, `make release-patch`, `make verify-release`, `make release-fresh-check`, task graph/private guard、diff check PASS。final ROM/BPS/ZIP SHA-256 `43bcc2bf20364f2e8fcf6e03e9bcbadf9f9f6c2308592bdb1bac364e3f00c478` / `2bd167ab762645becd4b2a3eeda348aeb109d4d636d3521e4c753d7ef33ca101` / `6031174f113f671d9001ed8f0b694ef411e5a3b10d4eb5700be89f79580c2d3c`。

## 2026-08-14T11:35:07+09:00

- Version: `v1.2.0`
- Commit: `3d81fd6a29de7d4ed96375809e9c28e71195327e`（release source tag。完了ログは本エントリを含むコミット）
- Task: `USER-20260814-FACILITY-RUNTIME` / Factoryのランダムrental・勝利後交換を実ROMで遊べるようにする
- Summary:
  - クチバへTrial受付NPCを物理配置し、固定CFRU-JPのLv.50候補6体から3体を選ぶsingle
    3v3×3、1・2勝後の任意交換、各戦全回復、3連勝9 BPをstage 20へ結合した。
  - 入場前party 600 byteをsector 31へ保存し、完走・敗北・辞退・cancel・save/reset復旧で
    exact復元する。図鑑はseen-only、Mirageと通常trainer状態は非干渉とした。
  - Standard / Full / Master、BP shop、施設外報酬遭遇はruntime未接続と明記し、v1.2.0の
    実装済み範囲をTrialへ限定した。
  - 32 MiB最終ROM、clean FireRed日本版Rev.0用BPS、9-member決定論ZIPを生成した。
- Verify: `make facility-runtime-check`、focused 16 tests、py_compile、`make final`,
  `make release-patch`, `make verify-release`, task graph/private guard、cached diff check PASS。
  重いfresh-checkはユーザー指示により再実行していない。final ROM/BPS/ZIP SHA-256
  `0976e5d84b12fc3e2175278ecce1ee2fda1cf3dc2c9b3ee1bbc4cd85e7b60ac3` /
  `29707aa8e1acde91bb4fb11c993e1b68cc7351663d7d350d93da8fd1691da10b` /
  `fad037c85632cda691cb6d7637310fd8be123cf62260c65bebeba2acd001fa82`。

## 2026-08-14T13:15:35+09:00

- Version: `first-battle-hotfix-stage21`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-FIRST-BATTLE-LOOP` / 初戦の行動順メッセージ無限ループを修正する
- Summary:
  - Item 0に残った不正Quick Claw/Custap indicatorを通知直前のhold effect再検証で破棄し、同じターンを継続するstage 21を生成した。
  - 初戦3分岐とfault injectionで不正通知0、PP/HP更新を確認し、正規Quick Claw / Custap / Quick Drawの先行効果と各1回通知を維持した。
  - 既存stage 20を再利用し、新規allocation 0、clean ROMからのBPS完全往復を確認した。公開release更新と重いfresh buildは後続統合まで保留した。
- Verify: `make first-battle-hotfix-check`、focused 4 tests、py_compile、task graph/private guard、diff check PASS。stage 21 SHA-256 `ac0bd8c54ea8a6ee76a56fb0e4cd124e01ace03c4a72ebe923e87e536c8ec521`。

## 2026-08-14T13:37:12+09:00

- Version: `hm-field-access-stage22`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-HM-FIELD-ACCESS` / HM所持だけで対応フィールド技を使用可能にする
- Summary:
  - Vega既存HM Item 339〜346をfield能力の正本にし、CFRU追加別名、badge、手持ち、習得、適性、技枠から分離した。
  - 8 callbackの未所持迂回を閉じ、既存map/terrain/follower/script境界を維持する408-byte runtimeをstage 22へ結合した。
  - 8 HM×手持ち3条件、保存相当復元、Surf状態、callback gate、BPS往復を実ROMで確認した。公開releaseと重いfresh buildは後続統合まで保留した。
- Verify: `make hm-field-access-check`、focused 4 tests、py_compile、task graph/private guard、diff check PASS。stage 22 SHA-256 `64dafd7c265f44153465e630dafd1a0928ba34819d657a6ad3870d2a181e87bf`。

## 2026-08-14T14:10:33+09:00

- Version: `battle-rules-stage23`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-BATTLE-RULES` / 状態異常・急所・天候を固定CFRU-JP既定へ統一する
- Summary:
  - stage 22の状態異常・行動順・急所・damage・天候が固定CFRU-JP payloadの単一ownerで、legacy defineとVega fallbackが有効でないことをsource/hook単位で確定した。
  - 麻痺、眠り、凍り、毒、猛毒、やけど、急所、4天候と単一damage予約を固定RNG実ROMで検証した。
  - 通常/trainer/double、Factory Trial、Raidを現行ROMで通し、追加patch 0のbyte-identical stage 23を確定した。公開releaseと重いfresh buildは後続統合まで保留した。
- Verify: `make battle-rules-check`、focused 6 tests、current-stage policy smoke、py_compile、task graph/private guard、diff check PASS。stage 23 SHA-256 `64dafd7c265f44153465e630dafd1a0928ba34819d657a6ad3870d2a181e87bf`。

## 2026-08-14T14:41:59+09:00

- Version: `battle-ui-stage24`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-BATTLE-UI` / 戦闘UIと有効度表示をCFRU/Factory系へ統一する
- Summary:
  - 固定CFRU-JPの技選択ownerを維持し、実damageと同じ事前計算値から実タイプ・有効度・STABを表示する956-byte adapterをstage 24へ結合した。
  - 1×、2×以上、0.5×以下、0×、Stellar/Tera Blast、double対象別表示を既存CFRU文字列・paletteで実ROM検証した。
  - canonical実使用名の未解決0件と、wild/trainer/double/Factory/Raidの入力復帰・cleanupを確認した。公開releaseと重いfresh buildは後続統合まで保留した。
- Verify: `make battle-ui-check`、focused 6 tests、UI 2-process / policy current-stage libmGBA smoke、py_compile、task graph/private guard、diff check PASS。stage 24 SHA-256 `870d3a49e9f4004e3bf7003469c2159dc73a96cb81c5101f572971a08af73387`。

## 2026-08-14T15:45:41+09:00

- Version: `move-memory-stage25`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-MOVE-MEMORY` / 無料の共通技管理「わざメモリー」を実装する
- Summary:
  - Item 347、1個目のバッジ報酬、シオウ、カラスバを無料の共通技管理coreへ接続し、キノコ・ハーブ消費を廃止した。
  - T09混在learnsetの現在Lv候補と、D・Hビル/HOF/ハーブ/空き枠で段階解禁するCFRUタマゴ技候補をvolatile modeで切り替えた。
  - HM忘却を許可し、最後の1技・PP Up・form・contextをguardした。削除はCFRU技slot経路を通し、ケルディオform連動とPP Up移動を維持した。
- Verify: `make move-memory-check`、focused 6 tests、libmGBA 2 process、py_compile、task graph/private guard、diff check PASS。stage 25 SHA-256 `0515f2bad9ea39728446779352f48db8c8eed10bb276470976893bce71e614a9`。

## 2026-08-14T21:01:50+09:00

- Version: `v1.3.3`
- Commit: `c6f15f4ad421d35e33853039fae4ae4fabedb3ec`（release source tag。完了ログは本エントリを含む後続コミット）
- Task: `USER-20260814-QOL-RELEASE` / 全QOL変更を統合して再現可能な遊べるreleaseを確定する
- Summary:
  - stage 20〜25の初戦、HM、固定CFRU戦闘規則、実タイプ・有効度・STAB UI、無料技管理を、既存Kanto/Factoryと同じ最終ROMへ統合した。
  - T06メタデータの可変経過時間をUI ABI pinから除外し、ROM、offsets、linked objectの決定的な契約へ修正した。最終ROMとsave形式は不変である。
  - clean FireRed日本版Rev.0用BPS、32 MiB BPRJ ROM、9-member決定論ZIP、日本語release/save文書をv1.3.3へ更新した。
  - annotated tag `v1.3.3` の隔離fresh checkoutから全chainを再構築し、final/BPS/ZIPを通常成果とbyte一致させた。
- Verify: `make release-fresh-check`, `make verify-release`, battle UI/QOL integration build+check、focused 16 tests、T17 check、task graph/private guard、diff check PASS。final ROM/BPS/ZIP SHA-256 `13eab962d4de4149e463e5120b683302a0ed18170cecca6fa71341aba0479d07` / `9f99d3663458b7f065de9ab0104eff54562331c0467c25fee3e9983935959c5f` / `aac8894833b5124e8ec82edd166291961c1c3c4c5e7c6a24c3c86fd96e894af5`。

## 2026-08-15T00:41:52+09:00

- Version: `v1.3.3`（追試・差分ビルド高速化。ROM byte変更なし）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260814-BATTLE-UI-LOOP-FAST-BUILD` / 戦闘UI・アクタシ初戦ループ・高速差分ビルドを検証・修正する
- Summary:
  - v1.3.3にstage 24 UIが既に適用済みと通常入力経路で確認した。等倍・タイプ不一致は元CFRUどおり空欄を維持し、L/R設定のLで技名・接触・威力・命中詳細を開閉する。
  - 自然new-game経路のアクタシ初戦で不正行動順通知0、PP/HP進行、RAM pointer/shadow安定を確認した。正常なQuick Claw/Custap/Quick Drawは維持した。
  - 検証済みstageと入力hashから変更所有stage以降だけを生成するfast ROM driverを追加し、後段3工程を214.313秒で完了した。
  - Windows Downloadsへ32 MiB verified ROMを配置した。SHA-256は既存v1.3.3と同じ`13eab962d4de4149e463e5120b683302a0ed18170cecca6fa71341aba0479d07`。
- Verify: first-battle/UI/QOL統合check、`final-fast`、focused 76 unittest＋release 9 tests、fast dry-run、py_compile、task graph/private guard、diff check PASS。

## 2026-08-15T05:40:28+09:00

- Version: `v1.3.4`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-BATTLE-UI-LOOP-AUDIT` / 直前修正を再監査して実症状を直す
- Summary:
  - アクタシの正規第2特性Ability 64へ残留したQuick Draw indicatorを通知前に破棄し、正規Ability 260の通知を維持した。
  - 固定CFRU objectにinline済みの旧表示をexact-prologue wrapperで覆い、実技カーソル経路へ抜群・半減・無効・STAB表示を接続した。
  - stage 20以前を再利用する差分chainでstage 21〜25、final、BPS、9-member ZIPを再生成し、旧v1.3.3と識別できるv1.3.4へ更新した。
  - RAM境界をfail-closedにし、UIレポートのJSONキー順driftを決定的出力へ修正した。
- Verify: first-battle/HM/battle-rules/UI/move-memory/QOL build+check、focused 29 tests、release BPS往復・archive検査、py_compile、task graph/private guard、diff check PASS。final ROM SHA-256 `0b04e0042312c90450c007a83ed94476a11b16b11b2f10f5307e76eed9acb497`。

## 2026-08-15T06:20:22+09:00

- Version: `v1.3.4`（Delta state診断追記。ROM byte変更なし）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-DELTA-STATE-DIAG` / v1.3.4 Delta再現stateと直前2コミットを再監査する
- Summary:
  - 2件のDelta stateで特性が異なっても、共通して戦闘構造pointerが0であることを確定した。ヘドロえきによる行動順変化ではなく、非互換実行stateの混入である。
  - 固定Delta/VBA-M engineの完全新規起動では、アクタシ初戦、技Type、PP/HP進行、行動順通知が正常だった。ROMは再生成せず、Auto Save削除・hard restart手順を保存互換文書へ追記した。
- Verify: 固定VBA-M fresh route、focused 20 tests、`make battle-ui-check`、`make first-battle-hotfix-check`、final/Windows SHA-256一致 PASS。

## 2026-08-15T08:04:45+09:00

- Version: `v1.3.5`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-BATTLE-HELP-COLLISION` / 戦闘中Lの旧HELP競合を再現して修正する
- Summary:
  - 旧savestate混入とした診断を訂正し、FR由来のHELP画面退避がCFRU戦闘EWRAMと競合して`gNewBS`を0にするROM側の根因を確定した。
  - 戦闘中だけ旧HELP openを抑止し、通常HELP設定のLをCFRU技詳細へ渡した。field HELP、L/R設定、既存battle modeは維持した。
  - stage 24以降を225.3秒で高速再生成し、固定VBA-M engineで最終ROMの画面と戦闘pointerを確認した。
- Verify: battle UI build/check、QOL integration check、focused 29 tests、最終ROM fixed-engine checkpoint、py_compile、task graph/private guard、diff check PASS。final SHA-256 `7db577ce5a2db02c9a33b1d87338be756f42e5cfe0cbad49bac4ff7dada45cc8`。

## 2026-08-15T11:04:35+09:00

- Version: `v1.3.6`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-RUNTIME-STABILITY` / trainer開始・外来生態・戦闘表示の実ROM安定化
- Summary:
  - Vega/appendで混在した初期技表ABIを統一し、追加Speciesを使うtrainer戦の黒画面停止を修正した。
  - T501を最初の草むらmap `3/19`へ正しく結合し、既存表保持の5%/8候補追加抽選を実ROMへ接続した。
  - 外来生態293設計行のうち通常方式153行が接続済み、専用方式140行は未接続という境界をmetadata・test・KI-006に固定した。
  - 通常turnのQuick Draw guardをfast path化し、アクタシの「げきりゅう」「ヘドロえき」のどちらでも不正な行動順通知が発生しないことを再検証した。
- Verify: `build_fast_rom.py --from species-surface` 363.6秒、最終`--from regression` 183.2秒、focused 53 tests、Species `1..1620`、有効trainer 772件、最初の草むら4096抽選/実遭遇、L詳細、傷薬HP表示、task graph/private guard/diff check PASS。final SHA-256 `aeaa8724db55aaff5261581b4faead9aaf91b013e0fc9fb04bb9ae5bf701f5e1`。

## 2026-08-15T18:45:51+09:00

- Version: `v1.3.7`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-ECOLOGY-RUNTIME` / 外来生態293行と生態レーダーを実ROMへ接続する
- Summary:
  - 外来生態設計293/293行を通常・朝昼・夜・日替わり群れ・釣り・隠れ探索の95 runtime entryへ変換し、0件保留で実遭遇入口へ接続した。
  - RTC自動と、朝昼・夜・群れ・隠れ探索を確認・切替できるItem 348「せいたいレーダー」を追加した。1個目バッジと既存save用シオウ補完から取得できる。
  - バッジ・竿・殿堂入りlevel条件を接続し、通常歩行、実釣り、屋内隠れ戦闘、最初の草むら、trainer/戦闘UI/HP/Factory/Raidを最終ROMで回帰した。
  - 検証済み前段を再利用する高速chainでv1.3.7を生成し、Downloadsへ別名のverified ROMを配置した。
- Verify: T17 build/check exact-ROM x2、最終stage 25レーダー実menu x2、QOL統合check、`final-fast`、focused 28 tests、py_compile、task graph/private guard/diff check PASS。final SHA-256 `cb8ac173bf8f9e0e4bc51ecd12adc581c6344761955f38766ce7211e2dd5f167`。

## 2026-08-15T22:35:58+09:00

- Version: `v1.3.8`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-SPECIES-DISPLAY` / 追加Species表示とタマゴID衝突を修正する
- Summary:
  - DPE追加1209行の画像／palette resource tag、stock Species 412上限、全表示table consumerをcanonical 1621行へ修正した。
  - タマゴを運用ID 412へ戻し、衝突したキャタピーだけを649へ交換した。ポッポ、グルトンを含む同種の表示破損を一括で解消した。
  - stock画像／図鑑関数の副作用を保持し、Facility、Raid、初戦、戦闘UI、技管理、全QOLを維持した。
  - 32 MiB最終ROM、ROMなしBPS、9-member ZIPを生成した。
- Verify: T09 exact-ROM Species／battle policy、fast T09→final、focused 35 tests、manifest/private guard、BPS往復・release archive検査 PASS。final SHA-256 `51b154c056f5bd83cdff6d9afbe124204d88ab65137d85271480ffce4448a1f2`。

## 2026-08-15T23:01:43+09:00

- Version: `-`（タスク登録のみ。ROM byte変更なし）
- Commit: `-`（本エントリを含むコミット）
- Task: `META-20260815-SPECIES-NAME-LENGTH-QUEUE` / 6文字Species名修正タスクを登録する
- Summary:
  - 旧5文字互換表による6文字名134行の末尾欠落を既知不具合として記録した。
  - 全40 consumerの境界監査、全UI移行、exact-ROM表示回帰を未着手タスクの受入条件にした。
  - 製品ROM、patch、生成stageは変更していない。
- Verify: task graph、task queue unit test、private guard、diff check PASS。

## 2026-08-16T00:47:00+09:00

- Version: `v1.3.9`
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260815-SPECIES-NAME-LENGTH` / 6文字のSpecies名を全UIで欠けずに表示する
- Summary:
  - canonical 1,621行の6文字名134行を8 byte互換ABIへ完全移行し、5文字以下1,487行をbyte不変にした。
  - stock直接参照40件、stride/bound 48件、戦闘nickname転送4件、表示clamp callerをfail-closed監査した。
  - エースバーン／ムゲンダイナの実戦メッセージとhealthbox OBJ tile、Lv.100フォーム、全下流QOLを再検証した。
  - final ROM `0f7406c70021adf9778f0e7a9220f4e014feaac73d7e988ba39700a63be97fcd`、BPS／9-member ZIPを生成した。
- Verify: T09 exact-ROM、fast stage 09→final、focused 39 tests、BPS完全往復、release archive、task graph/private guard/diff check PASS。

## 2026-08-16T03:10:47+09:00

- Version: `v1.4.0`
- Commit: `9c3671d617ad5c17b1a09acf317d2ac68d4a9704`（機能実装。完了記録は本エントリを含むコミット）
- Task: `USER-20260816-ACQUISITION-EVENTS` / 全コレクション対象の入手方法と取得イベントを実ROMへ統合する
- Summary:
  - 1,206種と10有効化フォームを既存経路または201取得イベントで全到達可能にし、24 host objectを19 mapへ復元・結合した。
  - 7取得方式の共通transaction、捕獲後確定、孵化時登録、party/PC満杯、rollback、reset復旧を実装した。
  - 既存2 KiB台帳へ240 byte取得blockを配置し、標準saveとsector 31の双方を跨ぐ永続化・移行を実ROMで確認した。
  - 通信進化30経路と野生内部ID2件を修正し、stage 26、v1.4.0 BPS、ROMなし9-member ZIPを生成した。
- Verify: package生成／negative／2,035 exact case、stage 26 build/check、libmGBA 2 process、focused 5 save tests、BPS完全往復、archive安全監査、task graph/private guard/diff check PASS。

## 2026-08-16T03:16:35+09:00

- Version: `v1.4.0`（最終release identity）
- Commit: `9c3671d617ad5c17b1a09acf317d2ac68d4a9704`（tag `v1.4.0`）／`6d4b558`（完了状態）
- Task: `USER-20260816-ACQUISITION-EVENTS` / release source固定
- Summary:
  - release sourceを機能実装コミットへtagで固定し、完了ログ追加後もfinal/BPS/ZIP検証を再現可能にした。
  - ROMとBPSは不変。tag検証済みmetadataを含む最終9-member ZIP SHA-256を`ca20130634c519fc08049464a21faa88e71f9708b3642af74b3cf8b55f739a1e`へ確定した。
- Verify: release final-fast / patch / verify、BPS完全往復、archive禁止物0、verify副作用なし PASS。

## 2026-08-17T23:22:41+09:00

- Version: `post-v1.4.0-stage27`（v1.4.0 release identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260817-BP-SHOP-RUNTIME` / クチバFactoryのBPショップを実ROMへ物理接続する
- Summary:
  - Factory Trial共通BPで購入する18品目のmanifest-backedショップを、map `96/5`の物理NPCと5件ページmenuへ接続した。
  - 解禁、残高不足、bag満杯、通常save＋sector 31確定、保存失敗時のitem／BP補償rollbackを実装した。
  - v1.4.0を固定入力とするstage 27と4,120 byteの差分BPSを生成し、正式tag／配布ROMを変更せずpost-release成果として分離した。
- Verify: `make bp-shop-runtime` / `make bp-shop-runtime-check`、libmGBA独立2 process、BPS完全往復、allocator／RAM overlap、manifest／task graph／private guard／focused unit test／diff check PASS。stage SHA-256 `c1266a414fcb80b5d3754adec1158effd0326aa8d8d75a8365a0fa0363b5e0b1`。

## 2026-08-18T00:54:20+09:00

- Version: `post-v1.4.0-stage28`（v1.4.0 release identityとstage 27は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260818-FACTORY-REWARD-RUNTIME` / Factory Trialの初回・連勝報酬を実ROMへ接続する
- Summary:
  - 既存Trial完了処理を先に呼ぶwrapperで、初回XS×5、S×2、追加3 BPと連勝3/7/14/21の4 encounter creditを接続した。
  - 基本9 BP、連勝更新、party復元、sector 31保存を保持し、claim bitによる一度限り付与、bag満杯繰越、保存失敗時補償を実装した。
  - stage 27を固定入力とするstage 28とincremental/cumulative BPSを生成し、正式tag／配布ROMを変更せずpost-release成果として分離した。
- Verify: `make factory-reward-runtime` / `make factory-reward-runtime-check`、libmGBA独立2 process、通常save／sector 31再読込、exact party復元、BPS完全往復、allocator／RAM overlap、declared span監査 PASS。stage SHA-256 `268b1f8e309f4e877c2aa77256abb81056a03e99044659d5956ede0fe271989a`。fresh全体監査は未実施。

## 2026-08-18T04:29:26+09:00

- Version: `post-v1.4.0-stage29`（v1.4.0 release identityとstage 27・28は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME` / Factory Trialの反復BP＋道具抽選を実ROMへ接続する
- Summary:
  - stage 28完了処理を先に呼ぶwrapperで、ACTIVE反復報酬2行をオレンのみ×1＋1 BP／ハイパーボール×1＋2 BPのstock RNG抽選へ接続した。
  - 初回claim完了済みの成功完走だけを対象にし、初回報酬、連勝credit、基本9 BP、party復元を維持した。bag満杯と保存失敗では反復item／追加BPだけを補償する。
  - stage 28を固定入力とするstage 29とincremental/cumulative BPSを生成し、正式tag／配布ROMを変更せずpost-release成果として分離した。
- Verify: `make factory-repeat-reward-runtime` / `make factory-repeat-reward-runtime-check`、libmGBA独立2 process、両RNG分岐、連勝共存、bag満杯、通常save／sector 31再読込、exact party復元、BPS完全往復、allocator／RAM overlap、declared span監査、focused 20 tests、manifest/task graph/private guard PASS。stage SHA-256 `00548aa770dc377eefe671b1825af9a78852374322471eb5e9b1cfb174a644a6`。fresh全体監査は未実施。

## 2026-08-18T06:51:55+09:00

- Version: `post-v1.4.0-stage30`（v1.4.0 release identityとstage 27〜29は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME` / Factory Trialの49連勝特殊イベントキーを実ROMへ接続する
- Summary:
  - stage 29完了処理を先に呼ぶwrapperで、ACTIVE 49連勝`SPECIAL_EVENT`をFactory Master解禁後のclaim bit 8へ一度だけ接続した。
  - Master未解禁、streak 48以下、既claimではStage 30の追加transactionを作らず、Stage 29の反復item/BP、基本9 BP、party復元を維持する。
  - stage 29を固定入力とするstage 30とincremental/cumulative BPSを生成し、100連勝色違い記念枠はstage 31候補として残した。
- Verify: `make factory-special-event-runtime` / `make factory-special-event-runtime-check`、libmGBA独立2 process、Master gate、threshold、catch-up、once、sector 31、exact party、BPS完全往復、allocator／RAM overlap、declared span監査、focused 24 tests、task graph/private guard/diff check PASS。stage SHA-256 `e605841d83c6f8e9acd7dbd58b5b4f3d7b262d0274c4c5b4369f0728dc25bf38`。fresh全体監査は未実施。

## 2026-08-18T08:24:32+09:00

- Version: `post-v1.4.0-stage31`（v1.4.0 release identityとstage 27〜30は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME` / Factory Trialの100連勝色違い記念枠を実ROMへ接続する
- Summary:
  - stage 30完了処理を先に呼ぶwrapperで、ACTIVE 100連勝`SHINY_MEMORIAL`をFactory Master解禁後のclaim bit 9へ一度だけ接続した。
  - special event catalogを除外した137種からLv.50のplayer OT色違いをparty／PCへ配布し、generated National／取得台帳bit表で図鑑・collectionを登録する。
  - PREPARED/STAGED journal、通常save＋sector 31、個体marker scanにより、容量不足、保存失敗、journal喪失でclaimを消費せず、二重配布を防いで再試行／commit復旧する。
  - stage 30を固定入力とするstage 31とincremental/cumulative BPSを生成し、正式tag／配布ROMを変更せずpost-release成果として分離した。
- Verify: Stage 31 build/check、libmGBA独立2 process、Master／100 gate、party／PC、強制色違い、National図鑑／取得台帳、once、満杯再試行、PREPARED／STAGED、通常save／sector 31失敗復旧、通常取得trampoline、Stage 30共存、BPS完全往復、allocator／RAM overlap、declared span監査、focused 9 tests、task graph/private guard/diff check PASS。stage SHA-256 `3a962877175d837ddb18d446182e6a63f5b72247567b93b0cc8982c74f1c8703`。fresh全体監査は未実施。

## 2026-08-18T15:06:38+09:00

- Version: `post-v1.4.0-stage32`（v1.4.0 release identityとstage 27〜31は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION` / Trainer V5先行25戦を実ROMへ安全に接続する
- Summary:
  - V5先行25戦を個別のStage 31物理bindingへ接続し、25 party／71 member、1,367行Trainer table、live sidecarを生成した。
  - グローバルflag APIとprivate party ABIをhookせず、trainer専用flag入口、公開party入口、exact kind-4再束縛だけを使用した。
  - 初回DOUBLE scriptの物理ID 702を維持し、実戦時だけID 1342へ解決して4体party／4 controllerまで検証した。
  - stage 32 ROMとincremental/cumulative BPSを決定的に生成した。
- Verify: `make trainer-v5-foundation` / `make trainer-v5-foundation-check`、libmGBA独立2 process 10 check、BPS完全往復、allocator／禁止領域／declared span、task graph／private guard／diff check PASS。stage SHA-256 `bd426a1fc48d09ee2bdaede9c7d56df3f1a125646852b6b54302589cdb758694`。

## 2026-08-19T05:07:39+09:00

- Version: `post-v1.4.0-stage33`（v1.4.0 release identityとstage 27〜32は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-TRAINER-V5-STAGE32-TOHOKU-BATCH02` / Trainer V5のTohoku次14物理命令を累積39戦へ接続する
- Summary:
  - Tohoku前章の次14物理trainerbattle命令を追加し、39戦／113 memberへ累積した。
  - exact pointer＋kind＋source IDで重複sourceと非整列kind-3を解決し、物理flag ownerと既存saveを保持した。
  - stage 33 ROMとincremental/cumulative BPSを決定的に生成した。
- Verify: `make trainer-v5-tohoku-batch02` / `make trainer-v5-tohoku-batch02-check`、libmGBA独立2 process 12 check、BPS完全往復、allocator／禁止領域／declared span、task graph／private guard／diff check PASS。stage SHA-256 `7d3ad7f55d76afdad92cb18965d4bba33ccf0c854f4efdc1268974f9829472f0`。

## 2026-08-19T05:45:47+09:00

- Version: `post-v1.4.0-stage34`（v1.4.0 release identityとstage 27〜33は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-TRAINER-V5-STAGE33-TOHOKU-BATCH03` / Gym1直後＋map 3/21次15物理命令を累積54戦へ接続する
- Summary:
  - Gym1直後のmap-script 1命令とmap `3/21`の連続14物理trainerbattle命令を追加し、54戦／171 memberへ累積した。
  - 共有sourceをcommand-data addressで分離するRematchMap V2 23行と、exact rebind／defeat flag 29行を生成した。
  - stage 34 ROMとincremental/cumulative BPSを決定的に生成した。
- Verify: `make trainer-v5-tohoku-batch03` / `make trainer-v5-tohoku-batch03-check`、libmGBA独立2 process 14 check、BPS完全往復、allocator／禁止領域／declared span、task graph／private guard／diff check PASS。stage SHA-256 `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`。

## 2026-08-19T20:08:50+09:00

- Version: `post-v1.4.0-stage35`（v1.4.0 release identityとstage 27〜34は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION` / Trainer ChangeKit 01〜06最終統合
- Summary:
  - 全1,302戦／6,490 memberを1,030 canonical／71 Archive／201 Kantoの一意物理consumerへ接続し、party・会話・報酬・再戦・saveをStage35へserializeした。
  - 1,228 SINGLE／74 DOUBLE、Mega 86／Zワザ111／ダイマックス4／テラスタル67をAIと全cleanup境界へ実ROM接続した。
  - 入力矛盾を非破壊正規化し、clean ROM直接BPS、自己完結完全版snapshot、fresh展開検証まで完了した。
- Verify: `make trainer-changekit-package-check`、mGBA quick/full、clean exact BPS chain、fresh snapshot `VERIFY_SNAPSHOT.py`、task graph/private guard/diff check PASS。Stage35 SHA-256 `2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180`。

## 2026-08-19T21:24:06+09:00

- Version: `post-v1.4.0-stage35-event-authoring-packet`（Stage35 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260819-CHATGPT-PRO-EVENT-AUTHORING-PACKET` / ChatGPT Pro向け実装可能イベント設計パケットを作成する
- Summary:
  - ChatGPT Pro用prompt、技術・出力契約、JSON Schema、self-contained validator、submission templateを追加した。
  - Stage35から253 map／47 logical location／201 Kanto trainer／24 acquisition host／35 QOL featureと安全なphysical host catalogを決定論的に生成するbuilderを追加した。
  - ROM・save・private inputを含まないZIP、companion prompt、checksumをWindows Downloadsへ出力し、再展開・manifest再hash・validator・再pack byte一致を確認した。
- Verify: focused unit 2 tests、builder、template validator、ZIP CRC／manifest 32件／再pack determinism、task graph／private guard／diff check PASS。ZIP SHA-256 `6426c11fa12f0b8f0b448fa4a1d8c0dee7233d71843a2d48867778ec2a3dc08d`。

## 2026-08-20T04:03:41+09:00

- Version: `post-v1.4.0-stage35-qol-task-queue`（Stage 35 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260820-QOL-TASK-QUEUE` / QOL production完成タスクをREADYへ追加する
- Summary:
  - T19をDAGのT18後へ追加し、別Codexセッションで選択可能な唯一のPRIMARYにした。
  - QOL 35機能のproduction binding、実UI／save／runtime接続、Stage 36 clean rebuildを受入条件として固定した。
  - ChatGPT Proのイベント設計との所有境界を固定し、イベント成果を待たずにQOL本体を実装できるようにした。
- Verify: taskctl sync/next/plan、task graph、private guard、diff check PASS。T19=`PENDING`／依存READY。

## 2026-08-20T16:00:46+09:00

- Version: `post-v1.4.0-stage36`（v1.4.0 release identityとStage 27〜35は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `T19` / Complete production QOL integration
- Summary:
  - QOL 35機能を35個の一意なLIVE production ownerと通常のOptions/summary/PSS/bag/field/daycare/battle/save入口へ接続した。
  - 実BoxPokemonのPC操作、共通数量UI、タマゴqueue、通常random野生の自動戦闘、文章/移動、育成、供給、保存transactionを97 hookでStage 36へ結合した。
  - Stage 35の1,302 trainerとgimmick/saveを不変に保ち、clean ROM直接BPSとStage35差分BPSの両方からbyte一致するStage 36を再構築した。
- Verify: production build/check、focused 20+9 tests、libmGBA quick/full独立2 process、受入条15/15、clean rebuild build/check、BPS完全往復、declared span/allocator/RAM overlap、task graph/private guard/diff check PASS。Stage 36 SHA-256 `c262fbb121957950f890c7b28ab64b19f9bc8fdf541b543747c39ab1f7c381dd`。

## 2026-08-20T16:20:42+09:00

- Version: `post-v1.4.0-stage36-event-design-task-queue`（Stage 36 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260820-EVENT-DESIGN-TASK-QUEUE` / 実装可能イベント設計の実ROM統合タスクを追加する
- Summary:
  - 76 event・7 batch・326会話の返却ZIPをGit管理外の読取専用原本へ取り込み、size/hash/CRC/path安全性とcatalog付きvalidatorをPASSした。
  - T19完了HEADとStage 36を固定し、Stage 35設計の63 physical placementとQOL serviceを現行実ROMで再解決するT20をDAGへ追加した。
  - 全76 eventの実入力、save/transaction、既存trainer/acquisition/QOL回帰、Stage 37、mGBA quick/full、clean rebuildをT20完了gateに固定した。
- Verify: ZIP sha256/cmp/CRC/safety、Stage 35 packet validator、taskctl sync/next/plan、task graph/private guard/diff check PASS。T20=`PENDING`／依存READY。

## 2026-08-20T17:45:24+09:00

- Version: `post-v1.4.0-stage37`（v1.4.0 release identityとStage 27〜36は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `T20` / 実装可能イベント設計76件をStage 36基準で実ROMへ最終統合する
- Summary:
  - 7 batch・76 event・63 physical placement・326会話を通常field入口へ接続し、80 state・160 condition・7 atomic rewardをStage 37へserializeした。
  - Stage 36実ROMから58 mapのrootを再解決し、既存trainer/acquisition/QOL ownerとsaveを保持した。
  - clean直接BPSとStage 36差分BPSの両経路からbyte一致するStage 37を決定的に再構築した。
- Verify: event-design build、focused 10 tests、libmGBA quick/full独立2 process・全76 field path、clean rebuild build/check、BPS完全往復、declared span/allocator/RAM/save重複、manifest/task graph/private guard/diff check PASS。Stage 37 SHA-256 `76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c`。

## 2026-08-20T18:51:50+09:00

- Version: `post-v1.4.0-stage37-chatgpt-pro-design-packets`（Stage 37 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260820-CHATGPT-PRO-DESIGN-PACKETS` / 未完成設計4件の自己完結入力ZIPを作成する
- Summary:
  - 報酬遭遇V2、技習得V4、Factory高難度mode V2、研究経済V1を、それぞれZIPだけでChatGPT Proがimplementation-ready成果へ完成できる入力packetにした。
  - 各packetへ日本語作業指示、固定catalog、出力schema、submission template、自己検証validatorを収録し、ROM／save／patch／private inputを除外した。
  - 4本をWindows Downloadsへ配置し、内容hash、CRC、privacy、path安全性、validator self-test、決定論的repack、コピーbyte一致を確認した。
- Verify: builder、4 ZIP CRC／manifest／SHA256／path／privacy／self-test／repack、Windows copy、未記入template negative test、完全再生成2回のbyte一致、py_compile PASS。ZIP SHA-256はReward `9a87f2f97889466b43c77bb7c510e6353b9d1d92f99bcee0ce10ad62d6d4558d`、Move `15b58d0a74f5f76b273ee72aa3e43c872efa3ba1442c81308c8b897f2343b77f`、Factory `9f579998a91784ccbb559c4107e06925517447bcfc42bd62cd70af670d2efb39`、Research `f0ac86d00932c011b069cc6befe9cc6f7ed698ea76e95ff4d619e3d309879ae7`。

## 2026-08-20T19:12:22+09:00

- Version: `post-v1.4.0-stage37-mirage-task-queue`（Stage 37 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260820-MIRAGE-TASK-QUEUE` / 設計済みMirageのproduction実装タスクを追加する
- Summary:
  - T21をT20後へ追加し、別Codexセッションで選択可能な唯一のPRIMARYにした。
  - 既存Mirage map、持込3体、Lv.100、7戦×4周、round別gimmick、仮想item、独立record/save、badge exact restoreをStage 38の受入条件へ固定した。
  - ChatGPT Pro待ち4領域をT21の読取・変更対象外にし、返却前でも独立実装できる所有境界を固定した。
- Verify: Stage 37 size/hash、Mirage manifest件数、taskctl sync/next/plan、task graph、private guard、ownership diff guard、diff check PASS。T21=`PENDING`／依存READY。

## 2026-08-21T00:47:46+09:00

- Version: `post-v1.4.0-stage38`（v1.4.0 release identityとStage 27〜37は不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `T21` / Connect Mirage modernization to production runtime
- Summary:
  - 既存Mirage受付へ持込3体・Lv.100・7戦×4周・round別gimmick・5段階virtual itemを接続し、16 runtime exportと7 expected-byte rootをStage 38へ配置した。
  - 664-byte volatile stateと既存40-byte台帳内8-byte journalでparty/badge、record/claim、保存失敗、fresh-core resetをFactoryと分離して原子的に復旧する。
  - 既存trainer/QOL/acquisition/T20 eventとPro待ち4領域を不変に保ち、clean chain/direct BPSの両方から同一Stage 38を再構築した。
- Verify: production build/check、focused 14 tests、libmGBA quick/full独立2 process・受入15/15・full 256 badge mask×8 exit、clean rebuild build/check、両BPS完全往復、declared span/allocator/RAM/save overlap、task graph/private guard/diff check PASS。Stage 38 SHA-256 `f66c4823e50d9db86a7c5ef07436558dd4c25c2f41ee3a94e413eadc4a37d941`。

## 2026-08-21T01:56:27+09:00

- Version: `post-v1.4.0-stage38-pro-return-task-queue`（Stage 38 ROM identityは不変）
- Commit: `-`（本エントリを含むコミット）
- Task: `USER-20260821-PRO-RETURN-TASK-QUEUE` / ChatGPT Pro返却4設計の検証・実装タスク化
- Summary:
  - 返却4 ZIPを安全監査・hash固定・読取専用取込し、全4本のvalidatorとopen question 0を確認した。
  - T22 Move、T23 Research、T24 Reward、T25 FactoryをStage 39〜42の直列DAGとして追加し、別セッションが追加設計なしで開始できる実装・検証契約を固定した。
  - Reward tier正常系を誤rejectする共通validatorを修正し、正常系・重複/欠落系の回帰testを追加した。
- Verify: 4 ZIP CRC/path/privacy/hash/cmp、4 validator PASS、focused 2 tests、py_compile、taskctl sync/next/plan、task graph、private guard、diff check PASS。T22=`PENDING`／唯一の依存READY。

## 2026-08-21T02:46:11+09:00

- Version: `post-v1.4.0-stage39`（v1.4.0 release identityとStage 27〜38は不変）
- Commit: `-`（本エントリを含むT22完了コミット）
- Task: `T22` / Integrate Move Distribution V4
- Summary:
  - level-up 28,274、egg 8,219、TM/tutor追加2,799、form 509、wild/source 1,206をcanonical IDへ解決し、production consumerへ接続した。
  - Stage 38のTutor旧20-byte strideをexpected-byte付き1命令adapterで16-byte正本へ統一し、既存TM/tutor許可を除去せず0→1追加だけを反映した。
  - 新規野生生成だけへ初期技を適用し、既存save個体、trainer、Factory、Mirage、Raid、Rewardを不変に保った。clean chain/direct BPSの両経路から同一Stage 39を再構築した。
- Verify: production build、focused 7 tests、libmGBA quick/full独立2 process・全acceptance・warnings/errors 0、clean rebuild build、task固有check 2件、BPS完全往復、declared span/allocator/ROM/RAM/save/hook overlap PASS。Stage 39 SHA-256 `c6d9d118e329512235e27efd876108d630b827bd8f2a8eb5b2bce63748e3f6dd`。

## 2026-08-21T10:39:31+09:00

- Version: `post-v1.4.0-stage40`（v1.4.0 release identityとStage 27〜39は不変）
- Commit: `-`（本エントリを含むT23完了コミット）
- Task: `T23` / Integrate Research Economy V1
- Summary:
  - 独立研究ポイント、active play 60分の研究日、6活動、7 rank、23品交換所を64-byte versioned ownerへ実装した。
  - 9 host・35会話を通常field入力へ接続し、釣り・生態・Game Cornerを既存production wrapperへchainした。
  - modern save v1→v2 migration、保存失敗rollback、取得runtime v2互換を加え、clean chain/direct BPSの両方から同一Stage 40を再構築した。
- Verify: production build/check、focused 16+19 tests、libmGBA quick/full独立2 process・受入10/10・warnings/errors 0、clean rebuild build/check、両BPS完全往復、21 physical patch、declared span/allocator/ROM/RAM/save/map/hook overlap PASS。Stage 40 SHA-256 `b46e28935675198db09f5947e6701918deafb49db27c03343f4b5b2ddaceb488`。

## 2026-08-21T12:03:13+09:00

- Version: `post-v1.4.0-stage41`（v1.4.0 release identityとStage 27〜40は不変）
- Commit: `-`（本エントリを含むT24完了コミット）
- Task: `T24` / Integrate Reward Encounters V2
- Summary:
  - 4 tier、24 pool、typed credit/BP、10 source、56会話を共有Scientistと既存Factory/T23 hookへ接続した。
  - 戦闘前pending persist、非捕獲・reset同一個体再戦、通常捕獲時atomic clear、保存失敗rollback、報酬戦副作用maskを既存ledger/save ownerで実装した。
  - clean chain/direct BPSの両方から同一Stage 41を再構築し、宣言span外変更とallocator/ROM/RAM/save/map/hook overlapを0にした。
- Verify: production build/check、focused 9+16+19 tests、libmGBA quick/full独立2 process・受入11/11・warnings/errors 0、32 transaction row、clean rebuild build/check、両BPS完全往復、T23回帰 PASS。Stage 41 SHA-256 `282ab4af1f4f509c2c4ce40bf77b1881a0b69b05b9cb509708f13735a93cc352`。

## 2026-08-21T13:33:03+09:00

- Version: `post-v1.4.0-stage42`（v1.4.0 release identityとStage 27〜41は不変）
- Commit: `-`（本エントリを含むT25完了コミット）
- Task: `T25` / Integrate Factory High Modes V2
- Summary:
  - 既存Trialをslot 0のexact delegateとして保持し、24 mode、28 requirement、248 rental、55 profile、16 reward、28会話を通常Factory受付へ接続した。
  - 有限generator、reset/reload forfeit、round境界retire、packed ABI、BP・49/100・T24 creditのatomic transaction、Mirage分離を実装した。
  - clean chain/direct BPSの両方から同一Stage 42を再構築し、宣言span外変更とallocator/ROM/RAM/save/UI/hook overlapを0にした。
- Verify: production build/check、focused T25 10 tests＋既存81 tests、7,440-row mode matrix、libmGBA quick/full独立2 process・受入11/11・warnings/errors 0、clean rebuild build/check、両BPS完全往復、Stage41回帰 PASS。Stage 42 SHA-256 `2e3c796b1deff84c83b68fde29c2eddf8672b1870f1ebe3e8308969fafde1068`。

## 2026-08-21T14:13:13+09:00

- Version: `tooling-ipad-wifi-ssh-1`（Stage 42 ROM identityは不変）
- Commit: `-`（本エントリを含む完了コミット）
- Task: `USER-20260821-IPAD-WIFI-SSH` / iPad Wi-Fi SSH Toolkitの安全取込・導入・実接続確認
- Summary:
  - ユーザー提供toolkitを全entry・同梱hashで検証し、秘密鍵を含む原本をGit管理外の読取専用private importへ保管した。
  - WSL/Codex用runtimeとmode 600のcredentialをユーザー領域へ導入し、固定host key・固定接続先を維持した。
  - iPadへのWi-Fi SSH doctorとremote command実行に成功し、このworkspaceから`ipad-wifi-ssh`を利用可能にした。
- Verify: ZIP CRC/SHA-256、同梱10 hash、private import権限、runtime/credential権限、固定鍵fingerprint、実SSH接続、通常PATH、remote `run` PASS。

## 2026-08-21T14:35:17+09:00

- Version: `post-v1.4.0-stage42-codex-battle-task-queue`（Stage 42 ROM identityは不変）
- Commit: `-`（本エントリを含む完了コミット）
- Task: `USER-20260821-CODEX-BATTLE-TASK-QUEUE` / Codex対戦をT26〜T28へ設計固定・タスク追加
- Summary:
  - 実iPadのRetroArch NCI/mGBA開始状態を読取専用監査し、外部controller＋versioned EWRAM mailbox方式を実装正本へ固定した。
  - T26 Stage 43の実機bridge、T27 Stage 44の双方6→3対戦、T28 Stage 45の任意報酬・Codex skill・iPad E2Eを直列DAGへ追加した。
  - Lv.50統一／自由、同一持ち物許可／禁止、会話で決めるteam/regulation/reward、ROM側safe transactionを受入条件へ固定した。
- Verify: iPad SSH read-only inventory、Stage 42 identity、taskctl sync/next/plan、focused 20 tests、task graph、JSON、private pattern、diff check PASS。T26が唯一のPRIMARY。

## 2026-08-21T16:18:30+09:00

- Version: `post-v1.4.0-stage43`（v1.4.0 release identityとStage 27〜42は不変）
- Commit: `-`（本エントリを含むT26完了コミット）
- Task: `T26` / Codex対戦ブリッジをStage 43で実証する
- Summary:
  - 512-byte EWRAM予約へ256-byte protocol 1.0 mailboxを実装し、旧ReadKeys delegateを保つmain-loop wrapperから初期化・poll・PING/PONGを接続した。
  - owner-only設定と安定JSON/exit codeを持つ安全な`vega-codex-battle` CLIを追加し、任意memory操作を公開せず宣言済み64-byte request spanだけを書けるようにした。
  - 実iPad RetroArch 1.22.2 / mGBAでStage 43を起動し、NCI `VERSION` / `GET_STATUS` / EWRAM read / mailbox write / sequence 1 PING/PONGを実証した。端末固有IP、credential、container pathは証跡から除外した。
  - clean chain/direct BPSの両方から同一Stage 43を再構築し、宣言span外変更とROM/RAM/save/hook overlapを0にした。
- Verify: production build/check、focused 10 tests、libmGBA quick/full独立2 process・受入11/11・invalid 10・保護span 7・warnings/errors 0、実iPad NCI read/write/PING/PONG、clean rebuild build/check、両BPS完全往復、task graph/private guard/diff check PASS。Stage 43 SHA-256 `4834d42bc28d044e99b2686263808718441f4abe2347353a9eca1592224d8a9c`、CRC32 `40CE01CE`。

## 2026-08-21T16:29:10+09:00

- Version: `post-v1.4.0-stage43-t27-prep`（Stage 43 ROM identityは不変）
- Commit: `-`（本エントリを含む準備完了コミット）
- Task: `USER-20260821-CODEX-BATTLE-T27-PREP` / T27 implementation-ready仕様更新
- Summary:
  - T26完了commitとStage 43 ROM／metadata／protocol hashをT27の固定入力へ記録した。
  - read-only構築catalog、公平なpending action非公開、Codex対戦限定`UPSTREAM_OPEN` gimmickをT27の固定仕様・CLI・受入条件へ追加した。
  - CLI/skillを能力提供と操作説明だけに限定し、戦略、選出、行動、報酬、理由説明のpolicyを呼出元Codex taskへ残した。
- Verify: Stage 43 identity、task graph/queue/task仕様/互換ミラー、taskctl next/plan、focused 20 tests、private guard、diff check PASS。T27が唯一のPRIMARY。

## 2026-08-21T16:34:36+09:00

- Version: `post-v1.4.0-stage43-t28-reward-ball-spec`（Stage 43 ROM identityは不変）
- Commit: `-`（本エントリを含む仕様追記コミット）
- Task: `USER-20260821-CODEX-BATTLE-REWARD-BALL` / T28 Pokémon報酬の捕獲ボール指定
- Summary:
  - `reward mon`のoptional fieldに`--ball BALL_ITEM_ID`を追加した。
  - 選択ボールを付与個体の捕獲ボール情報へ保存し、invalid/non-ball IDを無変更で拒否する受入条件を固定した。
- Verify: SKIP（ユーザー指示により再検証なし）。

## 2026-08-22T16:05:07+09:00

- Version: `post-v1.4.0-stage44`（v1.4.0 release identityとStage 27〜43は不変）
- Commit: `-`（本エントリを含むT27完了コミット）
- Task: `T27` / Codex操作6→3対戦をStage 44へproduction統合する
- Summary:
  - 双方6→3、Codexの全選出・技・交代・gimmick判断、pending player action非公開、`FLAT_50|OPEN`、`UPSTREAM_OPEN`を通常施設入口へ統合した。
  - own 3体のHP実数とactive live技/PP、player公開HP割合、状態・能力ランク・場・gimmick・公開event、opaque個体追跡、forced/voluntary switchをオンライン対戦相当のcompact stateとして実装した。
  - 全exitのparty/save exact restore、EXP等の副作用抑止、結果msgbox完了まで次matchを隔離するfield completion gateを実装し、実iPadで8 cycle以上の対戦と安全終了・マップ復帰を実証した。
  - clean chain/direct BPSの両方から同一Stage 44を再構築し、宣言span外変更とROM/RAM/save/UI/hook overlapを0にした。
- Verify: production build/check、focused 9 tests、libmGBA quick/full各18/18・warnings 0、実iPad必須12 test・pending privacy・Dynamax・通常/強制交代・EXPなし・exact cleanup、clean rebuild build/check、CLI installer/doctor、task graph/private guard/diff check PASS。Stage 44 SHA-256 `96820c78d6e43ef82951c23121618aac55f54579d4f196c27d6a24185ed7a256`、CRC32 `04CB658E`。

## 2026-08-23T07:43:08+09:00

- Version: `post-v1.4.0-stage45`（v1.4.0 release identityとStage 27〜44は不変）
- Commit: `-`（本エントリを含むT28完了コミット）
- Task: `T28` / 任意報酬とiPad最終ゲートをStage 45で完成させる
- Summary:
  - 正常resultに束縛した任意item/Pokémon報酬を、通常engine API、exactly-once journal、不可逆close、save migration付きでStage 45へ接続した。
  - Codex戦の賞金・全滅ワープを抑止し、party/money exact復元、PC Storage cache再水和、box/summary UIのlevel・技・特性・性格・ボール表示を修正した。
  - reward CLI、会話運用用companion skill、日本語operator guideを追加し、戦略・選出・報酬内容の判断は呼出元Codex taskへ残した。
  - 実iPadで6→3対戦、交代、双方Dynamax、通常敗北、指定カイリュー1回付与、通常save/restart/load、close再送無書込、最終PC残存まで完走した。
- Verify: production build、61 transaction、focused 17 tests、libmGBA quick/full各16/16・warnings 0、実iPad doctor/5 turn/reward/UI/save/restart/owner CRC、clean rebuild build/check、3 BPS完全往復、declared span外0、ROM/RAM/save/UI/hook overlap 0 PASS。Stage 45 SHA-256 `2eedbe64a50664d9077af19920bcffb2cf1953d0a0c2b5e3c419c2b2410b1eb7`、CRC32 `8FFD6131`。

## 2026-08-23T08:43:54+09:00

- Version: `post-v1.4.0-stage46`（v1.4.0 release identityとStage 27〜45は不変）
- Commit: `-`（本エントリを含むT29完了コミット）
- Task: `T29` / Windows対戦カタログをNPC前の一括生成導線へ接続する
- Summary:
  - NPC前の通常field・T27 `IDLE`・reward window `CLOSED`だけでcanonical item/Pokémon templateを通常bag／party／PCへ生成するcatalog command 15/16をStage 46へ追加した。
  - CLI 2.4へ`bank status/item/mon/batch`、1件単位commit、停止位置と再開index、owner-only exact retryを追加し、特定ROM filenameではなくprotocol contractから現行・将来Stageを発見する運用へした。
  - PCは14箱×30枠と既存save ABIのまま、回収はT19の複数box選択・一括逃がしを再利用した。Stage45既定runtimeとmatch-bound reward契約はbyte／実行回帰とも不変。
- Verify: Stage 46 build/check、libmGBA quick/full各8/8、focused 24 tests、1／6／30件batch、Stage45 byte identity、Stage47相当protocol互換、両BPS往復、declared span外0、ROM/RAM/save/hook overlap 0、task graph/private guard/diff check PASS。Stage 46 SHA-256 `7941e7b59772b60829aa80a67eea26b982b397851a9e8e02d0e26be17459f44c`、CRC32 `3D8B62B1`。

## 2026-08-23T16:35:51+09:00

- Version: `post-v1.4.0-stage46-ipad-copy`（Stage 46 ROM identityは不変）
- Commit: `-`（本エントリを含む転送証跡コミット）
- Task: `USER-20260823-STAGE46-IPAD-TRANSFER` / Stage 46対戦ROMをiPadへ別名配置する
- Summary:
  - Stage 46 ROMを既存Stage 45と同じiPadディレクトリへversioned filenameで新規配置した。
  - 既存ROM/save/savestateを変更せず、contentの起動とRetroArch操作は行っていない。
- Verify: 固定host key付きWi-Fi SSH、転送元identity、iPad側33,554,432 bytes、SHA-256 `7941e7b59772b60829aa80a67eea26b982b397851a9e8e02d0e26be17459f44c`一致 PASS。

## 2026-08-23T16:41:09+09:00

- Version: `post-v1.4.0-stage46-ipad-save-copy`（ROM identityは不変）
- Commit: `-`（本エントリを含むセーブ配置証跡コミット）
- Task: `USER-20260823-STAGE46-SAVE-COPY` / Stage 45セーブをStage 46用へ複製する
- Summary:
  - Stage 45の128 KiBセーブをbyte不変のままStage 46用filenameへ複製した。
  - 既存Stage 46セーブは同じsaveディレクトリへ退避し、元Stage 45セーブ、ROM、savestateは変更していない。
- Verify: 元／適用後セーブの131,072 bytesとSHA-256 `1289b8c3d4caf135c778f98523d6937c86d0ec9609c0043e348fcdc3298af2e2`一致、退避セーブSHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`一致 PASS。

## 2026-08-23T17:16:17+09:00

- Version: `post-v1.4.0-stage46-cli-2.4.1-live-batch`（Stage 46 ROM identity／save ABIは不変）
- Commit: `-`（本エントリを含む実機batch／CLI修正コミット）
- Task: `USER-20260823-STAGE46-LIVE-CATALOG-BATCH` / 実iPad対戦用30体・道具一括生成
- Summary:
  - 実iPadのStage 46へ指定12体＋Mega候補18体を全員Lv.50で通常PCへ、対戦用道具21種を通常bagへexactly onceで生成した。
  - CLI 2.4.1で物理境界拒否後の同一sequence再評価、旧応答識別、request staging前の旧commit marker無効化を追加した。
  - sequence 1〜51、response ACCEPTED、pending 0、journal COMMITTEDを公開ownerで確認し、ROM/save ABIは変更していない。
- Verify: 実iPad 51/51 commit PASS。`python3 -m unittest -v tests.test_windows_battle_catalog` 10 tests、`python3 -m py_compile tools/vega_codex_battle.py`、installer、`bank status`、task graph、private guard、`git diff --check` PASS。

## 2026-08-23T18:28:05+09:00

- Version: `post-v1.4.0-stage47`（v1.4.0 release identityとStage 27〜46は不変）
- Commit: `-`（本エントリを含むT30完了コミット）
- Task: `T30` / Box 14とWindows固有個体庫を双方向exact移動へ接続する
- Summary:
  - Box 14のCFRU展開済み80-byte `BoxPokemon`原本をowner-only Windows blobへdepositし、ABI互換ROMからwithdrawできるStage 47とCLI 2.5.1を追加した。
  - Windows先行永続化、slot単位通常save、pending再開、GBA確定後だけの在庫減算により、持ち物を含む個体原本を再生成せず移動する。
  - 預け入れ・引き出し・Windows catalog生成のNPC／map位置条件を廃止し、任意mapの通常fieldへ広げた。実iPadのBox 14から6体をWindowsへ移し、Box 14空・在庫6・pendingなしで終了した。
- Verify: Stage 47 build/check、libmGBA quick 7/7・warnings 0、focused 17 tests、0／1／6／30体exact往復、応答喪失再開、容量／ABI／破損拒否、実iPad doctor 13項目・6体deposit、blob SHA-256／mode、BPS往復、declared span外0、ROM/RAM/save/hook overlap 0、task graph/private guard/diff check PASS。Stage 47 SHA-256 `fccc882e7b11315a36b146715396d63348b726268e7560a99a55f4ccbad3d3c9`、CRC32 `51C5114B`。

## 2026-08-23T18:36:21+09:00

- Version: `post-v1.4.0-stage47-live-withdraw-6`（Stage 47 ROM identity／save ABIは不変）
- Commit: `-`（本エントリを含む実機withdraw証跡コミット）
- Task: `USER-20260823-STAGE47-VAULT-WITHDRAW-6` / Windows個体庫の6体をBox 14へ引き出す
- Summary:
  - Windows owner-only個体庫の互換6体を、持ち物を含む80-byte原本のまま実iPadのBox 14へ戻した。
  - 各個体の通常save確定後だけWindows在庫を減算し、Box 14 slot 0〜5の6体、Windows在庫0、pendingなしで終了した。
- Verify: 実iPad doctor 13項目、`vault withdraw` COMPLETE／moved 6、終了後`vault status` Box 14 occupied 6／Windows record 0／pendingなし PASS。

## 2026-08-24T01:46:34+09:00

- Version: `post-v1.4.0-stage48`
- Commit: `-`（本エントリを含むタスク完了コミット）
- Task: `USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT` / Species依存フォームとプレイヤー側背面戦闘画像を正規化する
- Summary:
  - Species/Form 1,621行とAbility 312行をmanifest生成aliasへ統一し、固定CFRU-JPのC/ASM 84ファイル・12,665参照を未変換0でfail-closed監査した。直接数値候補17件も全件review済み、unreviewed 0とした。
  - Hunger Switch、Disguise、Battle Bond、Schooling、Zen Mode、Ice Face、Power Constructと既存特性を実ROMで検証し、form後のbattle/party/type/stats/ability/表示と終了復元を固定した。
  - 追加Speciesのplayer backを64×64 OAM／2,048-byte OBJ tileとして検査し、Stage06〜47を再生成した。Stage48と旧Stage47差分／clean直接BPS、再生成可能reportを追加した。
- Verify: canonical Stage06/07/09 check、focused 87 tests、Stage36/42/46/47 check、Stage48 build/check、mGBA 2 process、BPS完全往復、task graph/private guard/diff check PASS。Stage48 SHA-256 `b8244d5d6fcde027aa33bc432b5d3eb11951d71f43ba2bebf2c1d29a50dd7243`、CRC32 `CA37AC3D`。

## 2026-08-24T06:51:41+09:00

- Version: `post-v1.4.0-stage48-ipad-copy`（Stage48 ROM identityは不変）
- Commit: `-`（本エントリを含む実機ROM転送証跡コミット）
- Task: `USER-20260824-STAGE48-IPAD-ROM-TRANSFER` / Stage 48修正版ROMだけをiPadへ配置する
- Summary:
  - Stage48 ROMをiPadの既存RetroArch ROMディレクトリへversioned filenameで新規配置した。
  - 既存ROM、save、savestateを変更せず、content起動やRetroArch操作も行っていない。
- Verify: fixed host key付きWi-Fi SSH、同名不在、iPad側33,554,432 bytes、SHA-256 `b8244d5d6fcde027aa33bc432b5d3eb11951d71f43ba2bebf2c1d29a50dd7243`一致、private guard、diff check PASS。

## 2026-08-24T08:20:39+09:00

- Version: `post-v1.4.0-stage49`
- Commit: `-`（本エントリを含むタスク完了コミット）
- Task: `USER-20260824-STAGE48-WORLD-ITEM-RECOVERY` / Stage 48のworld・item境界を総合復旧する
- Summary:
  - T17 serializerで失われたカントー一般NPC、回復／店service、看板／ごみ箱を安全scriptへ復旧し、全678 mapとtrainer 1,302戦／6,490 memberを再監査した。
  - T501〜T523の物理wild束縛をStage09 map-sectionへ固定し、95-row／294 candidate表を現行ROMへ反映した。低レベルRaid 6件を既存Raid ownerへ追加した。
  - stock Mystery2 accessorの旧item-count clampを0..998対応へ修正し、Focus Sashの満タン判定と正式消費を実ROMで回復した。
- Verify: Stage49 build/check、libmGBA 2 process、focused 34 tests、全678 map graph、1,302 trainer／6,490 member、BPS完全往復、allocator overlap 0、declared span外0、task graph/private guard/diff check PASS。Stage49 SHA-256 `780504cda0884bf53ed88f30fce18cbb54985740162210cb4724df0c6570ef5a`。

## 2026-08-24T08:41:45+09:00

- Version: `post-v1.4.0-stage49-ipad-npc-save`（Stage49 ROM identity／save ABIは不変）
- Commit: `-`（本エントリを含む実機配置証跡コミット）
- Task: `USER-20260824-STAGE49-IPAD-ROM-SAVE` / Stage49 ROMとCodex対戦NPC前セーブをiPadへ配置する
- Summary:
  - Stage49 exact ROMをiPadへversioned filenameで新規配置した。
  - Stage47 save候補をsector監査し、有効generation 56／Codex受付map `96/5`／座標`20/20`のセーブをStage49同名セーブへbyte同一複製した。
  - NPC前でない初回候補は完成扱いにせずrecoverable backupへ退避し、既存ROM／save／savestateと両Stage47原本を保持した。
- Verify: Wi-Fi SSH固定host key、iPad側ROM／save一意性・size・SHA-256、save 14/14 active section、Stage49自然Continue 2 process、save hash不変、private guard、diff check PASS。ROM `780504cd...`、save `4a83b7d2...`。

## 2026-08-24T10:01:30+09:00

- Version: `post-v1.4.0-stage50-interaction-owner-repair`
- Commit: `-`（本エントリを含むタスク完了コミット）
- Task: `USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIR` / Stage49のinteraction ownerを再構築する
- Summary:
  - NPC、trainer、item、field move、service、sign、hidden itemを別ownerへ再構築し、無効script NPC 86体と誤った一律会話を修正した。未完成low Raid host 6件は撤回した。
  - trainer視線652体を1マス補正し、511番水道land owner、移動時だけの遭遇判定、最低歩数猶予を追加した。
  - Dark Pulse 20%／Inner Focus／行動済み無効、Focus Sash、Species／Ability、Codex受付を回帰し、Stage50 ROMとCodex受付前saveをiPadへ別名配置した。
- Verify: Stage50 build/check、libmGBA exact-ROM 2 process、focused 6 tests、Species/Form Stage48 check、manifest、private guard、diff check、BPS完全往復、iPad ROM/save size・SHA-256一致 PASS。Stage50 SHA-256 `af9bd50194e16fc409a31b6c179ec8c53a15d6961220daf29a0bd38a2b7dc92d`。

## 2026-08-24T10:31:42+09:00

- Version: `post-v1.4.0-stage51-continue-save-freeze-repair`
- Commit: `-`（本エントリを含むタスク完了コミット）
- Task: `USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIR` / Stage50のContinue描画破損・1歩後入力停止を修正する
- Summary:
  - Stage50のARMv5専用Thumb `BLX register`をARM7TDMI互換tail-callへ置換し、1歩後のillegal opcodeと入力停止を修正した。
  - 強制進行saveの破損map viewを切り分け、正常なstock map viewと両slotを持つCodex受付前saveを再発行した。
  - Stage51 ROM／同名saveをiPadへ別名配置し、旧Stage49／50と既存save／savestateを保持した。
- Verify: Stage51 build/check、libmGBA interaction／自然Continue各2 process、3方向2歩以上、warning 0、focused 10 tests、Stage50回帰check、BPS完全往復、iPad ROM/save size・SHA-256一致 PASS。Stage51 SHA-256 `6cda0c65836fa389c27e18bdcd500df4410348bb2176a85c2ab2fa4d41ed96e4`、save `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`。

## 2026-08-24T11:35:14+09:00

- Version: `planning-only-stage51-world-runtime-e2e-repair`（ROM／save identity変更なし）
- Commit: `-`（本エントリを含む計画登録コミット）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR-REGISTRATION` / Stage51 world runtime再修正タスクの登録
- Summary:
  - Stage51のiPad実プレイ不合格を記録し、Stage51をworld interactionの配布候補から外した。
  - trainer、item／field object、非trainer NPC、wild cadenceを既存データから実入力E2Eで再構築するTODOを追加した。
  - 実装、ROM／save生成、iPad配置は行っていない。
- Verify: task graph、private guard、`git diff --check` PASS。

## 2026-08-24T14:13:41+09:00

- Version: `post-v1.4.0-stage52-world-runtime-e2e-repair-candidate`
- Commit: `-`（iPad実プレイ待ちcheckpoint commit）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage51 world runtimeの全map根本修復
- Summary:
  - 全678 mapのtrainer／item／field object／会話／wild ownerを再構築し、症状別global patchを撤去した。
  - trainer root／authored sightとparty人数snapshotの共通順序を修正し、通常item／hidden itemをstock transactionへ戻した。
  - Stage52 ROMと互換saveを旧成果物と別名でiPadへ配置した。ユーザー実プレイ承認までは非release候補／task IN_PROGRESSとする。
- Verify: Stage52 build/check、fresh-core実入力10 fixture×独立2 process・結果一致・warnings 0、全678 map／1,302 trainer／6,490 member監査、BPS完全往復、declared span外0、allocator overlap 0、focused 15 tests、task graph、private guard、diff check、iPad size／SHA-256一致 PASS。ROM `8e407a1547826c61c6fab7306cfb792ca56d4f2bfac8855b485229028be4f096`。

## 2026-08-24T14:46:17+09:00

- Version: `post-v1.4.0-stage52-ipad-save-placement-repair`（ROM identity／save ABI不変）
- Commit: `-`（本エントリを含むsave配置修復コミット）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage52のiPad save配置を修復する
- Summary:
  - RetroArch起動中のin-memory新規saveが正規Stage52 saveを上書きしていたことを、設定・既存save配置・hashから確定した。
  - 誤った新規saveとROM横の無効な同名saveを復旧可能に退避し、RetroArch停止中に正常なStage51互換saveを正規mGBA save先へ復元した。
  - Stage52のROMは変更せず、ユーザー実プレイ承認待ちを継続する。
- Verify: 正規Stage52 save 131,072 bytes／SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`、RetroArch停止、誤配置元不在 PASS。

## 2026-08-25T03:02:11+09:00

- Version: `post-v1.4.0-stage53-world-runtime-root-repair-candidate`
- Commit: `-`（iPad実プレイ待ちcheckpoint commit）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage52実機不合格の共通runtime修正
- Summary:
  - 誤っていたfixtureを実物理mapへ固定し、全13 wild-header consumer、完了歩判定、511番水道terrain、知恵の洞窟6 mapを共通修正した。
  - Codex ReadKeys／報酬復元／通常double入力を通常worldから隔離し、trainer flag・enemy count・停止transitionをstock通常戦の共通経路で修正した。
  - ヒスイ506入口の2 NPCをfinite dialogueへ戻し、Continueのあらすじだけを無効化した。save ABIと通常の「つづきから」は保持する。
  - Stage53はiPad未確認の非release候補であり、taskは`IN_PROGRESS`のまま保持する。
- Verify: Stage53 build、18 fresh-core fixture×独立2 process・完全一致・warnings 0、全678 map／1,302 trainer／6,490 member／265 wild header監査、BPS完全往復、declared span外0、allocator overlap 0、focused trainer/double/wild、unit、task graph、private guard、diff check PASS。ROM `b6ed65b8b7010bf652b55e0314c7202bcfe1bcf8b43c32a2547b1f4961ce6226`。

## 2026-08-25T05:44:15+09:00

- Version: `post-v1.4.0-stage53-ipad-rom-placement`（ROM identity不変）
- Commit: `-`（本エントリを含むiPad配置コミット）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage53修正版GBAのiPad配置
- Summary:
  - Stage53 GBAをiPadのStage52と同じROMフォルダへ別名で新規配置した。
  - 既存Stage52、save、savestateには触れず、転送一時ファイルも残していない。
  - ユーザー実プレイ承認まではtaskを`IN_PROGRESS`のまま保持する。
- Verify: iPad read-back 33,554,432 bytes／SHA-256 `b6ed65b8b7010bf652b55e0314c7202bcfe1bcf8b43c32a2547b1f4961ce6226`、旧Stage52不変、一時ファイル0、save変更0 PASS。

## 2026-08-25T06:28:37+09:00

- Version: `post-v1.4.0-stage53-ipad-save-placement-repair`（ROM identity／save ABI不変）
- Commit: `-`（本エントリを含むsave復元・runbookコミット）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage53のiPad mGBA save配置修復
- Summary:
  - 新規ゲーム側Stage53 saveを復旧可能に退避し、正常Stage52互換saveをStage53と同じbasenameで正規mGBA save directoryへ配置した。
  - ROM横配置を禁止し、`retroarch.cfg`の`savefile_directory`とsort設定から都度解決するrunbookを追加した。
  - ROM、save ABI、正常source save、旧Stage52、savestateは変更していない。
- Verify: Stage53 `.srm` 131,072 bytes／SHA-256 `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`、source不変、一時ファイル0、既存新規ゲームsave退避、実mGBA directory／basename一致 PASS。

## 2026-08-25T08:13:08+09:00

- Version: `chatgpt-pro-collection-supply-v1`（ROM／save identity変更なし）
- Commit: `-`（本エントリを含むタスク完了コミット）
- Task: `USER-20260825-CHATGPT-PRO-COLLECTION-SUPPLY-PACKET` / 全収集・供給設計をChatGPT Proへ渡す再現可能ZIPを作成する
- Summary:
  - 全1,621 Species、388 form、34 G-Max、999 Item、256 Raid、118 NPC候補を監査済みcatalogへ固定した。
  - 全件coverage、G-Max bit、反復供給、既存Raid state保持、post-world-fix物理束縛を検証する返却schema／validatorを追加した。
  - 決定的入力ZIPをWindows Downloadsへ配置し、再生成・Pro利用・Codex実装境界の正本を追加した。
- Verify: generator、完成submission fixture、共有validator回帰2 tests、task graph、private guard、ZIP CRC／決定性／copy hash、diff check PASS。ZIP SHA-256 `b93d0b8cdf758694084e98d7101074ea5c1886b9985fca1bd526c55404a28c27`。

## 2026-08-25T09:10:50+09:00

- Version: `post-v1.4.0-stage54-world-runtime-correct-map-candidate`
- Commit: `-`（iPad実プレイ待ちcheckpoint commit）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / 正しい博士NPCと知恵の洞窟の再修正
- Summary:
  - 博士NPCを`96/5 local 5 (25,7)`へ固定し、Reward Scientistの同期終了だけ無条件waitstateを迂回する。旧`3/2 local 9`から博士表記・専用会話を削除した。
  - 正しい洞窟`1/36`・`1/37`・`1/38`・`1/73`を北口・南口・B2Fの通常warp往復とB1F/B2F wild入力で回帰した。
  - Stage54はiPad未確認の非release候補で、taskは`IN_PROGRESS`のまま。旧Stage53は元の不合格identity `b6ed65...`へ復元・保持した。
- Verify: Stage54 build、20 fresh-core fixture×独立2 process・完全一致・warnings 0、博士同期／非同期復帰、洞窟10 normal warp、B1F Species 16 Lv.9、B2F Species 387 Lv.45、BPS完全往復、declared span外0、allocator overlap 0、unit 9 tests PASS。ROM `b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`。

## 2026-08-25T12:44:02+09:00

- Version: `post-v1.4.0-stage54-ipad-rom-save-placement`（ROM identity／save ABI不変）
- Commit: `-`（本エントリを含むiPad配置・運用規則コミット）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage54 GBAと正常進行saveのiPad配置
- Summary:
  - Stage54 ROMを旧Stage53と別basenameでiPadへ配置した。
  - 正常進行saveをROMと同一basenameの`.srm`として正規mGBA save directoryへ配置した。
  - iPad GBA配置前に正本runbookを必ず参照する規則を`AGENTS.md`へ追加した。
- Verify: iPad read-backでROM 33,554,432 bytes／`b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`、save 131,072 bytes／`406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`一致。RetroArch停止、一時ファイル0、既存Stage53不変 PASS。

## 2026-08-25T13:34:25+09:00

- Version: `post-v1.4.0-stage55-world-runtime-visible-feedback-candidate`
- Commit: `-`（iPad実プレイ待ちcheckpoint commit）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / 博士と一般NPCの可視応答を共通修正する
- Summary:
  - event-design TALK_OBJECTのsource fallbackがruntimeへ反映されない共通generator不良を修正し、15 dispatcherを可視応答可能なsource ownerへ接続した。
  - 博士の同期result 13種を可視メッセージへ接続し、`BUSY=9`の非同期待機だけを保持した。
  - Stage55 ROMと正常進行saveをWi-Fi SSHでiPadへ別basename配置し、旧Stage54を不変に保った。
- Verify: Stage55 build、22 fresh-core fixture×独立2 process・完全一致・warnings 0、全678 map／3,093 object可視応答契約監査、BPS往復、declared span外0、allocator overlap 0、unit 9 tests、iPad ROM／save read-back、旧Stage54不変、一時ファイル0 PASS。ROM `b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`。

## 2026-08-27T13:26:18+09:00

- Version: `post-v1.4.0-stage55-world-runtime-complete`（ROM identity不変）
- Commit: `-`（本エントリを含む完了commit）
- Task: `USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR` / Stage55をローカルgateで完了する
- Summary:
  - Stage55の既存ローカル再現可能証跡を完了gateとしてDONEへ確定した。
  - iPad配置、実機プレイ、人手承認を今後のtask／release／READY必須条件から分離した。
  - Stage56はStage55を完了baselineとして開始し、iPad配置は任意運用に限定する。
- Verify: task graph、private guard、diff check、Stage55既存22 fixture×独立2 process／BPS／span／overlap証跡 PASS。

## 2026-08-27T14:56:40+09:00

- Version: `post-v1.4.0-stage56-collection-supply-v1`
- Commit: `-`（本エントリを含む完了commit）
- Task: `USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION` / 全収集・供給V1をStage 56へproduction統合する
- Summary:
  - 388 form、34 G-Max、999 Item、14物理host、292 Raid pool、217 rewardをcanonical runtimeへcompileした。
  - Item／form／G-Max／Raid／world／sector 31 save／Box 14 raw80を実ROMへ接続し、既存Stage55とStage26〜30の契約を保持した。
  - iPad実機を完了条件から外したまま、決定的Stage56 ROMを確定した。任意のiPad配置は安全終了不可のため既存ファイル無変更で見送った。
- Verify: build、clean 3経路、差分／直接BPS、Collection quick／full各9 test、Stage55自然入力22 fixture×独立2 process、focused unit 17 tests、task graph、private guard、diff check PASS。ROM SHA-256 `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`。

## 2026-08-27T15:59:19+09:00

- Version: `post-v1.4.0-stage56-test-ready-save-v1`（ROM identity不変）
- Commit: `-`（実装checkpoint `6cfef3f`、本エントリを含む完了commit）
- Task: `USER-20260827-STAGE56-TEST-READY-SAVE` / Stage56標準テスト用セーブを生成・配置する
- Summary:
  - Stage56以降の標準テストsave profileと、blank flashから通常ROM APIだけで生成する決定的generator／exact-ROM verifierを正本化した。
  - Codex受付前、序盤取得済み、全Lv.服従、先頭Lv.100ミュウツー＋ミュウツナイトY＋4タイプ攻撃技、手持ち6体をfresh-loadで固定した。
  - Stage56 ROM／同名saveをiPadへ原子的に配置し、read-back byte一致、既存Stage55不変、一時ファイル0を確認した。実機プレイ／人手承認は要求していない。
- Verify: generator独立2 process、full／slot 0／slot 1、自然Continue、Codex受付A入力、focused unit 5 tests、iPad size／SHA／`cmp`、task graph、private guard、diff check PASS。save SHA-256 `bdc4eea8dacf093734be6fcaa26eb55351126bbe39654d156f61829a3b90a5f7`。

## 2026-08-27T20:29:55+09:00

- Version: `post-v1.4.0-stage56-test-ready-save-v2-overpowered-party`（ROM identity不変）
- Commit: `-`（登録commit `b59848e`、本エントリを含む完了commit）
- Task: `USER-20260827-STAGE56-OVERPOWERED-QA-PARTY` / Stage56標準QA手持ちをLv.100攻撃型6体へ更新する
- Summary:
  - 今後の標準QA partyを、ミュウツー先頭＋カイオーガ／グラードン／レックウザ／ゼルネアス／ムゲンダイナのLv.100 6体へ更新した。
  - 全24技を攻撃技とし、各個体へダブルバトル向けの複数対象技を設定した。Codex受付前、序盤取得済み、全個体服従は維持した。
  - iPadの旧Stage56 saveを日時付きで保全して更新saveを原子的に配置し、read-back byte一致を確認した。実機プレイ／人手承認は要求していない。
- Verify: standard save build／check、focused unit 5 tests、iPad size／SHA／`cmp`、旧save保全、Stage55不変、一時ファイル0、task graph、private guard、diff check PASS。save SHA-256 `3192100245672e13baa2d4398d115c2288758e901033e7b4c9830124164f90df`。

## 2026-08-28T00:00:12+09:00

- Version: `post-v1.4.0-stage57-comprehensive-debug-repair`
- Commit: `-`（登録commit `dfa0386`、本エントリを含む完了commit）
- Task: `USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR` / 野生identity・NPCメニュー・ストーリー導線の横断修復
- Summary:
  - 505番道路の古いmap binding、Species変更後の名前／技非同期、NPC script 9件、control-flow 3件、menu tile衝突10件、Factory cursorを修復した。
  - 通常story戦26件の再戦Lv.80〜100誤流入をLv.6〜47へ戻し、共有カントー高難度戦を別ID分離で保持した。
  - 7 domainの高速QA、全678 map／5,432 root／8,925 script、505番道路66遭遇、全Species、全14 Collection host、world 22経路をStage57へ固定した。
- Verify: mGBA全7 domain×独立2 process、warning 0、focused unit 18 tests、build／check、clean 3経路byte一致、差分／直接BPS往復、declared span外0、全overlap 0、task graph、private guard、staged diff PASS。ROM SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`。

## 2026-08-28T01:10:08+09:00

- Version: `post-v1.4.0-stage57-ipad-rom-save-placement`（ROM identity／save ABI不変）
- Commit: `-`（登録commit `3b9bd12`、本エントリを含む完了commit）
- Task: `USER-20260828-STAGE57-IPAD-ROM-SAVE-PLACEMENT` / Stage57 ROMと標準QAセーブのiPad配置
- Summary:
  - 標準save profileをStage57 exact ROMへ進め、ROM自身の通常APIでLv.100攻撃型6体saveを独立2 process生成した。
  - RetroArch停止とlive設定再解決後、Stage57 ROM／同名saveをiPadへ原子的に配置し、確定後read-backをsourceとbyte一致させた。
  - 既存Stage56 ROM／saveを不変に保ち、remote一時ファイルを0にした。端末固有情報はtracked成果へ保存していない。
- Verify: save build／check、full／両slot／自然Continue、focused unit 5 tests、iPad size／SHA／`cmp`、Stage56不変、一時ファイル0、task graph、private guard、staged diff PASS。ROM `546136a6...`、save `31921002...`。

## 2026-08-28T15:50:47+09:00

- Version: `post-v1.4.0-stage58-qol-world-convenience-debug`
- Commit: `-`（登録commit `63d118e`、本エントリを含む完了commit）
- Task: `USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG` / QOL実使用、Codex拠点、薄い場所、野生、item／shopをStage58へ改善する
- Summary:
  - QOL 36機能を通常Bag／cancel／効果／save／fresh reloadへ接続し、save key rotationをstock Bag ownerへ戻して知恵の洞窟B2F resetを根治した。
  - Codex受付の左右へ通常PC Storageと全回復人物、近隣へmoney martを追加し、既存BP shop／Codex／Windows bank／Box 14契約を保持した。
  - 薄い6地点のatomic item event、Kanto wild 133物理header、研究・Honey・Raid・Ability Patch経済を実ROMとmachine-readable監査で調整した。
- Verify: mGBA 10 domain・動的22 process・warnings 0、QOL 36／Bag 15／world 22、全678 map／265 wild header／2,733 slot／256 item transaction、build／check、clean 3経路、BPS往復、span／overlap、focused unit 173、task graph／private guard／diff check PASS。ROM SHA-256 `501c3fdda825abfb167bc62da63c189671fa2f026d7b866001fbfbac36700a0c`、CRC32 `673F2B41`。
