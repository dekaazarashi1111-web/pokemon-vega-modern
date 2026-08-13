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
