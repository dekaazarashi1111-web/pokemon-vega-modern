# report_lifecycle_index.md

プロジェクト内のレポート、調査メモ、検証結果の状態を管理するための索引です。

## active

- `design/current_state.md`
- `design/agent_context_map.md`
- `design/catalog.md`
- `design/import_inventory.md`: 私有入力のhashと配置を公開可能な情報だけで記録
- `design/import_review.md`: 受領資料の採否、既知課題、優先順位
- `state/source-lock.json`: bootstrap後の入力hash・上流commit
- `reports/generated/`: 現在の入力/source pinから再生成するローカル監査（Git管理外）
- T02 exact audit 11成果: `make t02-audit` で生成し、`make t02-check` が一時再生成byte一致、fixed-write/ROM/state意味契約、UNKNOWN 0を検証する。入力policy SHA-256は `d06c0895a24d67317beb40d73619a584f88ae391a05f7fd09af3b2271c2f4429`。
- T03 harness: `make harness` が `reports/generated/harness_smoke.md` と `build/stages/03_harness.{gba,json}` を生成し、`make harness-check` が現在の入力/config fingerprint、Vega-owned byte一致、module配置、allocation reportを照合する。
- T04 move port: `make moves` が `reports/generated/move_port.md`、`build/stages/04_moves.{gba,json}`、`generated/engine/moves/`、`manifests/move_ids.csv` を生成し、`make moves-check` が1063技model、V3 131行、70 adapter、178 repoint、allocation、ROM、runner identityを現在入力から照合する。
- T05 ID space model: `python3 scripts/build_id_spaces.py build` が `reports/generated/id_space_report.md`、`generated/engine/ids/`、Type/Ability/Item manifestを生成し、同`check`が999 itemを含む13成果のbyte一致、host/ARM C compile、公開header共存を副作用なしで照合する。ROM stageとallocator配置はT06で行う。
- T06 CFRU battle core: `python3 scripts/build_battle_core.py build` が `build/stages/06_battle_core.{gba,json}` と `reports/generated/{battle_hook_matrix.csv,battle_core_smoke.md,facility_core_smoke.md,trainer_ai_smoke.md}` を2回構築・3本のlibmGBA runner・publish gate後に公開する。同`check`は入力fingerprint、stage/payload/allocation/report identity、進化表・固定Pokémon ABIを副作用なしで再照合する。
- T07 Species port: `make species` が `build/stages/07_species.{gba,json}`、`generated/engine/species/`、`manifests/species_ids.csv`、`reports/generated/species_port.md` を生成し、追加Speciesのparty生成をlibmGBA 2 processで検証する。`make species-check`は1621行model、105 repoint、stage/report/table/smoke identity、生成C compileを副作用なしで再照合する。
- T08 RAM/save compatibility: `make save-layout` が `config/{ram_layout,save_layout}.csv` とversioned overlayのhashから `reports/generated/save_compatibility.md` を決定的生成する。`make save-layout-check` はlive interval overlap 0、report identity、DEFER/EXCLUDED ownerを副作用なしで照合し、focused testsがchecksum/migration/transaction fixtureを実行する。
- T09 Species surface: `make species-surface` が `build/stages/09_species_surface.{gba,json}`、`generated/engine/{species_assets,evolutions,learnsets}/`、`reports/generated/{dex_policy,species_asset_validation}.md`、孵化matrixを生成する。`make species-surface-check`は1621行境界、DPE圧縮/アライン、ID変換、stage/report/table identityを副作用なしで再照合する。
- T10 Engine slice: `make engine-slice` がstage 09のlibmGBA追加種生成とhost C継続save fixtureを実行し、10 fixture・2 report・`build/stages/10_engine_slice.json`を生成する。`make engine-slice-check`は公開成果、feature matrix、schema、compile fixtureを副作用なしで照合する。
- T11 Kanto importer: `python3 scripts/build_kanto_import.py build` が本土256 mapのmanifest/inventory、V2 47地点crosswalk、クチバ民家1のcanonical JSONとround-trip reportを生成する。同`check`はclean BPRJ raw照合、全dependency解決、story-state非混入、成果byte一致を副作用なしで照合する。
- T12 Symbolic content: `python3 scripts/build_content_schema.py build` が `content/normalized/` の541 family・125 shared capture・8 gym rewardと `reports/generated/content_schema.md` / dry-run JSONを生成する。同`check`はJSON schema、symbolic参照、V2 59検査、正規化、進行/供給/AI/encounter/facility/Raid制約、成果byte一致を副作用なしで照合する。physical emitはT13 resolutionなしで拒否する。
- T13 Vermilion slice: `make vermilion-slice` がT11 physical mapとT12 symbolic contentをbindし、クチバ往復・安全導線・認定章ジム・Factory Trial・遭遇transactionのfixtureと `reports/generated/vermilion_slice.md` を生成する。`make vermilion-slice-check` は5成果のbyte一致と副作用なしを照合する。
- T14 Full Kanto maps: `make kanto-maps` がscope 256件から253 operational map、canonical map JSON、connectivity/size reportを生成する。`make kanto-maps-check` は257成果のbyte一致、253/253到達、47地点coverage、warp/connection/ID/tileset/allocation gateを副作用なしで照合する。
- T15 Kanto progression: `make kanto-progression` が39-node DAG、253 map gate、35 QOL境界、Factory 4 tier、再戦/League、Research/TM/DexNav/Raid state matrixと `reports/generated/progression_graph.md` を生成する。`make kanto-progression-check` は5成果のbyte一致と副作用なしを照合する。
- T16 Content population: `make content-population` が15 manifest、4 content policy、`build/stages/16_content.{gba,json}`、中央allocation、`reports/generated/{kanto_content_audit,trainer_balance_audit}.md` を生成する。`make content-population-check` は96論理地点、541系統×2地方、125共有捕獲key、価格/進行/合法性、ROM payload、stage外byte不変、allocation overlap 0、29成果のbyte一致と副作用なしを照合する。
- T17 Regression: `make regression` が `build/stages/17_regression.{gba,json}`、中央allocation、QOL-B runtime、Kanto map/wild/trainer/progression実体、manual checkpointと4 regression reportを生成する。`make regression-check` は2回のbyte同一build、libmGBA 2 process、QOL-B host境界、253 map往復到達、400地方往復、125共有捕獲、施設/AI/event状態fixture、16成果のbyte一致を副作用なしで照合する。
- USER Trainer V4: `make trainer-rebalance` が `build/stages/19_trainer_rebalance.{gba,json}`、中央allocation、正規化CSV、binding台帳、結合reportを生成する。`make trainer-rebalance-check` は141戦・610体のID解決、既存Trainer record、party pointer、AI flags 1/3/5、Mirage保護、変更span、7成果のbyte一致を副作用なしで照合する。
- USER Factory runtime: `make facility-runtime` がstage 19へクチバFactory Trial受付NPC、候補6体、3体選択、3連戦、勝利後交換、BP、sector 31保存・復旧を結合し、`build/stages/20_facility_runtime.{gba,json}` と `reports/generated/facility_runtime.md` を生成する。`make facility-runtime-check` は中央allocation、物理script graph、自然new-gameからのlibmGBA exact-ROM smoke 2 process、7成果のbyte一致を副作用なしで照合する。
- USER 初戦ループ: `make first-battle-hotfix` がstage 20へhold effect再検証を適用し、`build/stages/21_first_battle_hotfix.{gba,json}`、allocation、libmGBA証跡、`reports/generated/first_battle_loop_fix.md` を生成する。`make first-battle-hotfix-check` は初戦3分岐、不正indicator注入、正規Quick Claw/Custap/Quick Draw、clean ROMからのBPS完全往復、5成果のbyte一致を副作用なしで照合する。
- T18 Release: `make final` / `make release-patch` がstage 20から32 MiB最終ROM、BPS、9-member決定論ZIP、`reports/generated/release_verification.md` を生成する。`make verify-release` はBPS完全往復とarchive禁止物を副作用なしで照合し、`make release-fresh-check` はtagged sourceの隔離worktreeからT01〜T17、V4、Factory runtimeを再構築してfinal/BPS/ZIPのbyte一致証跡を生成する。

`reports/generated/**` は `make clean-build` で削除可能なため、タスク完了時は生成コマンド、入力/source/config/tool fingerprint、主要成果hashを `design/run_log.md` または追跡対象manifestへ残す。生成レポートだけを唯一の跨セッション証跡にしない。

## reference

- `audit_seed/reports/conflict_report.json`: パッチのみの機械可読競合証跡
- `audit_seed/reports/conflict_report.md`: 269 ranges / 775 bytesの人間向け要約
- `audit_seed/reports/semantic_hotspots.md`: Move優先などの初期意味分析
- `audit_seed/reports/public_source_reference.md`: 初期監査時の公開source blob参照
- `design/imported/VEGA_CFRU_DPE_統合設計/`: V2に置き換えられたV1来歴資料

## archive

- `audit_seed/reports/legacy_summary.json`: 現行 `conflict_report.json` に置き換えられた旧形式

## review

- `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`: 二地方設計のactive review資料。JSON/SHA manifestは47/47 PASS。
- `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data/*.csv`: 付属59検査はPASSしたが、V1由来の意味不整合は `design/import_review.md` を参照。
- 受領資料を直接編集しない。修正済みschema/dataはT12等で `manifests/` / `content/` へ昇格する。
- 新しいレポートはactive / reference / archive / reviewのどれかと、生成条件（input hash、source commit、tool version）を明記する。
