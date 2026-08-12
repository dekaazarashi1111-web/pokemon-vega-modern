PYTHON ?= python3
CONFIG ?= config/project.toml

.PHONY: quickstart bootstrap preflight audit references t00 validate guard status next clean-build test verify imports-check

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

validate:
	$(PYTHON) scripts/validate_task_graph.py
	$(PYTHON) scripts/validate_manifests.py
	$(PYTHON) scripts/verify_imported_packages.py
	$(PYTHON) scripts/project_status.py --check

guard:
	$(PYTHON) scripts/guard_private_files.py

status:
	$(PYTHON) scripts/project_status.py
	$(PYTHON) scripts/taskctl.py next

next:
	$(PYTHON) scripts/taskctl.py next

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
