PYTHON ?= python3
CONFIG ?= config/project.toml
UPSTREAM_SANDBOX ?= /mnt/c/codex_tools/PokemonVegaT01

.PHONY: quickstart bootstrap preflight audit references t00 upstream-toolcheck upstream-repro t02-audit t02-check harness harness-check moves moves-check species species-check save-layout save-layout-check species-surface species-surface-check engine-slice engine-slice-check vermilion-slice vermilion-slice-check kanto-maps kanto-maps-check kanto-progression kanto-progression-check content-population content-population-check regression regression-check trainer-rebalance trainer-rebalance-check facility-runtime facility-runtime-check first-battle-hotfix first-battle-hotfix-check hm-field-access hm-field-access-check battle-rules battle-rules-check battle-ui battle-ui-check move-memory move-memory-check qol-release-smoke qol-release-smoke-check acquisition-events acquisition-events-check fast-rom fast-rom-battle-core fast-rom-battle-ui final release-patch verify-release release-fresh-check validate guard status next plan clean-build test verify imports-check bp-shop-runtime bp-shop-runtime-check factory-reward-runtime factory-reward-runtime-check factory-repeat-reward-runtime factory-repeat-reward-runtime-check factory-special-event-runtime factory-special-event-runtime-check

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

clean-build:
	@for dir in build generated reports/generated dist; do \
		test ! -L "$$dir" || { echo "Refusing symlinked generated directory: $$dir"; exit 1; }; \
		if test -d "$$dir"; then find "$$dir" -mindepth 1 -maxdepth 1 ! -name .gitkeep -exec rm -rf -- {} +; fi; \
	done
