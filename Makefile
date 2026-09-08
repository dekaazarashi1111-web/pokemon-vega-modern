PYTHON ?= python3
CONFIG ?= config/project.toml
UPSTREAM_SANDBOX ?= /mnt/c/codex_tools/PokemonVegaT01

.PHONY: quickstart bootstrap preflight audit references t00 upstream-toolcheck upstream-repro t02-audit t02-check harness harness-check moves moves-check species species-check save-layout save-layout-check species-surface species-surface-check engine-slice engine-slice-check vermilion-slice vermilion-slice-check kanto-maps kanto-maps-check kanto-progression kanto-progression-check content-population content-population-check regression regression-check trainer-rebalance trainer-rebalance-check trainer-v5-foundation trainer-v5-foundation-check trainer-v5-tohoku-batch02 trainer-v5-tohoku-batch02-check trainer-v5-tohoku-batch03 trainer-v5-tohoku-batch03-check trainer-changekit-inputs trainer-changekit-inputs-check trainer-changekit-final trainer-changekit-final-check trainer-changekit-clean-rebuild trainer-changekit-clean-rebuild-check trainer-changekit-package-check mirage-production mirage-production-check mirage-production-clean-rebuild mirage-production-clean-rebuild-check move-distribution-v4 move-distribution-v4-check move-distribution-v4-clean-rebuild move-distribution-v4-clean-rebuild-check research-economy-v1 research-economy-v1-check research-economy-v1-clean-rebuild research-economy-v1-clean-rebuild-check reward-encounters-v2 reward-encounters-v2-check reward-encounters-v2-clean-rebuild reward-encounters-v2-clean-rebuild-check factory-high-modes-v2 factory-high-modes-v2-check factory-high-modes-v2-clean-rebuild factory-high-modes-v2-clean-rebuild-check codex-battle-bridge codex-battle-bridge-check codex-battle-bridge-clean-rebuild codex-battle-bridge-clean-rebuild-check codex-battle-runtime codex-battle-runtime-check codex-battle-runtime-clean-rebuild codex-battle-runtime-clean-rebuild-check codex-battle-ipad-bootstrap facility-runtime facility-runtime-check first-battle-hotfix first-battle-hotfix-check hm-field-access hm-field-access-check battle-rules battle-rules-check battle-ui battle-ui-check move-memory move-memory-check qol-release-smoke qol-release-smoke-check acquisition-events acquisition-events-check fast-rom fast-rom-battle-core fast-rom-battle-ui final release-patch verify-release release-fresh-check validate guard status next plan clean-build test verify imports-check bp-shop-runtime bp-shop-runtime-check factory-reward-runtime factory-reward-runtime-check factory-repeat-reward-runtime factory-repeat-reward-runtime-check factory-special-event-runtime factory-special-event-runtime-check factory-shiny-memorial-runtime factory-shiny-memorial-runtime-check
.PHONY: codex-battle-rewards codex-battle-rewards-check codex-battle-rewards-clean-rebuild codex-battle-rewards-clean-rebuild-check codex-battle-skill-check
.PHONY: windows-battle-catalog windows-battle-catalog-check
.PHONY: windows-box14-vault windows-box14-vault-check
.PHONY: species-form-compat species-form-compat-check
.PHONY: test-ready-save test-ready-save-check
.PHONY: stage57-debug-repair stage57-debug-repair-check stage57-debug-clean-rebuild stage57-debug-clean-rebuild-check stage57-debug-quick stage57-debug-full stage57-debug-story stage57-mgba-quick stage57-mgba-smoke stage57-mgba-all
.PHONY: stage58-qol-world stage58-qol-world-check stage58-qol-world-clean-rebuild stage58-qol-world-clean-rebuild-check stage58-debug-full stage58-economy-audit stage58-world-audit stage58-mgba-all stage58-final-gate
.PHONY: stage59-wild-identity stage59-wild-identity-check stage59-mgba-all stage59-final-gate stage60-wild-species-root-repair stage60-wild-species-root-repair-check stage60-mgba-normal-input stage60-final-gate
.PHONY: stage61-wiki stage61-wiki-check
.PHONY: modernization-identity modernization-identity-check modernization-p01 modernization-p01-check modernization-p01-capacity-audit modernization-p01-mgba modernization-p01-focused-test
.PHONY: modernization-p02-contract-check modernization-p02-stage64 modernization-p02-stage64-check modernization-p02-mgba modernization-p02-mgba-check modernization-p02-focused-test
.PHONY: modernization-p02-acceptance modernization-p02-acceptance-check
.PHONY: modernization-p03-check modernization-p05-check modernization-p06-check modernization-p07-check modernization-contracts-focused-test
.PHONY: modernization-p03-stage65 modernization-p03-stage65-check modernization-p03-stage65-mgba modernization-p03-stage65-mgba-check modernization-p03-stage65-focused-test
.PHONY: modernization-p03-stage66 modernization-p03-stage66-check modernization-p03-stage66-mgba modernization-p03-stage66-mgba-check modernization-p03-stage66-focused-test
.PHONY: modernization-p03-stage67 modernization-p03-stage67-check modernization-p03-stage67-mgba modernization-p03-stage67-mgba-check modernization-p03-stage67-focused-test
.PHONY: modernization-p08-check modernization-p08-focused-test
.PHONY: modernization-p04-source-fetch modernization-p04-assets modernization-p04-assets-check modernization-p04-assets-focused-test modernization-p04-capacity-check modernization-p04-capacity-focused-test
.PHONY: modernization-p05-ability-runtime modernization-p05-ability-runtime-check modernization-p05-ability-runtime-focused-test
.PHONY: github-private-assets github-private-assets-check github-private-assets-restore github-battle-wrapper-test

quickstart:
	bash scripts/quickstart.sh

bootstrap:
	$(PYTHON) scripts/bootstrap_project.py --config $(CONFIG) --auto --lock-inputs

preflight:
	$(PYTHON) scripts/preflight.py --config $(CONFIG)

audit:
	$(PYTHON) scripts/run_baseline_audit.py --config $(CONFIG) --target audit

references:
	$(PYTHON) scripts/run_baseline_audit.py --config $(CONFIG) --target references

t00:
	$(PYTHON) scripts/run_baseline_audit.py --config $(CONFIG) --target t00

upstream-toolcheck:
	$(PYTHON) scripts/build_upstream.py toolcheck --config $(CONFIG) --sandbox-root $(UPSTREAM_SANDBOX)

upstream-repro:
	$(PYTHON) scripts/build_upstream.py reproduce --config $(CONFIG) --sandbox-root $(UPSTREAM_SANDBOX) --repeat 2

t02-audit:
	$(PYTHON) scripts/generate_t02_audit.py

t02-check:
	$(PYTHON) tools/validate/address_assertions.py

harness:
	$(PYTHON) scripts/build_project.py harness --config $(CONFIG)

harness-check:
	$(PYTHON) scripts/build_project.py check-harness --config $(CONFIG)

moves:
	$(PYTHON) scripts/build_move_stage.py build

moves-check:
	$(PYTHON) scripts/build_move_stage.py check

species:
	$(PYTHON) scripts/build_species_port.py build

species-check:
	$(PYTHON) scripts/build_species_port.py check

save-layout:
	$(PYTHON) scripts/build_save_compatibility.py build

save-layout-check:
	$(PYTHON) scripts/build_save_compatibility.py check

species-surface:
	$(PYTHON) scripts/build_species_surface.py build

species-surface-check:
	$(PYTHON) scripts/build_species_surface.py check

engine-slice:
	$(PYTHON) scripts/build_engine_vertical_slice.py build

engine-slice-check:
	$(PYTHON) scripts/build_engine_vertical_slice.py check

vermilion-slice:
	$(PYTHON) scripts/build_vermilion_slice.py build

vermilion-slice-check:
	$(PYTHON) scripts/build_vermilion_slice.py check

kanto-maps:
	$(PYTHON) scripts/build_full_kanto_import.py build

kanto-maps-check:
	$(PYTHON) scripts/build_full_kanto_import.py check

kanto-progression:
	$(PYTHON) scripts/build_kanto_progression.py build

kanto-progression-check:
	$(PYTHON) scripts/build_kanto_progression.py check

content-population:
	$(PYTHON) scripts/build_content_population.py build

content-population-check:
	$(PYTHON) scripts/build_content_population.py check

regression:
	$(PYTHON) scripts/build_regression.py build

regression-check:
	$(PYTHON) scripts/build_regression.py check

trainer-rebalance:
	$(PYTHON) scripts/build_trainer_rebalance_v4.py build

trainer-rebalance-check:
	$(PYTHON) scripts/build_trainer_rebalance_v4.py check

facility-runtime:
	$(PYTHON) scripts/build_facility_runtime.py build

facility-runtime-check:
	$(PYTHON) scripts/build_facility_runtime.py check

first-battle-hotfix:
	$(PYTHON) scripts/build_first_battle_hotfix.py build

first-battle-hotfix-check:
	$(PYTHON) scripts/build_first_battle_hotfix.py check

hm-field-access:
	$(PYTHON) scripts/build_hm_field_access.py build

hm-field-access-check:
	$(PYTHON) scripts/build_hm_field_access.py check

battle-rules:
	$(PYTHON) scripts/build_battle_rules.py build

battle-rules-check:
	$(PYTHON) scripts/build_battle_rules.py check

battle-ui:
	$(PYTHON) scripts/build_battle_ui.py build

battle-ui-check:
	$(PYTHON) scripts/build_battle_ui.py check

move-memory:
	$(PYTHON) scripts/build_move_memory.py build

move-memory-check:
	$(PYTHON) scripts/build_move_memory.py check

qol-release-smoke:
	$(PYTHON) scripts/build_qol_release.py build

qol-release-smoke-check:
	$(PYTHON) scripts/build_qol_release.py check

acquisition-events:
	$(PYTHON) scripts/build_acquisition_events.py build

acquisition-events-check:
	$(PYTHON) scripts/build_acquisition_events.py check

bp-shop-runtime:
	$(PYTHON) scripts/build_bp_shop_runtime.py build

bp-shop-runtime-check:
	$(PYTHON) scripts/build_bp_shop_runtime.py check

factory-reward-runtime:
	$(PYTHON) scripts/build_factory_reward_runtime.py build

factory-reward-runtime-check:
	$(PYTHON) scripts/build_factory_reward_runtime.py check

factory-repeat-reward-runtime:
	$(PYTHON) scripts/build_factory_repeat_reward_runtime.py build

factory-repeat-reward-runtime-check:
	$(PYTHON) scripts/build_factory_repeat_reward_runtime.py check

factory-special-event-runtime:
	$(PYTHON) scripts/build_factory_special_event_runtime.py build

factory-special-event-runtime-check:
	$(PYTHON) scripts/build_factory_special_event_runtime.py check

factory-shiny-memorial-runtime:
	$(PYTHON) scripts/build_factory_shiny_memorial_runtime.py build

factory-shiny-memorial-runtime-check:
	$(PYTHON) scripts/build_factory_shiny_memorial_runtime.py check

trainer-v5-foundation:
	$(PYTHON) scripts/build_trainer_v5_stage31.py build

trainer-v5-foundation-check:
	$(PYTHON) scripts/build_trainer_v5_stage31.py check

trainer-v5-tohoku-batch02:
	$(PYTHON) scripts/build_trainer_v5_stage32_batch02.py build

trainer-v5-tohoku-batch02-check:
	$(PYTHON) scripts/build_trainer_v5_stage32_batch02.py check

trainer-v5-tohoku-batch03:
	$(PYTHON) scripts/build_trainer_v5_stage32.py build

trainer-v5-tohoku-batch03-check:
	$(PYTHON) scripts/build_trainer_v5_stage32.py check

trainer-changekit-inputs:
	$(PYTHON) scripts/validate_trainer_changekit_inputs.py build

trainer-changekit-inputs-check:
	$(PYTHON) scripts/validate_trainer_changekit_inputs.py check

trainer-changekit-final:
	$(PYTHON) scripts/build_trainer_changekit_final.py build

trainer-changekit-final-check:
	$(PYTHON) scripts/build_trainer_changekit_final.py check

trainer-changekit-clean-rebuild:
	$(PYTHON) scripts/rebuild_trainer_changekit_final_from_clean.py build

trainer-changekit-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_trainer_changekit_final_from_clean.py check

trainer-changekit-package-check:
	$(PYTHON) scripts/validate_trainer_changekit_inputs.py check
	$(PYTHON) -m unittest tests.test_trainer_changekit_content tests.test_trainer_final_kanto_events tests.test_trainer_changekit_final_builder tests.test_trainer_changekit_final_runtime -v
	$(PYTHON) scripts/build_trainer_changekit_final.py check
	$(PYTHON) scripts/rebuild_trainer_changekit_final_from_clean.py check

mirage-production:
	$(PYTHON) scripts/build_mirage_production.py build

mirage-production-check:
	$(PYTHON) scripts/build_mirage_production.py check

mirage-production-clean-rebuild:
	$(PYTHON) scripts/rebuild_mirage_production_from_clean.py build

mirage-production-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_mirage_production_from_clean.py check

move-distribution-v4:
	$(PYTHON) scripts/build_move_distribution_v4.py build

move-distribution-v4-check:
	$(PYTHON) scripts/build_move_distribution_v4.py check

move-distribution-v4-clean-rebuild:
	$(PYTHON) scripts/rebuild_move_distribution_v4_from_clean.py build

move-distribution-v4-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_move_distribution_v4_from_clean.py check

research-economy-v1:
	$(PYTHON) scripts/build_research_economy_v1.py build

research-economy-v1-check:
	$(PYTHON) scripts/build_research_economy_v1.py check

research-economy-v1-clean-rebuild:
	$(PYTHON) scripts/rebuild_research_economy_v1_from_clean.py build

research-economy-v1-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_research_economy_v1_from_clean.py check

reward-encounters-v2:
	$(PYTHON) scripts/build_reward_encounters_v2.py build

reward-encounters-v2-check:
	$(PYTHON) scripts/build_reward_encounters_v2.py check

reward-encounters-v2-clean-rebuild:
	$(PYTHON) scripts/rebuild_reward_encounters_v2_from_clean.py build

reward-encounters-v2-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_reward_encounters_v2_from_clean.py check

factory-high-modes-v2:
	$(PYTHON) scripts/build_factory_high_modes_v2.py build

factory-high-modes-v2-check:
	$(PYTHON) scripts/build_factory_high_modes_v2.py check

factory-high-modes-v2-clean-rebuild:
	$(PYTHON) scripts/rebuild_factory_high_modes_v2_from_clean.py build

factory-high-modes-v2-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_factory_high_modes_v2_from_clean.py check

codex-battle-bridge:
	$(PYTHON) scripts/build_codex_battle_bridge.py build

codex-battle-bridge-check:
	$(PYTHON) scripts/build_codex_battle_bridge.py check

codex-battle-bridge-clean-rebuild:
	$(PYTHON) scripts/rebuild_codex_battle_bridge_from_clean.py build

codex-battle-bridge-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_codex_battle_bridge_from_clean.py check

codex-battle-runtime:
	$(PYTHON) scripts/build_codex_battle_runtime.py build

codex-battle-runtime-check:
	$(PYTHON) scripts/build_codex_battle_runtime.py check

codex-battle-runtime-clean-rebuild:
	$(PYTHON) scripts/rebuild_codex_battle_runtime_from_clean.py build

codex-battle-runtime-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_codex_battle_runtime_from_clean.py check

codex-battle-rewards:
	$(PYTHON) scripts/build_codex_battle_rewards.py build

codex-battle-rewards-check:
	$(PYTHON) scripts/build_codex_battle_rewards.py check

codex-battle-rewards-clean-rebuild:
	$(PYTHON) scripts/rebuild_codex_battle_rewards_from_clean.py build

codex-battle-rewards-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_codex_battle_rewards_from_clean.py check

windows-battle-catalog:
	$(PYTHON) scripts/build_windows_battle_catalog.py build

windows-battle-catalog-check:
	$(PYTHON) scripts/build_windows_battle_catalog.py check

windows-box14-vault:
	$(PYTHON) scripts/build_windows_box14_vault.py build

windows-box14-vault-check:
	$(PYTHON) scripts/build_windows_box14_vault.py check

species-form-compat:
	$(PYTHON) scripts/build_species_form_compat.py build

species-form-compat-check:
	$(PYTHON) scripts/build_species_form_compat.py check

codex-battle-skill-check:
	test -s tools/codex_skills/vega-codex-battle/SKILL.md
	bash -n scripts/install_vega_codex_battle_skill.sh

codex-battle-ipad-bootstrap:
	mkdir -p .local
	$(CC) -std=c11 -Wall -Wextra -Werror tools/mgba_codex_battle_ipad_bootstrap.c -o .local/mgba-codex-battle-ipad-bootstrap -lmgba
	.local/mgba-codex-battle-ipad-bootstrap build/stages/44_codex_battle_runtime.gba .local/44_codex_battle_runtime_verified.srm

test-ready-save:
	$(PYTHON) scripts/build_test_ready_save.py build

test-ready-save-check:
	$(PYTHON) scripts/build_test_ready_save.py check

stage57-debug-repair:
	$(PYTHON) scripts/build_stage57_comprehensive_debug_repair.py build

stage57-debug-repair-check:
	$(PYTHON) scripts/build_stage57_comprehensive_debug_repair.py check

stage57-debug-clean-rebuild:
	$(PYTHON) scripts/rebuild_stage57_comprehensive_debug_repair_from_clean.py build

stage57-debug-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_stage57_comprehensive_debug_repair_from_clean.py check

stage57-debug-quick:
	$(PYTHON) tools/stage57_debug_suite.py build/stages/57_comprehensive_debug_repair.gba --mode quick --metadata build/stages/57_comprehensive_debug_repair.json

stage57-debug-full:
	$(PYTHON) tools/stage57_debug_suite.py build/stages/57_comprehensive_debug_repair.gba --mode full --metadata build/stages/57_comprehensive_debug_repair.json

stage57-debug-story:
	$(PYTHON) tools/stage57_story_trainer_audit.py build/stages/57_comprehensive_debug_repair.gba

stage57-mgba-quick:
	$(PYTHON) scripts/run_stage57_mgba_validation.py --domain quick --no-write

stage57-mgba-smoke:
	$(PYTHON) scripts/run_stage57_mgba_validation.py --domain smoke --collection-mode quick --no-write

stage57-mgba-all:
	$(PYTHON) scripts/run_stage57_mgba_validation.py --domain all --collection-mode full

stage58-qol-world:
	$(PYTHON) scripts/build_stage58_qol_world_convenience_debug.py build

stage58-qol-world-check:
	$(PYTHON) scripts/build_stage58_qol_world_convenience_debug.py check

stage58-qol-world-clean-rebuild:
	$(PYTHON) scripts/rebuild_stage58_qol_world_convenience_debug_from_clean.py build

stage58-qol-world-clean-rebuild-check:
	$(PYTHON) scripts/rebuild_stage58_qol_world_convenience_debug_from_clean.py check

stage58-debug-full:
	$(PYTHON) tools/stage58_debug_suite.py

stage58-economy-audit:
	$(PYTHON) tools/stage58_qol_economy_audit.py \
		--rom build/stages/58_qol_world_convenience_debug.gba \
		--metadata build/stages/58_qol_world_convenience_debug.json

stage58-world-audit:
	$(PYTHON) tools/stage58_world_balance.py

stage58-mgba-all:
	$(PYTHON) scripts/run_stage58_mgba_validation.py --domain all --collection-mode full

stage58-final-gate:
	$(PYTHON) scripts/build_stage58_qol_world_convenience_debug.py build
	$(PYTHON) scripts/run_stage58_mgba_validation.py --domain all --collection-mode full
	$(PYTHON) scripts/build_stage58_qol_world_convenience_debug.py build --require-mgba
	$(PYTHON) scripts/build_stage58_qol_world_convenience_debug.py check --require-mgba
	$(PYTHON) scripts/rebuild_stage58_qol_world_convenience_debug_from_clean.py build --require-mgba
	$(PYTHON) scripts/rebuild_stage58_qol_world_convenience_debug_from_clean.py check --require-mgba

stage59-wild-identity:
	$(PYTHON) scripts/build_stage59_wild_identity_npc_regression_repair.py build

stage59-wild-identity-check:
	$(PYTHON) scripts/build_stage59_wild_identity_npc_regression_repair.py check

stage59-mgba-all:
	$(PYTHON) scripts/run_stage59_mgba_validation.py --domain all

stage59-final-gate:
	$(PYTHON) scripts/build_stage59_wild_identity_npc_regression_repair.py build
	$(PYTHON) scripts/run_stage59_mgba_validation.py --domain all
	$(PYTHON) scripts/build_stage59_wild_identity_npc_regression_repair.py check

stage60-wild-species-root-repair:
	$(PYTHON) scripts/build_stage60_wild_species_root_repair.py build

stage60-wild-species-root-repair-check:
	$(PYTHON) scripts/build_stage60_wild_species_root_repair.py check

stage60-mgba-normal-input:
	$(PYTHON) scripts/validate_stage60_wild_species_root_repair.py

stage60-final-gate:
	$(PYTHON) scripts/build_stage60_wild_species_root_repair.py build
	$(PYTHON) scripts/validate_stage60_wild_species_root_repair.py
	$(PYTHON) scripts/build_stage60_wild_species_root_repair.py check

stage61-wiki:
	$(PYTHON) scripts/build_stage61_wiki.py build

stage61-wiki-check:
	$(PYTHON) scripts/build_stage61_wiki.py check

modernization-identity:
	$(PYTHON) scripts/build_modernization_identity.py

modernization-identity-check:
	$(PYTHON) scripts/build_modernization_identity.py --check

modernization-p01:
	$(PYTHON) scripts/build_modernization_p01.py build

modernization-p01-check:
	$(PYTHON) scripts/build_modernization_p01.py check

modernization-p01-capacity-audit:
	$(PYTHON) scripts/audit_modernization_p01_rom.py --compact

modernization-p01-mgba:
	$(PYTHON) scripts/run_modernization_p01_mgba.py

modernization-p01-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p01 tests.test_modernization_identity tests.test_modernization_consumer_identity tests.test_modernization_p01_rom -v

modernization-p02-contract-check:
	$(PYTHON) scripts/build_modernization_p02.py --check

modernization-p02-stage64:
	$(PYTHON) scripts/build_modernization_p02_stage64.py build

modernization-p02-stage64-check:
	$(PYTHON) scripts/build_modernization_p02_stage64.py check

modernization-p02-mgba:
	$(PYTHON) scripts/run_modernization_p02_mgba.py run

modernization-p02-mgba-check:
	$(PYTHON) scripts/run_modernization_p02_mgba.py check

modernization-p02-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p02_species_surface_policy tests.test_modernization_p02 tests.test_modernization_p02_mgba tests.test_modernization_p02_stage64 -v

modernization-p02-acceptance:
	$(PYTHON) scripts/run_modernization_p02_acceptance.py run

modernization-p02-acceptance-check:
	$(PYTHON) scripts/run_modernization_p02_acceptance.py check

modernization-p03-check:
	$(PYTHON) scripts/build_modernization_p03.py --check

modernization-p03-stage65:
	$(PYTHON) scripts/build_modernization_p03_stage65.py build

modernization-p03-stage65-check:
	$(PYTHON) scripts/build_modernization_p03_stage65.py check

modernization-p03-stage65-mgba:
	$(PYTHON) scripts/run_modernization_p03_stage65_mgba.py run

modernization-p03-stage65-mgba-check:
	$(PYTHON) scripts/run_modernization_p03_stage65_mgba.py check

modernization-p03-stage65-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p03_stage65 -v

modernization-p03-stage66:
	$(PYTHON) scripts/build_modernization_p03_stage66.py build

modernization-p03-stage66-check:
	$(PYTHON) scripts/build_modernization_p03_stage66.py check

modernization-p03-stage66-mgba:
	$(PYTHON) scripts/run_modernization_p03_stage66_mgba.py run

modernization-p03-stage66-mgba-check:
	$(PYTHON) scripts/run_modernization_p03_stage66_mgba.py check

modernization-p03-stage66-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p03_stage66 -v

modernization-p03-stage67:
	$(PYTHON) scripts/build_modernization_p03_stage67.py build

modernization-p03-stage67-check:
	$(PYTHON) scripts/build_modernization_p03_stage67.py check

modernization-p03-stage67-mgba:
	$(PYTHON) scripts/run_modernization_p03_stage67_mgba.py run

modernization-p03-stage67-mgba-check:
	$(PYTHON) scripts/run_modernization_p03_stage67_mgba.py check

modernization-p03-stage67-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p03_stage67 -v

modernization-p08-check:
	$(PYTHON) scripts/build_modernization_p08.py --check

modernization-p08-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p08 -v

modernization-p04-source-fetch:
	$(PYTHON) scripts/build_modernization_p04_sources.py --fetch --compact

modernization-p04-assets:
	$(PYTHON) scripts/build_modernization_p04_assets.py --write --compact

modernization-p04-assets-check:
	$(PYTHON) scripts/build_modernization_p04_assets.py --check --compact

modernization-p04-assets-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p04_sources tests.test_modernization_p04_asset_importer -v

modernization-p04-capacity-check:
	$(PYTHON) scripts/build_modernization_p04_capacity.py --check --compact

modernization-p04-capacity-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p04_capacity -v

modernization-p05-check:
	$(PYTHON) scripts/build_modernization_p05.py --check

modernization-p05-ability-runtime:
	$(PYTHON) scripts/build_modernization_p05_ability_runtime.py --write --compact

modernization-p05-ability-runtime-check:
	$(PYTHON) scripts/build_modernization_p05_ability_runtime.py --check --compact

modernization-p05-ability-runtime-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p05_ability_runtime -v

modernization-p06-check:
	$(PYTHON) scripts/build_modernization_p06.py --compact

modernization-p07-check:
	$(PYTHON) scripts/build_modernization_p07.py --check

modernization-contracts-focused-test:
	$(PYTHON) -m unittest tests.test_modernization_p03 tests.test_modernization_p05 tests.test_modernization_p06 tests.test_modernization_p07 -v

fast-rom:
	$(PYTHON) scripts/build_fast_rom.py --from auto

fast-rom-battle-core:
	$(PYTHON) scripts/build_fast_rom.py --from battle-core

fast-rom-battle-ui:
	$(PYTHON) scripts/build_fast_rom.py --from battle-ui

final:
	$(PYTHON) scripts/build_release.py final

release-patch:
	$(PYTHON) scripts/build_release.py patch

verify-release:
	$(PYTHON) scripts/build_release.py verify

release-fresh-check:
	$(PYTHON) scripts/build_release.py fresh-check

validate:
	$(PYTHON) scripts/validate_task_graph.py
	$(PYTHON) scripts/validate_manifests.py
	$(PYTHON) scripts/verify_imported_packages.py

guard:
	$(PYTHON) scripts/guard_private_files.py

status:
	$(PYTHON) scripts/project_status.py
	$(PYTHON) scripts/taskctl.py next

next:
	$(PYTHON) scripts/taskctl.py next

plan:
	$(PYTHON) scripts/taskctl.py plan

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: validate guard test

imports-check:
	$(PYTHON) scripts/verify_imported_packages.py

github-private-assets:
	$(PYTHON) scripts/github_private_environment.py build

github-private-assets-check:
	$(PYTHON) scripts/github_private_environment.py check --archive-dir .local/github-private-environment/assets

github-private-assets-restore:
	$(PYTHON) scripts/github_private_environment.py restore --archive-dir .local/github-private-environment/assets

github-battle-wrapper-test:
	$(PYTHON) -m unittest tests.test_run_github_battle_command tests.test_github_private_environment tests.test_github_comment_control tests.test_github_large_file_bridge tests.test_github_result_summary tests.test_run_github_private_suite

clean-build:
	@for dir in build generated reports/generated dist; do \
		test ! -L "$$dir" || { echo "Refusing symlinked generated directory: $$dir"; exit 1; }; \
		if test -d "$$dir"; then find "$$dir" -mindepth 1 -maxdepth 1 ! -name .gitkeep -exec rm -rf -- {} +; fi; \
	done
