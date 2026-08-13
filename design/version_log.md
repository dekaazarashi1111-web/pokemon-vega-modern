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
