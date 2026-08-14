# catalog.md

## Project Docs

- `README.md`: プロジェクト入口
- `AGENTS.md`: エージェント運用規約
- `design/current_state.md`: 現在状態の要約
- `design/agent_context_map.md`: 読む順番の短縮地図
- `design/tasks_next.md`: 唯一のタスク状態正本
- `tasks/task_graph.json`: T00〜T18の依存関係正本
- `tasks/T*.md`: タスクごとの目的、成果物、完了条件
- `MASTER_PLAN.md`: 製品・技術ロードマップ
- `design/PLANS.md`: 運用計画索引
- `design/decisions.md`: 採択済みADR（追記のみ）
- `design/import_inventory.md`: 受領入力、hash、配置、上流pin
- `design/import_review.md`: 受領パッケージの採否と既知課題
- `design/kanto_feasibility.md`: 元FireRedカントー復元と二地方化の初期実証
- `design/run_log.md`: 実行ログ
- `design/version_log.md`: バージョン履歴
- `design/blockers.md`: ブロッカー記録
- `design/feature_ideas.md`: 将来案、気づき
- `design/report_lifecycle_index.md`: レポート類の状態管理

## Scripts

- `scripts/verify_linux.sh`: native Linux向け検証
- `scripts/verify_windows.ps1`: Windows向け検証
- `scripts/bootstrap_project.py`: 私有入力検証、上流取得、source lock生成
- `scripts/preflight.py`: 入力とtoolchainの事前検査
- `scripts/run_baseline_audit.py`: cleanからの参照ROMと厳密競合監査
- `scripts/generate_t02_audit.py`: T01成果、固定ROM、固定sourceからT02の11監査成果を決定的生成
- `scripts/build_project.py`: clean+Vega IPSから32 MiB T03 harnessを2回再構築し、module配置とlibmGBA smokeを検証
- `scripts/build_move_port.py`: Vega/CFRU/V3から1063技model、game-encoding表、70 effect adapterを生成
- `scripts/build_move_stage.py`: T03へ44,032-byte move bridgeと178 repointを適用し、実技smokeを検証
- `scripts/build_id_spaces.py`: Vega/CFRU/DPEのType・Ability・Itemを配置前stable modelへ統合し、manifest/C表/幅レポートを決定的生成
- `scripts/build_battle_core.py`: T04/T05へ固定CFRU battle coreを統合し、2回構築、3本のlibmGBA acceptance、publish gate、stage/report公開を決定的に実行
- `scripts/build_species_port.py`: T06へVega固定412種とDPE追加1209種のcanonical BaseStatsを統合し、manifest、公式捕獲count、実party生成smokeを決定的に実行
- `scripts/build_save_compatibility.py`: T08 RAM/save配置のlive overlapを検査し、versioned ledger入力hash付き互換性reportを決定的に生成・照合
- `scripts/build_species_surface.py`: T09の1621行画像/鳴き声/Dex/進化/learnset table、V2進化正規化、stage 09、孵化matrixを決定的に生成・照合
- `scripts/build_engine_vertical_slice.py`: T10追加要素・QOL-A・Factory/報酬遭遇/AI/TM/Mirage/Research/Raidの継続save fixture、libmGBA証跡、reportを生成・照合
- `scripts/build_kanto_import.py`: T11本土256 map manifest、V2 crosswalk、clean raw照合、1 map canonical import/round-tripを決定的生成・照合
- `scripts/build_content_schema.py`: T12 symbolic content、V2 59検査/正規化、dry-run、T13 resolution必須physical emitを生成・照合
- `scripts/build_vermilion_slice.py`: T13クチバ早期往復、physical binding、ジム・Factory・遭遇transaction fixtureを決定的生成・照合
- `scripts/build_full_kanto_import.py`: T14本土scope 256件を253 operational mapへ変換し、接続・ID・tileset・allocationを検証
- `scripts/build_kanto_progression.py`: T15の二段階Kanto進行、QOL、Factory 4 tier、再戦/League、Research/Raid境界を生成・照合
- `scripts/build_content_population.py`: T16の二地方encounter/trainer/item/facility/Raidを生成し、中央allocator管理の32 MiB stage 16へ配置・照合
- `scripts/build_trainer_rebalance_v4.py`: ユーザー提供V4の141戦・610体をcanonical IDへ解決し、既存本編Trainer IDへstage 19として決定的に結合・照合
- `scripts/build_facility_runtime.py`: stage 19へクチバFactory Trialの物理NPC、3戦script、CFRU候補生成・交換・sector 31保存runtimeをstage 20として決定的に結合・照合
- `scripts/taskctl.py`: `design/tasks_next.md` の安全な状態操作
- `scripts/guard_private_files.py`: 私有バイナリのGit混入防止
- `scripts/verify_imported_packages.py`: 受領した監査/設計資料の整合性検査
- `tools/validate/address_assertions.py`: T02成果を一時領域へ再生成し、byte一致と意味契約を検証

## Imported Evidence

- `audit_seed/`: 受領した単体競合監査パッケージの正本
- `design/imported/README.md`: active設計資料と旧版の案内
- `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`: 二地方設計のactive review資料
- `design/imported/VEGA_CFRU_DPE_統合設計/`: V1受領時点を保つ来歴資料
- `design/imported/VEGA_CFRU_DPE_技調整設計_V3/`: T04で採用した技現代化61件・Vega独自技70件の不変原本
- `reports/generated/`: 再実行可能なローカル監査結果（Git管理外）
- `userfile/imports/`: ROM、patch、元ZIP、展開バックアップ（Git管理外）

## Playbook

- `CODEX_START_HERE.md`: bootstrapと再開手順
- `CODEX_HANDOFF.md`: 短い受け渡し説明
- `WORKSTREAMS.md`: 並列レーンと所有権
- `docs/`: 入力、ID、ROM配置、Kanto、test、release方針
- `manifests/`: IDとコンテンツの機械可読正本候補
- `state/source-lock.json`: 入力hashと上流commitの固定記録

## Tools

- `tools/chatgpt_browser/README.md`: ChatGPT Web ブリッジ操作手順
- `audit_seed/tools/`: patch解析、参照ROM生成、source address監査
- `tools/t02/`: fixed source write、Vega ROM inventory、RAM/save/ID/state監査model
- `tools/rom_allocator.py`: 32 MiB named regionの決定的配置とoverlap拒否
- `tools/engine/extract_vega_moves.py`: 固定Vega ROMの512技・5 table・effect pointer抽出
- `tools/engine/cfru_move_inventory.py`: 固定CFRU-JPの992技・256 effect script inventory生成
- `tools/engine/extract_vega_id_spaces.py`: 固定Vega ROMのType・Ability・Item表と相性表をpointer/hash検証付きで抽出
- `tools/engine/cfru_id_space_inventory.py`: 固定CFRU-JP/DPE-JPのType・Ability・Item、表示、相性、ItemType、aliasを抽出
- `tools/engine/cfru_*`: T06のbattle write、runtime表、Factory、QOL、move effect、script tableを生成・検証
- `tools/engine/t06_publish_gate.py`: T06 stage、payload、進化表、固定Pokémon ABI、report identityを公開直前にfail-closed検証
- `tools/map_import/`: T11本土scope、物理ID分割、V2 logical-to-physical依存、story-safe canonical map変換
- `tools/content/`: T12 map/encounter/trainer/QOL/event/facility/currency/Raid schema検証、V2独立監査・正規化
- `tools/engine/extract_vega_species.py`: 固定Vega ROMのSpecies名412行と28-byte BaseStatsをpointer/hash検証付きで抽出
- `tools/mgba_move_smoke.c`: T04 synthetic wild battleでslot 0の実技実行、PP・HP変化を観測
- `tools/mgba_battle_{core,core_ai,policy}_smoke.c`: T06の通常戦、固定CFRU AI、Factory/Mirage/Raid policyを自然scheduler経路で検証
- `tools/mgba_species_smoke.c`: T07追加Speciesを実`CreateMon`でparty memoryへ生成し、Species・level・最大HPを検証
- `overlays/vega_adapter/`: hook 0件の再構築可能なT03 no-op Thumb module
- `overlays/cfru/`: T06 battle-local policy、QOL/Factory/Mirage/Raid bridge、固定幅runtime
- `config/t02_audit_policy.json`: T02入力hash、分類、overlap、移行・施設・AI契約の機械可読正本
- `config/rom_regions.csv`: ROM file offset half-open partitionの機械可読正本
- `config/id_spaces.json`: T05入力hash、抽出root、意味同一override、追加range、QOL item契約の正本
- `config/battle_core.json`: T06入力、battle-only分類、allocator/payload、runtime table、smoke/publish契約の正本
- `config/species_port.json`: T07固定Vega/DPE table hash、mapping、canonical BaseStats配置、stage/smoke契約の正本
- `config/ram_layout.csv`, `config/save_layout.csv`: T08のlive RAM ownerとversioned save field/migration/DEFER/EXCLUDED配置の正本
- `overlays/save_migration/`: T08 checksum、旧Vega migration、二地方/QOL、Factory/遭遇/Raid transaction runtime
- `overlays/species_surface/`: T09現代式孵化、タマゴ5個queue、party/PC原子的配送、孵化演出、compact IV/EV、まるいおまもりruntime
- `config/species_surface.json`: T09固定ROM/table root、canonical件数、配置、Oval Charm契約の正本
- `config/feature_matrix.csv`, `config/engine_manifest_schema.json`: T10/T17 QOL-A/B release既定値と凍結済みengine schemaの正本
- `overlays/engine_slice/`: T10の移動/文章/数量UI、TM license、Tohoku overlay、NORMAL/RESEARCH、Factory選択の境界adapter
- `content/`: T12 raw IDなしsymbolic正本、JSON schemas、541 family/125 shared capture/8 gym reward正規化成果
- `src/kanto/vermilion/`, `content/vermilion/`: T13の早期渡航runtime、クチバ安全導線、ジム、Factory Trial、建物外遭遇NPC契約
- `content/kanto_map_scope.csv`, `tools/map_import/full_kanto_import.py`: T14のINCLUDE/REBUILD/DEFER判断と全本土map canonical変換
- `content/{kanto,qol,facility,trainer}_progression.csv`, `content/kanto_state_model.csv`: T15の進行DAG、解禁境界、save ownership正本
- `content/{map_bindings,normal_table_protection,trainer_balance_constraints,activity_hooks}.csv`, `manifests/{kanto,tohoku,research,raid,facility,reward}*.csv`: T16の二地方物理binding、NORMAL保護、trainer/施設/報酬content正本
- `overlays/qol_b/`, `tools/regression/`, `scripts/build_regression.py`: T17のQOL-B、実Kanto ROM serializer、拡張trainer/progression、exact-ROM/state regression
- `config/trainer_rebalance_v4.json`, `content/trainer_rebalance_v4/`, `scripts/build_trainer_rebalance_v4.py`: V4入力hash、AI段階、既存Trainer ID対応、stage 19本編trainer結合の正本
- `overlays/facility_runtime/`, `tools/mgba_facility_runtime_smoke.c`, `scripts/build_facility_runtime.py`: Factory Trialの実ROM受付・候補6→選択3・勝利後交換・3連戦・BP・exact復元・stage 20の正本
- `tools/release/`, `scripts/build_release.py`: T18のBPS encode/decode、最終ROM、決定論release archive、安全監査、隔離fresh-checkout再構築
