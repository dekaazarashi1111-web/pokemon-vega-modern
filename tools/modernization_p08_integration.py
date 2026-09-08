#!/usr/bin/env python3
"""工程1～7の固定成果を統合監査し、工程8 checkpointを構築する。

入力は名前探索せず ``PINNED_TRACKED_INPUTS`` のみを読む。後続成果が新たに
現れても、明示更新されるまではこのcheckpointへ暗黙採用しない。重いROM実行は
行わず、既存ROM/metadataとcontractのhash接続を検証する。
"""

from __future__ import annotations

import binascii
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, Sequence


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P08"
STATUS = "CHECKPOINT_NOT_RELEASE_CANDIDATE"
SNAPSHOT_BASE_HEAD = "b4bdb67fcb9c49414661b2c591e0b1d9464aeafe"

# 完成済みとして引き渡されたtracked pathだけを固定する。globによる自動追加禁止。
PINNED_TRACKED_INPUTS: Mapping[str, tuple[int, str, str]] = {
    "config/active_play_baseline.json": (
        394, "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053", "BASELINE"
    ),
    "design/active_play_baseline.md": (
        5551, "e486dfa3fd9771084ba50390dd30b70d5c52e008a0b48f8cd186086e05e819f8", "BASELINE"
    ),
    "config/modernization_inputs.json": (
        5266, "b872a9793f6c29944d6c86d603aab8fbdf78df9c2f0ccf4595b6d308d23825f4", "P01"
    ),
    "config/modernization_candidate.json": (
        9098, "5654897da9490706e72c8ff92b305181253d9c64e73a2cfbbd435452072f7bf0", "CANDIDATE_CHAIN"
    ),
    "content/modernization/identity_contract.json": (
        1461322, "be4e08a27986b7e384eab8239f5608732b5c6575b060fdae50efd0c90a810443", "P01"
    ),
    "content/modernization/p02_evolution_contract.json": (
        1440826, "007f80996ad1a758e0f5365e65cd4685a6c9eb7c8a072d25544b86f2f613181b", "P02"
    ),
    "content/modernization/p02_stage64_checkpoint.json": (
        5462, "36730cfc31c4beebe74137db29dae28c931e927ae2436192b8bdd5a9a71c2276", "P02"
    ),
    "content/modernization/p02_stage64_mgba_runtime_gate.json": (
        5206, "640c6579365e682c59849392a8d2d15e4061ecbccaaff1094ab997aa91b762ea", "P02"
    ),
    "config/modernization_adoption_decisions.json": (
        601, "1fd74abe9b2fc1af2f8fdd77ae5d911dfd6abddee314313542f8958b0dab8e7e", "P03_P05"
    ),
    "config/modernization_p02_acceptance_gate.json": (
        3385, "234799dc97012196d47c286981a4a233cce7c5f6817dd3b183a5250ccd6190bb", "P02"
    ),
    "content/modernization/p02_acceptance_checkpoint.json": (
        18455, "cf2acf56cbe932786c1a610a02b2798098ed0b06dd2c8cd53c2063951ca1d179", "P02"
    ),
    "content/modernization/p03_compiled_index.json": (
        2327596, "a4258048c50df88ecbaf2525e04edaa6f2440da2a79d2f336ccb67e3a2362751", "P03"
    ),
    "content/modernization/p03_learnset_contract.json": (
        11826, "4e421a5c6110ad5b4e2de399d354b058b566815aaf5aa30b8cc445cba38a6033", "P03"
    ),
    "content/modernization/p03_runtime_handoff.json": (
        8692, "2458a0b3299f318f4a08dc460df6db876ea4f5f2347e6f8c48541d9b8a9f0479", "P03"
    ),
    "config/modernization_p03_stage65.json": (
        6733, "1846992a47218e8f6e65606e69d692bc611d974ede8177e137786aa0d405ec00", "P03"
    ),
    "content/modernization/p03_stage65_checkpoint.json": (
        9522, "3956ebc238c0acc9e715e87a8587051221a824d31a81bd24ba4dea4e04c7823d", "P03"
    ),
    "content/modernization/p03_stage65_mgba_runtime_gate.json": (
        6744, "d2acc9d2051e3043bbcd59666dc96f0dfd333771272a7d8201aaa2827a022816", "P03"
    ),
    "config/modernization_p03_stage66.json": (
        7580, "a6f1cdfff3bca980305c3284c3760a95765df65bcf8414e9e683aa9cdba444d1", "P03"
    ),
    "content/modernization/p03_stage66_bulk_route_audit.json": (
        15348, "fbd211961c03bbd7df02247c4251edd94685f2a89084134ad90bee35a38e7df6", "P03"
    ),
    "content/modernization/p03_stage66_change_audit.json": (
        317023, "9a02a00b14b63a7677ebcbc85204cb0bb521fdd78ac84d319cb66137e45b2d5e", "P03"
    ),
    "content/modernization/p03_stage66_checkpoint.json": (
        8156, "c542f388479a18d10eae5adc7fce267a0654c857f1d65816be43b2bf2ae452d4", "P03"
    ),
    "content/modernization/p03_stage66_mgba_runtime_gate.json": (
        10456, "9201a22bfb341c997867c76050e9383c135823cfecb6488bb7d112ad6b1da13a", "P03"
    ),
    "config/modernization_p03_stage67.json": (
        9974, "d477e805302192ca645adc673cc683ab41f224bbdd18b5c566212c07d7b55b83", "P03"
    ),
    "content/modernization/p03_stage67_consumer_route_audit.json": (
        92230, "9db0a2766711d6bb45d7822189833c6add033638ac78f51d5ea7e2ca450df0f0", "P03"
    ),
    "content/modernization/p03_stage67_change_audit.json": (
        762536, "13733c2f5af62305da0dd69894023099bd1da467a51dd27c3fb07335a8a97bcf", "P03"
    ),
    "content/modernization/p03_stage67_checkpoint.json": (
        11581, "90c6d83eba73ec9aee3450c111d1f4da607bc0b8b58945245cb13888cba96629", "P03"
    ),
    "content/modernization/p03_stage67_mgba_runtime_gate.json": (
        6852, "51bcd6fa2a606cdbd41bceabd0b1077c455dbd0c5f136888a19504ed80d9df20", "P03"
    ),
    "content/modernization/p04_asset_sources.json": (
        6748, "133c6b8dd56dc0afdb80acbb943c2e5b3ed1b72247bcc07350c78933e93e0636", "P04"
    ),
    "content/modernization/p04_candidate_manifest.json": (
        60095, "95fd141a4f38d4fd937af3a3873ae93f99028e94d9422db148279a1b90f6f9ac", "P04"
    ),
    "content/modernization/p04_official_sources.json": (
        9862, "eadd2eea75b5a3d4c7aacf9315b3025e0e7ece945354970ac9c372eb59548fcd", "P04"
    ),
    "content/modernization/p04_asset_import_manifest.json": (
        498512, "d175514c66ee66d055d8457d6f15ff19b8a0d60f4bceb621e2f8c5e9a5aa8cc0", "P04"
    ),
    "content/modernization/p04_capacity_allocation_manifest.json": (
        437769, "8377afbe70ff3a1da1c805f51f5e83d49fd0a5befd271e6c549cf0f76bf082fe", "P04"
    ),
    "content/modernization/p05_battle_content_contract.json": (
        76297, "3c91f05d716358b039ae020eaf980dec676c71c59e88d831d7dbc54db2aff404", "P05"
    ),
    "content/modernization/p05_data_only_patch_plan.json": (
        8391, "14716e137dd326e70982e89f690a0e11b4662cfe948899d6a6fc8a802c65c41e", "P05"
    ),
    "content/modernization/p05_runtime_handoff.json": (
        30762, "9498b71bc131ed78f6c0efcd930de74838b4e25ce910f1d828389bcaeb03405d", "P05"
    ),
    "config/modernization_p05_ability_runtime.json": (
        10863, "52c14a10faeefe6bee002fc0c1ea40b077ce8ea7ecbab9ffd88fa5226bb85eb4", "P05"
    ),
    "content/modernization/p05_ability_runtime_checkpoint.json": (
        24971, "41c505c1ed321e2d0b8271eb6f96ac802cbcc5c99290ba417ba2be8d2fa45c38", "P05"
    ),
    "content/modernization/p06_review_projection.json": (
        206313, "04efc32cb54e2f0adf8cbb5d4de480c322188e709856d876198f57d27427f01f", "P06"
    ),
    "content/modernization/p06_species_adjustment_contract.json": (
        6648, "1e26b64de260e30c266a0b7af02621bbd602d865436db793443b7428ae996405", "P06"
    ),
    "content/modernization/p07_layered_learnset_contract.json": (
        16337, "ca17b3e33989d0ae105e5ac6ecc1c62ed27daae7ddc8d0a16632be64852842c5", "P07"
    ),
    "content/modernization/p07_runtime_handoff.json": (
        3301, "5e53baeac5a8c12e89bce9cda7a86da992b3519c34ca86c3cf53a830e5de6dac", "P07"
    ),
}

CANDIDATE_ARTIFACTS: Mapping[str, tuple[int, str, str | None]] = {
    "build/stages/62_npc_placement_integrity_repair.gba": (
        33554432, "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f", "73E4FB73"
    ),
    "build/stages/62_npc_placement_integrity_repair.json": (
        1471, "0bf888d394c852d0b1a5d04bbfc54c493ae9a192e511b08de6c9cabd2107e491", None
    ),
    "build/stages/63_modernization_p01_identity_repair.gba": (
        33554432, "6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd", "FB09EF2D"
    ),
    "build/stages/63_modernization_p01_identity_repair.json": (
        5585, "9e5b1d6de4074271b7da8631a0b1908dc631d368cb57e0269b70b9a41bc580cf", None
    ),
    "build/stages/64_modernization_p02_rayquaza_parameter_repair.gba": (
        33554432, "ddb9bf76d7f35c375d44941cd276f07e64501ed5cee34b8d448e76f0454095c3", "BCD9417F"
    ),
    "build/stages/64_modernization_p02_rayquaza_parameter_repair.json": (
        3741, "0f9948fc9484361fd8b38bec06592845a97e7a4cefd43f16f59a3b228666ed1e", None
    ),
    "build/patches/stage62-to-stage63-modernization-p01-identity-repair.bps": (
        47, "7b400a62944bb976d94afdee2983c48bcf4f4482010f881f18bf7924eab0f352", None
    ),
    "build/patches/firered-jpn-rev0-to-stage63-modernization-p01-identity-repair.bps": (
        16726235, "f6fa12ebdd68882a0ff08d1c344151d4b792eaa1dfde1a22f3b9241ccb4a8680", None
    ),
    "build/patches/stage63-to-stage64-modernization-p02-rayquaza-parameter-repair.bps": (
        35, "6b27b12ffb0d8eca1bfa119848d35abb0b172e177dac5769630cca56af5ec852", None
    ),
    "build/patches/firered-jpn-rev0-to-stage64-modernization-p02-rayquaza-parameter-repair.bps": (
        16726245, "6adfcadd0c64ccf24bfa687fc1265efe25e0b26224c59d9108e44d78fdf62edc", None
    ),
    "build/stages/65_modernization_p03_caterpie_slice.gba": (
        33554432, "116781c8be7cbd327ba7783ebdad9d9dda77554c33839eebed15ae6b065bb680", "7FB7F282"
    ),
    "build/stages/65_modernization_p03_caterpie_slice.json": (
        8362, "ad5210529a62cc42571fcc255f98f53d183b8c8419bf0effbb9e1ecaa262aa2c", None
    ),
    "build/stages/65_modernization_p03_allocation.json": (
        38800, "7393007cfb6ed0f5d6f9264b60f8b73c1fdd5454ce767b1cdfb7cf268c867e18", None
    ),
    "build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps": (
        63, "0959b62a6ef48bc2be05ed50c63ac742310a51d3295871f097098674140d76b6", None
    ),
    "build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps": (
        16726260, "5efba3ca37e3bbf3dbd3a128b2444eb8bc8f278e4ea14e0a8d0df09526f40211", None
    ),
    "build/stages/66_modernization_p03_bulk_learnsets.gba": (
        33554432, "0d92f5377b4ad1a2fa5cbf905f81b5b6162e16cdd09a12c65c4a342e73c5c97e", "808D5140"
    ),
    "build/stages/66_modernization_p03_bulk_learnsets.json": (
        7304, "c0d7f9e1c77005f5f3921f2d4316458291a1c2a79c71d5ad8f3fd2c74d789e45", None
    ),
    "build/stages/66_modernization_p03_allocation.json": (
        39372, "d454fdde5fbece67e5411895b929980a43d64bcfa99f8b947093f5db37b706cc", None
    ),
    "build/patches/stage65-to-stage66-modernization-p03-bulk-learnsets.bps": (
        86322, "6d3bd8f75b8603f00d0f729ae0fe8bbcedce515ecaaaeecc423d13e0f0e14ed0", None
    ),
    "build/patches/firered-jpn-rev0-to-stage66-modernization-p03-bulk-learnsets.bps": (
        16785814, "9a84725f6c52e200a2275507d1fe6655736cfe4e2fe277ab4ddcb05778baed19", None
    ),
    "build/stages/67_modernization_p02_p03_consumers.gba": (
        33554432, "13e4ecb6f2bc72eeb5d7ffb5b5e5a7a2ae2876391bf37ec93cb6548587265111", "D94758FF"
    ),
    "build/stages/67_modernization_p02_p03_consumers.json": (
        11007, "0172ee5b4abd6afe275a6767a92f483e48b828037d7a35350b9baee3e92592ef", None
    ),
    "build/stages/67_modernization_p03_allocation.json": (
        40521, "3fe8f763c4c35dcdf15c2bcd256af569ef064ac051110ce3ed73ec62b9dcdac8", None
    ),
    "build/patches/stage66-p02-overlay-to-stage67-modernization-p03-consumers.bps": (
        53100, "44df541453beb72fc2c803ec56a27ec395a333e0aec9d61a589630290bb3f7cb", None
    ),
    "build/patches/firered-jpn-rev0-to-stage67-modernization-p02-p03-consumers.bps": (
        16802522, "1e98d68b26bfb48516c9c3672f8c53d3bc7ec68d5cf3ae839f70d93d6bd6b8b3", None
    ),
}

PARALLEL_OUTPUTS = {
    "P02_ACTUAL_CONSUMER_ACCEPTANCE": {
        "status": "INTEGRATED_PARTIAL_ACCEPTANCE_NOT_P02_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p02_acceptance_gate.json",
            "content/modernization/p02_acceptance_checkpoint.json",
            "scripts/run_modernization_p02_acceptance.py",
            "tools/mgba_modernization_p02_acceptance_smoke.c",
            "tests/test_modernization_p02_acceptance.py",
        ],
    },
    "P03_STAGE65": {
        "status": "INTEGRATED_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage65.json",
            "content/modernization/p03_stage65_checkpoint.json",
            "content/modernization/p03_stage65_mgba_runtime_gate.json",
            "scripts/build_modernization_p03_stage65.py",
            "scripts/run_modernization_p03_stage65_mgba.py",
            "tests/test_modernization_p03_stage65.py",
            "tools/mgba_modernization_p03_stage65_smoke.c",
            "tools/modernization_p03_stage65.py",
        ],
    },
    "P03_STAGE66": {
        "status": "INTEGRATED_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage66.json",
            "content/modernization/p03_stage66_bulk_route_audit.json",
            "content/modernization/p03_stage66_change_audit.json",
            "content/modernization/p03_stage66_checkpoint.json",
            "content/modernization/p03_stage66_mgba_runtime_gate.json",
            "scripts/build_modernization_p03_stage66.py",
            "scripts/run_modernization_p03_stage66_mgba.py",
            "tests/test_modernization_p03_stage66.py",
            "tools/mgba_modernization_p03_stage66_smoke.c",
            "tools/modernization_p03_stage66.py",
        ],
    },
    "P03_STAGE67": {
        "status": "INTEGRATED_CONSUMER_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage67.json",
            "content/modernization/p03_stage67_consumer_route_audit.json",
            "content/modernization/p03_stage67_change_audit.json",
            "content/modernization/p03_stage67_checkpoint.json",
            "content/modernization/p03_stage67_mgba_runtime_gate.json",
            "scripts/build_modernization_p03_stage67.py",
            "scripts/run_modernization_p03_stage67_mgba.py",
            "tests/test_modernization_p03_stage67.py",
            "tools/modernization_p03_stage67.py",
            "tools/mgba_modernization_p03_stage67_smoke.c",
        ],
    },
    "P04_ASSET_IMPORTER": {
        "status": "INTEGRATED_STAGING_ONLY_NOT_ROM_READY",
        "included": True,
        "expected_paths": [
            "content/modernization/p04_asset_import_manifest.json",
            "scripts/build_modernization_p04_assets.py",
            "tests/test_modernization_p04_asset_importer.py",
            "tools/modernization_p04_asset_importer.py",
        ],
    },
    "P04_CAPACITY_RESERVATION": {
        "status": "INTEGRATED_CHECKPOINT_NOT_RUNTIME_READY",
        "included": True,
        "expected_paths": [
            "content/modernization/p04_capacity_allocation_manifest.json",
            "scripts/build_modernization_p04_capacity.py",
            "tests/test_modernization_p04_capacity.py",
            "tools/modernization_p04_capacity.py",
        ],
    },
    "P05_ABILITY_HOST_RUNTIME": {
        "status": "HOST_RUNTIME_VERIFIED_ROM_LINK_PENDING",
        "included": True,
        "expected_paths": [
            "config/modernization_p05_ability_runtime.json",
            "content/modernization/p05_ability_runtime_checkpoint.json",
            "overlays/modernization_p05_abilities/modernization_p05_abilities.h",
            "overlays/modernization_p05_abilities/modernization_p05_abilities.c",
            "overlays/modernization_p05_abilities/modernization_p05_abilities_fixture.c",
            "scripts/build_modernization_p05_ability_runtime.py",
            "tools/modernization_p05_ability_runtime.py",
            "tests/test_modernization_p05_ability_runtime.py",
        ],
    },
}

# 生成済みJSONだけでなく、それを作る実装とfocused testもsnapshotへ含める。
# hashはbuild時に実ファイルから計算し、tracked P08 outputとのbyte比較でdriftを
# 検出する。ここへglobを使うと後発ファイルを暗黙採用するため、pathは明示する。
PINNED_IMPLEMENTATION_PATHS: Mapping[str, str] = {
    "config/modernization_p01_runtime.json": "P01",
    "scripts/audit_modernization_p01_rom.py": "P01",
    "scripts/build_modernization_identity.py": "P01",
    "scripts/build_modernization_p01.py": "P01",
    "scripts/run_modernization_p01_mgba.py": "P01",
    "tools/modernization_capacity.py": "P01",
    "tools/modernization_identity.py": "P01",
    "tests/test_modernization_consumer_identity.py": "P01",
    "tests/test_modernization_identity.py": "P01",
    "tests/test_modernization_p01.py": "P01",
    "tests/test_modernization_p01_rom.py": "P01",
    "scripts/build_modernization_p02.py": "P02",
    "config/modernization_p02_mgba_gate.json": "P02",
    "config/modernization_p02_stage64.json": "P02",
    "scripts/build_modernization_p02_stage64.py": "P02",
    "scripts/run_modernization_p02_mgba.py": "P02",
    "tools/modernization_evolution.py": "P02",
    "tools/mgba_modernization_p02_evolution_smoke.c": "P02",
    "tests/test_modernization_p02.py": "P02",
    "tests/test_modernization_p02_mgba.py": "P02",
    "tests/test_modernization_p02_species_surface_policy.py": "P02",
    "tests/test_modernization_p02_stage64.py": "P02",
    "scripts/run_modernization_p02_acceptance.py": "P02",
    "tools/mgba_modernization_p02_acceptance_smoke.c": "P02",
    "tests/test_modernization_p02_acceptance.py": "P02",
    "scripts/build_modernization_p03.py": "P03",
    "config/modernization_p03_stage65.json": "P03",
    "scripts/build_modernization_p03_stage65.py": "P03",
    "scripts/run_modernization_p03_stage65_mgba.py": "P03",
    "tools/modernization_learnsets.py": "P03",
    "tools/modernization_p03_stage65.py": "P03",
    "tools/mgba_modernization_p03_stage65_smoke.c": "P03",
    "tests/test_modernization_p03.py": "P03",
    "tests/test_modernization_p03_stage65.py": "P03",
    "scripts/build_modernization_p03_stage66.py": "P03",
    "scripts/run_modernization_p03_stage66_mgba.py": "P03",
    "tools/modernization_p03_stage66.py": "P03",
    "tools/mgba_modernization_p03_stage66_smoke.c": "P03",
    "tests/test_modernization_p03_stage66.py": "P03",
    "scripts/build_modernization_p03_stage67.py": "P03",
    "scripts/run_modernization_p03_stage67_mgba.py": "P03",
    "tools/modernization_p03_stage67.py": "P03",
    "tools/mgba_modernization_p03_stage67_smoke.c": "P03",
    "tests/test_modernization_p03_stage67.py": "P03",
    "scripts/build_modernization_p04_assets.py": "P04",
    "scripts/build_modernization_p04_capacity.py": "P04",
    "scripts/build_modernization_p04_sources.py": "P04",
    "scripts/github_private_environment.py": "P04",
    "tools/modernization_p04_asset_importer.py": "P04",
    "tools/modernization_p04_capacity.py": "P04",
    "tools/modernization_p04_sources.py": "P04",
    "config/github_private_environment.json": "P04",
    "tests/test_github_private_environment.py": "P04",
    "tests/test_modernization_p04_asset_importer.py": "P04",
    "tests/test_modernization_p04_capacity.py": "P04",
    "tests/test_modernization_p04_sources.py": "P04",
    "scripts/build_modernization_p05.py": "P05",
    "tools/modernization_p05_contract.py": "P05",
    "tests/test_modernization_p05.py": "P05",
    "scripts/build_modernization_p05_ability_runtime.py": "P05",
    "tools/modernization_p05_ability_runtime.py": "P05",
    "tests/test_modernization_p05_ability_runtime.py": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities.h": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities.c": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities_fixture.c": "P05",
    "scripts/build_modernization_p06.py": "P06",
    "tools/modernization_p06_species.py": "P06",
    "tests/test_modernization_p06.py": "P06",
    "scripts/build_modernization_p07.py": "P07",
    "tools/modernization_p07_learnsets.py": "P07",
    "tests/test_modernization_p07.py": "P07",
    "scripts/build_modernization_p08.py": "P08",
    "scripts/run_github_private_suite.py": "P08",
    "tools/modernization_p08_integration.py": "P08",
    "tests/test_modernization_p08.py": "P08",
    "tests/test_run_github_private_suite.py": "P08",
    "scripts/build_trainer_v5_stage32.py": "SHARED",
    "tools/rom_allocator.py": "SHARED",
    "tools/release/__init__.py": "SHARED",
    "tools/release/bps.py": "SHARED",
    "Makefile": "CI",
    ".github/workflows/private-runtime.yml": "CI",
    ".github/workflows/chatgpt-comment-control.yml": "CI",
    "infra/setup_github_actions.sh": "CI",
    "infra/toolchain_manifest.json": "CI",
}

DECLARED_EVIDENCE_SOURCE_GROUPS: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "P02_STAGE64_MGBA": (
        "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ("inputs", "sources"),
    ),
    "P02_ACTUAL_CONSUMER_ACCEPTANCE": (
        "content/modernization/p02_acceptance_checkpoint.json",
        ("inputs", "sources"),
    ),
    "P03_RUNTIME_HANDOFF": (
        "content/modernization/p03_runtime_handoff.json",
        ("connection_points", "source_files"),
    ),
    "P03_STAGE67_MGBA": (
        "content/modernization/p03_stage67_mgba_runtime_gate.json",
        ("inputs", "sources"),
    ),
    "P05_ABILITY_IMPLEMENTATION": (
        "content/modernization/p05_ability_runtime_checkpoint.json",
        ("implementation", "files"),
    ),
}
DECLARED_EVIDENCE_IDENTITY_GROUPS: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "P02_MGBA_CONFIG": (
        "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ("inputs", "config"),
    ),
    "P02_STAGE64_BUILDER_CONFIG": (
        "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ("inputs", "stage64_generation", "builder_config"),
    ),
}
EXPECTED_EVIDENCE_SOURCE_COUNTS: Mapping[str, int] = {
    "P02_STAGE64_MGBA": 4,
    "P02_ACTUAL_CONSUMER_ACCEPTANCE": 4,
    "P03_RUNTIME_HANDOFF": 7,
    "P03_STAGE67_MGBA": 9,
    "P05_ABILITY_IMPLEMENTATION": 3,
    "P02_MGBA_CONFIG": 1,
    "P02_STAGE64_BUILDER_CONFIG": 1,
}


class ModernizationP08Error(ValueError):
    """統合入力、完了境界、候補継承、またはrelease判定の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP08Error(message)


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_relative(path: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or str(pure) != path:
        _fail(f"固定入力pathが安全な相対pathではありません: {path!r}")


def verify_exact_bytes(
    label: str, raw: bytes, expected_size: int, expected_sha256: str
) -> dict[str, Any]:
    """size/hash driftをfail closedで検出する小さな共通primitive。"""

    digest = _sha256(raw)
    if len(raw) != expected_size or digest != expected_sha256:
        _fail(
            f"{label} identity drift: size={len(raw)} sha256={digest}; "
            f"expected size={expected_size} sha256={expected_sha256}"
        )
    return {"path": label, "size": len(raw), "sha256": digest}


def _regular_bytes(root: Path, relative: str) -> bytes:
    _safe_relative(relative)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"固定入力が通常ファイルではありません: {relative}")
    return path.read_bytes()


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}がUTF-8 JSONではありません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label}のrootがobjectではありません")
    return value


def _tracked_paths(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        _fail(f"tracked input一覧を取得できません: {error}")
    return {
        item.decode("utf-8")
        for item in result.stdout.split(b"\0") if item
    }


def _audit_inputs(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], set[str]]:
    tracked = _tracked_paths(root)
    required = set(PINNED_TRACKED_INPUTS)
    missing_tracking = sorted(required - tracked)
    if missing_tracking:
        _fail(f"固定入力がGit trackingから外れています: {missing_tracking}")
    documents: dict[str, dict[str, Any]] = {}
    identities: list[dict[str, Any]] = []
    for relative, (size, digest, phase) in PINNED_TRACKED_INPUTS.items():
        raw = _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, size, digest)
        identity["phase"] = phase
        identities.append(identity)
        if relative.endswith(".json"):
            documents[relative] = _json(raw, relative)
    return documents, identities, tracked


def _audit_candidate_artifacts(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    identities: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    for relative, (size, digest, expected_crc) in CANDIDATE_ARTIFACTS.items():
        raw = _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, size, digest)
        if expected_crc is not None:
            actual_crc = f"{binascii.crc32(raw) & 0xFFFFFFFF:08X}"
            if actual_crc != expected_crc:
                _fail(f"{relative} CRC32 drift: {actual_crc} != {expected_crc}")
            identity["crc32"] = actual_crc
        identities.append(identity)
        if relative.endswith(".json"):
            documents[relative] = _json(raw, relative)
    return {"artifacts": identities}, documents


def _require(value: bool, message: str) -> None:
    if not value:
        _fail(message)


def validate_active_baseline(
    active: Mapping[str, Any], active_markdown: bytes, stage62_identity: Mapping[str, Any]
) -> dict[str, Any]:
    expected_sha = CANDIDATE_ARTIFACTS[
        "build/stages/62_npc_placement_integrity_repair.gba"
    ][1]
    rom = active.get("rom")
    _require(active.get("status") == "ACTIVE", "active baseline statusがACTIVEではありません")
    _require(active.get("stage") == 62, "active baselineをStage62から変更しています")
    _require(isinstance(rom, Mapping), "active baseline ROM identityがありません")
    _require(rom.get("path") == stage62_identity.get("path"), "active baseline ROM path不一致")
    _require(rom.get("size") == stage62_identity.get("size"), "active baseline ROM size不一致")
    _require(rom.get("sha256") == expected_sha == stage62_identity.get("sha256"), "active baseline ROM hash不一致")
    _require(rom.get("crc32") == stage62_identity.get("crc32") == "73E4FB73", "active baseline ROM CRC32不一致")
    try:
        markdown = active_markdown.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"active baseline文書がUTF-8ではありません: {error}")
    _require("Stage62" in markdown and expected_sha in markdown, "人向けactive baseline文書がStage62 identityと不一致")
    return {
        "stage": 62,
        "config_path": "config/active_play_baseline.json",
        "config_sha256": PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1],
        "documentation_path": "design/active_play_baseline.md",
        "documentation_sha256": PINNED_TRACKED_INPUTS["design/active_play_baseline.md"][1],
        "rom": dict(stage62_identity),
        "changed": False,
        "candidate_auto_promoted": False,
    }


def _identity_by_path(items: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item["path"]): item for item in items}


def _validate_candidate_chain(
    artifact_audit: Mapping[str, Any], metadata: Mapping[str, Mapping[str, Any]],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    by_path = _identity_by_path(artifact_audit["artifacts"])
    s62 = by_path["build/stages/62_npc_placement_integrity_repair.gba"]
    s63 = by_path["build/stages/63_modernization_p01_identity_repair.gba"]
    s64 = by_path["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"]
    s65 = by_path["build/stages/65_modernization_p03_caterpie_slice.gba"]
    s66 = by_path["build/stages/66_modernization_p03_bulk_learnsets.gba"]
    s67 = by_path["build/stages/67_modernization_p02_p03_consumers.gba"]
    m63 = metadata["build/stages/63_modernization_p01_identity_repair.json"]
    m64 = metadata["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"]
    m65 = metadata["build/stages/65_modernization_p03_caterpie_slice.json"]
    m66 = metadata["build/stages/66_modernization_p03_bulk_learnsets.json"]
    m67 = metadata["build/stages/67_modernization_p02_p03_consumers.json"]
    a67 = metadata["build/stages/67_modernization_p03_allocation.json"]
    _require(m63.get("task") == "USER-MODERNIZATION-P01" and m63.get("status") == "PASS", "Stage63 metadata identity不正")
    _require(m63.get("stage") == 63 and m63.get("scope", {}).get("active_play_baseline_changed") is False, "Stage63 scope不正")
    _require(m63.get("input", {}).get("parent", {}).get("sha256") == s62["sha256"], "Stage63親がStage62ではありません")
    _require(m63.get("output", {}).get("sha256") == s63["sha256"], "Stage63出力hash不一致")
    _require(
        m63.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage62-to-stage63-modernization-p01-identity-repair.bps"]["sha256"]
        and m63.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage63-modernization-p01-identity-repair.bps"]["sha256"]
        and m63.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m63.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage63 BPS identity/round-trip evidence不一致",
    )
    _require(m64.get("task") == "USER-MODERNIZATION-P02-RAYQUAZA" and m64.get("status") == "CHECKPOINT", "Stage64 metadata identity不正")
    _require(m64.get("stage") == 64 and m64.get("done") is False, "Stage64をDONEと誤認しています")
    _require(m64.get("scope", {}).get("active_play_baseline_changed") is False, "Stage64がactive baselineを変更しています")
    _require(m64.get("input", {}).get("parent_rom", {}).get("sha256") == s63["sha256"], "Stage64親ROMがStage63ではありません")
    _require(
        m64.get("input", {}).get("parent_metadata", {}).get("sha256")
        == by_path["build/stages/63_modernization_p01_identity_repair.json"]["sha256"],
        "Stage64親metadataがStage63ではありません",
    )
    _require(m64.get("output", {}).get("sha256") == s64["sha256"], "Stage64出力hash不一致")
    _require(
        m64.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage63-to-stage64-modernization-p02-rayquaza-parameter-repair.bps"]["sha256"]
        and m64.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage64-modernization-p02-rayquaza-parameter-repair.bps"]["sha256"]
        and m64.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m64.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage64 BPS identity/round-trip evidence不一致",
    )
    _require(m64.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_DONE", "Stage64 completion境界不正")
    _require(
        m65.get("task") == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and m65.get("status") == "CHECKPOINT" and m65.get("done") is False,
        "Stage65 metadata identity/DONE境界不正",
    )
    _require(
        m65.get("stage") == 65
        and m65.get("scope", {}).get("active_play_baseline_changed") is False
        and m65.get("scope", {}).get("all_p03_routes_implemented") is False,
        "Stage65 scope境界不正",
    )
    _require(
        m65.get("input", {}).get("parent_rom", {}).get("sha256") == s64["sha256"]
        and m65.get("input", {}).get("parent_metadata", {}).get("sha256")
        == by_path["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"]["sha256"],
        "Stage65親がStage64 exact artifactではありません",
    )
    _require(m65.get("output", {}).get("sha256") == s65["sha256"], "Stage65出力hash不一致")
    _require(
        m65.get("allocation", {}).get("sha256")
        == by_path["build/stages/65_modernization_p03_allocation.json"]["sha256"],
        "Stage65 allocation hash接続不一致",
    )
    _require(
        m65.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps"]["sha256"]
        and m65.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps"]["sha256"]
        and m65.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m65.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage65 BPS identity/round-trip evidence不一致",
    )
    _require(
        m65.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_P03_DONE",
        "Stage65をP03 DONEと誤認しています",
    )
    _require(
        m66.get("task")
        == "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT"
        and m66.get("status") == "CHECKPOINT" and m66.get("done") is False,
        "Stage66 metadata identity/DONE境界不正",
    )
    _require(
        m66.get("stage") == 66
        and m66.get("scope", {}).get("active_play_baseline_changed") is False
        and m66.get("scope", {}).get("all_p03_routes_implemented") is False
        and m66.get("scope", {}).get("routes_materialized_by_this_checkpoint") == 47548
        and m66.get("scope", {}).get("routes_not_materialized_by_this_checkpoint") == 70980,
        "Stage66 scope境界不正",
    )
    _require(
        m66.get("input", {}).get("parent_rom", {}).get("sha256") == s65["sha256"]
        and m66.get("input", {}).get("parent_metadata", {}).get("sha256")
        == by_path["build/stages/65_modernization_p03_caterpie_slice.json"]["sha256"],
        "Stage66親がStage65 exact artifactではありません",
    )
    _require(m66.get("output", {}).get("sha256") == s66["sha256"], "Stage66出力hash不一致")
    _require(
        m66.get("input", {}).get("mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_mgba_runtime_gate.json"][1]
        and m66.get("route_audit", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_bulk_route_audit.json"][1]
        and m66.get("change_audit", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_change_audit.json"][1],
        "Stage66 metadataのgate/audit hash接続不一致",
    )
    _require(
        m66.get("allocation", {}).get("sha256")
        == by_path["build/stages/66_modernization_p03_allocation.json"]["sha256"],
        "Stage66 allocation hash接続不一致",
    )
    _require(
        m66.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path["build/patches/stage65-to-stage66-modernization-p03-bulk-learnsets.bps"]["sha256"]
        and m66.get("bps", {}).get("clean", {}).get("sha256")
        == by_path["build/patches/firered-jpn-rev0-to-stage66-modernization-p03-bulk-learnsets.bps"]["sha256"]
        and m66.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m66.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage66 BPS identity/round-trip evidence不一致",
    )
    _require(
        m66.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_P03_DONE",
        "Stage66をP03 DONEと誤認しています",
    )
    _require(
        m67.get("task")
        == "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        and m67.get("stage") == 67
        and m67.get("status") == "CHECKPOINT"
        and m67.get("done") is False
        and m67.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE",
        "Stage67 metadata identity/DONE境界不正",
    )
    scope67 = m67.get("scope", {})
    _require(
        scope67.get("source_routes") == 118528
        and scope67.get("selected_routes") == 118369
        and scope67.get("non_adopted_move_1063_routes") == 159
        and scope67.get("stage67_new_materialized_routes") == 3603
        and scope67.get("cumulative_materialized_routes") == 51151
        and scope67.get("selected_routes_deferred") == 67218
        and scope67.get("move_1063_implemented_or_replaced") is False
        and scope67.get("all_p03_routes_implemented") is False,
        "Stage67 route partition/completion境界不正",
    )
    _require(
        m67.get("input", {}).get("stage66_rom", {}).get("sha256") == s66["sha256"]
        and m67.get("input", {}).get("p02_overlay_parent", {}).get("sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and m67.get("input", {}).get("p02_overlay_parent", {}).get(
            "changed_bytes_from_stage66"
        ) == 60,
        "Stage67 parent/P02 overlay hash接続不一致",
    )
    _require(m67.get("output", {}).get("sha256") == s67["sha256"], "Stage67出力hash不一致")
    _require(
        m67.get("allocation", {}).get("sha256")
        == by_path["build/stages/67_modernization_p03_allocation.json"]["sha256"],
        "Stage67 allocation hash接続不一致",
    )
    _require(
        m67.get("bps", {}).get("incremental", {}).get("sha256")
        == by_path[
            "build/patches/stage66-p02-overlay-to-stage67-modernization-p03-consumers.bps"
        ]["sha256"]
        and m67.get("bps", {}).get("incremental", {}).get("source_sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and m67.get("bps", {}).get("incremental", {}).get("round_trip") is True
        and m67.get("bps", {}).get("clean", {}).get("sha256")
        == by_path[
            "build/patches/firered-jpn-rev0-to-stage67-modernization-p02-p03-consumers.bps"
        ]["sha256"]
        and m67.get("bps", {}).get("clean", {}).get("round_trip") is True,
        "Stage67 BPS identity/round-trip evidence不一致",
    )
    future_tail_allocations = [
        row for row in a67.get("allocations", []) if row.get("region") == "future_tail"
    ]
    future_tail_end = max(
        (row.get("end_exclusive", 0) for row in future_tail_allocations), default=0
    )
    _require(
        a67.get("schema_version") == 1
        and a67.get("summaries", {}).get("overlap_count") == 0
        and future_tail_end == 33491922
        and 33554432 - future_tail_end == 62510,
        "Stage67 allocation future_tail残量/overlap境界不正",
    )
    # 累積candidate registryでは「最後に完了した工程」と「最後のcheckpoint」を
    # 別フィールドとして扱う。checkpointed_through=P03をP03 DONEへ昇格させない。
    _require(
        registry.get("schema_version") == 2
        and registry.get("status") == "P03_STAGE67_CONSUMERS_VERIFIED_CHECKPOINT"
        and registry.get("completed_through") == "USER-MODERNIZATION-P01"
        and registry.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        and registry.get("source", {}).get("stage67_checkpoint_commit")
        == "b4bdb67fcb9c49414661b2c591e0b1d9464aeafe"
        and registry.get("release_ready") is False
        and registry.get("active_play_baseline_changed") is False,
        "candidate v2 registryの完了/checkpoint/release境界不正",
    )
    _require(
        registry.get("active_parent", {}).get("stage") == 62
        and registry.get("active_parent", {}).get("sha256") == s62["sha256"]
        and registry.get("parent", {}).get("stage") == 66
        and registry.get("parent", {}).get("sha256") == s66["sha256"]
        and registry.get("candidate", {}).get("stage") == 67
        and registry.get("candidate", {}).get("sha256") == s67["sha256"]
        and registry.get("p02_overlay_parent", {}).get("sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and registry.get("p02_overlay_parent", {}).get("changed_bytes_from_stage66")
        == 60,
        "candidate v2 Stage67 parent/overlay/candidate identity不正",
    )
    _require(
        registry.get("adopted_delta", {}).get("p04_adoption_scope") == {
            "mega_species_and_forms": 49,
            "new_normal_species": 0,
            "mega_stones": 45,
            "new_abilities": 6,
            "winds_waves_user_non_adopted_species": 3,
            "held_pikachu_appearance_candidates": 2,
            "private_asset_files_ready": 670,
            "rom_materialized": False,
        },
        "candidate v2 P04 49 Mega採用/Winds・Waves非採用scope不正",
    )
    return {
        "active_stage": 62,
        "selected_checkpoint_stage": 67,
        "selection": "HIGHEST_EXPLICITLY_PINNED_CANDIDATE_NOT_ACTIVE_BASELINE",
        "registry": {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "P03_STAGE67_CONSUMERS_VERIFIED_CHECKPOINT",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT",
            "checkpoint_commit": "b4bdb67fcb9c49414661b2c591e0b1d9464aeafe",
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 66,
            "candidate_stage": 67,
        },
        "inheritance": [
            {"stage": 62, "role": "ACTIVE_PLAY_BASELINE", "rom": dict(s62)},
            {"stage": 63, "role": "P01_COMPLETED_CANDIDATE", "parent_stage": 62, "rom": dict(s63)},
            {"stage": 64, "role": "P02_CHECKPOINT_NOT_DONE", "parent_stage": 63, "rom": dict(s64)},
            {"stage": 65, "role": "P03_INTEGRATED_CHECKPOINT_NOT_DONE", "parent_stage": 64, "rom": dict(s65)},
            {"stage": 66, "role": "P03_BULK_CHECKPOINT_NOT_DONE", "parent_stage": 65, "rom": dict(s66)},
            {"stage": 67, "role": "P02_P03_CONSUMER_CHECKPOINT_NOT_DONE", "parent_stage": 66, "parent_overlay_sha256": "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb", "rom": dict(s67)},
        ],
        "parent_chain_verified": True,
        "stage65_integrated": True,
        "stage65_scope": {
            "representative_species": 1,
            "routes_materialized": 4,
            "routes_remaining": 118524,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "stage66_integrated": True,
        "stage66_scope": {
            "corrected_targets": 1300,
            "source_routes_validated": 118528,
            "routes_materialized": 47548,
            "routes_remaining": 70980,
            "level_up_routes_materialized": 18515,
            "machine_existing_slot_routes_materialized": 29033,
            "machine_supply_required_routes_deferred": 26347,
            "move_1063_routes_deferred": 159,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "stage67_integrated": True,
        "stage67_scope": {
            "source_routes": 118528,
            "selected_routes": 118369,
            "non_adopted_move_1063_routes": 159,
            "stage67_new_materialized_routes": 3603,
            "cumulative_materialized_routes": 51151,
            "selected_routes_remaining": 67218,
            "evolution_routes_materialized": 341,
            "tutor_existing_slot_routes_materialized": 740,
            "normal_egg_routes_materialized": 2522,
            "p02_overlay_changed_bytes": 60,
            "stage67_changed_bytes_from_overlay": 46455,
            "future_tail_remaining_bytes": 62510,
            "consumers_exercised": ["evolution", "tutor", "egg"],
            "full_p03_done": False,
        },
        "release_candidate": False,
    }


def _nested_value(
    document: Mapping[str, Any], keys: Sequence[str], label: str,
) -> Any:
    value: Any = document
    for key in keys:
        if not isinstance(value, Mapping) or key not in value:
            _fail(f"{label} source bindingがありません: {'.'.join(keys)}")
        value = value[key]
    return value


def _nested_rows(
    document: Mapping[str, Any], keys: Sequence[str], label: str,
) -> list[Any]:
    value = _nested_value(document, keys, label)
    if not isinstance(value, list) or not value:
        _fail(f"{label} source bindingが空です")
    return value


def audit_declared_source_rows(
    root: Path,
    rows: Sequence[Any],
    tracked: set[str],
    *,
    binding: str,
) -> list[dict[str, Any]]:
    """Evidence内の宣言size/hashを現行tracked sourceへ再照合する。"""

    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _fail(f"{binding} source binding rowがobjectではありません")
        relative = row.get("path")
        if not isinstance(relative, str) or relative not in tracked:
            _fail(f"{binding} sourceがtrackedではありません: {relative!r}")
        identity = verify_exact_bytes(
            relative, _regular_bytes(root, relative), row.get("size"), row.get("sha256")
        )
        identity["binding"] = binding
        identity["status"] = "PASS"
        result.append(identity)
    return result


def _audit_declared_source_bindings(
    root: Path,
    documents: Mapping[str, Mapping[str, Any]],
    tracked: set[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for binding, (relative, keys) in DECLARED_EVIDENCE_SOURCE_GROUPS.items():
        result.extend(
            audit_declared_source_rows(
                root,
                _nested_rows(documents[relative], keys, binding),
                tracked,
                binding=binding,
            )
        )
    for binding, (relative, keys) in DECLARED_EVIDENCE_IDENTITY_GROUPS.items():
        row = _nested_value(documents[relative], keys, binding)
        result.extend(
            audit_declared_source_rows(
                root, [row], tracked, binding=binding,
            )
        )
    return result


def _audit_implementation_inputs(
    root: Path, tracked: set[str],
) -> list[dict[str, Any]]:
    missing = sorted(set(PINNED_IMPLEMENTATION_PATHS) - tracked)
    if missing:
        _fail(f"固定implementation sourceがGit trackingから外れています: {missing}")
    result: list[dict[str, Any]] = []
    for relative, phase in PINNED_IMPLEMENTATION_PATHS.items():
        raw = _regular_bytes(root, relative)
        result.append(
            {
                "path": relative,
                "size": len(raw),
                "sha256": _sha256(raw),
                "phase": phase,
            }
        )
    return result


def build_integration_fingerprint(
    tracked_inputs: Sequence[Mapping[str, Any]],
    implementation_inputs: Sequence[Mapping[str, Any]],
    referenced_source_bindings: Sequence[Mapping[str, Any]],
    candidate_artifacts: Sequence[Mapping[str, Any]],
    phases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """自己循環なしでP08の全入力・semantic境界を束ねる指紋を返す。"""

    phase_projection = [
        {
            key: row.get(key)
            for key in (
                "phase",
                "completion_state",
                "contract_statuses",
                "adoption",
                "not_adopted",
                "rom_reflection",
                "required_gates",
                "blockers",
            )
        }
        for row in phases
    ]
    component_values: tuple[tuple[str, Sequence[Mapping[str, Any]]], ...] = (
        ("tracked_inputs", tracked_inputs),
        ("implementation_inputs", implementation_inputs),
        ("referenced_source_bindings", referenced_source_bindings),
        ("candidate_artifacts", candidate_artifacts),
        ("phase_projection", phase_projection),
    )
    components = {
        name: {
            "count": len(rows),
            "sha256": _sha256(stable_json(rows)),
        }
        for name, rows in component_values
    }
    return {
        "algorithm": "SHA256_STABLE_JSON_COMPONENTS_V1",
        "components": components,
        "sha256": _sha256(stable_json(components)),
    }


def _validate_contract_chain(documents: Mapping[str, Mapping[str, Any]]) -> None:
    active_hash = PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1]
    p01_inputs = documents["config/modernization_inputs.json"]
    p01_candidate = documents["config/modernization_candidate.json"]
    decisions = documents["config/modernization_adoption_decisions.json"]
    p02_checkpoint = documents["content/modernization/p02_stage64_checkpoint.json"]
    p02_mgba = documents["content/modernization/p02_stage64_mgba_runtime_gate.json"]
    p02_acceptance = documents["content/modernization/p02_acceptance_checkpoint.json"]
    p03 = documents["content/modernization/p03_learnset_contract.json"]
    p03_stage65_config = documents["config/modernization_p03_stage65.json"]
    p03_stage65 = documents["content/modernization/p03_stage65_checkpoint.json"]
    p03_stage65_mgba = documents["content/modernization/p03_stage65_mgba_runtime_gate.json"]
    p03_stage66_config = documents["config/modernization_p03_stage66.json"]
    p03_stage66_routes = documents[
        "content/modernization/p03_stage66_bulk_route_audit.json"
    ]
    p03_stage66_changes = documents[
        "content/modernization/p03_stage66_change_audit.json"
    ]
    p03_stage66 = documents["content/modernization/p03_stage66_checkpoint.json"]
    p03_stage66_mgba = documents[
        "content/modernization/p03_stage66_mgba_runtime_gate.json"
    ]
    p03_stage67_config = documents["config/modernization_p03_stage67.json"]
    p03_stage67_routes = documents[
        "content/modernization/p03_stage67_consumer_route_audit.json"
    ]
    p03_stage67_changes = documents[
        "content/modernization/p03_stage67_change_audit.json"
    ]
    p03_stage67 = documents["content/modernization/p03_stage67_checkpoint.json"]
    p03_stage67_mgba = documents[
        "content/modernization/p03_stage67_mgba_runtime_gate.json"
    ]
    p04_manifest = documents["content/modernization/p04_candidate_manifest.json"]
    p04_official = documents["content/modernization/p04_official_sources.json"]
    p04_assets = documents["content/modernization/p04_asset_sources.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p04_capacity = documents[
        "content/modernization/p04_capacity_allocation_manifest.json"
    ]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p05_plan = documents["content/modernization/p05_data_only_patch_plan.json"]
    p05_runtime = documents["content/modernization/p05_runtime_handoff.json"]
    p05_ability = documents["content/modernization/p05_ability_runtime_checkpoint.json"]
    p06 = documents["content/modernization/p06_species_adjustment_contract.json"]
    p07 = documents["content/modernization/p07_layered_learnset_contract.json"]
    p07_runtime = documents["content/modernization/p07_runtime_handoff.json"]

    _require(
        p01_inputs.get("active_parent", {}).get("identity_source_sha256") == active_hash,
        "P01 inputs→active baseline hash接続が不一致です",
    )
    side_decision = decisions.get("decisions", {}).get("MOVE_KEY_ALLYSWITCH", {})
    _require(
        side_decision.get("decision") == "NOT_ADOPTED"
        and side_decision.get("requested_project_id") == 1063
        and side_decision.get("source_route_count") == 159
        and side_decision.get("route_action")
        == "EXCLUDE_FROM_ALL_LEARNSET_CONSUMERS"
        and side_decision.get("runtime_action") == "DO_NOT_IMPLEMENT_OR_ALLOCATE"
        and side_decision.get("replacement_move_key") is None,
        "Side Change非採用判断が明示境界と一致しません",
    )
    _require(
        p01_candidate.get("schema_version") == 2
        and p01_candidate.get("status") == "P03_STAGE67_CONSUMERS_VERIFIED_CHECKPOINT"
        and p01_candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and p01_candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        and p01_candidate.get("release_ready") is False
        and p01_candidate.get("active_play_baseline_changed") is False,
        "candidate v2のP01完了/P03 checkpoint/release境界不正",
    )
    _require(
        p01_candidate.get("active_parent", {}).get("stage") == 62
        and p01_candidate.get("active_parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/62_npc_placement_integrity_repair.gba"][1]
        and p01_candidate.get("active_parent", {}).get("promotion_status")
        == "UNCHANGED_NOT_PROMOTED",
        "candidate v2 active_parentがStage62 exact identityではありません",
    )
    _require(
        p01_candidate.get("parent", {}).get("stage") == 66
        and p01_candidate.get("parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.gba"][1]
        and p01_candidate.get("parent", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.json"][1],
        "candidate v2 parentがStage66 exact identityではありません",
    )
    _require(
        p01_candidate.get("candidate", {}).get("stage") == 67
        and p01_candidate.get("candidate", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/67_modernization_p02_p03_consumers.gba"][1]
        and p01_candidate.get("candidate", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/67_modernization_p02_p03_consumers.json"][1]
        and p01_candidate.get("candidate", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/67_modernization_p03_allocation.json"][1],
        "candidate v2 candidateがStage67 exact identityではありません",
    )
    _require(
        p01_candidate.get("patches", {}).get("from_parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage66-p02-overlay-to-stage67-modernization-p03-consumers.bps"][1]
        and p01_candidate.get("patches", {}).get("from_parent", {}).get("round_trip") is True
        and p01_candidate.get("patches", {}).get("from_parent", {}).get("source_sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and p01_candidate.get("patches", {}).get("from_clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/firered-jpn-rev0-to-stage67-modernization-p02-p03-consumers.bps"][1]
        and p01_candidate.get("patches", {}).get("from_clean", {}).get("round_trip") is True,
        "candidate v2 Stage67 BPS identity/round-trip不正",
    )
    expected_stage_chain = [
        (63, "USER-MODERNIZATION-P01", "COMPLETED", 10,
         CANDIDATE_ARTIFACTS["build/stages/63_modernization_p01_identity_repair.gba"][1]),
        (64, "USER-MODERNIZATION-P02-RAYQUAZA", "CHECKPOINT_NOT_DONE", 2,
         CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"][1]),
        (65, "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE", "CHECKPOINT_NOT_P03_DONE", 17,
         CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]),
        (66, "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT", "CHECKPOINT_NOT_P03_DONE", 81693,
         CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.gba"][1]),
        (67, "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT", "CHECKPOINT_NOT_P03_DONE", 46515,
         CANDIDATE_ARTIFACTS["build/stages/67_modernization_p02_p03_consumers.gba"][1]),
    ]
    stage_chain = p01_candidate.get("stage_chain")
    _require(isinstance(stage_chain, list) and len(stage_chain) == 5, "candidate v2 stage_chain件数不正")
    for row, (stage, task, state, changed, digest) in zip(stage_chain, expected_stage_chain):
        _require(
            row.get("stage") == stage and row.get("task") == task
            and row.get("state") == state and row.get("changed_bytes_from_parent") == changed
            and row.get("sha256") == digest,
            f"candidate v2 stage_chain不正: Stage{stage}",
        )
    _require(
        p02_checkpoint.get("input", {}).get("p02_static_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_evolution_contract.json"][1]
        and p02_checkpoint.get("input", {}).get("p02_mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_stage64_mgba_runtime_gate.json"][1],
        "P02 checkpointのcontract/gate hash接続が不一致です",
    )
    _require(
        p02_mgba.get("inputs", {}).get("p02_static_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_evolution_contract.json"][1]
        and p02_mgba.get("inputs", {}).get("stage64", {}).get("resolution")
        == "GENERATED_IN_MEMORY_FROM_STAGE63"
        and p02_mgba.get("inputs", {}).get("stage64_generation", {}).get(
            "disk_stage64_required"
        ) is False,
        "P02 mGBA clean-bootstrap/contract hash接続が不一致です",
    )
    p02_claims = p02_acceptance.get("claims", {})
    p02_runtime = p02_acceptance.get("runtime_result", {})
    hidden_ability_readback = p02_runtime.get("hidden_ability_readback", {})
    _require(
        p02_acceptance.get("status") == "CHECKPOINT_NOT_DONE"
        and p02_acceptance.get("classification")
        == "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX"
        and p02_acceptance.get("execution", {}).get("process_runs") == 2
        and p02_claims.get("real_get_evolution_target_species_executed") is True
        and p02_claims.get("real_item_evolution_removal_executed") is True
        and p02_claims.get("level_held_item_slot_priority_root_fixed") is True
        and p02_claims.get("hidden_ability_bit_readback_verified") is True
        and p02_claims.get("exact_p02_overlay_parent") is True
        and p02_claims.get("full_evolution_acceptance") is False
        and p02_runtime.get("status") == "PASS"
        and p02_runtime.get("level_item_priority_repair", {}).get(
            "repaired_species_count"
        ) == 6
        and hidden_ability_readback == {
            "after_calculate_stats": True,
            "after_selection": True,
            "after_species_write": True,
            "all_observed_preserved": True,
            "before_selection": True,
            "bit_mask": 16,
            "conditional_item_consumed_cases": 6,
            "negative_branch_cases": 6,
            "regular_branch_cases": 12,
        },
        "P02 actual consumer 24-case checkpoint境界不正",
    )
    _require(
        p02_acceptance.get("inputs", {}).get("config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p02_acceptance_gate.json"][1]
        and p02_acceptance.get("inputs", {}).get("static_evolution_contract", {}).get(
            "sha256"
        ) == PINNED_TRACKED_INPUTS["content/modernization/p02_evolution_contract.json"][1]
        and p02_acceptance.get("inputs", {}).get("candidate_rom", {}).get("sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb",
        "P02 actual consumer checkpointのconfig/contract/candidate hash接続不一致",
    )
    _require(
        p03.get("inputs", {}).get("identity_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/identity_contract.json"][1],
        "P03→P01 identity hash接続が不一致です",
    )
    _require(
        p03_stage65_config.get("task") == "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        and p03_stage65_config.get("stage") == 65,
        "P03 Stage65 config identity不正",
    )
    _require(
        p03_stage65.get("status") == "CHECKPOINT"
        and p03_stage65.get("done") is False
        and p03_stage65.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage65.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_P03_DONE",
        "P03 Stage65 checkpointをP03 DONEと誤認しています",
    )
    _require(
        p03_stage65.get("input", {}).get("mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage65_mgba_runtime_gate.json"][1]
        and p03_stage65.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]
        and p03_stage65.get("input", {}).get("parent_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"][1],
        "P03 Stage65 checkpointのgate/output/parent hash接続不一致",
    )
    _require(
        p03_stage65.get("input", {}).get("parent_metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"][1]
        and p03_stage65.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_allocation.json"][1]
        and p03_stage65.get("bps", {}).get("incremental", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage64-to-stage65-modernization-p03-caterpie-slice.bps"][1]
        and p03_stage65.get("bps", {}).get("clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/firered-jpn-rev0-to-stage65-modernization-p03-caterpie-slice.bps"][1],
        "P03 Stage65 checkpointのmetadata/allocation/BPS hash接続不一致",
    )
    _require(
        p03_stage65_mgba.get("status") == "PASS"
        and p03_stage65_mgba.get("task_completion") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage65_mgba.get("claims", {}).get("full_p03_acceptance") is False
        and p03_stage65_mgba.get("inputs", {}).get("stage65", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1],
        "P03 Stage65 mGBA gate境界/hash接続不一致",
    )
    _require(
        p03_stage65_mgba.get("inputs", {}).get("config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p03_stage65.json"][1]
        ,
        "P03 Stage65 mGBA gateのhistorical config hash接続不一致",
    )
    _require(
        p03_stage66_config.get("task")
        == "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT"
        and p03_stage66_config.get("stage") == 66
        and p03_stage66_config.get("acceptance", {}).get("task_completion")
        == "CHECKPOINT_NOT_P03_DONE",
        "P03 Stage66 config identity/completion境界不正",
    )
    stage66_inputs = p03_stage66_config.get("inputs", {})
    _require(
        stage66_inputs.get("parent_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1]
        and stage66_inputs.get("parent_metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.json"][1],
        "P03 Stage66 historical configのparent hash接続不一致",
    )
    _require(
        p03_stage66_routes.get("status") == "CHECKPOINT"
        and p03_stage66_routes.get("done") is False
        and p03_stage66_routes.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage66_routes.get("source_validation", {}).get("corrected_target_count") == 1300
        and p03_stage66_routes.get("source_validation", {}).get("compiled_route_count") == 118528
        and p03_stage66_routes.get("materialization", {}).get("materialized_routes") == 47548
        and p03_stage66_routes.get("materialization", {}).get("deferred_routes") == 70980,
        "P03 Stage66 route audit件数/completion境界不正",
    )
    _require(
        p03_stage66_changes.get("status") == "PASS"
        and p03_stage66_changes.get("changed_byte_count") == 81693
        and p03_stage66_changes.get("changed_span_count") == 3520
        and p03_stage66_changes.get("outside_declared_range_count") == 0,
        "P03 Stage66 change audit境界不正",
    )
    _require(
        p03_stage66.get("status") == "CHECKPOINT"
        and p03_stage66.get("done") is False
        and p03_stage66.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage66.get("acceptance", {}).get("task_completion")
        == "CHECKPOINT_NOT_P03_DONE",
        "P03 Stage66 checkpointをP03 DONEと誤認しています",
    )
    _require(
        p03_stage66.get("input", {}).get("mgba_runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_mgba_runtime_gate.json"][1]
        and p03_stage66.get("route_audit", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_bulk_route_audit.json"][1]
        and p03_stage66.get("change_audit", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_stage66_change_audit.json"][1]
        and p03_stage66.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.gba"][1]
        and p03_stage66.get("input", {}).get("parent_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/65_modernization_p03_caterpie_slice.gba"][1],
        "P03 Stage66 checkpointのgate/audit/output/parent hash接続不一致",
    )
    _require(
        p03_stage66.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_allocation.json"][1]
        and p03_stage66.get("bps", {}).get("incremental", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage65-to-stage66-modernization-p03-bulk-learnsets.bps"][1]
        and p03_stage66.get("bps", {}).get("clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/firered-jpn-rev0-to-stage66-modernization-p03-bulk-learnsets.bps"][1],
        "P03 Stage66 checkpointのallocation/BPS hash接続不一致",
    )
    _require(
        p03_stage66_mgba.get("status") == "PASS"
        and p03_stage66_mgba.get("task_completion") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage66_mgba.get("claims", {}).get("full_p03_acceptance") is False
        and p03_stage66_mgba.get("claims", {}).get("scheduler_e2e") is False
        and p03_stage66_mgba.get("inputs", {}).get("stage66", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.gba"][1],
        "P03 Stage66 mGBA gate境界/hash接続不一致",
    )
    _require(
        p03_stage66_mgba.get("inputs", {}).get("config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p03_stage66.json"][1]
        ,
        "P03 Stage66 mGBA gateのhistorical config hash接続不一致",
    )
    _require(
        p03_stage67_config.get("task")
        == "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        and p03_stage67_config.get("stage") == 67
        and p03_stage67_config.get("scope", {}).get("source_routes") == 118528
        and p03_stage67_config.get("scope", {}).get("selected_routes") == 118369
        and p03_stage67_config.get("scope", {}).get(
            "non_adopted_move_1063_routes"
        ) == 159
        and p03_stage67_config.get("scope", {}).get(
            "cumulative_materialized_routes"
        ) == 51151
        and p03_stage67_config.get("scope", {}).get("selected_routes_deferred")
        == 67218,
        "P03 Stage67 configのroute partition境界不正",
    )
    stage67_inputs = p03_stage67_config.get("inputs", {})
    _require(
        stage67_inputs.get("stage66_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/66_modernization_p03_bulk_learnsets.gba"][1]
        and stage67_inputs.get("p02_acceptance_config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p02_acceptance_gate.json"][1]
        and stage67_inputs.get("p02_acceptance_checkpoint", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p02_acceptance_checkpoint.json"][1]
        and stage67_inputs.get("p02_overlay_parent", {}).get("sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and stage67_inputs.get("p03_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_learnset_contract.json"][1]
        and stage67_inputs.get("p03_compiled_index", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_compiled_index.json"][1]
        and stage67_inputs.get("p03_runtime_handoff", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_runtime_handoff.json"][1]
        and stage67_inputs.get("adoption_decisions", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_adoption_decisions.json"][1],
        "P03 Stage67のStage66/P02/current P03/decision hash接続不一致",
    )
    _require(
        p03_stage67_routes.get("status") == "CHECKPOINT"
        and p03_stage67_routes.get("done") is False
        and p03_stage67_routes.get("source_validation", {}).get("source_route_count")
        == 118528
        and p03_stage67_routes.get("source_validation", {}).get("selected_route_count")
        == 118369
        and p03_stage67_routes.get("source_validation", {}).get(
            "non_adopted_route_count"
        ) == 159
        and p03_stage67_routes.get("materialization", {}).get(
            "stage67_new_routes_materialized"
        ) == 3603
        and p03_stage67_routes.get("materialization", {}).get(
            "cumulative_routes_materialized"
        ) == 51151
        and p03_stage67_routes.get("materialization", {}).get(
            "selected_routes_deferred"
        ) == 67218
        and p03_stage67_routes.get("claims", {}).get(
            "move_1063_serialized_or_replaced"
        ) is False,
        "P03 Stage67 route audit件数/Side Change境界不正",
    )
    _require(
        p03_stage67_changes.get("status") == "PASS"
        and p03_stage67_changes.get("changed_byte_count") == 46455
        and p03_stage67_changes.get("outside_declared_range_count") == 0,
        "P03 Stage67 change audit境界不正",
    )
    _require(
        p03_stage67.get("status") == "CHECKPOINT"
        and p03_stage67.get("done") is False
        and p03_stage67.get("checkpoint_marker") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage67.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/67_modernization_p02_p03_consumers.gba"][1]
        and p03_stage67.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/67_modernization_p03_allocation.json"][1]
        and p03_stage67.get("bps", {}).get("incremental", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/patches/stage66-p02-overlay-to-stage67-modernization-p03-consumers.bps"
        ][1]
        and p03_stage67.get("bps", {}).get("clean", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/patches/firered-jpn-rev0-to-stage67-modernization-p02-p03-consumers.bps"
        ][1]
        and p03_stage67.get("input", {}).get("runtime_gate", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p03_stage67_mgba_runtime_gate.json"
        ][1],
        "P03 Stage67 checkpoint output/allocation/BPS/mGBA hash接続不一致",
    )
    _require(
        p03_stage67_mgba.get("status") == "PASS"
        and p03_stage67_mgba.get("task_completion") == "CHECKPOINT_NOT_P03_DONE"
        and p03_stage67_mgba.get("execution", {}).get("process_runs") == 2
        and p03_stage67_mgba.get("claims", {}).get("full_p03_acceptance") is False
        and p03_stage67_mgba.get("claims", {}).get(
            "all_materialized_evolution_routes_executed"
        ) is True
        and p03_stage67_mgba.get("claims", {}).get(
            "all_materialized_tutor_routes_executed"
        ) is True
        and p03_stage67_mgba.get("claims", {}).get(
            "all_materialized_normal_egg_routes_executed"
        ) is True
        and p03_stage67_mgba.get("runtime_result", {}).get("counts", {}).get(
            "evolution_routes"
        ) == 341
        and p03_stage67_mgba.get("runtime_result", {}).get("counts", {}).get(
            "tutor_positive_routes"
        ) == 740
        and p03_stage67_mgba.get("runtime_result", {}).get("counts", {}).get(
            "egg_routes"
        ) == 2522,
        "P03 Stage67 actual consumer mGBA gate境界不正",
    )
    _require(
        p04_manifest.get("task") == "USER-MODERNIZATION-P04"
        and p04_official.get("task") == "USER-MODERNIZATION-P04"
        and p04_assets.get("task") == "USER-MODERNIZATION-P04",
        "P04 source/candidate identityが不一致です",
    )
    coverage04 = p04_import.get("coverage", {})
    consumer04 = p04_import.get("consumer_scope", {})
    output04 = p04_import.get("output", {})
    _require(
        p04_import.get("task") == "USER-MODERNIZATION-P04-ASSET-IMPORT"
        and p04_import.get("status") == "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS",
        "P04 importer manifest identity不正",
    )
    _require(
        p04_import.get("inputs", {}).get("asset_source_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_asset_sources.json"][1]
        and p04_import.get("inputs", {}).get("candidate_manifest", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_candidate_manifest.json"][1],
        "P04 importer upstream hash接続不一致",
    )
    _require(
        coverage04.get("mega_candidate_records") == {"covered": 49, "required": 49}
        and coverage04.get("mega_stones") == {"covered": 45, "required": 45}
        and coverage04.get("gba_full_species_palette_compatibility") == {"ready": 49, "required": 49}
        and coverage04.get("winds_waves_new_species") == {"covered": 0, "required": 0},
        "P04 importer coverage境界不正",
    )
    _require(
        p04_import.get("missing_assets") == []
        and output04.get("payload_file_count") == 670
        and output04.get("payload_total_size") == 426648
        and output04.get("asset_set_sha256")
        == "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c",
        "P04 49 Mega private asset payload identity不正",
    )
    _require(
        consumer04.get("integration_status") == "STAGING_ONLY_NOT_ROM_READY"
        and consumer04.get("rom_modified") is False
        and consumer04.get("id_assignments_created") is False,
        "P04 importerをROM/ID統合済みと誤認しています",
    )
    capacity_inputs = p04_capacity.get("inputs", {})
    _require(
        p04_capacity.get("status") == "CHECKPOINT_NOT_RUNTIME_READY"
        and p04_capacity.get("runtime_ready") is False
        and p04_capacity.get("rom_mutated") is False
        and p04_capacity.get("save_mutated") is False
        and p04_capacity.get("shared_manifests_mutated") is False,
        "P04容量予約をruntime反映済みと誤認しています",
    )
    _require(
        capacity_inputs.get("p04_candidate_manifest", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_candidate_manifest.json"][1]
        and capacity_inputs.get("p04_asset_manifest", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p04_asset_import_manifest.json"][1]
        and capacity_inputs.get("p05_battle_content_contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p05_battle_content_contract.json"][1]
        and capacity_inputs.get("p05_runtime_handoff", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p05_runtime_handoff.json"][1],
        "P04容量予約のP04/P05 upstream hash接続不一致",
    )
    expected_reservations = {
        "species_form": (1621, 1669, 49),
        "item": (999, 1043, 45),
        "ability": (312, 317, 6),
        "move": (None, None, 0),
    }
    reservations = p04_capacity.get("id_reservations", {})
    for domain, (start, end, count) in expected_reservations.items():
        row = reservations.get(domain, {})
        _require(
            row.get("reserved_start_id") == start
            and row.get("reserved_end_id") == end
            and row.get("append_count") == count,
            f"P04容量予約range不一致: {domain}",
        )
    winds_capacity = p04_capacity.get("asset_readiness_separate_gate", {}).get(
        "winds_waves", {}
    )
    _require(
        winds_capacity.get("scope") == "NON_ADOPTED_USER_SCOPE"
        and winds_capacity.get("reserved_ids") == 0
        and winds_capacity.get("asset_requirement_count") == 0
        and winds_capacity.get("missing_record_keys") == []
        and winds_capacity.get("consumer_requirement")
        == "NOT_APPLICABLE_NON_ADOPTED",
        "P04 Winds/Waves 3種の無予約・素材不要境界不正",
    )
    p05_p03 = p05.get("inputs", {}).get("p03_runtime", {})
    _require(
        p05_p03.get("content_sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p03_runtime_handoff.json"][1],
        "P05→P03 runtime hash接続が不一致です",
    )
    _require(
        p05_plan.get("status") == "NO_CONFIRMED_DATA_ONLY_PATCH"
        and p05_plan.get("plan", {}).get("confirmed_patch_count") == 0,
        "P05 data-only patch境界が不一致です",
    )
    _require(
        p05_runtime.get("status") == p05.get("status")
        and len(p05_runtime.get("new_move_requirements", [])) == 0
        and len(p05_runtime.get("non_adopted_move_candidates", [])) == 1
        and len(p05_runtime.get("new_ability_requirements", [])) == 6
        and len(p05_runtime.get("non_adopted_p04_records", [])) == 3,
        "P05 runtime handoffがbattle contractと不一致です",
    )
    _require(
        {
            row.get("record_key")
            for row in p05_runtime.get("non_adopted_p04_records", [])
            if isinstance(row, Mapping)
        }
        == {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"}
        and all(
            isinstance(row, Mapping)
            and row.get("selection_status") == "NOT_ADOPTED_BY_USER_DECISION"
            and row.get("manifest_allocation") is False
            and row.get("runtime_implementation") is False
            for row in p05_runtime.get("non_adopted_p04_records", [])
        ),
        "P05 Winds/Waves 3種非採用・無割当境界不正",
    )
    non_adopted_move = p05_runtime.get("non_adopted_move_candidates", [None])[0]
    _require(
        isinstance(non_adopted_move, Mapping)
        and non_adopted_move.get("move_key") == "MOVE_KEY_ALLYSWITCH"
        and non_adopted_move.get("requested_project_id") == 1063
        and non_adopted_move.get("canonical_id") is None
        and non_adopted_move.get("selection_status")
        == "NOT_ADOPTED_BY_USER_DECISION"
        and non_adopted_move.get("exclusion", {}).get("replacement_move_key") is None
        and non_adopted_move.get("exclusion", {}).get("manifest_allocation") is False
        and non_adopted_move.get("exclusion", {}).get("runtime_implementation") is False,
        "P05 Side Change非採用・無置換・無割当境界不正",
    )
    _require(
        p05_ability.get("status") == "HOST_RUNTIME_VERIFIED_ROM_LINK_PENDING"
        and p05_ability.get("host_runtime_verified") is True
        and p05_ability.get("rom_linked") is False
        and p05_ability.get("rom_mutated") is False
        and p05_ability.get("save_mutated") is False
        and p05_ability.get("shared_manifests_mutated") is False
        and p05_ability.get("ability_allocation", {}).get("reserved_range")
        == [312, 317]
        and len(p05_ability.get("ability_allocation", {}).get("rows", [])) == 6
        and p05_ability.get("fixture", {}).get("independent_process_runs") == 2
        and p05_ability.get("fixture", {}).get("summary", {}).get("case_count") == 46
        and p05_ability.get("fixture", {}).get("summary", {}).get("failure_count") == 0
        and p05_ability.get("completion_boundary", {}).get("release_ready") is False,
        "P05 6 Ability host runtime checkpoint境界不正",
    )
    _require(
        p05_ability.get("inputs", {}).get("config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p05_ability_runtime.json"][1]
        and p05_ability.get("inputs", {}).get("capacity_checkpoint", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p04_capacity_allocation_manifest.json"
        ][1],
        "P05 Ability config/capacity hash接続不一致",
    )
    _require(
        p06.get("review_partition", {}).get("projection_sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/p06_review_projection.json"][1],
        "P06→review projection hash接続が不一致です",
    )
    declared = p07.get("inputs", {}).get("upstream_contracts")
    _require(isinstance(declared, Mapping), "P07 upstream hash接続がありません")
    expected_paths = (
        "content/modernization/p03_compiled_index.json",
        "content/modernization/p03_learnset_contract.json",
        "content/modernization/p03_runtime_handoff.json",
        "content/modernization/p04_candidate_manifest.json",
        "content/modernization/p05_battle_content_contract.json",
        "content/modernization/p06_review_projection.json",
        "content/modernization/p06_species_adjustment_contract.json",
    )
    for path in expected_paths:
        _require(
            declared.get(path, {}).get("sha256") == PINNED_TRACKED_INPUTS[path][1],
            f"P07 upstream hash接続が不一致です: {path}",
        )
    _require(
        p07_runtime.get("status") == p07.get("status")
        and p07_runtime.get("summary") == p07.get("summary")
        and p07_runtime.get("runtime_handoff") == p07.get("runtime_handoff"),
        "P07 runtime handoffがlayered contractと不一致です",
    )


def _gate(key: str, status: str, evidence: Sequence[str]) -> dict[str, Any]:
    return {"gate": key, "status": status, "evidence": list(evidence)}


def _phase_records(documents: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    identity = documents["content/modernization/identity_contract.json"]
    candidate = documents["config/modernization_candidate.json"]
    p02 = documents["content/modernization/p02_evolution_contract.json"]
    p02_cp = documents["content/modernization/p02_stage64_checkpoint.json"]
    p02_mgba = documents["content/modernization/p02_stage64_mgba_runtime_gate.json"]
    p02_acceptance = documents["content/modernization/p02_acceptance_checkpoint.json"]
    p03 = documents["content/modernization/p03_learnset_contract.json"]
    p03_index = documents["content/modernization/p03_compiled_index.json"]
    p03_runtime = documents["content/modernization/p03_runtime_handoff.json"]
    p03_stage65 = documents["content/modernization/p03_stage65_checkpoint.json"]
    p03_stage65_mgba = documents["content/modernization/p03_stage65_mgba_runtime_gate.json"]
    p03_stage66_config = documents["config/modernization_p03_stage66.json"]
    p03_stage66_routes = documents[
        "content/modernization/p03_stage66_bulk_route_audit.json"
    ]
    p03_stage66_changes = documents[
        "content/modernization/p03_stage66_change_audit.json"
    ]
    p03_stage66 = documents["content/modernization/p03_stage66_checkpoint.json"]
    p03_stage66_mgba = documents[
        "content/modernization/p03_stage66_mgba_runtime_gate.json"
    ]
    p03_stage67_config = documents["config/modernization_p03_stage67.json"]
    p03_stage67_routes = documents[
        "content/modernization/p03_stage67_consumer_route_audit.json"
    ]
    p03_stage67_changes = documents[
        "content/modernization/p03_stage67_change_audit.json"
    ]
    p03_stage67 = documents["content/modernization/p03_stage67_checkpoint.json"]
    p03_stage67_mgba = documents[
        "content/modernization/p03_stage67_mgba_runtime_gate.json"
    ]
    p04 = documents["content/modernization/p04_candidate_manifest.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p04_capacity = documents[
        "content/modernization/p04_capacity_allocation_manifest.json"
    ]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p05_ability = documents["content/modernization/p05_ability_runtime_checkpoint.json"]
    p06 = documents["content/modernization/p06_species_adjustment_contract.json"]
    p06_projection = documents["content/modernization/p06_review_projection.json"]
    p07 = documents["content/modernization/p07_layered_learnset_contract.json"]

    _require(identity.get("status") == "PASS", "P01 identity contractがPASSではありません")
    norm = identity.get("target_normalization", {}).get("summary", {})
    _require(norm.get("changed_keys") == ["SPECIES_KEY_EGG", "SPECIES_KEY_CATERPIE"], "P01訂正key集合不一致")
    _require(
        candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        and candidate.get("release_ready") is False
        and candidate.get("active_play_baseline_changed") is False,
        "P01 completion evidenceとP03 checkpoint境界不正",
    )

    _require(p02.get("status") == "PASS" and p02.get("release_gate") == "BLOCKED_BY_REQUIRED_FIXES_AND_DEFERRED_RUNTIME_ACCEPTANCE", "P02 static/blocked境界不正")
    _require(p02_cp.get("status") == "CHECKPOINT" and p02_cp.get("done") is False, "P02 checkpointをDONEと誤認しています")
    _require(p02_cp.get("acceptance", {}).get("task_completion") == "CHECKPOINT_NOT_DONE", "P02 completion gate不正")
    _require(p02_mgba.get("status") == "PASS" and p02_mgba.get("claims", {}).get("full_evolution_acceptance") is False, "P02 bounded mGBA境界不正")
    _require(
        p02_acceptance.get("status") == "CHECKPOINT_NOT_DONE"
        and p02_acceptance.get("claims", {}).get(
            "level_held_item_slot_priority_root_fixed"
        ) is True
        and p02_acceptance.get("claims", {}).get(
            "hidden_ability_bit_readback_verified"
        ) is True
        and p02_acceptance.get("claims", {}).get("full_evolution_acceptance")
        is False
        and p02_acceptance.get("runtime_result", {}).get("status") == "PASS"
        and p02_acceptance.get("runtime_result", {}).get(
            "hidden_ability_readback", {}
        ).get("all_observed_preserved") is True,
        "P02 actual consumer partial acceptance境界不正",
    )

    adoption03 = p03.get("corrected_adoption", {})
    selection03 = p03.get("runtime_selection", {})
    _require(
        p03.get("status") == "PASS"
        and adoption03.get("records") == 1300
        and adoption03.get("routes") == 118528
        and selection03.get("selected_routes") == 118369
        and selection03.get("excluded_routes") == 159,
        "P03 source/runtime selection件数不正",
    )
    _require(
        p03_index.get("status") == "PASS"
        and p03_index.get("record_count") == 1300
        and p03_index.get("route_count") == 118528
        and p03_index.get("selected_route_count") == 118369
        and p03_index.get("excluded_route_count") == 159,
        "P03 index source/runtime selection件数不正",
    )
    side = p03_runtime.get("side_change_1063", {})
    _require(p03_runtime.get("status") == "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS", "P03 runtime未完了境界不正")
    _require(
        side.get("status") == "NOT_ADOPTED_BY_USER_DECISION"
        and side.get("source_route_count") == 159
        and side.get("adopted_route_count") == 0
        and side.get("excluded_route_count") == 159
        and side.get("decision", {}).get("replacement_move_key") is None,
        "P03 Side Change1063非採用境界不正",
    )
    _require(
        p03_stage65.get("status") == "CHECKPOINT"
        and p03_stage65.get("scope", {}).get("routes_materialized_by_this_checkpoint") == 4
        and p03_stage65.get("scope", {}).get("routes_not_materialized_by_this_checkpoint") == 118524
        and p03_stage65_mgba.get("status") == "PASS",
        "P03 Stage65統合checkpoint件数不正",
    )
    _require(
        p03_stage66.get("status") == "CHECKPOINT"
        and p03_stage66.get("scope", {}).get("routes_materialized_by_this_checkpoint") == 47548
        and p03_stage66.get("scope", {}).get("routes_not_materialized_by_this_checkpoint") == 70980
        and p03_stage66.get("scope", {}).get("machine_supply_required_routes_deferred") == 26347
        and p03_stage66_routes.get("materialization", {}).get("materialized_routes") == 47548
        and p03_stage66_changes.get("changed_byte_count") == 81693
        and p03_stage66_changes.get("outside_declared_range_count") == 0
        and p03_stage66_mgba.get("status") == "PASS",
        "P03 Stage66 bulk checkpoint件数不正",
    )
    _require(
        p03_stage67_config.get("stage") == 67
        and p03_stage67.get("status") == "CHECKPOINT"
        and p03_stage67.get("done") is False
        and p03_stage67.get("scope", {}).get("source_routes") == 118528
        and p03_stage67.get("scope", {}).get("selected_routes") == 118369
        and p03_stage67.get("scope", {}).get("non_adopted_move_1063_routes")
        == 159
        and p03_stage67.get("scope", {}).get("stage67_new_materialized_routes")
        == 3603
        and p03_stage67.get("scope", {}).get("cumulative_materialized_routes")
        == 51151
        and p03_stage67.get("scope", {}).get("selected_routes_deferred") == 67218
        and p03_stage67_changes.get("changed_byte_count") == 46455
        and p03_stage67_changes.get("outside_declared_range_count") == 0
        and p03_stage67_mgba.get("status") == "PASS"
        and p03_stage67_mgba.get("execution", {}).get("process_runs") == 2,
        "P03 Stage67 consumer checkpoint件数/runtime境界不正",
    )

    counts04 = p04.get("expected_counts", {})
    _require(
        counts04.get("all_records") == 54
        and counts04.get("adoption_candidate_records") == 49
        and counts04.get("classification_hold_records") == 2
        and counts04.get("non_adopted_user_scope_records") == 3,
        "P04候補/hold/非採用件数不正",
    )
    _require(
        counts04.get("mega_runtime_records") == 49
        and counts04.get("unique_mega_stones") == 45
        and counts04.get("new_species_records") == 3
        and counts04.get("adopted_new_species_records") == 0,
        "P04 Mega採用/Winds・Waves非採用内訳不正",
    )
    _require(
        p04_import.get("status") == "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS"
        and p04_import.get("consumer_scope", {}).get("rom_modified") is False
        and p04_import.get("consumer_scope", {}).get("id_assignments_created") is False,
        "P04 importer staging-only境界不正",
    )
    capacity_tables = p04_capacity.get("table_capacity", {})
    _require(
        p04_capacity.get("status") == "CHECKPOINT_NOT_RUNTIME_READY"
        and p04_capacity.get("runtime_ready") is False
        and capacity_tables.get("known_fixed_table_count") == 34
        and capacity_tables.get("known_fixed_delta_bytes") == 19857,
        "P04 capacity checkpoint境界不正",
    )
    capacity_dry_run = p04_capacity.get("allocator_audit", {}).get(
        "known_fixed_table_dry_run", {}
    )
    stage66_allocation = p03_stage66_config.get("allocation", {})
    stage66_start = int(str(stage66_allocation.get("start")), 16)
    stage66_size = stage66_allocation.get("size")
    _require(
        capacity_dry_run.get("source_stage") == 65
        and capacity_dry_run.get("region") == "integration_modules"
        and capacity_dry_run.get("candidate_span_start") == 21307984
        and capacity_dry_run.get("candidate_span_end_exclusive") == 23068672
        and capacity_dry_run.get("bundle_bytes_including_alignment") == 636392
        and capacity_dry_run.get("bundle_end_exclusive") == 21944376
        and 23068672 - capacity_dry_run.get("bundle_end_exclusive") == 1124296,
        "P04 capacityのStage65 basis/integration_modules span不正",
    )
    _require(
        stage66_allocation.get("region") == "future_tail"
        and stage66_start == 33399368
        and stage66_size == 60116
        and stage66_start >= capacity_dry_run.get("candidate_span_end_exclusive")
        and 33554432 - (stage66_start + stage66_size) == 94948,
        "P04 capacityとStage66 allocationの非衝突/残量cross-check不正",
    )

    summary05 = p05.get("summary", {})
    _require(p05.get("status") == "CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS", "P05 runtime未完了境界不正")
    _require(
        summary05.get("adopted_performance_adjustment_count") == 0
        and summary05.get("new_move_requirement_count") == 0
        and summary05.get("non_adopted_move_candidate_count") == 1
        and summary05.get("new_ability_requirement_count") == 6
        and summary05.get("existing_official_ability_assignment_count") == 29
        and summary05.get("non_adopted_p04_record_count") == 3,
        "P05採用/非採用件数不正",
    )
    _require(
        p05_ability.get("status") == "HOST_RUNTIME_VERIFIED_ROM_LINK_PENDING"
        and p05_ability.get("fixture", {}).get("summary", {}).get("case_count") == 46
        and p05_ability.get("fixture", {}).get("independent_process_runs") == 2
        and p05_ability.get("rom_linked") is False,
        "P05 Ability host runtime checkpoint境界不正",
    )

    adoption06 = p06.get("adoption", {})
    _require(p06.get("status") == "CHECKPOINT_ADOPTED_DELTA_EMPTY", "P06 checkpoint境界不正")
    _require(adoption06.get("adopted_delta_count") == 0 and adoption06.get("runtime_patch_authorized") is False, "P06採用差分境界不正")
    _require(p06.get("handoff", {}).get("completion_state") == "CHECKPOINT_NOT_P06_DONE", "P06をDONEと誤認しています")
    _require(p06_projection.get("partition", {}).get("review_record_count") == 194, "P06 review件数不正")

    summary07 = p07.get("summary", {})
    _require(p07.get("status") == "CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED", "P07 checkpoint境界不正")
    _require(summary07.get("normal_species_to_vega_move_adopted") == 0 and summary07.get("vega_species_to_normal_move_adopted") == 0 and summary07.get("explicit_deletions_adopted") == 0, "P07採用差分0件境界不正")
    _require(p07.get("runtime_handoff", {}).get("runtime_implemented") is False, "P07 runtimeを実装済みと誤認しています")

    return [
        {
            "phase": "P01", "completion_state": "COMPLETED", "contract_statuses": ["PASS"],
            "adoption": {"identity_changed_keys": 2, "runtime_corrections": 2, "changed_rom_bytes": 10},
            "not_adopted": ["P02_TO_P07_CONTENT", "ACTIVE_BASELINE_PROMOTION"],
            "rom_reflection": {"reflected": True, "stage": 63},
            "required_gates": [
                _gate("IDENTITY_CONTRACT", "PASS", ["content/modernization/identity_contract.json"]),
                _gate("STAGE63_EXACT_ROM_AND_BPS", "PASS", ["build/stages/63_modernization_p01_identity_repair.json"]),
                _gate("TASK_COMPLETION", "PASS", ["config/modernization_candidate.json"]),
            ],
            "blockers": [],
        },
        {
            "phase": "P02", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["PASS", "CHECKPOINT", "PASS", "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX"],
            "adoption": {"static_contract_records": 1, "stage64_changed_evolution_rows": 1, "stage64_changed_rom_bytes": 2, "slot_priority_repaired_species": 6, "actual_consumer_case_count": 24, "actual_consumer_process_runs": 2, "hidden_ability_readback_verified": True, "hidden_ability_bit_mask": 16, "hidden_ability_observed_case_count": 24},
            "not_adopted": ["REVIEW_ONLY_BRANCHES", "FULL_EVOLUTION_RUNTIME_ACCEPTANCE"],
            "rom_reflection": {
                "reflected": True,
                "stage": 67,
                "ancestor_stage": 64,
                "scope": "RAYQUAZA_FIX_PLUS_6_SPECIES_PRIORITY_REPAIR_IN_STAGE67_OVERLAY",
            },
            "required_gates": [
                _gate("STATIC_CONTRACT", "PASS", ["content/modernization/p02_evolution_contract.json"]),
                _gate("BOUNDED_DIRECT_CALL_MGBA", "PASS_NOT_FULL_E2E", ["content/modernization/p02_stage64_mgba_runtime_gate.json"]),
                _gate("ACTUAL_EVOLUTION_CONSUMERS", "PASS_PARTIAL_24_CASES_WITH_HIDDEN_ABILITY_READBACK_NOT_FULL_E2E", ["content/modernization/p02_acceptance_checkpoint.json"]),
                _gate("FULL_EVOLUTION_ACCEPTANCE", "BLOCKED", ["content/modernization/p02_stage64_checkpoint.json"]),
            ],
            "blockers": ["EVOLUTION_SCENE_CANCEL_BAG_MOVE_ABILITY_SAVE_RELOAD_NOT_RUN", "FULL_EVOLUTION_ACCEPTANCE_FALSE"],
        },
        {
            "phase": "P03", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["PASS", "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS", "STAGE65_ANCESTOR_CHECKPOINT", "STAGE66_HISTORICAL_BULK_CHECKPOINT", "STAGE67_CONSUMER_CHECKPOINT", "PASS_NOT_FULL_P03_ACCEPTANCE"],
            "adoption": {"reference_records": 1300, "source_routes": 118528, "runtime_selected_routes": 118369, "side_change_1063_source_routes": 159, "side_change_1063_excluded_routes": 159, "side_change_1063_adopted_routes": 0, "side_change_1063_replacement_move_key": None, "stage65_preserved_ancestor_routes": 4, "stage65_changed_rom_bytes": 17, "stage66_corrected_targets": 1300, "stage66_routes_materialized": 47548, "stage66_level_up_routes_materialized": 18515, "stage66_machine_existing_slot_routes_materialized": 29033, "stage66_changed_rom_bytes": 81693, "stage67_new_routes_materialized": 3603, "stage67_evolution_routes_materialized": 341, "stage67_tutor_existing_slot_routes_materialized": 740, "stage67_normal_egg_routes_materialized": 2522, "cumulative_routes_materialized": 51151, "selected_routes_remaining": 67218, "stage67_changed_rom_bytes_from_overlay": 46455, "stage67_changed_rom_bytes_from_stage66": 46515, "stage67_future_tail_remaining_bytes": 62510},
            "not_adopted": ["SIDE_CHANGE_1063_ALL_159_SOURCE_ROUTES_EXCLUDED_NO_REPLACEMENT", "SELECTED_ROUTES_REMAINING_67218", "MACHINE_TUTOR_SUPPLY_REQUIRED_26648", "FORM_CARRY_REMINDER_SHARED_AND_SPECIAL_EGG_CONSUMERS", "FULL_SCHEDULER_BREEDING_AND_SAVE_RELOAD"],
            "rom_reflection": {"reflected": True, "stage": 67, "scope": "P02_OVERLAY_PLUS_EVOLUTION_TUTOR_NORMAL_EGG_CONSUMER_CHECKPOINT"},
            "required_gates": [
                _gate("STREAMING_CONTRACT_AND_INDEX", "PASS", ["content/modernization/p03_learnset_contract.json", "content/modernization/p03_compiled_index.json"]),
                _gate("STAGE65_REPRESENTATIVE_RUNTIME", "PRESERVED_ANCESTOR_CHECKPOINT", ["content/modernization/p03_stage65_checkpoint.json", "content/modernization/p03_stage65_mgba_runtime_gate.json"]),
                _gate("STAGE66_BULK_RUNTIME", "INTEGRATED_CHECKPOINT_NOT_P03_DONE", ["content/modernization/p03_stage66_checkpoint.json", "content/modernization/p03_stage66_mgba_runtime_gate.json", "content/modernization/p03_stage66_bulk_route_audit.json", "content/modernization/p03_stage66_change_audit.json"]),
                _gate("STAGE67_CONSUMER_RUNTIME", "PASS_ALL_MATERIALIZED_DIRECT_CALLS_NOT_E2E", ["content/modernization/p03_stage67_checkpoint.json", "content/modernization/p03_stage67_mgba_runtime_gate.json", "content/modernization/p03_stage67_consumer_route_audit.json", "content/modernization/p03_stage67_change_audit.json"]),
                _gate("SIDE_CHANGE_NON_ADOPTION", "PASS_EXCLUDED_159_NO_REPLACEMENT", ["config/modernization_adoption_decisions.json", "content/modernization/p03_runtime_handoff.json"]),
                _gate("FULL_SELECTED_ROUTE_SUPPLY", "BLOCKED", ["content/modernization/p03_runtime_handoff.json", "content/modernization/p03_stage66_bulk_route_audit.json"]),
            ],
            "blockers": ["SELECTED_ROUTES_REMAINING_67218", "MACHINE_TUTOR_SUPPLY_REQUIRED_ROWS_26648", "FORM_CARRY_REMINDER_SHARED_SPECIAL_EGG_CONSUMERS_PENDING", "FULL_SCHEDULER_BREEDING_AND_SAVE_RELOAD_NOT_RUN"],
        },
        {
            "phase": "P04", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CANDIDATE_MANIFEST_ONLY", "PRIVATE_USE_STAGING_WITH_DECLARED_GAPS", "CAPACITY_RESERVATION_CHECKPOINT_NOT_RUNTIME_READY"],
            "adoption": {"runtime_adopted_records": 0, "selected_candidate_records": 49, "held_records": 2, "mega_records": 49, "stone_records": 45, "new_species_reference_records": 3, "adopted_new_species_records": 0, "non_adopted_user_scope_records": 3, "asset_staging": {"mega_covered": 49, "mega_required": 49, "stones_covered": 45, "stones_required": 45, "palette_ready": 49, "palette_required": 49, "winds_waves_covered": 0, "winds_waves_required": 0, "missing_assets": 0, "payload_file_count": 670, "payload_total_bytes": 426648, "asset_set_sha256": "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c"}, "capacity_reservation": {"capacity_basis_stage": 65, "species_form": [1621, 1669], "item": [999, 1043], "ability": [312, 317], "move": None, "move_append_count": 0, "fixed_table_count": 34, "fixed_table_delta_bytes": 19857, "aligned_bundle_bytes": 636392, "integration_modules_remaining_bytes": 1124296, "stage66_cross_check": {"allocation_region": "future_tail", "allocation_start": 33399368, "allocation_size": 60116, "allocation_end_exclusive": 33459484, "stage65_future_tail_remaining_bytes": 155064, "stage66_future_tail_remaining_bytes": 94948, "p04_candidate_region": "integration_modules", "p04_candidate_start": 21307984, "p04_candidate_end_exclusive": 23068672, "overlap": False}, "runtime_ready": False}},
            "not_adopted": ["SHARED_ID_MATERIALIZATION", "ROM_TABLE_RELOCATION", "WINDS_WAVES_NEW_SPECIES_3_USER_SCOPE", "PUBLIC_REDISTRIBUTION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("OFFICIAL_SOURCE_AND_CANDIDATE_SET", "PASS", ["content/modernization/p04_candidate_manifest.json", "content/modernization/p04_official_sources.json"]),
                _gate("ASSET_IMPORTER", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY", ["content/modernization/p04_asset_import_manifest.json"]),
                _gate("ID_CAPACITY_RESERVATION", "INTEGRATED_CHECKPOINT_NOT_RUNTIME_READY", ["content/modernization/p04_capacity_allocation_manifest.json"]),
                _gate("ID_MATERIALIZATION_AND_RUNTIME", "BLOCKED", ["content/modernization/p04_capacity_allocation_manifest.json"]),
            ],
            "blockers": ["FIXED_TABLES_REQUIRE_RELOCATION_AND_REPOINT", "ITEM_IDS_1024_TO_1043_EXCEED_10_BIT_CONSUMERS", "ABILITY_U8_LEGACY_REACHABILITY_UNPROVEN", "SAVE_MIGRATION_NOT_DESIGNED", "RIGHTS_REVIEW", "ROM_AND_ID_NOT_INTEGRATED"],
        },
        {
            "phase": "P05", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS", "HOST_RUNTIME_VERIFIED_ROM_LINK_PENDING"],
            "adoption": {"performance_adjustments": 0, "data_only_patches": 0, "new_move_requirements": 0, "non_adopted_move_candidates": 1, "side_change_1063_adopted": False, "temporary_ability_assignments": 14, "existing_official_assignments": 29, "new_abilities": 6, "non_adopted_p04_records": 3, "ability_host_runtime_cases": 46, "ability_host_runtime_processes": 2},
            "not_adopted": ["SIDE_CHANGE_1063_RUNTIME_AND_ALLOCATION", "WINDS_WAVES_NEW_SPECIES_3_RUNTIME_AND_ALLOCATION", "ABILITY_ROM_LINK_AND_FIXED_TABLES"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("BATTLE_CONTENT_CONTRACT", "PASS", ["content/modernization/p05_battle_content_contract.json"]),
                _gate("SIDE_CHANGE_1063_EXCLUSION", "PASS_NON_ADOPTED_NO_REPLACEMENT", ["config/modernization_adoption_decisions.json", "content/modernization/p05_runtime_handoff.json"]),
                _gate("WINDS_WAVES_NEW_SPECIES_EXCLUSION", "PASS_NON_ADOPTED_NO_ID_ASSET_RUNTIME", ["content/modernization/p04_candidate_manifest.json", "content/modernization/p04_capacity_allocation_manifest.json", "content/modernization/p05_runtime_handoff.json"]),
                _gate("P04_NEW_ABILITIES_HOST_RUNTIME", "PASS_46_CASES_X2_ROM_LINK_PENDING", ["content/modernization/p05_ability_runtime_checkpoint.json"]),
                _gate("P04_NEW_ABILITIES_ROM_LINK", "BLOCKED", ["content/modernization/p05_ability_runtime_checkpoint.json"]),
            ],
            "blockers": ["SIX_ABILITIES_ROM_LINK_FIXED_TABLE_TEXT_UI_MGBA_PENDING"],
        },
        {
            "phase": "P06", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CHECKPOINT_ADOPTED_DELTA_EMPTY"],
            "adoption": {"species_adjustment_records": 0, "review_records": 194, "runtime_patch_authorized": False},
            "not_adopted": ["ALL_REVIEW_PROJECTION_ROWS", "SCYTHER_VERIFIED_DISCREPANCY"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("REVIEW_PARTITION", "PASS", ["content/modernization/p06_review_projection.json"]),
                _gate("EXPLICIT_ADOPTION_SPEC", "MISSING", ["content/modernization/p06_species_adjustment_contract.json"]),
                _gate("SPECIES_RUNTIME_AND_SAVE", "BLOCKED", ["content/modernization/p06_species_adjustment_contract.json"]),
            ],
            "blockers": ["NO_EXPLICIT_SPECIES_ADJUSTMENT_SPEC", "CHECKPOINT_NOT_P06_DONE"],
        },
        {
            "phase": "P07", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CHECKPOINT_NO_ADOPTED_CROSS_DISTRIBUTION_RUNTIME_BLOCKED"],
            "adoption": {"normal_to_vega_move": 0, "vega_to_normal_move": 0, "explicit_deletions": 0},
            "not_adopted": ["UNSUBMITTED_CROSS_DISTRIBUTION", "RUNTIME_LAYER_COMPILATION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("LAYER_PRECEDENCE_AND_CONFLICT", "PASS", ["content/modernization/p07_layered_learnset_contract.json"]),
                _gate("P06_REVIEW_DEPENDENCY", "BLOCKED", ["content/modernization/p07_runtime_handoff.json"]),
                _gate("ROUTE_RUNTIME_UI_SAVE", "BLOCKED", ["content/modernization/p07_runtime_handoff.json"]),
            ],
            "blockers": ["NO_ADOPTED_DISTRIBUTION_ROWS", "P06_NOT_DONE", "ROUTE_RUNTIME_NOT_IMPLEMENTED"],
        },
        {
            "phase": "P08", "completion_state": STATUS, "contract_statuses": [STATUS],
            "adoption": {"release_candidate": False, "active_baseline_change": False},
            "not_adopted": ["CANDIDATE_PROMOTION", "RELEASE_PACKAGING", "P03_TO_P07_RUNTIME_COMPLETION"],
            "rom_reflection": {"reflected": False, "stage": None},
            "required_gates": [
                _gate("PINNED_INPUT_HASH_CHAIN", "PASS", ["content/modernization/p08_integration_matrix.json"]),
                _gate("ALL_PHASE_RUNTIME_ACCEPTANCE", "BLOCKED", ["content/modernization/p08_release_handoff.json"]),
                _gate("ACTIVE_BASELINE_PROMOTION", "NOT_AUTHORIZED", ["config/active_play_baseline.json"]),
            ],
            "blockers": ["P02_TO_P07_NOT_DONE", "RELEASE_READY_FALSE"],
        },
    ]


def _traceability() -> list[dict[str, Any]]:
    rows = [
        ("P01_IDENTITY", "P01", "identity_contract + Stage63 metadata", "tests/test_modernization_p01.py", "IMPLEMENTED_AND_VERIFIED"),
        ("P01_COLLECTION_RUNTIME", "P01", "Stage63 collection runtime correction", "tests/test_modernization_p01_rom.py", "IMPLEMENTED_AND_VERIFIED"),
        ("P02_EVOLUTION_CONTRACT", "P02", "p02_evolution_contract", "tests/test_modernization_p02.py", "STATIC_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P02_RAYQUAZA_SLICE", "P02", "Stage64 exact 2-byte repair", "tests/test_modernization_p02_stage64.py", "CHECKPOINT_VERIFIED"),
        ("P02_ACTUAL_CONSUMERS", "P02", "6種level+held-item root repair + hidden ability実測readback + actual consumers", "scripts/run_modernization_p02_acceptance.py", "PARTIAL_ACCEPTANCE_24_CASES_X2_HIDDEN_ABILITY_READBACK"),
        ("P02_FULL_RUNTIME", "P02", "deferred runtime acceptance", "tests/test_modernization_p02_mgba.py", "BLOCKED"),
        ("P03_ORIGINAL_LEARNSETS", "P03", "streamed 1300/118528 contract", "tests/test_modernization_p03.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P03_STAGE65_SLICE", "P03", "Stage65 Caterpie 4-route ancestor checkpoint", "tests/test_modernization_p03_stage65.py", "PRESERVED_ANCESTOR_CHECKPOINT"),
        ("P03_STAGE66_BULK", "P03", "Stage66 47,548-route bulk ROM checkpoint", "tests/test_modernization_p03_stage66.py", "INTEGRATED_CHECKPOINT_NOT_P03_DONE"),
        ("P03_STAGE67_CONSUMERS", "P03", "Stage67 evolution/tutor/normal-egg 3,603-route consumer checkpoint", "tests/test_modernization_p03_stage67.py", "INTEGRATED_CHECKPOINT_NOT_P03_DONE"),
        ("P04_CANDIDATE_SCOPE", "P04", "49 Mega採用候補 + Winds/Waves 3種非採用 + 2 hold", "tests/test_modernization_p04_sources.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P04_ASSET_IMPORT", "P04", "private-use asset import manifest", "tests/test_modernization_p04_asset_importer.py", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY"),
        ("P04_CAPACITY_RESERVATION", "P04", "49/45/6/0 append reservation + 34-table capacity audit", "tests/test_modernization_p04_capacity.py", "INTEGRATED_CHECKPOINT_NOT_RUNTIME_READY"),
        ("P05_MOVE_ABILITY", "P05", "Side Change/Winds・Waves 3種非採用 + battle content contract", "tests/test_modernization_p05.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P05_ABILITY_HOST_RUNTIME", "P05", "6 Ability portable runtime", "tests/test_modernization_p05_ability_runtime.py", "HOST_VERIFIED_46_CASES_X2_ROM_LINK_PENDING"),
        ("P06_SPECIES_ADJUSTMENT", "P06", "empty adopted delta + review projection", "tests/test_modernization_p06.py", "CHECKPOINT_NO_ADOPTED_DELTA"),
        ("P07_CROSS_DISTRIBUTION", "P07", "empty explicit layered delta", "tests/test_modernization_p07.py", "CHECKPOINT_NO_ADOPTED_DELTA"),
        ("P08_INPUT_AND_COMPLETION_GUARD", "P08", "pinned integration validator", "tests/test_modernization_p08.py", "IMPLEMENTED_CHECKPOINT_ONLY"),
        ("P08_RELEASE", "P08", "release handoff", "tests/test_modernization_p08.py", "BLOCKED"),
    ]
    return [
        {
            "requirement_key": key,
            "phase": phase,
            "implementation_evidence": implementation,
            "test_evidence": test,
            "status": status,
        }
        for key, phase, implementation, test, status in rows
    ]


def build_integration_matrix(root: Path) -> dict[str, Any]:
    root = root.resolve()
    documents, identities, tracked = _audit_inputs(root)
    artifact_audit, metadata = _audit_candidate_artifacts(root)
    by_artifact = _identity_by_path(artifact_audit["artifacts"])
    active_markdown = _regular_bytes(root, "design/active_play_baseline.md")
    active = validate_active_baseline(
        documents["config/active_play_baseline.json"],
        active_markdown,
        by_artifact["build/stages/62_npc_placement_integrity_repair.gba"],
    )
    candidate_chain = _validate_candidate_chain(
        artifact_audit,
        metadata,
        documents["config/modernization_candidate.json"],
    )
    _validate_contract_chain(documents)
    source_bindings = _audit_declared_source_bindings(root, documents, tracked)
    implementation_inputs = _audit_implementation_inputs(root, tracked)
    phases = _phase_records(documents)
    fingerprint = _sha256(stable_json(identities))
    implementation_fingerprint = _sha256(stable_json(implementation_inputs))
    integration_fingerprint = build_integration_fingerprint(
        identities,
        implementation_inputs,
        source_bindings,
        artifact_audit["artifacts"],
        phases,
    )
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "snapshot": {
            "selection_base_head": SNAPSHOT_BASE_HEAD,
            "mode": "EXPLICIT_TRACKED_PATH_LIST_WITH_EXACT_WORKTREE_CONTENT_HASHES",
            "auto_discovery": False,
            "tracked_input_count": len(identities),
            "tracked_input_fingerprint_sha256": fingerprint,
            "tracked_inputs": identities,
            "implementation_input_count": len(implementation_inputs),
            "implementation_input_fingerprint_sha256": implementation_fingerprint,
            "implementation_inputs": implementation_inputs,
            "integration_fingerprint": integration_fingerprint,
            "parallel_outputs": PARALLEL_OUTPUTS,
            "rule": "後発成果は存在だけで採用せず、固定path listと生成済みsnapshot hashを明示更新して再監査する",
        },
        "active_play_baseline": active,
        "candidate_chain": candidate_chain,
        "candidate_artifacts": artifact_audit["artifacts"],
        "referenced_source_bindings": source_bindings,
        "phases": phases,
        "traceability": _traceability(),
        "integration_summary": {
            "phase_count": 8,
            "completed_phase_count": 1,
            "completed_phases": ["P01"],
            "checkpoint_or_blocked_phase_count": 7,
            "active_stage": 62,
            "highest_pinned_candidate_stage": 67,
            "runtime_reflected_phase_count": 3,
            "release_ready": False,
        },
        "release_blockers": [
            "P02_FULL_EVOLUTION_ACCEPTANCE_NOT_COMPLETE",
            "P03_STAGE67_CONSUMER_CHECKPOINT_INTEGRATED_BUT_67218_SELECTED_ROUTES_REMAIN",
            "P04_49_MEGA_ASSET_AND_CAPACITY_CHECKPOINTS_INTEGRATED_BUT_ID_MATERIALIZATION_ROM_AND_RIGHTS_REVIEW_NOT_COMPLETE",
            "P05_SIDE_CHANGE_EXCLUDED_BUT_SIX_ABILITIES_NOT_ROM_LINKED",
            "P06_NO_ADOPTED_SPECIES_ADJUSTMENT",
            "P07_NO_ADOPTED_CROSS_DISTRIBUTION_AND_RUNTIME_NOT_COMPLETE",
            "CANDIDATE_STAGE67_IS_NOT_ACTIVE_STAGE62",
        ],
        "runtime_execution": {
            "heavy_rom_execution_performed_by_p08": False,
            "existing_evidence_reused": True,
            "new_rom_written": False,
            "active_baseline_written": False,
        },
    }
    validate_integration_matrix(matrix)
    return matrix


def validate_integration_matrix(matrix: Mapping[str, Any]) -> None:
    _require(matrix.get("schema_version") == SCHEMA_VERSION and matrix.get("task") == TASK, "P08 matrix identity不正")
    _require(matrix.get("status") == STATUS and matrix.get("release_ready") is False, "P08をrelease candidateと誤表示しています")
    snapshot = matrix.get("snapshot")
    _require(isinstance(snapshot, Mapping) and snapshot.get("auto_discovery") is False, "P08 input listが固定されていません")
    rows = snapshot.get("tracked_inputs") if isinstance(snapshot, Mapping) else None
    _require(isinstance(rows, list) and len(rows) == len(PINNED_TRACKED_INPUTS), "P08固定入力件数不一致")
    actual_by_path = _identity_by_path(rows)
    _require(set(actual_by_path) == set(PINNED_TRACKED_INPUTS), "P08固定入力path集合不一致")
    for path, (size, digest, phase) in PINNED_TRACKED_INPUTS.items():
        row = actual_by_path[path]
        _require(row.get("size") == size and row.get("sha256") == digest and row.get("phase") == phase, f"P08固定入力identity不一致: {path}")
    _require(snapshot.get("tracked_input_fingerprint_sha256") == _sha256(stable_json(rows)), "P08 input fingerprint不一致")
    implementation_rows = snapshot.get("implementation_inputs")
    _require(
        isinstance(implementation_rows, list)
        and len(implementation_rows) == len(PINNED_IMPLEMENTATION_PATHS)
        and snapshot.get("implementation_input_count") == len(implementation_rows),
        "P08 implementation source件数不一致",
    )
    implementation_by_path = _identity_by_path(implementation_rows)
    _require(
        set(implementation_by_path) == set(PINNED_IMPLEMENTATION_PATHS),
        "P08 implementation source path集合不一致",
    )
    for path, phase in PINNED_IMPLEMENTATION_PATHS.items():
        row = implementation_by_path[path]
        _require(
            row.get("phase") == phase
            and isinstance(row.get("size"), int) and row.get("size") > 0
            and isinstance(row.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
            f"P08 implementation source identity不正: {path}",
        )
    _require(
        snapshot.get("implementation_input_fingerprint_sha256")
        == _sha256(stable_json(implementation_rows)),
        "P08 implementation source fingerprint不一致",
    )
    active = matrix.get("active_play_baseline")
    _require(isinstance(active, Mapping) and active.get("stage") == 62 and active.get("changed") is False and active.get("candidate_auto_promoted") is False, "P08 active baseline境界不正")
    _require(
        active.get("config_sha256")
        == PINNED_TRACKED_INPUTS["config/active_play_baseline.json"][1]
        and active.get("documentation_sha256")
        == PINNED_TRACKED_INPUTS["design/active_play_baseline.md"][1],
        "P08 active baseline正本hash不一致",
    )
    active_rom = active.get("rom")
    stage62_expected = CANDIDATE_ARTIFACTS[
        "build/stages/62_npc_placement_integrity_repair.gba"
    ]
    _require(
        isinstance(active_rom, Mapping)
        and active_rom.get("size") == stage62_expected[0]
        and active_rom.get("sha256") == stage62_expected[1]
        and active_rom.get("crc32") == stage62_expected[2],
        "P08 active Stage62 ROM identity不一致",
    )
    artifact_rows = matrix.get("candidate_artifacts")
    _require(
        isinstance(artifact_rows, list)
        and set(_identity_by_path(artifact_rows)) == set(CANDIDATE_ARTIFACTS),
        "P08候補artifact集合不一致",
    )
    artifact_by_path = _identity_by_path(artifact_rows)
    for path, (size, digest, crc) in CANDIDATE_ARTIFACTS.items():
        row = artifact_by_path[path]
        _require(
            row.get("size") == size and row.get("sha256") == digest
            and (crc is None or row.get("crc32") == crc),
            f"P08候補artifact identity不一致: {path}",
        )
    chain = matrix.get("candidate_chain")
    _require(isinstance(chain, Mapping) and chain.get("active_stage") == 62 and chain.get("selected_checkpoint_stage") == 67 and chain.get("stage65_integrated") is True and chain.get("stage66_integrated") is True and chain.get("stage67_integrated") is True and chain.get("release_candidate") is False, "P08候補chain境界不正")
    _require(
        chain.get("registry") == {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "P03_STAGE67_CONSUMERS_VERIFIED_CHECKPOINT",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT",
            "checkpoint_commit": "b4bdb67fcb9c49414661b2c591e0b1d9464aeafe",
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 66,
            "candidate_stage": 67,
        },
        "P08 candidate v2 registryの完了/checkpoint/親chain境界不正",
    )
    _require(
        chain.get("stage65_scope") == {
            "representative_species": 1,
            "routes_materialized": 4,
            "routes_remaining": 118524,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "P03 Stage65 scopeを全P03完了と誤認しています",
    )
    _require(
        chain.get("stage66_scope") == {
            "corrected_targets": 1300,
            "source_routes_validated": 118528,
            "routes_materialized": 47548,
            "routes_remaining": 70980,
            "level_up_routes_materialized": 18515,
            "machine_existing_slot_routes_materialized": 29033,
            "machine_supply_required_routes_deferred": 26347,
            "move_1063_routes_deferred": 159,
            "consumers_exercised": ["level_up", "machine"],
            "full_p03_done": False,
        },
        "P03 Stage66 scopeを全P03完了と誤認しています",
    )
    _require(
        chain.get("stage67_scope") == {
            "source_routes": 118528,
            "selected_routes": 118369,
            "non_adopted_move_1063_routes": 159,
            "stage67_new_materialized_routes": 3603,
            "cumulative_materialized_routes": 51151,
            "selected_routes_remaining": 67218,
            "evolution_routes_materialized": 341,
            "tutor_existing_slot_routes_materialized": 740,
            "normal_egg_routes_materialized": 2522,
            "p02_overlay_changed_bytes": 60,
            "stage67_changed_bytes_from_overlay": 46455,
            "future_tail_remaining_bytes": 62510,
            "consumers_exercised": ["evolution", "tutor", "egg"],
            "full_p03_done": False,
        },
        "P03 Stage67 scopeを全P03完了と誤認しています",
    )
    _require(snapshot.get("parallel_outputs") == PARALLEL_OUTPUTS, "P08並行成果の非統合境界不正")
    source_bindings = matrix.get("referenced_source_bindings")
    binding_counts = {
        binding: sum(
            1 for row in source_bindings
            if isinstance(row, Mapping) and row.get("binding") == binding
        )
        for binding in EXPECTED_EVIDENCE_SOURCE_COUNTS
    } if isinstance(source_bindings, list) else {}
    _require(
        isinstance(source_bindings, list)
        and binding_counts == EXPECTED_EVIDENCE_SOURCE_COUNTS
        and all(
            isinstance(row, Mapping) and row.get("status") == "PASS"
            for row in source_bindings
        ),
        "P02/P03 evidence source/hash binding監査が不完全です",
    )
    phases = matrix.get("phases")
    _require(isinstance(phases, list) and [row.get("phase") for row in phases] == [f"P0{i}" for i in range(1, 9)], "P08 phase集合/順序不正")
    expected_integration_fingerprint = build_integration_fingerprint(
        rows,
        implementation_rows,
        source_bindings,
        artifact_rows,
        phases,
    )
    _require(
        snapshot.get("integration_fingerprint")
        == expected_integration_fingerprint,
        "P08 composite integration fingerprint不一致",
    )
    completion = {row["phase"]: row.get("completion_state") for row in phases}
    _require(completion["P01"] == "COMPLETED", "P01 completionが失われています")
    for phase in ("P02", "P03", "P04", "P05", "P06", "P07"):
        _require(completion[phase] == "CHECKPOINT_NOT_DONE", f"{phase}を虚偽DONEとしています")
    _require(completion["P08"] == STATUS, "P08自身をDONE/release扱いしています")
    # static contractのPASSは工程完了を意味しない。
    by_phase = {row["phase"]: row for row in phases}
    _require("PASS" in by_phase["P02"]["contract_statuses"] and by_phase["P02"]["completion_state"] != "COMPLETED", "P02 PASSを工程DONEと誤認しています")
    _require("PASS" in by_phase["P03"]["contract_statuses"] and by_phase["P03"]["completion_state"] != "COMPLETED", "P03 PASSを工程DONEと誤認しています")
    _require(
        by_phase["P02"].get("adoption", {}).get(
            "hidden_ability_readback_verified"
        ) is True
        and by_phase["P02"].get("adoption", {}).get(
            "hidden_ability_bit_mask"
        ) == 16
        and by_phase["P02"].get("adoption", {}).get(
            "hidden_ability_observed_case_count"
        ) == 24,
        "P02 hidden ability実測readback境界不正",
    )
    _require(
        by_phase["P02"].get("rom_reflection")
        == {
            "reflected": True,
            "stage": 67,
            "ancestor_stage": 64,
            "scope": "RAYQUAZA_FIX_PLUS_6_SPECIES_PRIORITY_REPAIR_IN_STAGE67_OVERLAY",
        },
        "P02 Stage64祖先＋Stage67 overlay反映境界不正",
    )
    _require(
        by_phase["P03"].get("rom_reflection", {}).get("stage") == 67
        and by_phase["P03"].get("adoption", {}).get("stage65_preserved_ancestor_routes") == 4
        and by_phase["P03"].get("adoption", {}).get("stage66_routes_materialized") == 47548
        and by_phase["P03"].get("adoption", {}).get("runtime_selected_routes") == 118369
        and by_phase["P03"].get("adoption", {}).get("side_change_1063_excluded_routes") == 159
        and by_phase["P03"].get("adoption", {}).get("side_change_1063_adopted_routes") == 0
        and by_phase["P03"].get("adoption", {}).get("side_change_1063_replacement_move_key") is None
        and by_phase["P03"].get("adoption", {}).get("cumulative_routes_materialized") == 51151
        and by_phase["P03"].get("adoption", {}).get("selected_routes_remaining") == 67218
        and by_phase["P03"].get("adoption", {}).get("stage67_new_routes_materialized") == 3603,
        "P03 Stage67 consumer checkpointの統合境界不正",
    )
    _require(
        by_phase["P05"].get("adoption", {}).get("new_move_requirements") == 0
        and by_phase["P05"].get("adoption", {}).get("non_adopted_move_candidates") == 1
        and by_phase["P05"].get("adoption", {}).get("side_change_1063_adopted") is False
        and by_phase["P05"].get("adoption", {}).get("new_abilities") == 6
        and by_phase["P05"].get("adoption", {}).get("non_adopted_p04_records") == 3
        and by_phase["P05"].get("adoption", {}).get("ability_host_runtime_cases") == 46
        and by_phase["P05"].get("adoption", {}).get("ability_host_runtime_processes") == 2,
        "P05 Side Change非採用/6 Ability host runtime境界不正",
    )
    p04_staging = by_phase["P04"].get("adoption", {}).get("asset_staging", {})
    p04_adoption = by_phase["P04"].get("adoption", {})
    p04_capacity = by_phase["P04"].get("adoption", {}).get(
        "capacity_reservation", {}
    )
    _require(
        p04_adoption.get("selected_candidate_records") == 49
        and p04_adoption.get("mega_records") == 49
        and p04_adoption.get("new_species_reference_records") == 3
        and p04_adoption.get("adopted_new_species_records") == 0
        and p04_adoption.get("non_adopted_user_scope_records") == 3,
        "P04 49 Mega採用/Winds・Waves 3種非採用境界不正",
    )
    _require(
        p04_staging == {
            "mega_covered": 49, "mega_required": 49,
            "stones_covered": 45, "stones_required": 45,
            "palette_ready": 49, "palette_required": 49,
            "winds_waves_covered": 0, "winds_waves_required": 0,
            "missing_assets": 0,
            "payload_file_count": 670,
            "payload_total_bytes": 426648,
            "asset_set_sha256": "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c",
        }
        and by_phase["P04"].get("rom_reflection", {}).get("reflected") is False,
        "P04 importer staging-only coverage境界不正",
    )
    _require(
        p04_capacity == {
            "capacity_basis_stage": 65,
            "species_form": [1621, 1669],
            "item": [999, 1043],
            "ability": [312, 317],
            "move": None,
            "move_append_count": 0,
            "fixed_table_count": 34,
            "fixed_table_delta_bytes": 19857,
            "aligned_bundle_bytes": 636392,
            "integration_modules_remaining_bytes": 1124296,
            "stage66_cross_check": {
                "allocation_region": "future_tail",
                "allocation_start": 33399368,
                "allocation_size": 60116,
                "allocation_end_exclusive": 33459484,
                "stage65_future_tail_remaining_bytes": 155064,
                "stage66_future_tail_remaining_bytes": 94948,
                "p04_candidate_region": "integration_modules",
                "p04_candidate_start": 21307984,
                "p04_candidate_end_exclusive": 23068672,
                "overlap": False,
            },
            "runtime_ready": False,
        },
        "P04 capacity予約をruntime実装済みと誤認しています",
    )
    _require(all(row.get("required_gates") for row in phases), "必須gate一覧が欠落しています")
    trace = matrix.get("traceability")
    _require(isinstance(trace, list) and len(trace) >= 14, "要件→実装→test対応が不足しています")
    _require(all(row.get("requirement_key") and row.get("implementation_evidence") and row.get("test_evidence") and row.get("status") for row in trace), "traceability rowが不完全です")
    summary = matrix.get("integration_summary")
    _require(isinstance(summary, Mapping) and summary.get("completed_phase_count") == 1 and summary.get("completed_phases") == ["P01"] and summary.get("highest_pinned_candidate_stage") == 67 and summary.get("runtime_reflected_phase_count") == 3 and summary.get("release_ready") is False, "P08統合summaryがP01のみ完了/Stage67 checkpointと不一致です")
    _require(len(matrix.get("release_blockers", [])) == 7, "P08 release blocker集合不一致")
    execution = matrix.get("runtime_execution")
    _require(isinstance(execution, Mapping) and execution.get("heavy_rom_execution_performed_by_p08") is False and execution.get("new_rom_written") is False and execution.get("active_baseline_written") is False, "P08 checkpointがROM/baselineを変更しています")


def build_runtime_handoff(matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "active_play_baseline": matrix["active_play_baseline"],
        "candidate_chain": matrix["candidate_chain"],
        "integration_fingerprint": matrix["snapshot"]["integration_fingerprint"],
        "phase_runtime": [
            {
                "phase": row["phase"],
                "completion_state": row["completion_state"],
                "rom_reflection": row["rom_reflection"],
                "required_gates": row["required_gates"],
                "blockers": row["blockers"],
            }
            for row in matrix["phases"]
        ],
        "runtime_execution": matrix["runtime_execution"],
    }


def build_release_handoff(matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": STATUS,
        "release_ready": False,
        "active_stage": 62,
        "candidate_stage": 67,
        "completed_phases": ["P01"],
        "not_completed_phases": ["P02", "P03", "P04", "P05", "P06", "P07", "P08"],
        "release_blockers": matrix["release_blockers"],
        "promotion": {
            "authorized": False,
            "active_play_baseline_changed": False,
            "reason": "P02～P07のruntime acceptance未完了。Stage67は選択118,369経路中51,151経路を反映したconsumer checkpointだが67,218経路が残り、release candidateではない",
        },
        "next_integration_rule": "各工程の完成済みtracked成果だけをPINNED_TRACKED_INPUTSへ明示追加し、全hash/gate/親chainを再監査する",
        "integration_fingerprint": matrix["snapshot"]["integration_fingerprint"],
    }


__all__ = [
    "CANDIDATE_ARTIFACTS",
    "DECLARED_EVIDENCE_IDENTITY_GROUPS",
    "DECLARED_EVIDENCE_SOURCE_GROUPS",
    "EXPECTED_EVIDENCE_SOURCE_COUNTS",
    "ModernizationP08Error",
    "PARALLEL_OUTPUTS",
    "PINNED_IMPLEMENTATION_PATHS",
    "PINNED_TRACKED_INPUTS",
    "STATUS",
    "audit_declared_source_rows",
    "build_integration_fingerprint",
    "build_integration_matrix",
    "build_release_handoff",
    "build_runtime_handoff",
    "stable_json",
    "validate_active_baseline",
    "validate_integration_matrix",
    "verify_exact_bytes",
]
