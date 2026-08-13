PYTHON ?= python3
CONFIG ?= config/project.toml
UPSTREAM_SANDBOX ?= /mnt/c/codex_tools/PokemonVegaT01

.PHONY: quickstart bootstrap preflight audit references t00 upstream-toolcheck upstream-repro t02-audit t02-check harness harness-check moves moves-check species species-check save-layout save-layout-check species-surface species-surface-check engine-slice engine-slice-check validate guard status next plan clean-build test verify imports-check

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
