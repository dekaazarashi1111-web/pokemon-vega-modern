.PHONY: all

OUT_DIR ?= $(CURDIR)/build
ROM_ORIGIN ?= 0x09200000
TOOLCHAIN_MANIFEST ?= $(abspath $(CURDIR)/../../infra/toolchain_manifest.json)

all:
	@/usr/bin/python3 -I "$(CURDIR)/build_module.py" \
		--manifest "$(TOOLCHAIN_MANIFEST)" \
		--out-dir "$(OUT_DIR)" \
		--rom-origin "$(ROM_ORIGIN)"
