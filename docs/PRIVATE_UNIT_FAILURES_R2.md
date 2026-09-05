# 全unit失敗58件の追跡表（修復作業中）

Task: `USER-20260905-PRIVATE-FULL-UNIT-R2`

## 原本と分類

元run `33967241290` / job `101309429531`を監査run `33975817811`で独立再取得した。1594 tests、1230.020秒、FAIL 17、ERROR 41、skip 29、capstone 0。原本ログSHA-256は`8eefbe29075cc80f9c14dd22852d13922ac1837a0d1b0b479e71b79fba6620be`。任意の例外本文とprivate byteは記載しない。

A=純粋unit/compile fixture・validatorの不整合（7件）。B=古い固定契約/生成証跡（32件）。C=hosted Linux差（4件）。D=private fixture不足（3件）。E=WSL実環境への依存（2件）。F?=実装回帰または正本不整合の候補（10件、回帰と断定しない）。B/F?の未修復項目はソース照合からの暫定分類であり、実ROM再生成を済ませた意味ではない。

PASSは当該focused testの実測であり、全unit PASSとは異なる。D34は元のsave不足を固定hashの独立2プロセス生成で解消したが、その先のStage61 runtime symbol検査で失敗している。F?を「環境の問題」として処理しない。新しい期待値を根拠なく採用していない。

## 58件（原本の出現順）

| # | 原本 | 分類 | テスト | 確認状態 |
|---:|---|---|---|---|
| 1 | ERROR | B | `test_battle_ui.BattleUITests.test_all_move_menu_profiles_share_the_fixed_cfru_owner` | 未修復 |
| 2 | ERROR | B | `test_battle_ui.BattleUITests.test_source_abi_is_pinned_and_original_ui_macros_were_disabled` | 未修復 |
| 3 | ERROR | B | `test_battle_ui.BattleUITests.test_stage_build_is_deterministic_and_changes_only_five_owner_entries` | 未修復 |
| 4 | ERROR | F? | `test_build_battle_core.BattleCoreBuilderTests.test_fixed_inputs_and_models_are_exact` | 未修復 |
| 5 | ERROR | F? | `test_build_battle_core.PublishedBattleCoreTests.test_check_is_read_only_and_passes` | 未修復 |
| 6 | ERROR | B | `test_build_species_port.PublishedSpeciesPortTests.test_check_is_read_only_and_passes` | 未修復 |
| 7 | ERROR | E | `test_build_upstream.SandboxPathTests.test_accepts_ascii_path_on_windows_mount` | focused PASS |
| 8 | ERROR | E | `test_build_upstream.SandboxPathTests.test_rejects_existing_symlink_in_parent_chain` | focused PASS |
| 9 | ERROR | B | `test_engine_vertical_slice.EngineVerticalSliceTests.test_manifest_schema_frozen_and_check_read_only` | 未修復 |
| 10 | ERROR | C | `test_event_authoring_packet.EventAuthoringPacketTests.test_packet_is_deterministic_private_free_and_self_validating` | focused PASS |
| 11 | ERROR | C | `test_event_authoring_packet.EventAuthoringPacketTests.test_validator_rejects_cross_map_host_claim` | focused PASS |
| 12 | ERROR | B | `test_factory_high_modes_v2.FactoryHighModesV2Tests.setUpClass` | 未修復 |
| 13 | ERROR | B | `test_move_distribution_v4.MoveDistributionV4Test.setUpClass` | 未修復 |
| 14 | ERROR | B | `test_move_memory.MoveMemoryTests.test_stage_build_is_deterministic_and_declared_only` | 未修復 |
| 15 | ERROR | B | `test_qol_release.QolReleaseIntegrationTest.test_check_mode_has_no_artifact_drift` | 未修復 |
| 16 | ERROR | B | `test_qol_release.QolReleaseIntegrationTest.test_published_fixture_uses_one_final_rom_for_every_component` | 未修復 |
| 17 | ERROR | F? | `test_regression.RegressionReleaseCandidateTest.setUpClass` | 未修復 |
| 18 | ERROR | B | `test_release.ReleaseContractTests.test_final_stage_requires_complete_qol_chain` | 未修復 |
| 19 | ERROR | B | `test_reward_encounters_v2.RewardEncountersBuildContractTests.test_builder_reproduces_all_static_outputs_without_mutation` | 未修復 |
| 20 | ERROR | B | `test_stage58_qol_world_convenience_debug.Stage58QolWorldConvenienceTests.setUpClass` | 未修復 |
| 21 | ERROR | A | `test_stage61_catalog_state_matrix.Stage61CatalogStateMatrixUnitTests.test_runtime_toolchain_manifest_is_complete_and_abi_closed` | focused PASS |
| 22 | ERROR | B | `test_stage61_cyclic_decision_contracts.Stage61CyclicDecisionContractTests.setUpClass` | 未修復 |
| 23 | ERROR | A | `test_stage61_factory_prepare_error_adapter.Stage61FactoryPrepareErrorAdapterTest.setUpClass` | focused PASS |
| 24 | ERROR | F? | `test_stage61_interaction_oracle.Stage61GiftStorageFossilFocusedTests.setUpClass` | 未修復 |
| 25 | ERROR | F? | `test_stage61_interaction_oracle.Stage61InteractionOracleTests.setUpClass` | 未修復 |
| 26 | ERROR | B | `test_stage61_interaction_oracle.Stage61PartyMinigameRFUFocusedTests.test_rfu_initializer_zero_and_double_retry_are_rejected_product_wide` | 未修復 |
| 27 | ERROR | B | `test_stage61_interaction_oracle.Stage61PartyMoveTransactionFocusedTests.setUpClass` | 未修復 |
| 28 | ERROR | B | `test_stage61_interaction_oracle.Stage61RepeatingMenuExecutorTests.test_product_berry_vendor_correlates_amount_and_executes_real_exit` | 未修復 |
| 29 | ERROR | B | `test_stage61_interaction_oracle.Stage61RepeatingMenuExecutorTests.test_product_celio_forced_accept_uses_one_no_witness_then_actual_yes` | 未修復 |
| 30 | ERROR | B | `test_stage61_interaction_oracle.Stage61RepeatingMenuExecutorTests.test_product_pc_menu_all_flag_domains_then_actual_b_exit` | 未修復 |
| 31 | ERROR | B | `test_stage61_interaction_oracle.Stage61RepeatingMenuExecutorTests.test_product_seagallop_pages_use_one_cycle_then_actual_b_exit` | 未修復 |
| 32 | ERROR | B | `test_stage61_interaction_oracle.Stage61RepeatingMenuExecutorTests.test_product_vending_contract_keeps_each_real_purchase_then_b_exit` | 未修復 |
| 33 | ERROR | A | `test_stage61_seafoam_engine_canonicalization.Stage61SeafoamEngineCanonicalizationTest.test_arm7tdmi_wrapper_compile_and_object_code` | focused PASS |
| 34 | ERROR | D | `test_stage61_state_namespace_collision_audit.Stage61StateNamespaceCollisionAuditTest.setUpClass` | save生成成功／後続監査失敗 |
| 35 | ERROR | A | `test_stage61_stateful_menu_mgba_contract.Stage61StatefulMenuMgbaContractTests.setUpClass` | focused PASS |
| 36 | ERROR | B | `test_t02_state_inventory.StateInventoryTests.setUpClass` | 未修復 |
| 37 | ERROR | D | `test_trainer_changekit_content.TrainerChangeKitContentTest.setUpClass` | 未修復 |
| 38 | ERROR | D | `test_trainer_changekit_final_builder.TrainerChangeKitFinalBuilderTests.setUpClass` | 未修復 |
| 39 | ERROR | A | `test_validate_manifests.ValidateManifestsTests.test_generated_manifests_fail_when_only_some_pinned_sources_exist` | focused PASS |
| 40 | ERROR | A | `test_validate_manifests.ValidateManifestsTests.test_generated_manifests_pass_when_all_pinned_sources_are_absent` | focused PASS |
| 41 | ERROR | C | `test_vega_adapter.VegaAdapterTests.setUpClass` | focused PASS |
| 42 | FAIL | B | `test_battle_ui.BattleUITests.test_battle_core_pin_ignores_elapsed_time_but_keeps_ui_abi` | 未修復 |
| 43 | FAIL | B | `test_cfru_id_space_inventory.CFRUIdSpaceInventoryTests.test_fixed_source_and_t01_baseline_hashes_are_recorded` | 未修復 |
| 44 | FAIL | B | `test_codex_battle_bridge.CodexBattleBridgeTests.test_fixed_input_and_ram_contract` | 未修復 |
| 45 | FAIL | F? | `test_content_population.ContentPopulationTest.test_rom_payload_and_central_allocation` | 未修復 |
| 46 | FAIL | F? | `test_event_design_implementation.EventDesignPhysicalBuildTests.test_upstream_trainer_acquisition_qol_and_service_owners_are_preserved` | 未修復 |
| 47 | FAIL | C | `test_extract_vega_moves.FixedVegaMoveExtractionTests.test_cli_reads_only_fixed_config_and_reference_and_emits_json` | focused PASS |
| 48 | FAIL | B | `test_mirage_production.MirageProductionPhysicalBuildTests.test_pinned_stage37_and_stage38_identity_are_exact` | 未修復 |
| 49 | FAIL | F? | `test_mirage_production.MirageProductionPhysicalBuildTests.test_runtime_symbols_and_seven_rooted_physical_patches_are_live` | 未修復 |
| 50 | FAIL | B | `test_release.ReleaseContractTests.test_release_identity_is_v1_3_9` | focused PASS |
| 51 | FAIL | F? | `test_research_economy_v1.ResearchEconomyPhysicalBuildTests.test_all_eleven_exact_hooks_and_nine_hosts_are_live` | 未修復 |
| 52 | FAIL | B | `test_research_economy_v1.ResearchEconomyPhysicalBuildTests.test_pinned_stage39_and_stage40_identity_are_exact` | 未修復 |
| 53 | FAIL | B | `test_reward_encounters_v2.RewardEncountersBuildContractTests.test_stage41_bps_routes_are_byte_identical` | 未修復 |
| 54 | FAIL | B | `test_reward_encounters_v2.RewardEncountersEvidenceTests.test_clean_rebuild_evidence_revalidates_without_writes` | 未修復 |
| 55 | FAIL | F? | `test_stage61_interaction_oracle.Stage61CoinsABIFocusedTests.test_product_prize_room_checkcoins_result_is_path_exact` | 未修復 |
| 56 | FAIL | A | `test_stage61_mgba_validation.Stage61MgbaValidationTests.test_control_abi_registry_all_domains_and_internal_trace_fail_closed` | local PASS／HEAD検証待ち |
| 57 | FAIL | B | `test_stage61_normal_save_cow_contract.Stage61NormalSaveCowMetadataContractTest.test_builder_declares_the_same_exact_metadata_contract` | focused PASS |
| 58 | FAIL | B | `test_stage61_wiki.Stage61WikiTest.test_search_index_and_species_links_are_resolvable` | focused PASS |

## 修復根拠と残件

A21/23/33: 現行Cの必須rematch alias macroを既存builderと同じABI値でcompile fixtureへ供給。A35: real RFU peripheral C実装をlinkへ追加。A39/40: population inventory不在は検証エラーへ変換し、manifest単体とpopulation統合の依存を分離。A56: 現行制御5種類を既存の決定的fixture生成元から補い、全種類集合、binary size、未解決producer等の負例を保持。

B50: release builder正本v1.4.0/Stage26 acquisitionと歴史的Stage25入力を区別。B57: COWの完全契約と9キー要約を別々に厳密検証。B58: tracked Wiki正本4248件（species1621/move1063/ability312/item999/story12/map47/battle77/fixed_capture117）を生成元ID集合とリンクまで照合。根拠の詳細は`PRIVATE_UNIT_REPAIR_R2_20260905.md`。

C10/11: Git祖先確認はtemp Gitの実履歴へ分離。C41: Python reference SHAを残したうえで、異なるsecurity revisionはauthenticated APT package SHA256、実行file member SHA256、package/version/architecture、SOABI、実機能を検証する。ARM toolの固定hashは従来どおり。d3396fe2のActionsでadapter 6 testsが成功。C47: ignored project.tomlをtracked example由来のtemp fixtureへ移行。E7/8: mount境界mockと実temp symlinkでWSLへの依存を除去、実装のpath guardは維持。

D34: published report SHA256と元bootstrap CのSHA256を固定し、現行ゲームのbootstrapは戻さず歴史的生成元をsource fixtureへ保存。2独立mGBA processのreport・save全byte一致、131072 bytes、既存期待SHA256一致を必須とする。生成はignored領域のみで既存saveを上書きしない。d3396fe2で生成を通過し、後続の現行Stage61 auditが復元runtime symbol不足を検出した。D37/38はTask06 authoring registryが未復元であり、まだ解消していない。

未修復の具体例: vendor CFRU-JPのdirty差分を意図したpatchと確認する必要がある。Stage06固定入力、Stage09 validator/生成証跡、Stage61 cyclic source pinが古い。Stage61 custom saveの必要symbolが復元metadataに不足する。QOL hook数94対97、ability patch命令byte、compatibility patch数0対1、checkcoins経路blockerは実装/生成元の調査が必要。hash確認を無効にして通していない。

## 元runの29 skips

| 理由 | 件数 | テスト群 | 扱い |
|---|---:|---|---|
| T05固定入力不足 | 18 | `test_build_id_spaces.IdSpaceBuilderTests` | 妥当なplatform skipとは未承認 |
| T06 AI stage不足 | 1 | `test_mgba_battle_core_ai_smoke.FixedStageBattleCoreAiSmokeTests` | 復元/生成不足の確認が必要 |
| T06 battle-core不足 | 2 | `test_mgba_battle_core_smoke.FixedStageBattleCoreSmokeTests` | 復元/生成不足の確認が必要 |
| runtime-trigger生成物不足 | 1 | `test_stage61_runtime_trigger_inputs` | 現行正本から生成する必要あり |
| test-ready-save生成物不足 | 1 | `test_test_ready_save` | 新fixture生成後の全unitは未計測 |
| Task06 private ChangeKit不足 | 6 | `test_trainer_final_kanto_events.KantoEventFullPlanTests` | private registry不足、未解消 |

29件は元runの観測値であり、最終HEADの残skip数ではない。現時点のfocused runはskip 0。全unitを実行していないHEADについて、errors 0 / failures 0とは報告しない。

## 運用境界

PRIVATEを維持し、PR #1/#2、main、既存Stage60 IN_PROGRESSを変更しない。新規のPR-event workflowによる検証とmain上のissue_comment定義を区別する。source blob準備workflowはhash固定の未参照blobだけを作り、branch/ref/commitを自動更新しない。`make test`向け新runnerは標準unittest discoveryと同一pattern/load_testsを使い、全結果種別を通常unittestと照合する単体テストを持つ。テスト選択/skip/assertionは変えず、Python/native/child出力と任意の例外本文をログから除外する。
