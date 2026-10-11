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

from tools.release.bps import apply_bps


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P08"
STATUS = "CHECKPOINT_NOT_RELEASE_CANDIDATE"
SNAPSHOT_BASE_HEAD = "137c6945c6bf5c633944ddd5287dffca9c5692c0"
STAGE75_IMPLEMENTATION_COMMIT = "595909446b6ad67749c9894b23fdc536f82c638e"
STAGE76_IMPLEMENTATION_COMMIT = "cbf98eddf712ee677eef011e6fc106a67e536c08"

LATEST_INCREMENTAL_BPS_PATHS: tuple[tuple[str, str, str], ...] = (
    (
        "build/stages/69_modernization_floette_gift.gba",
        "build/stages/70_modernization_p04_species_runtime.bps",
        "build/stages/70_modernization_p04_species_runtime.gba",
    ),
    (
        "build/stages/70_modernization_p04_species_runtime.gba",
        "build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps",
        "build/stages/71_modernization_p04_mega_runtime.gba",
    ),
    (
        "build/stages/71_modernization_p04_mega_runtime.gba",
        "build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps",
        "build/stages/72_modernization_p05_ability_rom_runtime.gba",
    ),
    (
        "build/stages/72_modernization_p05_ability_rom_runtime.gba",
        "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps",
        "build/stages/73_modernization_p03_consumer_runtime.gba",
    ),
    (
        "build/stages/73_modernization_p03_consumer_runtime.gba",
        "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps",
        "build/stages/74_modernization_p03_supply_runtime.gba",
    ),
    (
        "build/stages/74_modernization_p03_supply_runtime.gba",
        "build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps",
        "build/stages/75_modernization_rockruff_own_tempo.gba",
    ),
    (
        "build/stages/75_modernization_rockruff_own_tempo.gba",
        "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
        "build/stages/76_modernization_p05_edges.gba",
    ),
    (
        "build/stages/76_modernization_p05_edges.gba",
        "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps",
        "build/stages/77_modernization_p05_circus_suppression.gba",
    ),
)

CANDIDATE_PATCH_CHAIN_PATHS: tuple[tuple[str, str, str, str], ...] = (
    (
        "stage67_to_stage68",
        "build/stages/67_modernization_p02_p03_consumers.gba",
        "build/stages/68_modernization_mega_shop.bps",
        "build/stages/68_modernization_mega_shop.gba",
    ),
    (
        "stage68_to_stage69",
        "build/stages/68_modernization_mega_shop.gba",
        "build/stages/69_modernization_floette_gift.bps",
        "build/stages/69_modernization_floette_gift.gba",
    ),
    (
        "stage69_to_stage70",
        "build/stages/69_modernization_floette_gift.gba",
        "build/stages/70_modernization_p04_species_runtime.bps",
        "build/stages/70_modernization_p04_species_runtime.gba",
    ),
    (
        "stage70_to_stage71",
        "build/stages/70_modernization_p04_species_runtime.gba",
        "build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps",
        "build/stages/71_modernization_p04_mega_runtime.gba",
    ),
    (
        "stage71_to_stage72",
        "build/stages/71_modernization_p04_mega_runtime.gba",
        "build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps",
        "build/stages/72_modernization_p05_ability_rom_runtime.gba",
    ),
    (
        "stage72_to_stage73",
        "build/stages/72_modernization_p05_ability_rom_runtime.gba",
        "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps",
        "build/stages/73_modernization_p03_consumer_runtime.gba",
    ),
    (
        "stage73_to_stage74",
        "build/stages/73_modernization_p03_consumer_runtime.gba",
        "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps",
        "build/stages/74_modernization_p03_supply_runtime.gba",
    ),
    (
        "stage74_to_stage75",
        "build/stages/74_modernization_p03_supply_runtime.gba",
        "build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps",
        "build/stages/75_modernization_rockruff_own_tempo.gba",
    ),
    (
        "stage75_to_stage76",
        "build/stages/75_modernization_rockruff_own_tempo.gba",
        "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
        "build/stages/76_modernization_p05_edges.gba",
    ),
    (
        "from_parent",
        "build/stages/76_modernization_p05_edges.gba",
        "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps",
        "build/stages/77_modernization_p05_circus_suppression.gba",
    ),
)

RELEASE_BLOCKERS: tuple[str, ...] = (
    "P02_STAGE71_EXACT_UI_ACCEPTANCE_PENDING_AND_PRODUCTION_RUNTIME_UNJUDGED",
    "P03_STAGE75_OWN_TEMPO_ROCKRUFF_CONNECTED_BUT_PROVISIONAL_ARCHIVE_ECONOMY_AND_FINAL_MGBA_REMAIN",
    "P04_STAGE71_49_MEGA_RUNTIME_CONNECTED_BUT_FINAL_MGBA_AND_FLOETTE_FULL_FRESH_RELOAD_REMAIN",
    "P05_STAGE77_BATTLE_CIRCUS_SUPPRESSION_CONNECTED_BUT_EELEVATE_SWITCH_AI_AND_FINAL_CUMULATIVE_MGBA_REMAIN",
    "P06_NO_ADOPTED_SPECIES_ADJUSTMENT",
    "P07_NO_ADOPTED_CROSS_DISTRIBUTION_AND_RUNTIME_NOT_COMPLETE",
    "CANDIDATE_STAGE77_IS_NOT_ACTIVE_STAGE62",
)

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
        25208, "a7ec3f1ed18a0e058e37a6a50195437c2b411a3f4a9622afb94fe4028436505a", "CANDIDATE_CHAIN"
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
    "config/modernization_mega_shop.json": (
        4298, "ac60c5941e2d510d9473353290a51b019c35198bf7f6466fae17b8f32cfb5fc3", "P04"
    ),
    "config/modernization_mega_shop_item_bounds.json": (
        6508, "f0ce972f39ec12fe5a2259ea588e954fed0a40f84916bb6662eabe5092573ec6", "P04"
    ),
    "config/modernization_mega_shop_pointer_sites.json": (
        30219, "a5bd12b2ae08bbb7bcc1bbb6e14441ba8f9edcc4d43fad4b1cfebaefc2b59019", "P04"
    ),
    "content/modernization/mega_shop_catalog.json": (
        35588, "ddb8f0828ea998bbf04fd22dda80d722ee26c08c5f01705e93f48988ae8f2ed9", "P04"
    ),
    "content/modernization/mega_shop_checkpoint.json": (
        37093, "8ef28eb0395aa7a4d91623914b1e5136b94f3fb387206e20d456e973ceed0b29", "P04"
    ),
    "content/modernization/mega_shop_mgba_runtime_gate.json": (
        4318, "5b7b499ccb5af5777033aad1b1d234b2ec49c785d5fe02f818f9312715f8f03c", "P04"
    ),
    "config/modernization_floette_gift.json": (
        6670, "140da74d3e43a857b728417eeb8c701f44cfed0f6575719a6ff13ccab9c093c8", "P04"
    ),
    "content/modernization/floette_gift_contract.json": (
        22396, "6c28376c1356fa0df08dabc58408449d69bf676514efbc23f1ed84b555a7ace5", "P04"
    ),
    "content/modernization/floette_gift_checkpoint.json": (
        27893, "25f729c990975d0ef5164192ca69af5fc9965fdb30118b2dafa2fa2e71ab2a71", "P04"
    ),
    "content/modernization/floette_gift_mgba_runtime_gate.json": (
        4119, "1547522c0ddd386ec997514ee0363868e0918e8cb2e24ccc861be8abfab79cc0", "P04"
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
    "config/modernization_p02_stage71_acceptance_gate.json": (
        6632, "90b18fecb127aa3cbea31558f5ffc3d194a9e5f67c7e3b4a94dad4f562f32007", "P02"
    ),
    "content/modernization/p02_stage71_acceptance_checkpoint.json": (
        13359, "78734433ec215d376ab862d607d939be707abf200735c60f97d621bcd6aa4531", "P02"
    ),
    "config/modernization_p03_stage73_consumers.json": (
        5064, "61d53ed8059c2fbad935885d995c4a406b9e4b19b8e3035d688742188f4f0b27", "P03"
    ),
    "config/modernization_p03_stage73_runtime.json": (
        6839, "7e3110936c10421086d883b411c10283be5ca98f926bd41f61d149d91a50b4f7", "P03"
    ),
    "content/modernization/p03_stage73_consumer_runtime_checkpoint.json": (
        2857, "ea930a0df1d48aba9da9e6ea1bb808b117d3c03d2cdb297752c557b28f0bf82d", "P03"
    ),
    "content/modernization/p03_stage73_consumer_runtime_route_audit.json": (
        12992, "d3af91e38635c12e0f985ab8f1f2467d81cb1acd8e2716c5dd285eda98044275", "P03"
    ),
    "config/modernization_p03_stage74_supply.json": (
        10937, "aa3cdd33683be5799a30184dfa03485012f03fa5928d0c341028ff88722708fc", "P03"
    ),
    "content/modernization/p03_stage74_supply_runtime_checkpoint.json": (
        4162, "5e73c008a866d579a7939f64eb02f78d2d55eb7efb31f18c4ce2b221ee977ba2", "P03"
    ),
    "config/modernization_rockruff_own_tempo_stage75.json": (
        8066, "2accef3c5cb3e45e3b032035acfbc727b2785deafd652a45f56ca0db3ebbf121", "P03"
    ),
    "content/modernization/rockruff_own_tempo_stage75_contract.json": (
        5799, "f57efb88124fdf18681a012d520d4382b715763c917fd40eb56a30ba6dce5684", "P03"
    ),
    "content/modernization/rockruff_own_tempo_stage75_checkpoint.json": (
        4874, "c4f6d822950cd27fa65134d3806c2cbed3409b6de4b2358a8f12924524d65705", "P03"
    ),
    "config/modernization_p04_species_runtime.json": (
        11675, "260537ad559a5891bf238058159623e506d6901bb46839aa40e831ef6ede7e11", "P04"
    ),
    "content/modernization/p04_species_runtime_contract.json": (
        413133, "80ded428ec1df683b758555c8e4357123baee2ce8b5201dea960fa89618818a4", "P04"
    ),
    "content/modernization/p04_species_runtime_checkpoint.json": (
        59914, "a0a1f12bada8fe57545be67e24e4ef7016821ab8ae80624b6de3f4b6822f0dbf", "P04"
    ),
    "config/modernization_p04_mega_runtime.json": (
        14614, "3c3116a95d2b39b20b43f032aad0582ca11012390ede4ecffc85a400cad7c765", "P04"
    ),
    "content/modernization/p04_mega_runtime_mapping.json": (
        59026, "31e4a36301dda169f7b894a62ee823d00ebd1374945a33f1478f3c9eecf5401f", "P04"
    ),
    "content/modernization/p04_mega_runtime_checkpoint.json": (
        30529, "0277f745b2f09af0e111cdcdd580bfb3104a74b95afc63ad45770fce539ae73c", "P04"
    ),
    "config/modernization_p05_ability_rom_runtime.json": (
        8975, "862fa1e89606a00ee71350c107c53014722392c4cd8c06af93dbcbe405b42cd6", "P05"
    ),
    "content/modernization/p05_ability_rom_runtime_checkpoint.json": (
        1464, "1683e4fa6d2ed8d445e8ffd7d78aa97004a52e537453d1abf1394afbeb9f71bb", "P05"
    ),
    "content/modernization/p05_ability_rom_runtime_surface_matrix.json": (
        3737, "0cff6c86ac2d18d3858d0921931df3de8457cd0951d3defcf250362fd8a5d94b", "P05"
    ),
    "config/modernization_p05_stage76_edges.json": (
        11451, "98da12855ec46c456e0a01912d33659ce2a4d7d49fb250e131355ff6e48eb26f", "P05"
    ),
    "content/modernization/p05_stage76_edges_contract.json": (
        3469, "e7bb30ccd0fe8540970295d0ad3f9ced6ce6aeb67bfcd1c67ab7cd4cf0ba295b", "P05"
    ),
    "content/modernization/p05_stage76_edges_checkpoint.json": (
        7018, "f2951cd2a1cb770d5d325e8f1f596f6251f855e19b2e92d7c05b4f5ce205aa23", "P05"
    ),
    "config/modernization_p05_stage77_suppression.json": (
        25769, "c2f2612191ab35b8c9ca12ef8a3ac683d47d5ff3b4f42aa29f882d3693aebd12", "P05"
    ),
    "content/modernization/p05_stage77_suppression_contract.json": (
        5053, "68ae45c8253fa907d594f3a4b5668bd750e91166b3747d153a2420a9e37bb3de", "P05"
    ),
    "content/modernization/p05_stage77_suppression_checkpoint.json": (
        12579, "aa169bcefca033474bca131f3f5322ab6ec37000c2ed945c970f12f3505e55fa", "P05"
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
    "build/stages/68_modernization_mega_shop.gba": (
        33554432, "1ff9103becdeff8a22b5ffd45d3487b87d23bc7656415d660652d8a413da9639", "DAFDD099"
    ),
    "build/stages/68_modernization_mega_shop.json": (
        59479, "f2d046b20ba93ed745823cf73da467ad0c886ce1e94a984213e9aa4d536db75e", None
    ),
    "build/stages/68_modernization_mega_shop_allocation.json": (
        41017, "f5e1745c9ebd9a12e7b84c02fb7d2ae6972b94e90f7c355f8e11f6dc22585d4b", None
    ),
    "build/stages/68_modernization_mega_shop.bps": (
        59135, "d360cfb630ae60f740f10d7cfcb25bfbefe7e0ff95a7ec1042d3c7998ea3952c", None
    ),
    "build/stages/69_modernization_floette_gift.gba": (
        33554432, "6532002dabd3197ee6b8ded8b153a495d3241acf062fc931210987093172cb95", "4849DD0F"
    ),
    "build/stages/69_modernization_floette_gift.json": (
        14772, "1a375d8af0638cefe14a610505bd06ca22927a472e26573e9d783da62b14de66", None
    ),
    "build/stages/69_modernization_floette_gift_allocation.json": (
        41584, "a5be7b923d4cd09466b89ddd4482a2f56fac1b3660de91737e5590eb127ae265", None
    ),
    "build/stages/69_modernization_floette_gift.bps": (
        1849, "4a630083fe5152010516a4d511696bc0ccededd536f3386b4c12d039a5d42bd0", None
    ),
    "build/stages/70_modernization_p04_species_runtime.gba": (
        33554432, "5519bda92ddc9024e9dcd7583fc170797f533f78e5fb552bda328f246722f3ef", "301238C1"
    ),
    "build/stages/70_modernization_p04_species_runtime.json": (
        469965, "b2b58dda953398206002ccdc450853aacdf5975ff9cfb923db8fa99f13f840dc", None
    ),
    "build/stages/70_modernization_p04_species_runtime_allocation.json": (
        42175, "3c685b4ea01d9ec6d18b4b3ec97fa83e1d6d4f79ed67cfba7617a9e019224fb8", None
    ),
    "build/stages/70_modernization_p04_species_runtime.bps": (
        538759, "76c562226dcebcf970414faca190e9295df8120d6d8190986e30c7f4e4f20047", None
    ),
    "build/stages/71_modernization_p04_mega_runtime.gba": (
        33554432, "dbcc1194511f234c7d34c196082d59bfc0cb6aca6bb3b9c0f911bc8add4230bb", "426A7A7F"
    ),
    "build/stages/71_modernization_p04_mega_runtime.json": (
        30073, "7050385f0609ec61c7356cef2d0f44c92e42ea72e7295a6bc0bf00968896419c", None
    ),
    "build/stages/71_modernization_p04_mega_runtime_allocation.json": (
        42175, "814cb27f4a5028ddc9bb544b8f1aca7947ac9ba0fb67d638b70af54b17812cbf", None
    ),
    "build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps": (
        979, "6c3a8877a25f17cd97977152bf90c401dea13f4f1cb20302eb9c0adbc889f487", None
    ),
    "build/stages/72_modernization_p05_ability_rom_runtime.gba": (
        33554432, "f27411a2dcef2ec2c1f3c06de624b24838683f5e77017fafa9bf445edc00d059", "F981D1CB"
    ),
    "build/stages/72_modernization_p05_ability_rom_runtime.json": (
        15789, "d3998b9d8a2eea0b2fff7dbc79538673d0bd48931faa373e277a12dd36c28c8f", None
    ),
    "build/stages/72_modernization_p05_ability_rom_runtime_allocation.json": (
        42769, "8caad52acb7cf8a16dd6105526c844935119c01d56895508a710be0de9d5f9e2", None
    ),
    "build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps": (
        7635, "9e9933d85e5b6cfc75a81efd49f214b3037af9ee50070dd7521ad5c2cab54a9a", None
    ),
    "build/stages/73_modernization_p03_consumer_runtime.gba": (
        33554432, "25329a1d5dd71a4f3c0adff8b337af1c4b3496e0aae64439ed2adebe338ce26a", "B4907165"
    ),
    "build/stages/73_modernization_p03_consumer_runtime.json": (
        5270, "c18fd7a2e3537632b3e13e3d528907d52e4c9c3a9729da6a0ccd539bdbc7b887", None
    ),
    "build/stages/73_modernization_p03_consumer_runtime_allocation.json": (
        43959, "f8dab8da8dadd9163f0b8249b59672d91c4b52a26a472e8392fd508c8934173a", None
    ),
    "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps": (
        36300, "8b901363aedff24d13fa60530dcb1512e02317b6da675e96586ac2dd83af6a61", None
    ),
    "build/stages/74_modernization_p03_supply_runtime.gba": (
        33554432, "481083bc50bd353955990375e3cc5e0a76f9b0f681ae54caa6c31f66ef22d65e", "C9929F79"
    ),
    "build/stages/74_modernization_p03_supply_runtime.json": (
        7600, "2fef4dbe682f23140ca14fa1169aaec50105130189428508ee9570a40fa23ae7", None
    ),
    "build/stages/74_modernization_p03_supply_runtime_allocation.json": (
        44607, "d7a2425d59aac259f2803d4b5fbd8a88f0be94c906e9262ebef69a2a31401f23", None
    ),
    "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps": (
        70627, "8480efe4b6d69233393649260943a5119d595cfd9b8bf28ddebf7ca82fd65abd", None
    ),
    "generated/runtime/modernization_p03_stage74_supply_runtime.bin": (
        70572, "e4922f42818efa4fb8d7369bcab254688a021f8950a82fc64c95bdf0714463a1", None
    ),
    "generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json": (
        4333, "49a9e87097acc46270e80f4f3bccb69f670b7c9353d3ac4b7a86d270b1542da3", None
    ),
    "generated/runtime/modernization_p03_stage74_supply_runtime_audit.json": (
        615290, "ac2899119bed544079edce56e0e13c26e9c762807e7467f9ef1117b01685eb55", None
    ),
    "generated/runtime/modernization_p03_stage74_supply_route_audit.json": (
        680038, "64b7f72f99bc01d777045536ff5ba82ab049e4e008035fe3760d377355334f10", None
    ),
    "build/stages/75_modernization_rockruff_own_tempo.gba": (
        33554432, "a179c024294f4f1bbf34eb603af255f6896265d9d8523344719b349f8a4495c3", "1511F429"
    ),
    "build/stages/75_modernization_rockruff_own_tempo.json": (
        151435, "be84b5a54c7ea8de23d4245402a427cc0dd444949363b8b6ca3e206b5ecd93f4", None
    ),
    "build/stages/75_modernization_rockruff_own_tempo_allocation.json": (
        45230, "90a68321eebbebde765077eca81643f176d91152f331be77360cb8c52e188f09", None
    ),
    "build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps": (
        336487, "23c012b655b15a3ac5d97813b4d8c64661aadb93c9bf8539d8e8c22a10bdeba7", None
    ),
    "generated/runtime/modernization_rockruff_own_tempo_stage75.bin": (
        565280, "18a62cc6fad32eb5997e569d4c340a87ed56f068826ae841dbe36a9764616206", None
    ),
    "generated/runtime/modernization_rockruff_own_tempo_stage75_symbols.json": (
        7027, "48b2251110325dcc5a03b32a0bf820d73f02fca74a51ab5ff1073a6dcc8ac769", None
    ),
    "generated/runtime/modernization_rockruff_own_tempo_stage75_audit.json": (
        1086089, "51c564a4b372e15cf43edb1899760a705c528be4af826f2a9dc8d077dac6ac99", None
    ),
    "generated/runtime/modernization_rockruff_own_tempo_stage75_route_audit.json": (
        2604, "ac3deebaa4eb190ab1e581666bb5d56aa98540e2fa15e72a2ffd22ffb1c255a5", None
    ),
    "build/stages/76_modernization_p05_edges.gba": (
        33554432, "f753f13720aeb5331cfc8a9bf9dd5fd4ad9ac34537356d20d76b73e0100100ac", "0A78B46A"
    ),
    "build/stages/76_modernization_p05_edges.json": (
        6059, "46eb197ba064f4380d6bfd31b16b7ad04bc63599707b72254adde2231aa4d792", None
    ),
    "build/stages/76_modernization_p05_edges_allocation.json": (
        45818, "64f992d8288b3d861a8e2cc160af880991e76de1eb1ae7dd4081ee4e8c59ae3e", None
    ),
    "build/patches/stage75-to-stage76-modernization-p05-edges.bps": (
        2191, "f06a18fb9c26b1d09e621eb81c208c3c6a018607e58727ac5dd04091a45b1810", None
    ),
    "generated/runtime/modernization_p05_stage76_edges.bin": (
        2066, "c9c34af10900cb6cedbaaeef9dacd2d95a2fc0df0be39cb3aa29f8226ffbc92e", None
    ),
    "generated/runtime/modernization_p05_stage76_edges_symbols.json": (
        1518, "15291753650a4d7d3af61016e2fd6960233c0b4142db5e23e7ce44c044f8faf8", None
    ),
    "generated/runtime/modernization_p05_stage76_edges_audit.json": (
        10537, "c15e42cd1fc405bf3bb007c0959fcb989f6f896e8b2bb54744cbea85b469facc", None
    ),
    "build/stages/77_modernization_p05_circus_suppression.gba": (
        33554432, "245133a4740dda9faa0663d321505ee793293d64b0b318d601fd91933b84973f", "F1CE0EAC"
    ),
    "build/stages/77_modernization_p05_circus_suppression.json": (
        5933, "773042fc80d4a048e4f4a894e01de8f073d6de42cf5f4029421c882b0c35b6ff", None
    ),
    "build/stages/77_modernization_p05_circus_suppression_allocation.json": (
        46425, "20649eff6be00d367064c51782f50f8a2e7a26b059f637b2c496c2f6f999243d", None
    ),
    "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps": (
        1489, "50a779b3cca8b7ffbb386872ed989a6392e050c18a3716e7c252c24412047df7", None
    ),
    "generated/runtime/modernization_p05_stage77_suppression.bin": (
        1220, "933c8d7fdf731eaae0aa87c74974803de356dda8e64c055ef09beee4d229c672", None
    ),
    "generated/runtime/modernization_p05_stage77_suppression_symbols.json": (
        2010, "9b939a791e054e7c114065fba42be9b945fcc4e1f05e643e00dd7b34312370fa", None
    ),
    "generated/runtime/modernization_p05_stage77_suppression_audit.json": (
        29184, "49707fa81ce04df11fcf51d5e3b49a103daaf22b0fffe324bcbc343ff4d3cb4d", None
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
    "P04_STAGE68_MEGA_STONE_BP_SHOP": {
        "status": "EXACT_ROM_RUNTIME_PASS_NOT_P04_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_mega_shop.json",
            "config/modernization_mega_shop_item_bounds.json",
            "config/modernization_mega_shop_pointer_sites.json",
            "content/modernization/mega_shop_catalog.json",
            "content/modernization/mega_shop_checkpoint.json",
            "content/modernization/mega_shop_mgba_runtime_gate.json",
            "overlays/modernization_mega_shop/modernization_mega_shop.c",
            "overlays/modernization_mega_shop/modernization_mega_shop.h",
            "overlays/modernization_mega_shop/modernization_mega_shop_host_harness.c",
            "scripts/build_modernization_mega_shop.py",
            "scripts/run_modernization_mega_shop_mgba.py",
            "tools/mgba_modernization_mega_shop_smoke.c",
            "tools/modernization_mega_shop.py",
            "tests/test_modernization_mega_shop.py",
            "tests/test_modernization_mega_shop_mgba.py",
        ],
    },
    "P04_STAGE69_FLOETTE_ETERNAL_GIFT": {
        "status": "EXACT_PARTY_PC_PARTIAL_PASS_FULL_RELOAD_PENDING_NOT_P04_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_floette_gift.json",
            "content/modernization/floette_gift_contract.json",
            "content/modernization/floette_gift_checkpoint.json",
            "content/modernization/floette_gift_mgba_runtime_gate.json",
            "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c",
            "overlays/modernization_floette_gift/modernization_floette_gift.c",
            "overlays/modernization_floette_gift/modernization_floette_gift.h",
            "overlays/modernization_floette_gift/modernization_floette_gift_host_test.c",
            "scripts/build_modernization_floette_gift.py",
            "tools/modernization_floette_gift.py",
            "tests/test_modernization_floette_gift.py",
        ],
    },
    "P02_STAGE71_EXACT_UI_ACCEPTANCE": {
        "status": "STOPPED_EXACT_UI_PENDING_PRODUCTION_UNJUDGED",
        "included": True,
        "expected_paths": [
            "config/modernization_p02_stage71_acceptance_gate.json",
            "content/modernization/p02_stage71_acceptance_checkpoint.json",
            "scripts/run_modernization_p02_stage71_acceptance.py",
            "tools/mgba_modernization_p02_stage71_acceptance_smoke.c",
            "tests/test_modernization_p02_stage71_acceptance.py",
        ],
    },
    "P03_STAGE73_PREFLIGHT": {
        "status": "INTEGRATED_PREFLIGHT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage73_consumers.json",
            "tools/modernization_p03_stage73_consumers.py",
            "tests/test_modernization_p03_stage73_consumers.py",
        ],
    },
    "P03_STAGE73_CONSUMER_RUNTIME": {
        "status": "INTEGRATED_FIVE_GROUP_CONSUMER_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage73_runtime.json",
            "content/modernization/p03_stage73_consumer_runtime_checkpoint.json",
            "content/modernization/p03_stage73_consumer_runtime_route_audit.json",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.h",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.ld",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime_hooks.S",
            "scripts/build_modernization_p03_stage73_runtime.sh",
            "tests/test_modernization_p03_stage73_runtime.py",
            "tools/modernization_p03_stage73_runtime.py",
        ],
    },
    "P03_STAGE74_DIRECT_SUPPLY_RUNTIME": {
        "status": "INTEGRATED_DIRECT_SUPPLY_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p03_stage74_supply.json",
            "content/modernization/p03_stage74_supply_runtime_checkpoint.json",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.h",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.ld",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S",
            "scripts/build_modernization_p03_stage74_supply.sh",
            "tests/test_modernization_p03_stage74_supply.py",
            "tools/modernization_p03_stage74_supply.py",
        ],
    },
    "P03_STAGE75_OWN_TEMPO_ROCKRUFF": {
        "status": "INTEGRATED_INTERNAL_FORM_CHECKPOINT_NOT_P03_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_rockruff_own_tempo_stage75.json",
            "content/modernization/rockruff_own_tempo_stage75_contract.json",
            "content/modernization/rockruff_own_tempo_stage75_checkpoint.json",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.h",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.ld",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75_scripts.S",
            "scripts/build_modernization_rockruff_own_tempo_stage75.sh",
            "tests/test_modernization_rockruff_own_tempo_stage75.py",
            "tools/modernization_rockruff_own_tempo_stage75.py",
        ],
    },
    "P04_STAGE70_SPECIES_RUNTIME": {
        "status": "INTEGRATED_STATIC_RUNTIME_MGBA_PENDING_NOT_P04_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p04_species_runtime.json",
            "content/modernization/p04_species_runtime_contract.json",
            "content/modernization/p04_species_runtime_checkpoint.json",
            "overlays/modernization_p04_species_runtime/README.md",
            "scripts/build_modernization_p04_species_runtime.py",
            "tests/test_modernization_p04_species_runtime.py",
            "tools/modernization_p04_species_runtime.py",
        ],
    },
    "P04_STAGE71_MEGA_RUNTIME": {
        "status": "INTEGRATED_FORWARD_REVERSE_RUNTIME_MGBA_PENDING_NOT_P04_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p04_mega_runtime.json",
            "content/modernization/p04_mega_runtime_checkpoint.json",
            "content/modernization/p04_mega_runtime_mapping.json",
            "overlays/modernization_p04_mega_runtime/README.md",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.c",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.h",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle_host.c",
            "scripts/build_modernization_p04_mega_runtime.py",
            "tests/test_modernization_p04_mega_runtime.py",
            "tools/modernization_p04_mega_runtime.py",
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
    "P05_STAGE72_ABILITY_ROM_RUNTIME": {
        "status": "INTEGRATED_STATIC_RUNTIME_MGBA_AI_UI_EDGES_PENDING_NOT_P05_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p05_ability_rom_runtime.json",
            "content/modernization/p05_ability_rom_runtime_checkpoint.json",
            "content/modernization/p05_ability_rom_runtime_surface_matrix.json",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.ld",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S",
            "scripts/build_modernization_p05_ability_rom_runtime.py",
            "tests/test_modernization_p05_ability_rom_runtime.py",
            "tools/modernization_p05_ability_rom_runtime.py",
        ],
    },
    "P05_STAGE76_SAFE_AI_UI_EDGES": {
        "status": "INTEGRATED_THREE_EDGES_EELEVATE_MGBA_PENDING_NOT_P05_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p05_stage76_edges.json",
            "content/modernization/p05_stage76_edges_contract.json",
            "content/modernization/p05_stage76_edges_checkpoint.json",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.c",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.h",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.ld",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges_hooks.S",
            "scripts/build_modernization_p05_stage76_edges.sh",
            "tests/test_modernization_p05_stage76_edges.py",
            "tools/modernization_p05_stage76_edges.py",
        ],
    },
    "P05_STAGE77_BATTLE_CIRCUS_SUPPRESSION": {
        "status": "INTEGRATED_29_HOOK_33_SURFACE_SUPPRESSION_EELEVATE_MGBA_PENDING_NOT_P05_DONE",
        "included": True,
        "expected_paths": [
            "config/modernization_p05_stage77_suppression.json",
            "content/modernization/p05_stage77_suppression_contract.json",
            "content/modernization/p05_stage77_suppression_checkpoint.json",
            "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S",
            "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.ld",
            "scripts/build_modernization_p05_stage77_suppression.sh",
            "tests/test_modernization_p05_stage77_suppression.py",
            "tools/modernization_p05_stage77_suppression.py",
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
    "tools/modernization_p03_stage73_consumers.py": "P03",
    "tests/test_modernization_p03_stage73_consumers.py": "P03",
    "scripts/build_modernization_p03_stage73_runtime.sh": "P03",
    "tools/modernization_p03_stage73_runtime.py": "P03",
    "tests/test_modernization_p03_stage73_runtime.py": "P03",
    "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c": "P03",
    "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.h": "P03",
    "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.ld": "P03",
    "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime_hooks.S": "P03",
    "scripts/build_modernization_p03_stage74_supply.sh": "P03",
    "tools/modernization_p03_stage74_supply.py": "P03",
    "tests/test_modernization_p03_stage74_supply.py": "P03",
    "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c": "P03",
    "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.h": "P03",
    "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.ld": "P03",
    "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S": "P03",
    "scripts/build_modernization_rockruff_own_tempo_stage75.sh": "P03",
    "tools/modernization_rockruff_own_tempo_stage75.py": "P03",
    "tests/test_modernization_rockruff_own_tempo_stage75.py": "P03",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c": "P03",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.h": "P03",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.ld": "P03",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75_scripts.S": "P03",
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
    "scripts/build_modernization_mega_shop.py": "P04",
    "scripts/run_modernization_mega_shop_mgba.py": "P04",
    "tools/modernization_mega_shop.py": "P04",
    "tools/mgba_modernization_mega_shop_smoke.c": "P04",
    "tests/test_modernization_mega_shop.py": "P04",
    "tests/test_modernization_mega_shop_mgba.py": "P04",
    "overlays/modernization_mega_shop/README.md": "P04",
    "overlays/modernization_mega_shop/modernization_mega_shop.c": "P04",
    "overlays/modernization_mega_shop/modernization_mega_shop.h": "P04",
    "overlays/modernization_mega_shop/modernization_mega_shop_host_harness.c": "P04",
    "scripts/build_modernization_floette_gift.py": "P04",
    "tools/modernization_floette_gift.py": "P04",
    "tests/test_modernization_floette_gift.py": "P04",
    "overlays/modernization_floette_gift/README.md": "P04",
    "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c": "P04",
    "overlays/modernization_floette_gift/modernization_floette_gift.c": "P04",
    "overlays/modernization_floette_gift/modernization_floette_gift.h": "P04",
    "overlays/modernization_floette_gift/modernization_floette_gift_host_test.c": "P04",
    "scripts/build_modernization_p04_species_runtime.py": "P04",
    "tools/modernization_p04_species_runtime.py": "P04",
    "tests/test_modernization_p04_species_runtime.py": "P04",
    "overlays/modernization_p04_species_runtime/README.md": "P04",
    "scripts/build_modernization_p04_mega_runtime.py": "P04",
    "tools/modernization_p04_mega_runtime.py": "P04",
    "tests/test_modernization_p04_mega_runtime.py": "P04",
    "overlays/modernization_p04_mega_runtime/README.md": "P04",
    "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.c": "P04",
    "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.h": "P04",
    "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle_host.c": "P04",
    "scripts/build_modernization_p05.py": "P05",
    "tools/modernization_p05_contract.py": "P05",
    "tests/test_modernization_p05.py": "P05",
    "scripts/build_modernization_p05_ability_runtime.py": "P05",
    "tools/modernization_p05_ability_runtime.py": "P05",
    "tests/test_modernization_p05_ability_runtime.py": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities.h": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities.c": "P05",
    "overlays/modernization_p05_abilities/modernization_p05_abilities_fixture.c": "P05",
    "scripts/build_modernization_p05_ability_rom_runtime.py": "P05",
    "tools/modernization_p05_ability_rom_runtime.py": "P05",
    "tests/test_modernization_p05_ability_rom_runtime.py": "P05",
    "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c": "P05",
    "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h": "P05",
    "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.ld": "P05",
    "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S": "P05",
    "scripts/build_modernization_p05_stage76_edges.sh": "P05",
    "tools/modernization_p05_stage76_edges.py": "P05",
    "tests/test_modernization_p05_stage76_edges.py": "P05",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.c": "P05",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.h": "P05",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.ld": "P05",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges_hooks.S": "P05",
    "scripts/build_modernization_p05_stage77_suppression.sh": "P05",
    "tools/modernization_p05_stage77_suppression.py": "P05",
    "tests/test_modernization_p05_stage77_suppression.py": "P05",
    "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S": "P05",
    "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.ld": "P05",
    "scripts/run_modernization_p02_stage71_acceptance.py": "P02",
    "tools/mgba_modernization_p02_stage71_acceptance_smoke.c": "P02",
    "tests/test_modernization_p02_stage71_acceptance.py": "P02",
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
    "P04_STAGE68_MGBA_CHECKPOINT": (
        "content/modernization/mega_shop_mgba_runtime_gate.json",
        ("inputs", "checkpoint"),
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
    "P04_STAGE68_MGBA_CHECKPOINT": 1,
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


def _candidate_inheritance(
    by_path: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    def rom(relative: str) -> dict[str, Any]:
        return dict(by_path[relative])

    return [
        {"stage": 62, "role": "ACTIVE_PLAY_BASELINE", "rom": rom("build/stages/62_npc_placement_integrity_repair.gba")},
        {"stage": 63, "role": "P01_COMPLETED_CANDIDATE", "parent_stage": 62, "rom": rom("build/stages/63_modernization_p01_identity_repair.gba")},
        {"stage": 64, "role": "P02_CHECKPOINT_NOT_DONE", "parent_stage": 63, "rom": rom("build/stages/64_modernization_p02_rayquaza_parameter_repair.gba")},
        {"stage": 65, "role": "P03_INTEGRATED_CHECKPOINT_NOT_DONE", "parent_stage": 64, "rom": rom("build/stages/65_modernization_p03_caterpie_slice.gba")},
        {"stage": 66, "role": "P03_BULK_CHECKPOINT_NOT_DONE", "parent_stage": 65, "rom": rom("build/stages/66_modernization_p03_bulk_learnsets.gba")},
        {"stage": 67, "role": "P02_P03_CONSUMER_CHECKPOINT_NOT_DONE", "parent_stage": 66, "parent_overlay_sha256": "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb", "rom": rom("build/stages/67_modernization_p02_p03_consumers.gba")},
        {"stage": 68, "role": "P04_MEGA_STONE_BP_SHOP_EXACT_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 67, "rom": rom("build/stages/68_modernization_mega_shop.gba")},
        {"stage": 69, "role": "P04_FLOETTE_ETERNAL_EXACT_PARTIAL_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 68, "rom": rom("build/stages/69_modernization_floette_gift.gba")},
        {"stage": 70, "role": "P04_SPECIES_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 69, "rom": rom("build/stages/70_modernization_p04_species_runtime.gba")},
        {"stage": 71, "role": "P04_MEGA_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 70, "rom": rom("build/stages/71_modernization_p04_mega_runtime.gba")},
        {"stage": 72, "role": "P05_ABILITY_ROM_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 71, "rom": rom("build/stages/72_modernization_p05_ability_rom_runtime.gba")},
        {"stage": 73, "role": "P03_FIVE_GROUP_CONSUMER_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 72, "rom": rom("build/stages/73_modernization_p03_consumer_runtime.gba")},
        {"stage": 74, "role": "P03_DIRECT_SUPPLY_RUNTIME_CHECKPOINT_NOT_DONE", "parent_stage": 73, "rom": rom("build/stages/74_modernization_p03_supply_runtime.gba")},
        {"stage": 75, "role": "P03_OWN_TEMPO_ROCKRUFF_INTERNAL_FORM_CHECKPOINT_NOT_DONE", "parent_stage": 74, "rom": rom("build/stages/75_modernization_rockruff_own_tempo.gba")},
        {"stage": 76, "role": "P05_THREE_SAFE_AI_UI_EDGES_CHECKPOINT_NOT_DONE", "parent_stage": 75, "rom": rom("build/stages/76_modernization_p05_edges.gba")},
        {"stage": 77, "role": "P05_BATTLE_CIRCUS_GLOBAL_SUPPRESSION_CHECKPOINT_NOT_DONE", "parent_stage": 76, "rom": rom("build/stages/77_modernization_p05_circus_suppression.gba")},
    ]


def _candidate_patch_declarations() -> dict[str, dict[str, Any]]:
    declarations: dict[str, dict[str, Any]] = {}
    for key, source, patch, target in CANDIDATE_PATCH_CHAIN_PATHS:
        patch_size, patch_sha256, _ = CANDIDATE_ARTIFACTS[patch]
        row: dict[str, Any] = {
            "path": patch,
            "size": patch_size,
            "sha256": patch_sha256,
            "source_sha256": CANDIDATE_ARTIFACTS[source][1],
            "target_sha256": CANDIDATE_ARTIFACTS[target][1],
            "round_trip": True,
        }
        if key == "stage72_to_stage73":
            row["source_classification"] = "STAGE72_EXACT_ROM"
        elif key == "stage73_to_stage74":
            row["source_classification"] = "STAGE73_EXACT_ROM"
        elif key == "stage74_to_stage75":
            row["source_classification"] = "STAGE74_EXACT_ROM"
        elif key == "stage75_to_stage76":
            row["source_classification"] = "STAGE75_EXACT_ROM"
        elif key == "from_parent":
            row["source_classification"] = "STAGE76_EXACT_ROM"
        declarations[key] = row
    return declarations


def _verify_incremental_bps(
    root: Path, source_path: str, patch_path: str, target_path: str,
) -> dict[str, Any]:
    source = _regular_bytes(root, source_path)
    patch = _regular_bytes(root, patch_path)
    target = _regular_bytes(root, target_path)
    _require(apply_bps(source, patch) == target, f"BPS exact apply不一致: {patch_path}")
    return {
        "source": source_path,
        "patch": patch_path,
        "target": target_path,
        "status": "PASS_EXACT_APPLY",
    }


def _validate_candidate_chain(
    root: Path, artifact_audit: Mapping[str, Any],
    metadata: Mapping[str, Mapping[str, Any]], registry: Mapping[str, Any],
) -> dict[str, Any]:
    by_path = _identity_by_path(artifact_audit["artifacts"])
    s62 = by_path["build/stages/62_npc_placement_integrity_repair.gba"]
    s63 = by_path["build/stages/63_modernization_p01_identity_repair.gba"]
    s64 = by_path["build/stages/64_modernization_p02_rayquaza_parameter_repair.gba"]
    s65 = by_path["build/stages/65_modernization_p03_caterpie_slice.gba"]
    s66 = by_path["build/stages/66_modernization_p03_bulk_learnsets.gba"]
    s67 = by_path["build/stages/67_modernization_p02_p03_consumers.gba"]
    s68 = by_path["build/stages/68_modernization_mega_shop.gba"]
    s69 = by_path["build/stages/69_modernization_floette_gift.gba"]
    s70 = by_path["build/stages/70_modernization_p04_species_runtime.gba"]
    s71 = by_path["build/stages/71_modernization_p04_mega_runtime.gba"]
    s72 = by_path["build/stages/72_modernization_p05_ability_rom_runtime.gba"]
    s73 = by_path["build/stages/73_modernization_p03_consumer_runtime.gba"]
    s74 = by_path["build/stages/74_modernization_p03_supply_runtime.gba"]
    s75 = by_path["build/stages/75_modernization_rockruff_own_tempo.gba"]
    s76 = by_path["build/stages/76_modernization_p05_edges.gba"]
    s77 = by_path["build/stages/77_modernization_p05_circus_suppression.gba"]
    m63 = metadata["build/stages/63_modernization_p01_identity_repair.json"]
    m64 = metadata["build/stages/64_modernization_p02_rayquaza_parameter_repair.json"]
    m65 = metadata["build/stages/65_modernization_p03_caterpie_slice.json"]
    m66 = metadata["build/stages/66_modernization_p03_bulk_learnsets.json"]
    m67 = metadata["build/stages/67_modernization_p02_p03_consumers.json"]
    a67 = metadata["build/stages/67_modernization_p03_allocation.json"]
    m68 = metadata["build/stages/68_modernization_mega_shop.json"]
    a68 = metadata["build/stages/68_modernization_mega_shop_allocation.json"]
    m69 = metadata["build/stages/69_modernization_floette_gift.json"]
    a69 = metadata["build/stages/69_modernization_floette_gift_allocation.json"]
    m70 = metadata["build/stages/70_modernization_p04_species_runtime.json"]
    a70 = metadata["build/stages/70_modernization_p04_species_runtime_allocation.json"]
    m71 = metadata["build/stages/71_modernization_p04_mega_runtime.json"]
    a71 = metadata["build/stages/71_modernization_p04_mega_runtime_allocation.json"]
    m72 = metadata["build/stages/72_modernization_p05_ability_rom_runtime.json"]
    a72 = metadata["build/stages/72_modernization_p05_ability_rom_runtime_allocation.json"]
    m73 = metadata["build/stages/73_modernization_p03_consumer_runtime.json"]
    a73 = metadata["build/stages/73_modernization_p03_consumer_runtime_allocation.json"]
    m74 = metadata["build/stages/74_modernization_p03_supply_runtime.json"]
    a74 = metadata["build/stages/74_modernization_p03_supply_runtime_allocation.json"]
    m75 = metadata["build/stages/75_modernization_rockruff_own_tempo.json"]
    a75 = metadata["build/stages/75_modernization_rockruff_own_tempo_allocation.json"]
    m76 = metadata["build/stages/76_modernization_p05_edges.json"]
    a76 = metadata["build/stages/76_modernization_p05_edges_allocation.json"]
    m77 = metadata["build/stages/77_modernization_p05_circus_suppression.json"]
    a77 = metadata[
        "build/stages/77_modernization_p05_circus_suppression_allocation.json"
    ]
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
    _require(
        m68.get("task") == "USER-MODERNIZATION-MEGA-STONE-BP-SHOP"
        and m68.get("stage") == 68
        and m68.get("status") == "PASS_HOST_STATIC_EXACT_ROM_PENDING",
        "Stage68 Mega Stone shop metadata identity不正",
    )
    _require(
        m68.get("input", {}).get("sha256") == s67["sha256"]
        and m68.get("output", {}).get("sha256") == s68["sha256"]
        and m68.get("allocation", {}).get("path")
        == "build/stages/68_modernization_mega_shop_allocation.json"
        and a68.get("summaries", {}).get("overlap_count") == 0,
        "Stage68 parent/output/allocation identity不正",
    )
    _require(
        m68.get("release_patch_round_trip", {}).get("sha256")
        == by_path["build/stages/68_modernization_mega_shop.bps"]["sha256"]
        and m68.get("release_patch_round_trip", {}).get("source_sha256")
        == s67["sha256"]
        and m68.get("release_patch_round_trip", {}).get("target_sha256")
        == s68["sha256"]
        and m68.get("release_patch_round_trip", {}).get("exact") is True,
        "Stage68 BPS identity/round-trip evidence不正",
    )
    catalog68 = m68.get("catalog", {})
    _require(
        catalog68.get("entry_count") == 45
        and catalog68.get("item_ids") == list(range(999, 1044))
        and catalog68.get("prices_bp") == [16]
        and catalog68.get("key_stone_item_id") == 580
        and m68.get("invariants", {}).get("cfru_item_bounds_999_through_1043")
        is True,
        "Stage68 45 Mega Stone/16BP/Item boundary境界不正",
    )
    _require(
        m69.get("task") == "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT"
        and m69.get("stage") == 69
        and m69.get("status")
        == "PASS_HOST_AND_EXACT_PARTIAL_RUNTIME_FULL_RELOAD_PENDING",
        "Stage69 Floette Eternal metadata identity不正",
    )
    _require(
        m69.get("parent", {}).get("sha256") == s68["sha256"]
        and m69.get("output", {}).get("sha256") == s69["sha256"]
        and m69.get("allocation", {}).get("path")
        == "build/stages/69_modernization_floette_gift_allocation.json"
        and a69.get("summaries", {}).get("overlap_count") == 0,
        "Stage69 parent/output/allocation identity不正",
    )
    _require(
        m69.get("release_patch_round_trip", {}).get("sha256")
        == by_path["build/stages/69_modernization_floette_gift.bps"]["sha256"]
        and m69.get("release_patch_round_trip", {}).get("source_sha256")
        == s68["sha256"]
        and m69.get("release_patch_round_trip", {}).get("target_sha256")
        == s69["sha256"]
        and m69.get("release_patch_round_trip", {}).get("exact") is True,
        "Stage69 BPS identity/round-trip evidence不正",
    )
    gift69 = m69.get("gift", {})
    _require(
        gift69.get("species_id") == 1029
        and gift69.get("level") == 50
        and gift69.get("unlock_item_id") == 580
        and gift69.get("claim_flag") == 0x14CD
        and m69.get("validation", {}).get("exact_rom_runtime_smoke")
        == "PARTIAL_PASS_FULL_AND_RELOAD_PENDING",
        "Stage69 Floette Eternal gift/runtime boundary不正",
    )
    _require(
        m70.get("task") == "USER-MODERNIZATION-P04-SPECIES-RUNTIME-STAGE70"
        and m70.get("stage") == 70
        and m70.get("status") == "ROM_MATERIALIZED_CHECKPOINT"
        and m70.get("parent_rom", {}).get("sha256") == s69["sha256"]
        and m70.get("output_rom", {}).get("sha256") == s70["sha256"]
        and m70.get("allocation_report_sha256")
        == by_path["build/stages/70_modernization_p04_species_runtime_allocation.json"]["sha256"],
        "Stage70 species runtime metadata/parent/output/allocation identity不正",
    )
    checks70 = m70.get("checks", {})
    allocation70 = next(
        (row for row in a70.get("allocations", []) if row.get("sequence") == 73),
        {},
    )
    _require(
        checks70.get("all_49_rows_materialized") == "PASS"
        and checks70.get("existing_prefixes_byte_exact") == "PASS"
        and checks70.get("floette_eternal_species_id_1029_preserved") == "PASS"
        and checks70.get("rom_outside_declared_spans_unchanged") == "PASS"
        and m70.get("scope", {}).get("side_change") == "NOT_REFERENCED"
        and a70.get("summaries", {}).get("allocation_count") == 74
        and a70.get("summaries", {}).get("overlap_count") == 0
        and allocation70.get("name")
        == "modernization_p04_species_runtime_stage70_payload"
        and allocation70.get("content_sha256")
        == "ef91ae7d159891b40509fae674c9236a3b2e9d1142722d9cdd753be0c95c8c0b",
        "Stage70 49形態/prefix/allocator/除外境界不正",
    )
    _require(
        m71.get("task") == "USER-MODERNIZATION-P04-MEGA-RUNTIME-STAGE71"
        and m71.get("stage") == 71
        and m71.get("status") == "CHECKPOINT_STAGE72_ABILITY_EFFECTS_PENDING"
        and m71.get("done") is False
        and m71.get("release_candidate") is False
        and m71.get("parent", {}).get("sha256") == s70["sha256"]
        and m71.get("output", {}).get("sha256") == s71["sha256"]
        and m71.get("bps", {}).get("sha256")
        == by_path["build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps"]["sha256"]
        and m71.get("bps", {}).get("round_trip") is True,
        "Stage71 Mega runtime metadata/parent/output/BPS境界不正",
    )
    evolution71 = m71.get("evolution_table", {})
    _require(
        evolution71.get("forward_entries_added") == 49
        and evolution71.get("reverse_entries_added") == 49
        and evolution71.get("existing_mega_entries_preserved") == 80
        and m71.get("change_allowlist", {}).get("changed_byte_count") == 383
        and m71.get("change_allowlist", {}).get("outside_allowlist_count") == 0
        and m71.get("validation", {}).get("mapping_49") == "PASS"
        and m71.get("validation", {}).get("wrong_stone_rejected")
        == "PASS_ALL_OTHER_NEW_STONES"
        and a71.get("summaries", {}).get("allocation_count") == 74
        and a71.get("summaries", {}).get("overlap_count") == 0
        and m71.get("allocation", {}).get("new_allocation_count") == 0
        and m71.get("allocation", {}).get("output_sha256")
        == by_path["build/stages/71_modernization_p04_mega_runtime_allocation.json"]["sha256"],
        "Stage71 49順逆/既存Mega/allowlist/allocation境界不正",
    )
    _require(
        m72.get("task") == "USER-MODERNIZATION-P05-ABILITY-ROM-RUNTIME-STAGE72"
        and m72.get("stage") == 72
        and m72.get("status")
        == "CHECKPOINT_STATIC_RUNTIME_CONNECTED_MGBA_AND_DOCUMENTED_AI_UI_EDGES_PENDING"
        and m72.get("release_candidate") is False
        and m72.get("parent", {}).get("sha256") == s71["sha256"]
        and m72.get("output", {}).get("sha256") == s72["sha256"]
        and m72.get("allocation_report_sha256")
        == by_path["build/stages/72_modernization_p05_ability_rom_runtime_allocation.json"]["sha256"]
        and m72.get("bps", {}).get("sha256")
        == by_path["build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps"]["sha256"]
        and m72.get("bps", {}).get("round_trip") is True,
        "Stage72 Ability runtime metadata/parent/output/allocation/BPS境界不正",
    )
    _require(
        [row.get("id") for row in m72.get("ability_rows", [])]
        == [312, 313, 314, 315, 316, 317]
        and len(m72.get("hooks", [])) == 29
        and m72.get("validation", {}).get("ability_0_311_unchanged") == "PASS"
        and m72.get("validation", {}).get("mega_bindings_312_317") == "PASS"
        and m72.get("validation", {}).get("allowlist_outside") == 0
        and m72.get("validation", {}).get("mgba") == "NOT_RUN_BY_STAGE72_OWNER"
        and len(m72.get("release_blockers", [])) == 5
        and a72.get("summaries", {}).get("allocation_count") == 75
        and a72.get("summaries", {}).get("overlap_count") == 0,
        "Stage72 6 Ability/29 hook/未完了/allocation境界不正",
    )
    _require(
        m73.get("task") == "USER-MODERNIZATION-P03-STAGE73-CONSUMER-RUNTIME"
        and m73.get("stage") == 73
        and m73.get("status")
        == "CHECKPOINT_FIVE_CONSUMER_BOUNDARY_CONNECTED_SUPPLY_DEPENDENCIES_REMAIN"
        and m73.get("completion_claim")
        == "FIVE_GROUP_CONSUMER_BOUNDARY_CHECKPOINT_NOT_FULL_P03"
        and m73.get("release_candidate") is False
        and m73.get("parent_identity", {}).get("commit")
        == "bbab6b2e943186cf437a6dca90712c01f0319ded"
        and m73.get("parent_identity", {}).get("sha256") == s72["sha256"]
        and m73.get("output", {}).get("sha256") == s73["sha256"]
        and str(m73.get("output", {}).get("crc32", "")).upper() == s73["crc32"]
        and m73.get("allocation_report", {}).get("sha256")
        == by_path["build/stages/73_modernization_p03_consumer_runtime_allocation.json"]["sha256"]
        and m73.get("bps", {}).get("sha256")
        == by_path["build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps"]["sha256"]
        and m73.get("bps", {}).get("round_trip") is True,
        "Stage73 consumer metadata/parent/output/CRC/allocation/BPS境界不正",
    )
    _require(
        m74.get("task") == "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME"
        and m74.get("stage") == 74
        and m74.get("status")
        == "CHECKPOINT_DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_OWNER_REVIEW_AND_MGBA_REMAIN"
        and m74.get("completion_claim")
        == "DIRECT_MACHINE_TUTOR_SUPPLY_26648_COMPLETE_CHECKPOINT_NOT_FULL_P03_DONE"
        and m74.get("done") is False
        and m74.get("release_candidate") is False
        and m74.get("parent_identity", {}).get("commit")
        == "1dd2a9ab8da73f7eb17dbd5b8fa8fcd96109443e"
        and m74.get("parent_identity", {}).get("sha256") == s73["sha256"]
        and m74.get("output", {}).get("sha256") == s74["sha256"]
        and str(m74.get("output", {}).get("crc32", "")).upper() == s74["crc32"]
        and m74.get("allocation_report", {}).get("sha256")
        == by_path["build/stages/74_modernization_p03_supply_runtime_allocation.json"]["sha256"]
        and m74.get("bps", {}).get("sha256")
        == by_path["build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps"]["sha256"]
        and m74.get("bps", {}).get("source_sha256") == s73["sha256"]
        and m74.get("bps", {}).get("target_sha256") == s74["sha256"]
        and m74.get("bps", {}).get("round_trip") is True
        and m74.get("changed_bytes") == 70480
        and len(m74.get("hooks", [])) == 2,
        "Stage74 supply metadata/parent/output/CRC/allocation/BPS境界不正",
    )
    _require(
        m75.get("task") == "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75"
        and m75.get("stage") == 75
        and m75.get("status") == "CHECKPOINT_OWN_TEMPO_ROCKRUFF_RUNTIME_CONNECTED"
        and m75.get("full_p03_done") is False
        and m75.get("release_candidate") is False
        and m75.get("parent", {}).get("path") == s74["path"]
        and m75.get("parent", {}).get("sha256") == s74["sha256"]
        and m75.get("output", {}).get("path") == s75["path"]
        and m75.get("output", {}).get("sha256") == s75["sha256"]
        and str(m75.get("output", {}).get("crc32", "")).upper() == s75["crc32"]
        and m75.get("source_evidence", {}).get("config_sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_rockruff_own_tempo_stage75.json"][1]
        and m75.get("source_evidence", {}).get("parent_metadata_sha256")
        == by_path["build/stages/74_modernization_p03_supply_runtime.json"]["sha256"]
        and m75.get("source_evidence", {}).get("parent_allocation_sha256")
        == by_path["build/stages/74_modernization_p03_supply_runtime_allocation.json"]["sha256"],
        "Stage75 Own Tempo Rockruff metadata/親/output/CRC/config identity不正",
    )
    identity75 = m75.get("identity", {})
    route75 = m75.get("route_audit", {})
    _require(
        identity75 == {
            "ability_id": 20,
            "ability_slots": [20, 20, 20],
            "classification": "INTERNAL_CONDITIONAL_FORM",
            "collection_class": 4,
            "collection_weight": 0,
            "dusk_species_id": 1263,
            "form_key": "FORM_KEY_ROCKRUFF_OWN_TEMPO",
            "national_dex": 744,
            "normal_species_id": 1142,
            "reference_id": "scarletviolet:0744.01",
            "save_layout_changed": False,
            "species_id": 1670,
            "species_key": "SPECIES_KEY_ROCKRUFF_OWN_TEMPO",
        }
        and route75.get("pre_evolution_carry", {}).get("path_count") == 38
        and route75.get("pre_evolution_carry", {}).get("missing_owner_path_count") == 0
        and route75.get("pre_evolution_carry", {}).get("reference_owner") == 1670
        and route75.get("pre_evolution_carry", {}).get("target_species") == 1263
        and route75.get("pre_evolution_carry", {}).get("direct_conversion") == "FORBIDDEN"
        and route75.get("pre_evolution_carry", {}).get("resolution_counts")
        == {"reference_existing_slot": 21, "reference_stage74_archive": 17}
        and route75.get("source_route_clone", {}).get("route_count") == 60
        and route75.get("accounting", {}).get("materialized_routes_before") == 83162
        and route75.get("accounting", {}).get("materialized_routes_after") == 83162
        and route75.get("accounting", {}).get("selected_routes_before") == 118369
        and route75.get("accounting", {}).get("selected_routes_after") == 118369
        and route75.get("accounting", {}).get("route_accounting_delta") == 0
        and route75.get("exclusions", {}).get("side_change_materialized") == 0
        and route75.get("exclusions", {}).get("browt_pombon_gecqua_materialized") == 0
        and route75.get("exclusions", {}).get("prohibited_coercions_materialized") == 0,
        "Stage75 internal form/38 carry/route accounting/除外境界不正",
    )
    expected_edges76 = {
        "eelevate_dedicated_switch": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
        "mega_sol_solar_charge_popup": "IMPLEMENT",
        "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
        "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
    }
    _require(
        m76.get("task") == "USER-MODERNIZATION-P05-STAGE76-EDGES"
        and m76.get("stage") == 76
        and m76.get("status") == "THREE_EDGES_ROM_MATERIALIZED_EELEVATE_AND_MGBA_PENDING"
        and m76.get("parent") == {
            "commit": STAGE75_IMPLEMENTATION_COMMIT,
            "path": s75["path"],
            "sha256": s75["sha256"],
            "size": 33554432,
            "stage": 75,
        }
        and m76.get("output", {}).get("path") == s76["path"]
        and m76.get("output", {}).get("sha256") == s76["sha256"]
        and str(m76.get("output", {}).get("crc32", "")).upper() == s76["crc32"]
        and m76.get("edges") == expected_edges76
        and m76.get("implemented_edge_count") == 3
        and m76.get("pending_edge_count") == 1
        and m76.get("done") is False
        and m76.get("full_p05_done") is False
        and m76.get("release_ready") is False,
        "Stage76 P05 3実装/1 pending/親commit/output/未完了境界不正",
    )
    checks76 = m76.get("checks", {})
    _require(
        checks76.get("active_play_baseline_unchanged") == "PASS"
        and checks76.get("parent_stage75_implementation_cross_link") == "PASS"
        and checks76.get("parent_first79_rows_all_fields_preserved") == "PASS"
        and checks76.get("rom_diff_outside_payload_plus_four_patches") == 0
        and checks76.get("eelevate_parent_sites_preserved") == "PASS"
        and checks76.get("eelevate_unsafe_hooks_installed") == 0
        and checks76.get("side_change_added") == 0
        and checks76.get("browt_pombon_gecqua_added") == 0
        and checks76.get("mgba_runtime") == "NOT_RUN"
        and m76.get("bps", {}).get("path")
        == "build/patches/stage75-to-stage76-modernization-p05-edges.bps"
        and m76.get("bps", {}).get("sha256")
        == by_path["build/patches/stage75-to-stage76-modernization-p05-edges.bps"]["sha256"]
        and m76.get("bps", {}).get("source_sha256") == s75["sha256"]
        and m76.get("bps", {}).get("target_sha256") == s76["sha256"]
        and m76.get("bps", {}).get("round_trip") is True,
        "Stage76 checks/BPS/Eelevate/除外/mGBA境界不正",
    )
    suppression77 = m77.get("suppression", {})
    checks77 = m77.get("checks", {})
    _require(
        m77.get("task") == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION"
        and m77.get("stage") == 77
        and m77.get("status")
        == "BATTLE_CIRCUS_GLOBAL_SUPPRESSION_MATERIALIZED_MGBA_AND_EELEVATE_SWITCH_PENDING"
        and m77.get("done") is False
        and m77.get("full_p05_done") is False
        and m77.get("release_ready") is False
        and m77.get("parent", {}).get("commit") == STAGE76_IMPLEMENTATION_COMMIT
        and m77.get("parent", {}).get("stage") == 76
        and m77.get("parent", {}).get("path") == s76["path"]
        and m77.get("parent", {}).get("sha256") == s76["sha256"]
        and m77.get("output", {}).get("path") == s77["path"]
        and m77.get("output", {}).get("sha256") == s77["sha256"]
        and str(m77.get("output", {}).get("crc32", "")).upper() == s77["crc32"]
        and suppression77 == {
            "ability_surface_occurrence_count": 33,
            "battle_circus_global_fixed": True,
            "hook_count": 29,
            "ordinary_suppression_changed": False,
        }
        and m77.get("allocation_sequence") == 80
        and m77.get("bps", {}).get("path")
        == "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps"
        and m77.get("bps", {}).get("sha256")
        == by_path[
            "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps"
        ]["sha256"]
        and m77.get("bps", {}).get("source_sha256") == s76["sha256"]
        and m77.get("bps", {}).get("target_sha256") == s77["sha256"]
        and m77.get("bps", {}).get("round_trip") is True,
        "Stage77 Circus suppression metadata/親/output/BPS/未完了境界不正",
    )
    _require(
        checks77.get("parent_stage76_commit_and_six_identities") == "PASS"
        and checks77.get("stage72_unique_hooks_repointed") == 29
        and checks77.get("stage72_ability_surface_occurrences_guarded") == 33
        and checks77.get("battle_circus_global_suppression_delegates_original") == "PASS"
        and checks77.get("normal_path_delegates_stage72_wrapper") == "PASS"
        and checks77.get("ordinary_gastro_neutralizing_gas_mold_breaker_semantics_unchanged") == "PASS"
        and checks77.get("stage76_pointer_and_three_hooks_preserved") == "PASS"
        and checks77.get("rom_diff_outside_payload_plus_29_hooks") == 0
        and checks77.get("eelevate_unsafe_switch_hooks_installed") == 0
        and checks77.get("side_change_added") == 0
        and checks77.get("browt_pombon_gecqua_added") == 0
        and checks77.get("active_play_baseline_unchanged") == "PASS"
        and checks77.get("mgba_runtime") == "NOT_RUN",
        "Stage77 29 hook/33 surface/Circus/通常経路保持/除外/mGBA境界不正",
    )
    accounting73 = m73.get("consumer_accounting", {})
    accounting74 = m74.get("accounting", {})
    direct74 = m74.get("direct_supply", {})
    validation74 = m74.get("validation", {})
    allocation_rows70 = {row.get("sequence"): row for row in a70.get("allocations", [])}
    allocation_rows71 = {row.get("sequence"): row for row in a71.get("allocations", [])}
    allocation_rows72 = {row.get("sequence"): row for row in a72.get("allocations", [])}
    allocation_rows73 = {row.get("sequence"): row for row in a73.get("allocations", [])}
    allocation_rows74 = {row.get("sequence"): row for row in a74.get("allocations", [])}
    allocation_rows75 = {row.get("sequence"): row for row in a75.get("allocations", [])}
    allocation_rows76 = {row.get("sequence"): row for row in a76.get("allocations", [])}
    allocation_rows77 = {row.get("sequence"): row for row in a77.get("allocations", [])}
    stage73_rom = _regular_bytes(root, str(s73["path"]))
    stage74_rom = _regular_bytes(root, str(s74["path"]))
    stage74_sequence33_slice_sha256 = _sha256(stage74_rom[19726128:19729096])
    stage74_sequence77_slice_sha256 = _sha256(stage74_rom[22256768:22327340])
    stage75_rom = _regular_bytes(root, str(s75["path"]))
    stage76_rom = _regular_bytes(root, str(s76["path"]))
    stage77_rom = _regular_bytes(root, str(s77["path"]))

    def allocation_layout_projection(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in row.items()
            if key not in {"content_sha256", "placement"}
        }

    def allocation_owner_projection(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in row.items()
            if key != "placement"
        }

    _require(
        accounting73.get("consumer_boundary_accounted_routes") == 40570
        and accounting73.get("new_runtime_materialized_routes") == 5363
        and accounting73.get("existing_owner_accounted_routes") == 35207
        and accounting73.get("machine_tutor_upstream_supply_dependency") == 23595
        and accounting73.get("new_runtime_materialized_routes")
        + accounting73.get("existing_owner_accounted_routes") == 40570
        and len(m73.get("hooks", [])) == 3
        and m73.get("validation", {}).get("side_change") == 0
        and m73.get("validation", {}).get("browt_pombon_gecqua") == 0
        and m73.get("validation", {}).get("prohibited_coercions") == 0
        and m73.get("validation", {}).get("allowlist_outside") == 0
        and m73.get("validation", {}).get("normal_reminder_capacity_drop") == 0
        and m73.get("validation", {}).get("legacy_shared_egg_capacity_drop") == 0
        and a73.get("summaries", {}).get("allocation_count") == 77
        and a73.get("summaries", {}).get("overlap_count") == 0
        and a73.get("summaries", {}).get("region_usage", [])[-1].get("remaining_bytes")
        == 47507
        and 33554432 - max(row.get("end_exclusive", 0) for row in a73.get("allocations", []))
        == 47490,
        "Stage73 route勘定/除外/capacity/allocation境界不正",
    )
    families74 = direct74.get("families", {})
    preservation74 = {
        key.removeprefix("build_learnable_preservation_"): value
        for key, value in validation74.items()
        if key.startswith("build_learnable_preservation_")
    }
    _require(
        accounting74 == {
            "cumulative_accounted_routes": 118369,
            "cumulative_runtime_materialized_routes": 83162,
            "full_p03_done": False,
            "selected_direct_supply_routes_remaining": 0,
            "stage67_materialized_routes": 51151,
            "stage73_existing_owner_accounted_routes": 35207,
            "stage73_new_runtime_materialized_routes": 5363,
            "stage74_direct_supply_materialized_routes": 26648,
        }
        and direct74.get("route_count") == 26648
        and direct74.get("species_family_move_pair_count") == 26648
        and direct74.get("duplicate_species_family_move_pairs") == 0
        and direct74.get("set_sha256")
        == "5ef6be8c533e60c07ec1240c3ee8cc1e56c90c505689f3d41436719f338f7968"
        and families74.get("machine", {}).get("routes") == 26279
        and families74.get("machine", {}).get("max_rows_per_species") == 131
        and families74.get("tutor", {}).get("routes") == 369
        and families74.get("tutor", {}).get("max_rows_per_species") == 12
        and direct74.get("family_set_sha256", {}).get("machine")
        == "c36479fe7ccca18a2f0861597d7e9667d0f30f2cc1a32d33dc32efea12e107fd"
        and direct74.get("family_set_sha256", {}).get("tutor")
        == "085379dc87fb5127e2f8f29d35d4f51805b138c7c86ecc022a68b5979da24f15"
        and direct74.get("existing_slot_projection_set_sha256")
        == "f4be2d83dae734c9339b790583d1e8c427daac49c964c87205b2f970b6deb3f1"
        and direct74.get("selected_direct_partition")
        == {"existing": 29773, "new": 26648, "total": 56421}
        and direct74.get("cross_family_same_move_ids")
        == [173, 264, 304, 340, 352, 395, 700, 701, 702, 793]
        and direct74.get("same_species_cross_family_pair_count") == 0
        and validation74.get("side_change") == 0
        and validation74.get("browt_pombon_gecqua") == 0
        and validation74.get("prohibited_coercions") == 0
        and validation74.get("family_table_union") == 0
        and validation74.get("machine_paging_silent_drop") == 0
        and validation74.get("empty_final_pages") == 0
        and validation74.get("build_learnable_selected_routes_checked") == 118369
        and preservation74 == {
            "accounting_added": 0,
            "missing_paths": 4014,
            "target_moves": 2223,
            "ui_routes_added": 0,
        }
        and validation74.get("build_learnable_buffer_entries") == 238
        and validation74.get("build_learnable_unique_entries") == 234
        and validation74.get("build_learnable_overflow_species") == 0,
        "Stage74 direct family分離/勘定/paging/preservation/capacity/除外境界不正",
    )
    _require(
        set(allocation_rows70) == set(range(74))
        and set(allocation_rows71) == set(range(74))
        and set(allocation_rows72) == set(range(75))
        and set(allocation_rows73) == set(range(77))
        and set(allocation_rows74) == set(range(78))
        and all(
            allocation_rows70[sequence] == allocation_rows71[sequence]
            for sequence in range(73)
        )
        and allocation_layout_projection(allocation_rows70[73])
        == allocation_layout_projection(allocation_rows71[73])
        and allocation_rows70[73].get("content_sha256")
        == "ef91ae7d159891b40509fae674c9236a3b2e9d1142722d9cdd753be0c95c8c0b"
        and allocation_rows71[73].get("content_sha256")
        == "6a7793e653bff4737082e94311c3967eef8a90cbe1f0bcaefdcb9e9bcdc99c5c"
        and all(
            allocation_owner_projection(allocation_rows71[sequence])
            == allocation_owner_projection(allocation_rows72[sequence])
            for sequence in range(74)
        )
        and all(
            allocation_owner_projection(allocation_rows72[sequence])
            == allocation_owner_projection(allocation_rows73[sequence])
            for sequence in range(75)
        )
        and all(
            allocation_rows73[sequence] == allocation_rows74[sequence]
            for sequence in range(77) if sequence != 33
        )
        and allocation_layout_projection(allocation_rows73[33])
        == allocation_layout_projection(allocation_rows74[33])
        and allocation_rows73[33].get("content_sha256")
        == "f62631fbfabd7e1a3af77c0640140a0a27fab2cfe8f9076556aee7cab4cee40a"
        and _sha256(stage73_rom[19726128:19729096])
        == "3b0e990853da8e4fa1a1f0c859ab624e7dbced767bf562891820f281bdb317af"
        and m74.get("allocation_mutations") == [{
            "layout_changed": False,
            "name": "move_memory_runtime",
            "output_content_sha256": "ac6a2008d9dc66c5ca8d4f224daa003ed752bcc4b6d92208dad83c62085cb53c",
            "parent_content_sha256": "f62631fbfabd7e1a3af77c0640140a0a27fab2cfe8f9076556aee7cab4cee40a",
            "parent_effective_rom_content_sha256": "3b0e990853da8e4fa1a1f0c859ab624e7dbced767bf562891820f281bdb317af",
            "reason": "normalize the pinned Stage73 effective owner slice (including four known post-Stage25 patches) and redirect Move Memory ItemScriptPointer to Stage74",
            "sequence": 33,
        }]
        and allocation_rows74[33].get("content_sha256")
        == "ac6a2008d9dc66c5ca8d4f224daa003ed752bcc4b6d92208dad83c62085cb53c"
        and stage74_sequence33_slice_sha256
        == allocation_rows74[33].get("content_sha256")
        and (
            allocation_rows72[74].get("name"),
            allocation_rows72[74].get("owner"),
            allocation_rows72[74].get("region"),
            allocation_rows72[74].get("start"),
            allocation_rows72[74].get("end_exclusive"),
            allocation_rows72[74].get("size"),
            allocation_rows72[74].get("content_sha256"),
        ) == (
            "modernization_p05_ability_rom_runtime_stage72_payload",
            "USER-MODERNIZATION-P05-ABILITY-ROM-RUNTIME-STAGE72",
            "integration_modules",
            22227936, 22235076, 7140,
            "0d2e7fb9e238ba339c9494e8159bf1eed31f3525bc95a8c13854a64a747f2190",
        )
        and (
            allocation_rows73[75].get("name"),
            allocation_rows73[75].get("owner"),
            allocation_rows73[75].get("region"),
            allocation_rows73[75].get("start"),
            allocation_rows73[75].get("end_exclusive"),
            allocation_rows73[75].get("size"),
            allocation_rows73[75].get("content_sha256"),
        ) == (
            "modernization_p03_stage73_consumer_runtime_payload",
            "USER-MODERNIZATION-P03-STAGE73-CONSUMER-RUNTIME",
            "integration_modules",
            22235088, 22256766, 21678,
            "aff0b17e3b1c243d084c3a412ccac9a74d2fa599600d6efe70b3f652f66e0f45",
        )
        and (
            allocation_rows73[76].get("name"),
            allocation_rows73[76].get("owner"),
            allocation_rows73[76].get("region"),
            allocation_rows73[76].get("start"),
            allocation_rows73[76].get("end_exclusive"),
            allocation_rows73[76].get("size"),
            allocation_rows73[76].get("content_sha256"),
        ) == (
            "modernization_p03_stage73_exact_egg_rows",
            "USER-MODERNIZATION-P03-STAGE73-CONSUMER-RUNTIME",
            "future_tail",
            33491924, 33506942, 15018,
            "0aeb5095cbfe717dc360bd50433bb0475ea334254d85d0d326731383e6f19778",
        )
        and (
            allocation_rows74[77].get("name"),
            allocation_rows74[77].get("owner"),
            allocation_rows74[77].get("region"),
            allocation_rows74[77].get("start"),
            allocation_rows74[77].get("end_exclusive"),
            allocation_rows74[77].get("size"),
            allocation_rows74[77].get("content_sha256"),
        ) == (
            "modernization_p03_stage74_supply_runtime_payload",
            "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME",
            "integration_modules",
            22256768, 22327340, 70572,
            "e4922f42818efa4fb8d7369bcab254688a021f8950a82fc64c95bdf0714463a1",
        )
        and a74.get("summaries", {}).get("allocation_count") == 78
        and a74.get("summaries", {}).get("overlap_count") == 0
        and a74.get("summaries", {}).get("remaining_allocatable_bytes") == 789003
        and next(
            row for row in a74.get("summaries", {}).get("region_usage", [])
            if row.get("region") == "integration_modules"
        ).get("remaining_bytes") == 741496
        and next(
            row for row in a74.get("summaries", {}).get("region_usage", [])
            if row.get("region") == "future_tail"
        ).get("remaining_bytes") == 47507
        and 33554432 - max(
            row.get("end_exclusive", 0) for row in a74.get("allocations", [])
        ) == 47490
        and stage74_sequence77_slice_sha256
        == allocation_rows74[77].get("content_sha256"),
        "Stage70～74 allocation lineage/sequence33 mutation/sequence77 identity不正",
    )
    mutation_sequences75 = [25, 27, 33, 34, 44, 48, 61, 62, 66]
    mutations75 = m75.get("allocation_mutations", [])
    _require(
        set(allocation_rows75) == set(range(79))
        and set(allocation_rows76) == set(range(80))
        and set(allocation_rows77) == set(range(81))
        and a74.get("regions") == a75.get("regions") == a76.get("regions") == a77.get("regions")
        and all(
            allocation_layout_projection(allocation_rows74[sequence])
            == allocation_layout_projection(allocation_rows75[sequence])
            for sequence in range(78)
        )
        and all(
            allocation_rows74[sequence] == allocation_rows75[sequence]
            for sequence in range(78) if sequence not in mutation_sequences75
        )
        and [row.get("sequence") for row in mutations75] == mutation_sequences75
        and all(
            row.get("name") == allocation_rows75[row["sequence"]].get("name")
            and row.get("parent_declared_sha256")
            == allocation_rows74[row["sequence"]].get("content_sha256")
            and row.get("parent_effective_sha256")
            == _sha256(stage74_rom[
                allocation_rows74[row["sequence"]]["start"]:
                allocation_rows74[row["sequence"]]["end_exclusive"]
            ])
            and row.get("output_effective_sha256")
            == allocation_rows75[row["sequence"]].get("content_sha256")
            and row.get("output_effective_sha256")
            == _sha256(stage75_rom[
                allocation_rows75[row["sequence"]]["start"]:
                allocation_rows75[row["sequence"]]["end_exclusive"]
            ])
            for row in mutations75
        )
        and allocation_rows75[78] == {
            "alignment": 16,
            "content_sha256": "18a62cc6fad32eb5997e569d4c340a87ed56f068826ae841dbe36a9764616206",
            "end_exclusive": 22892624,
            "gba_end_exclusive": 157110352,
            "gba_start": 156545072,
            "name": "modernization_rockruff_own_tempo_stage75_payload",
            "owner": "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75",
            "placement": "FIRST_FIT",
            "purpose": "Own Tempo Rockruff internal form species tables, evolution, breeding, acquisition, and P03 owner runtime",
            "region": "integration_modules",
            "sequence": 78,
            "size": 565280,
            "start": 22327344,
        }
        and _sha256(stage75_rom[22327344:22892624])
        == allocation_rows75[78]["content_sha256"]
        and a75.get("summaries", {}).get("allocation_count") == 79
        and a75.get("summaries", {}).get("overlap_count") == 0
        and a75.get("summaries", {}).get("remaining_allocatable_bytes") == 223723,
        "Stage75 allocation first78 layout/mutation/new sequence78境界不正",
    )
    _require(
        all(allocation_rows75[sequence] == allocation_rows76[sequence] for sequence in range(79))
        and _sha256(stable_json(a75.get("allocations", [])))
        == "8cf50825cd00551477106946878c76e6ecdfd9339d86ae212fb9812e08e72d3a"
        and _sha256(stable_json(a76.get("allocations", [])[:79]))
        == "8cf50825cd00551477106946878c76e6ecdfd9339d86ae212fb9812e08e72d3a"
        and allocation_rows76[79] == {
            "alignment": 16,
            "content_sha256": "c9c34af10900cb6cedbaaeef9dacd2d95a2fc0df0be39cb3aa29f8226ffbc92e",
            "end_exclusive": 22894690,
            "gba_end_exclusive": 157112418,
            "gba_start": 157110352,
            "name": "modernization_p05_stage76_edges_payload",
            "owner": "USER-MODERNIZATION-P05-STAGE76-EDGES",
            "placement": "FIRST_FIT",
            "purpose": "Mega Sol production Solar Beam popup plus Piercing Drill and Spicy Spray AI edge adapters",
            "region": "integration_modules",
            "sequence": 79,
            "size": 2066,
            "start": 22892624,
        }
        and _sha256(stage76_rom[22892624:22894690])
        == allocation_rows76[79]["content_sha256"]
        and a76.get("summaries", {}).get("allocation_count") == 80
        and a76.get("summaries", {}).get("overlap_count") == 0
        and a76.get("summaries", {}).get("remaining_allocatable_bytes") == 221657
        and m76.get("allocation_lineage") == {
            "first79_all_fields_equal": True,
            "new_count": 80,
            "new_first79_sha256": "8cf50825cd00551477106946878c76e6ecdfd9339d86ae212fb9812e08e72d3a",
            "new_sequence": 79,
            "parent_count": 79,
            "parent_first79_sha256": "8cf50825cd00551477106946878c76e6ecdfd9339d86ae212fb9812e08e72d3a",
            "parent_last_sequence": 78,
            "payload_slice_sha256": "c9c34af10900cb6cedbaaeef9dacd2d95a2fc0df0be39cb3aa29f8226ffbc92e",
        }
        and sum(left != right for left, right in zip(stage74_rom, stage75_rom)) == 540757
        and sum(left != right for left, right in zip(stage75_rom, stage76_rom)) == 2081,
        "Stage76 allocation first79完全保持/new sequence79/ROM差分境界不正",
    )
    _require(
        all(allocation_rows76[sequence] == allocation_rows77[sequence] for sequence in range(80))
        and _sha256(stable_json(a76.get("allocations", [])))
        == "f7cb757186024897cea03e71b02d8e25afc27829d407dc319f3e5a678fa87594"
        and _sha256(stable_json(a77.get("allocations", [])[:80]))
        == "f7cb757186024897cea03e71b02d8e25afc27829d407dc319f3e5a678fa87594"
        and allocation_rows77[80] == {
            "alignment": 16,
            "content_sha256": "933c8d7fdf731eaae0aa87c74974803de356dda8e64c055ef09beee4d229c672",
            "end_exclusive": 22895924,
            "gba_end_exclusive": 157113652,
            "gba_start": 157112432,
            "name": "modernization_p05_stage77_circus_suppression_payload",
            "owner": "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION",
            "placement": "FIRST_FIT",
            "purpose": "Battle Circus global ability-suppression dispatch for all 29 Stage72 ability hooks",
            "region": "integration_modules",
            "sequence": 80,
            "size": 1220,
            "start": 22894704,
        }
        and _sha256(stage77_rom[22894704:22895924])
        == allocation_rows77[80]["content_sha256"]
        and a77.get("summaries", {}).get("allocation_count") == 81
        and a77.get("summaries", {}).get("overlap_count") == 0
        and a77.get("summaries", {}).get("remaining_allocatable_bytes") == 220437
        and m77.get("allocation_lineage") == {
            "first80_all_fields_equal": True,
            "new_count": 81,
            "new_first80_sha256": "f7cb757186024897cea03e71b02d8e25afc27829d407dc319f3e5a678fa87594",
            "new_sequence": 80,
            "parent_count": 80,
            "parent_first80_sha256": "f7cb757186024897cea03e71b02d8e25afc27829d407dc319f3e5a678fa87594",
            "parent_last_sequence": 79,
            "payload_slice_sha256": "933c8d7fdf731eaae0aa87c74974803de356dda8e64c055ef09beee4d229c672",
        }
        and sum(left != right for left, right in zip(stage76_rom, stage77_rom)) == 1307,
        "Stage77 allocation first80完全保持/new sequence80/ROM差分境界不正",
    )
    latest_bps_audit = [
        _verify_incremental_bps(root, source, patch, target)
        for source, patch, target in LATEST_INCREMENTAL_BPS_PATHS
    ]
    # 累積candidate registryでは「最後に完了した工程」と「最後のcheckpoint」を
    # 別フィールドとして扱う。Stage77まで接続してもP02～P07をDONEへ昇格させない。
    source = registry.get("source", {})
    _require(
        registry.get("schema_version") == 2
        and registry.get("status")
        == "STAGE77_BATTLE_CIRCUS_SUPPRESSION_CHECKPOINT_NOT_RELEASE_CANDIDATE"
        and registry.get("completed_through") == "USER-MODERNIZATION-P01"
        and registry.get("checkpointed_through")
        == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION-CHECKPOINT"
        and source.get("stage68_checkpoint_commit")
        == "2a7197f6134509749da780aec61bf0db29147a0e"
        and source.get("stage69_checkpoint_commit")
        == "2a7197f6134509749da780aec61bf0db29147a0e"
        and source.get("stage70_checkpoint_commit")
        == "cc490045033b126c2b28f3b56c20432d8105287c"
        and source.get("stage71_checkpoint_commit")
        == "ee8062094f84fff42f529793cb95f09d2078ae33"
        and source.get("stage72_checkpoint_commit")
        == "bbab6b2e943186cf437a6dca90712c01f0319ded"
        and source.get("stage73_checkpoint_commit")
        == "1dd2a9ab8da73f7eb17dbd5b8fa8fcd96109443e"
        and source.get("stage74_checkpoint_commit")
        == "ddeb853a12af8b0bf3a76ceb16060de4fc686ec7"
        and source.get("stage75_checkpoint_commit") == STAGE75_IMPLEMENTATION_COMMIT
        and source.get("stage76_checkpoint_commit") == STAGE76_IMPLEMENTATION_COMMIT
        and source.get("stage77_checkpoint_commit") == SNAPSHOT_BASE_HEAD
        and source.get("stage73_preflight_commit")
        == "c2bb0afb26085a6815d5bd10a2d5b29db80f966d"
        and source.get("p02_stage71_acceptance_commit")
        == "ebc6fa00fe39a6c4a8d2d9fea13baf4eacf8faec"
        and source.get("uncommitted_checkpoint_identity") is None
        and registry.get("release_ready") is False
        and registry.get("active_play_baseline_changed") is False,
        "candidate v2 Stage77 registryの完了/checkpoint/release境界不正",
    )
    _require(
        registry.get("active_parent", {}).get("stage") == 62
        and registry.get("active_parent", {}).get("sha256") == s62["sha256"]
        and registry.get("parent", {}).get("stage") == 76
        and registry.get("parent", {}).get("sha256") == s76["sha256"]
        and registry.get("parent", {}).get("metadata", {}).get("sha256")
        == by_path["build/stages/76_modernization_p05_edges.json"]["sha256"]
        and registry.get("parent", {}).get("allocation", {}).get("sha256")
        == by_path["build/stages/76_modernization_p05_edges_allocation.json"]["sha256"]
        and registry.get("candidate", {}).get("stage") == 77
        and registry.get("candidate", {}).get("sha256") == s77["sha256"]
        and registry.get("candidate", {}).get("metadata", {}).get("sha256")
        == by_path["build/stages/77_modernization_p05_circus_suppression.json"]["sha256"]
        and registry.get("candidate", {}).get("allocation", {}).get("sha256")
        == by_path["build/stages/77_modernization_p05_circus_suppression_allocation.json"]["sha256"]
        and registry.get("p02_overlay_parent", {}).get("sha256")
        == "ddbb9c22ce3a42b32e84ffff040d098b4fb2f49a17b5a84792eaa3f92aa512bb"
        and registry.get("p02_overlay_parent", {}).get("changed_bytes_from_stage66")
        == 60,
        "candidate v2 Stage76 parent/Stage77 candidate identity不正",
    )
    adopted = registry.get("adopted_delta", {})
    p03_73 = adopted.get("p03_stage73_consumer_checkpoint", {})
    p03_74 = adopted.get("p03_stage74_supply_checkpoint", {})
    p03_75 = adopted.get("p03_stage75_own_tempo_checkpoint", {})
    p04_scope = adopted.get("p04_adoption_scope", {})
    p05_72 = adopted.get("p05_stage72_ability_runtime", {})
    p05_76 = adopted.get("p05_stage76_edges_checkpoint", {})
    p05_77 = adopted.get("p05_stage77_suppression_checkpoint", {})
    p02_71 = adopted.get("p02_stage71_acceptance", {})
    _require(
        p03_73.get("new_runtime_materialized_routes") == 5363
        and p03_73.get("existing_owner_accounted_routes") == 35207
        and p03_73.get("consumer_boundary_accounted_routes") == 40570
        and p03_73.get("cumulative_new_runtime_materialized_routes") == 56514
        and p03_73.get("cumulative_consumer_boundary_accounted_routes") == 91721
        and p03_73.get("machine_tutor_upstream_supply_dependency_routes") == 23595
        and p03_73.get("hook_count") == 3
        and p03_73.get("remaining_direct_machine_routes") == 26279
        and p03_73.get("remaining_direct_tutor_routes") == 369
        and p03_73.get("remaining_direct_supply_routes") == 26648
        and 56514 + 35207 + 26648 == 118369
        and p03_73.get("shared_egg_kept_out_of_normal_egg_table") is True
        and p03_73.get("reminder_kept_out_of_level_zero_rows") is True
        and p03_73.get("side_change_materialized") == 0
        and p03_73.get("browt_pombon_gecqua_materialized") == 0
        and p03_73.get("prohibited_coercions_materialized") == 0
        and p03_73.get("outside_declared_ranges") == 0,
        "candidate v2 P03 Stage73 materialized/accounted/supply/table分離/除外境界不正",
    )
    _require(
        p03_74 == {
            "direct_supply_materialized_routes": 26648,
            "direct_machine_routes": 26279,
            "direct_tutor_routes": 369,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "remaining_direct_supply_routes": 0,
            "preservation_missing_paths": 4014,
            "preservation_target_move_pairs": 2223,
            "preservation_species": 501,
            "preservation_target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
            "preservation_ui_supply_routes_added": 0,
            "preservation_route_accounting_added": 0,
            "build_learnable_maximum_entries": 238,
            "build_learnable_capacity": 429,
            "build_learnable_overflow_species": 0,
            "unlock_flag": "0x082C",
            "economy": "PROVISIONAL_REPLACEABLE",
            "withheld_own_tempo_rockruff_routes": 38,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
            "outside_declared_ranges": 0,
        }
        and p03_73.get("cumulative_new_runtime_materialized_routes")
        + p03_74.get("direct_supply_materialized_routes")
        == p03_74.get("cumulative_runtime_materialized_routes")
        and p03_74.get("cumulative_runtime_materialized_routes")
        + p03_73.get("existing_owner_accounted_routes")
        == p03_74.get("cumulative_accounted_routes"),
        "candidate v2 P03 Stage74 supply/preservation/capacity/economy/除外境界不正",
    )
    _require(
        p03_75 == {
            "internal_species_id": 1670,
            "normal_species_id": 1142,
            "dusk_species_id": 1263,
            "national_dex": 744,
            "ability_id": 20,
            "species_count": 1671,
            "pre_evolution_carry_paths": 38,
            "missing_owner_paths": 0,
            "source_owner_clone_routes": 60,
            "route_accounting_delta": 0,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "save_layout_changed": False,
            "archive_economy": "PROVISIONAL_REPLACEABLE",
            "allocation_sequence": 78,
            "allocation_count": 79,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        },
        "candidate v2 P03 Stage75 Own Tempo/accounting/save/economy/除外境界不正",
    )
    checkpoints = registry.get("checkpoints", {})
    deferred = registry.get("deferred", {})
    _require(
        adopted.get("changed_bytes_by_stage", {}).get("p03_stage74_from_stage73") == 70480
        and adopted.get("changed_bytes_by_stage", {}).get("p03_stage75_from_stage74") == 540757
        and adopted.get("changed_bytes_by_stage", {}).get("p05_stage76_from_stage75") == 2081
        and adopted.get("changed_bytes_by_stage", {}).get("p05_stage77_from_stage76") == 1307
        and checkpoints.get("p03")
        == "STAGE75_OWN_TEMPO_ROCKRUFF_CONNECTED_PROVISIONAL_ECONOMY_FINAL_MGBA_PENDING_NOT_P03_DONE"
        and checkpoints.get("p03_stage73_consumer")
        == "FIVE_GROUP_CONSUMER_BOUNDARY_CONNECTED_SUPPLY_MGBA_PENDING_NOT_P03_DONE"
        and checkpoints.get("p03_stage74_supply")
        == "DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_ROCKRUFF_MGBA_PENDING_NOT_P03_DONE"
        and checkpoints.get("p03_stage75_own_tempo")
        == "OWN_TEMPO_ROCKRUFF_INTERNAL_FORM_CONNECTED_PROVISIONAL_ECONOMY_FINAL_MGBA_PENDING_NOT_P03_DONE"
        and deferred.get("p03_full_materialization")
        == "DIRECT_SUPPLY_AND_OWN_TEMPO_ROCKRUFF_0744_01_CONNECTED_PROVISIONAL_ARCHIVE_ECONOMY_AND_FINAL_MGBA_REMAIN"
        and deferred.get("p03_machine_tutor_supply")
        == "RESOLVED_STAGE74_26648_DIRECT_ROUTES_CONNECTED",
        "candidate v2 Stage75～77 checkpoint/deferred解決・残件境界不正",
    )
    _require(
        p04_scope.get("mega_species_and_forms") == 49
        and p04_scope.get("new_normal_species") == 0
        and p04_scope.get("mega_stone_item_ids_materialized") == 45
        and p04_scope.get("mega_stone_bp_shop_entries") == 45
        and p04_scope.get("mega_stone_bp_price_each") == 16
        and p04_scope.get("floette_eternal_existing_species_id") == 1029
        and p04_scope.get("floette_eternal_exact_party_pc_delivery") is True
        and p04_scope.get("floette_eternal_exact_full_and_fresh_reload") is False
        and p04_scope.get("mega_form_species_runtime_materialized") is True
        and p04_scope.get("mega_form_battle_runtime_materialized") is True
        and p04_scope.get("mega_form_battle_runtime_records") == 49
        and p04_scope.get("mega_form_runtime_exact_mgba") is False,
        "candidate v2 P04 49 Mega/shop/Floette runtime境界不正",
    )
    _require(
        p05_72.get("ability_ids") == list(range(312, 318))
        and p05_72.get("ability_count") == 6
        and p05_72.get("battle_hook_count") == 29
        and p05_72.get("rom_linked") is True
        and p05_72.get("exact_mgba") is False
        and p05_72.get("documented_ai_ui_edges_pending") == 4
        and p05_76 == {
            "implemented_edge_count": 3,
            "pending_edge_count": 1,
            "mega_sol_solar_charge_popup": "IMPLEMENT",
            "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
            "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
            "eelevate_dedicated_switch": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
            "allocation_parent_count": 79,
            "allocation_count": 80,
            "allocation_sequence": 79,
            "parent_first79_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 5,
            "changed_bytes_inside_allowlist": 2081,
            "changed_bytes_outside_allowlist": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
        }
        and p05_77 == {
            "unique_hook_count": 29,
            "ability_surface_occurrence_count": 33,
            "battle_circus_global_fixed": True,
            "battle_type_mask": "0x04000000",
            "ability_suppression_mask": "0x80000000",
            "predicate": "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0",
            "normal_path": "TAIL_DELEGATE_STAGE72_WRAPPER",
            "suppressed_path": "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE",
            "ordinary_suppression_changed": False,
            "allocation_parent_count": 80,
            "allocation_count": 81,
            "allocation_sequence": 80,
            "parent_first80_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 30,
            "changed_bytes_inside_allowlist": 1307,
            "changed_bytes_outside_allowlist": 0,
            "stage76_pointer_and_three_hooks_preserved": True,
            "eelevate_unsafe_switch_hooks_installed": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
        }
        and checkpoints.get("p05")
        == "STAGE77_BATTLE_CIRCUS_SUPPRESSION_CONNECTED_EELEVATE_AND_FINAL_CUMULATIVE_MGBA_REMAIN"
        and checkpoints.get("p05_stage76_edges")
        == "THREE_SAFE_AI_UI_EDGES_CONNECTED_EELEVATE_AND_FINAL_MGBA_PENDING_NOT_P05_DONE"
        and checkpoints.get("p05_stage77_suppression")
        == "BATTLE_CIRCUS_29_HOOK_33_SURFACE_SUPPRESSION_CONNECTED_EELEVATE_AND_FINAL_CUMULATIVE_MGBA_PENDING_NOT_P05_DONE"
        and deferred.get("p05_new_abilities")
        == "6_ROM_LINKED_THREE_SAFE_AI_UI_EDGES_AND_BATTLE_CIRCUS_GLOBAL_SUPPRESSION_CONNECTED_EELEVATE_SWITCH_AI_AND_FINAL_CUMULATIVE_MGBA_PENDING"
        and p02_71 == {
            "status": "STOPPED_EXACT_UI_PENDING",
            "production_runtime": "UNJUDGED",
            "exact_ui_acceptance": False,
            "additional_mgba_deferred": True,
        },
        "candidate v2 P02 Stage71/P05 Stage72/76/77境界不正",
    )
    return {
        "active_stage": 62,
        "selected_checkpoint_stage": 77,
        "selection": "HIGHEST_EXPLICITLY_PINNED_CANDIDATE_NOT_ACTIVE_BASELINE",
        "registry": {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "STAGE77_BATTLE_CIRCUS_SUPPRESSION_CHECKPOINT_NOT_RELEASE_CANDIDATE",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION-CHECKPOINT",
            "checkpoint_commit": SNAPSHOT_BASE_HEAD,
            "last_committed_checkpoint": SNAPSHOT_BASE_HEAD,
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 76,
            "candidate_stage": 77,
        },
        "inheritance": _candidate_inheritance(by_path),
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
        "stage68_integrated": True,
        "stage68_scope": {
            "mega_stone_item_ids": [999, 1043],
            "mega_stone_item_count": 45,
            "shop_entry_count": 45,
            "currency": "BP",
            "price_each": 16,
            "mega_ring_gate_item_id": 580,
            "claim_flags": [0x14A0, 0x14CC],
            "exact_rom_runtime_gate": "PASS",
            "mega_form_battle_runtime_materialized": False,
            "full_p04_done": False,
        },
        "stage69_integrated": True,
        "stage69_scope": {
            "existing_species_id": 1029,
            "level": 50,
            "mega_ring_gate_item_id": 580,
            "claim_flag": 0x14CD,
            "canonical_collection_bit": 850,
            "exact_party_delivery": True,
            "exact_pc_delivery": True,
            "exact_full_and_fresh_reload": False,
            "host_full_rollback_reload": True,
            "runtime_gate": "PARTIAL_PASS_HARNESS_FIXTURE_BLOCKED",
            "full_p04_done": False,
        },
        "stage70_integrated": True,
        "stage70_scope": {
            "mega_species_and_forms": 49,
            "existing_species_prefix_byte_exact": True,
            "floette_eternal_species_id_1029_preserved": True,
            "side_change_referenced": False,
            "new_normal_species": 0,
            "exact_mgba": False,
            "full_p04_done": False,
        },
        "stage71_integrated": True,
        "stage71_scope": {
            "forward_entries_added": 49,
            "reverse_entries_added": 49,
            "existing_mega_entries_preserved": 80,
            "mega_form_battle_runtime_records": 49,
            "exact_mgba": False,
            "full_p04_done": False,
        },
        "stage72_integrated": True,
        "stage72_scope": {
            "ability_ids": list(range(312, 318)),
            "ability_count": 6,
            "battle_hook_count": 29,
            "rom_linked": True,
            "documented_ai_ui_edges_pending": 4,
            "exact_mgba": False,
            "full_p05_done": False,
        },
        "stage73_integrated": True,
        "stage73_scope": {
            "new_runtime_materialized_routes": 5363,
            "existing_owner_accounted_routes": 35207,
            "consumer_boundary_accounted_routes": 40570,
            "cumulative_new_runtime_materialized_routes": 56514,
            "cumulative_consumer_boundary_accounted_routes": 91721,
            "machine_tutor_upstream_supply_dependency_routes": 23595,
            "remaining_direct_supply_routes": 26648,
            "hook_count": 3,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        },
        "stage74_integrated": True,
        "stage74_scope": {
            "direct_supply_materialized_routes": 26648,
            "direct_machine_routes": 26279,
            "direct_tutor_routes": 369,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "remaining_direct_supply_routes": 0,
            "preservation_missing_paths": 4014,
            "preservation_target_move_pairs": 2223,
            "preservation_species": 501,
            "preservation_target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
            "preservation_ui_supply_routes_added": 0,
            "preservation_route_accounting_added": 0,
            "build_learnable_maximum_entries": 238,
            "build_learnable_capacity": 429,
            "build_learnable_overflow_species": 0,
            "unlock_flag": "0x082C",
            "economy": "PROVISIONAL_REPLACEABLE",
            "withheld_own_tempo_rockruff_routes": 38,
            "hook_count": 2,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        },
        "stage75_integrated": True,
        "stage75_scope": {
            "internal_species_id": 1670,
            "normal_species_id": 1142,
            "dusk_species_id": 1263,
            "national_dex": 744,
            "ability_id": 20,
            "species_count": 1671,
            "pre_evolution_carry_paths": 38,
            "missing_owner_paths": 0,
            "source_owner_clone_routes": 60,
            "route_accounting_delta": 0,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "save_layout_changed": False,
            "archive_economy": "PROVISIONAL_REPLACEABLE",
            "allocation_sequence": 78,
            "allocation_count": 79,
            "full_p03_done": False,
            "exact_mgba": False,
        },
        "stage76_integrated": True,
        "stage76_scope": {
            "implemented_edge_count": 3,
            "pending_edge_count": 1,
            "edges": expected_edges76,
            "allocation_parent_count": 79,
            "allocation_count": 80,
            "allocation_sequence": 79,
            "parent_first79_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 5,
            "changed_bytes_inside_allowlist": 2081,
            "changed_bytes_outside_allowlist": 0,
            "eelevate_unsafe_hooks_installed": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
            "exact_mgba": False,
        },
        "stage77_integrated": True,
        "stage77_scope": {
            "unique_hook_count": 29,
            "ability_surface_occurrence_count": 33,
            "battle_circus_global_fixed": True,
            "battle_type_mask": "0x04000000",
            "ability_suppression_mask": "0x80000000",
            "predicate": "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0",
            "normal_path": "TAIL_DELEGATE_STAGE72_WRAPPER",
            "suppressed_path": "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE",
            "ordinary_suppression_changed": False,
            "allocation_parent_count": 80,
            "allocation_count": 81,
            "allocation_sequence": 80,
            "parent_first80_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 30,
            "changed_bytes_inside_allowlist": 1307,
            "changed_bytes_outside_allowlist": 0,
            "stage76_pointer_and_three_hooks_preserved": True,
            "eelevate_unsafe_switch_hooks_installed": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
            "exact_mgba": False,
        },
        "latest_incremental_bps": latest_bps_audit,
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
        from tools.modernization_p08_historical_sources import resolve
        try:
            historical = resolve(root, row, tracked, binding)
        except ValueError as error:
            _fail(str(error))
        raw = historical[0] if historical else _regular_bytes(root, relative)
        identity = verify_exact_bytes(relative, raw, row.get("size"), row.get("sha256"))
        if historical:
            identity["source_resolution"] = historical[1]
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
    p02_stage71 = documents[
        "content/modernization/p02_stage71_acceptance_checkpoint.json"
    ]
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
    p03_stage73_preflight = documents["config/modernization_p03_stage73_consumers.json"]
    p03_stage73_config = documents["config/modernization_p03_stage73_runtime.json"]
    p03_stage73 = documents[
        "content/modernization/p03_stage73_consumer_runtime_checkpoint.json"
    ]
    p03_stage73_routes = documents[
        "content/modernization/p03_stage73_consumer_runtime_route_audit.json"
    ]
    p03_stage74_config = documents["config/modernization_p03_stage74_supply.json"]
    p03_stage74 = documents[
        "content/modernization/p03_stage74_supply_runtime_checkpoint.json"
    ]
    p03_stage75_config = documents["config/modernization_rockruff_own_tempo_stage75.json"]
    p03_stage75_contract = documents[
        "content/modernization/rockruff_own_tempo_stage75_contract.json"
    ]
    p03_stage75 = documents[
        "content/modernization/rockruff_own_tempo_stage75_checkpoint.json"
    ]
    p04_manifest = documents["content/modernization/p04_candidate_manifest.json"]
    p04_official = documents["content/modernization/p04_official_sources.json"]
    p04_assets = documents["content/modernization/p04_asset_sources.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p04_capacity = documents[
        "content/modernization/p04_capacity_allocation_manifest.json"
    ]
    mega_shop_config = documents["config/modernization_mega_shop.json"]
    mega_shop_bounds = documents["config/modernization_mega_shop_item_bounds.json"]
    mega_shop_catalog = documents["content/modernization/mega_shop_catalog.json"]
    mega_shop_checkpoint = documents["content/modernization/mega_shop_checkpoint.json"]
    mega_shop_mgba = documents[
        "content/modernization/mega_shop_mgba_runtime_gate.json"
    ]
    floette_config = documents["config/modernization_floette_gift.json"]
    floette_contract = documents["content/modernization/floette_gift_contract.json"]
    floette_checkpoint = documents[
        "content/modernization/floette_gift_checkpoint.json"
    ]
    floette_mgba = documents[
        "content/modernization/floette_gift_mgba_runtime_gate.json"
    ]
    p04_stage70_config = documents["config/modernization_p04_species_runtime.json"]
    p04_stage70_contract = documents[
        "content/modernization/p04_species_runtime_contract.json"
    ]
    p04_stage70 = documents[
        "content/modernization/p04_species_runtime_checkpoint.json"
    ]
    p04_stage71_config = documents["config/modernization_p04_mega_runtime.json"]
    p04_stage71_mapping = documents[
        "content/modernization/p04_mega_runtime_mapping.json"
    ]
    p04_stage71 = documents["content/modernization/p04_mega_runtime_checkpoint.json"]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p05_plan = documents["content/modernization/p05_data_only_patch_plan.json"]
    p05_runtime = documents["content/modernization/p05_runtime_handoff.json"]
    p05_ability = documents["content/modernization/p05_ability_runtime_checkpoint.json"]
    p05_stage72_config = documents["config/modernization_p05_ability_rom_runtime.json"]
    p05_stage72 = documents[
        "content/modernization/p05_ability_rom_runtime_checkpoint.json"
    ]
    p05_stage72_surface = documents[
        "content/modernization/p05_ability_rom_runtime_surface_matrix.json"
    ]
    p05_stage76_config = documents["config/modernization_p05_stage76_edges.json"]
    p05_stage76_contract = documents[
        "content/modernization/p05_stage76_edges_contract.json"
    ]
    p05_stage76 = documents[
        "content/modernization/p05_stage76_edges_checkpoint.json"
    ]
    p05_stage77_config = documents["config/modernization_p05_stage77_suppression.json"]
    p05_stage77_contract = documents[
        "content/modernization/p05_stage77_suppression_contract.json"
    ]
    p05_stage77 = documents[
        "content/modernization/p05_stage77_suppression_checkpoint.json"
    ]
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
        and p01_candidate.get("status")
        == "STAGE77_BATTLE_CIRCUS_SUPPRESSION_CHECKPOINT_NOT_RELEASE_CANDIDATE"
        and p01_candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and p01_candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION-CHECKPOINT"
        and p01_candidate.get("release_ready") is False
        and p01_candidate.get("active_play_baseline_changed") is False,
        "candidate v2のP01完了/Stage77 checkpoint/release境界不正",
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
        p01_candidate.get("parent", {}).get("stage") == 76
        and p01_candidate.get("parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
        and p01_candidate.get("parent", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.json"][1]
        and p01_candidate.get("parent", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/76_modernization_p05_edges_allocation.json"
        ][1],
        "candidate v2 parentがStage76 exact identityではありません",
    )
    _require(
        p01_candidate.get("candidate", {}).get("stage") == 77
        and p01_candidate.get("candidate", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/77_modernization_p05_circus_suppression.gba"
        ][1]
        and p01_candidate.get("candidate", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/77_modernization_p05_circus_suppression.json"
        ][1]
        and p01_candidate.get("candidate", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/77_modernization_p05_circus_suppression_allocation.json"
        ][1],
        "candidate v2 candidateがStage77 exact identityではありません",
    )
    _require(
        p01_candidate.get("patches") == _candidate_patch_declarations(),
        "candidate v2 Stage67～77 BPS path/size/source/target/hash/round-trip不正",
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
        (68, "USER-MODERNIZATION-MEGA-STONE-BP-SHOP", "P04_ACQUISITION_CHECKPOINT_NOT_P04_DONE", 65821,
         CANDIDATE_ARTIFACTS["build/stages/68_modernization_mega_shop.gba"][1]),
        (69, "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT", "P04_ACQUISITION_CHECKPOINT_NOT_P04_DONE", 1960,
         CANDIDATE_ARTIFACTS["build/stages/69_modernization_floette_gift.gba"][1]),
        (70, "USER-MODERNIZATION-P04-SPECIES-RUNTIME-STAGE70", "P04_SPECIES_RUNTIME_CHECKPOINT_NOT_P04_DONE", 818994,
         CANDIDATE_ARTIFACTS["build/stages/70_modernization_p04_species_runtime.gba"][1]),
        (71, "USER-MODERNIZATION-P04-MEGA-RUNTIME-STAGE71", "P04_MEGA_RUNTIME_CHECKPOINT_NOT_P04_DONE", 383,
         CANDIDATE_ARTIFACTS["build/stages/71_modernization_p04_mega_runtime.gba"][1]),
        (72, "USER-MODERNIZATION-P05-ABILITY-ROM-RUNTIME-STAGE72", "P05_ABILITY_ROM_RUNTIME_CHECKPOINT_NOT_P05_DONE", 7257,
         CANDIDATE_ARTIFACTS["build/stages/72_modernization_p05_ability_rom_runtime.gba"][1]),
        (73, "USER-MODERNIZATION-P03-STAGE73-CONSUMER-RUNTIME", "P03_CONSUMER_RUNTIME_CHECKPOINT_NOT_P03_DONE", 36585,
         CANDIDATE_ARTIFACTS["build/stages/73_modernization_p03_consumer_runtime.gba"][1]),
        (74, "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME", "P03_DIRECT_SUPPLY_CHECKPOINT_NOT_P03_DONE", 70480,
         CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.gba"][1]),
        (75, "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75", "P03_OWN_TEMPO_ROCKRUFF_CHECKPOINT_NOT_P03_DONE", 540757,
         CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.gba"][1]),
        (76, "USER-MODERNIZATION-P05-STAGE76-EDGES", "P05_THREE_EDGES_CHECKPOINT_NOT_P05_DONE", 2081,
         CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]),
        (77, "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION", "P05_BATTLE_CIRCUS_SUPPRESSION_CHECKPOINT_NOT_P05_DONE", 1307,
         CANDIDATE_ARTIFACTS["build/stages/77_modernization_p05_circus_suppression.gba"][1]),
    ]
    stage_chain = p01_candidate.get("stage_chain")
    _require(isinstance(stage_chain, list) and len(stage_chain) == 15, "candidate v2 stage_chain件数不正")
    for row, (stage, task, state, changed, digest) in zip(stage_chain, expected_stage_chain):
        _require(
            row.get("stage") == stage and row.get("task") == task
            and row.get("state") == state and row.get("changed_bytes_from_parent") == changed
            and row.get("sha256") == digest,
            f"candidate v2 stage_chain不正: Stage{stage}",
        )
    _require(
        stage_chain[-4].get("exact_runtime_gate")
        == "STATIC_ONLY_ROCKRUFF_SEMANTICS_AND_MGBA_PENDING"
        and stage_chain[-3].get("exact_runtime_gate") == "STATIC_ONLY_FINAL_MGBA_PENDING"
        and stage_chain[-2].get("exact_runtime_gate")
        == "HOST_STATIC_EELEVATE_AND_MGBA_PENDING"
        and stage_chain[-1].get("exact_runtime_gate")
        == "HOST_STATIC_EELEVATE_AND_CUMULATIVE_MGBA_PENDING",
        "candidate v2 Stage74～77 exact runtime gate境界不正",
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
    _require(
        mega_shop_config.get("stage") == 68
        and mega_shop_config.get("catalog", {}).get("entry_count") == 45
        and mega_shop_config.get("catalog", {}).get("first_item_id") == 999
        and mega_shop_config.get("catalog", {}).get("last_item_id") == 1043
        and mega_shop_config.get("catalog", {}).get("price_bp") == 16
        and mega_shop_config.get("catalog", {}).get("key_stone_item_id") == 580,
        "Stage68 Mega Stone shop config境界不正",
    )
    _require(
        mega_shop_bounds.get("old_max_inclusive") == 998
        and mega_shop_bounds.get("new_max_inclusive") == 1043
        and mega_shop_bounds.get("first_rejected") == 1044
        and mega_shop_bounds.get("site_count") == 12,
        "Stage68 CFRU item consumer bound境界不正",
    )
    _require(
        mega_shop_catalog.get("status") == "ROM_MATERIALIZED"
        and mega_shop_catalog.get("entry_count") == 45
        and len(mega_shop_catalog.get("entries", [])) == 45
        and all(row.get("price_bp") == 16 for row in mega_shop_catalog.get("entries", [])),
        "Stage68 Mega Stone catalog materialization不正",
    )
    _require(
        mega_shop_checkpoint.get("stage") == 68
        and mega_shop_checkpoint.get("status") == "PASS_HOST_STATIC_EXACT_ROM_PENDING"
        and mega_shop_checkpoint.get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/68_modernization_mega_shop.gba"][1]
        and mega_shop_mgba.get("status") == "PASS"
        and mega_shop_mgba.get("claims", {}).get("exact_stage68_rom") is True
        and mega_shop_mgba.get("claims", {}).get(
            "item_consumer_boundaries_and_mega_semantics"
        ) is True
        and mega_shop_mgba.get("claims", {}).get(
            "normal_save_fresh_core_once_rejection"
        ) is True,
        "Stage68 exact mGBA runtime gate境界不正",
    )
    _require(
        floette_config.get("stage") == 69
        and floette_config.get("gift", {}).get("species_id") == 1029
        and floette_config.get("gift", {}).get("level") == 50
        and floette_config.get("gift", {}).get("unlock_item_id") == 580
        and floette_config.get("gift", {}).get("claim_flag") == "0x14CD",
        "Stage69 Floette Eternal config境界不正",
    )
    _require(
        floette_contract.get("status") == "PASS_STATIC_CONTRACT"
        and floette_contract.get("identity", {}).get("species_id") == 1029
        and floette_contract.get("identity", {}).get("level") == 50
        and floette_checkpoint.get("status")
        == "PASS_HOST_AND_EXACT_PARTIAL_RUNTIME_FULL_RELOAD_PENDING"
        and floette_checkpoint.get("parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/68_modernization_mega_shop.gba"][1],
        "Stage69 Floette contract/checkpoint境界不正",
    )
    exact_floette = floette_mgba.get("exact_rom_confirmed", {})
    _require(
        floette_mgba.get("status") == "PARTIAL_PASS_HARNESS_FIXTURE_BLOCKED"
        and floette_mgba.get("release_gate")
        == "PENDING_EXACT_PARTY_PC_FULL_AND_FRESH_RELOAD"
        and floette_mgba.get("rom_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/69_modernization_floette_gift.gba"][1]
        and exact_floette.get("party_delivery_species1029_level50") is True
        and exact_floette.get("full_party_pc_delivery_species1029_level50") is True
        and floette_mgba.get("not_yet_executed_exact_rom", {}).get(
            "fresh_core_standard_save_reload"
        ) == "PENDING",
        "Stage69 Floette exact partial/runtime pending境界不正",
    )
    _require(
        p02_stage71.get("status") == "STOPPED_EXACT_UI_PENDING"
        and p02_stage71.get("classification")
        == "STAGE71_EXACT_ROM_TWO_HARNESS_FAILURES_PRODUCTION_RUNTIME_UNJUDGED"
        and p02_stage71.get("stage71", {}).get("rom_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/71_modernization_p04_mega_runtime.gba"
        ][1]
        and p02_stage71.get("stage71", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/71_modernization_p04_mega_runtime.json"
        ][1]
        and p02_stage71.get("stage71", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/71_modernization_p04_mega_runtime_allocation.json"
        ][1]
        and p02_stage71.get("claims", {}).get("stage71_exact_rom_executed") is True
        and p02_stage71.get("claims", {}).get("p02_production_runtime_judged") is False
        and p02_stage71.get("claims", {}).get("full_evolution_acceptance") is False
        and p02_stage71.get("execution", {}).get("p02_production_runtime_judgment")
        == "UNJUDGED"
        and len(p02_stage71.get("completed_acceptance", [])) == 2
        and len(p02_stage71.get("remaining_acceptance", [])) == 9
        and p02_stage71.get("release_ready") is False,
        "P02 Stage71 exact UI停止/production未判定境界不正",
    )
    _require(
        p03_stage73_preflight.get("status") == "PREFLIGHT_ONLY_PARENT_PENDING"
        and p03_stage73_preflight.get("parent_identity", {}).get(
            "stage72_commit"
        ) == "PENDING"
        and p03_stage73_preflight.get("claim_policy", {}).get(
            "stage73_completion_claim_allowed"
        ) is False
        and p03_stage73_preflight.get("selection_boundary", {}).get(
            "browt_pombon_gecqua_adopted_count"
        ) == 0
        and p03_stage73_preflight.get("selection_boundary", {}).get(
            "side_change_global_excluded_count"
        ) == 159,
        "P03 Stage73 historical preflight境界不正",
    )
    _require(
        p03_stage73_config.get("status") == "STAGE72_IDENTITY_PINNED"
        and p03_stage73_config.get("parent_identity", {}).get(
            "stage72_commit"
        ) == "bbab6b2e943186cf437a6dca90712c01f0319ded"
        and p03_stage73_config.get("parent_identity", {}).get("rom", {}).get(
            "sha256"
        ) == CANDIDATE_ARTIFACTS[
            "build/stages/72_modernization_p05_ability_rom_runtime.gba"
        ][1]
        and p03_stage73_config.get("parent_identity", {}).get("metadata", {}).get(
            "sha256"
        ) == CANDIDATE_ARTIFACTS[
            "build/stages/72_modernization_p05_ability_rom_runtime.json"
        ][1]
        and p03_stage73_config.get("parent_identity", {}).get("allocation", {}).get(
            "sha256"
        ) == CANDIDATE_ARTIFACTS[
            "build/stages/72_modernization_p05_ability_rom_runtime_allocation.json"
        ][1]
        and p03_stage73_config.get("parent_identity", {}).get("checkpoint", {}).get(
            "sha256"
        ) == PINNED_TRACKED_INPUTS[
            "content/modernization/p05_ability_rom_runtime_checkpoint.json"
        ][1]
        and p03_stage73_config.get("inputs", {}).get(
            "consumer_preflight", {}
        ).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p03_stage73_consumers.json"][1]
        and p03_stage73_config.get("consumer_contract", {}).get(
            "accounted_route_count"
        ) == 40570
        and p03_stage73_config.get("consumer_contract", {}).get(
            "new_runtime_materialized_route_count"
        ) == 5363
        and p03_stage73_config.get("consumer_contract", {}).get(
            "existing_owner_accounted_route_count"
        ) == 35207
        and p03_stage73_config.get("consumer_contract", {}).get(
            "remaining_full_p03_routes", {}
        ).get("total") == 26648,
        "P03 Stage73 runtime config parent/preflight/accounting境界不正",
    )
    accounting73 = p03_stage73_routes.get("accounting", {})
    remaining73 = p03_stage73_routes.get("remaining_full_p03_routes", {})
    breeding_owner73 = p03_stage73_routes.get(
        "conditional_breeding_existing_owner_evidence", {}
    )
    serialization73 = p03_stage73_routes.get("serialization", {})
    breeding_instructions73 = serialization73.get(
        "conditional_breeding_existing_parent_owner", {}
    ).get("instruction_evidence", {})
    _require(
        p03_stage73.get("status")
        == "CHECKPOINT_FIVE_CONSUMER_BOUNDARY_CONNECTED_SUPPLY_DEPENDENCIES_REMAIN"
        and p03_stage73.get("done") is False
        and p03_stage73.get("release_candidate") is False
        and p03_stage73.get("output_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/73_modernization_p03_consumer_runtime.gba"
        ][1]
        and p03_stage73.get("parent_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/72_modernization_p05_ability_rom_runtime.gba"
        ][1]
        and p03_stage73.get("allocation_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/73_modernization_p03_consumer_runtime_allocation.json"
        ][1]
        and p03_stage73.get("route_audit_sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p03_stage73_consumer_runtime_route_audit.json"
        ][1]
        and p03_stage73.get("bps", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps"
        ][1]
        and p03_stage73.get("bps", {}).get("round_trip") is True
        and p03_stage73.get("mgba") == "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "P03 Stage73 checkpoint親/output/allocation/audit/BPS境界不正",
    )
    _require(
        accounting73.get("new_runtime_materialized_routes") == 5363
        and accounting73.get("existing_owner_accounted_routes") == 35207
        and accounting73.get("consumer_boundary_accounted_routes") == 40570
        and accounting73.get("machine_tutor_upstream_supply_dependency") == 23595
        and 51151 + 5363 == 56514
        and 51151 + 40570 == 91721
        and remaining73 == {"machine": 26279, "total": 26648, "tutor": 369}
        and 56514 + 35207 + remaining73["total"] == 118369
        and p03_stage73_routes.get("side_change_materialized") == 0
        and p03_stage73_routes.get("browt_pombon_gecqua_materialized") == 0
        and p03_stage73_routes.get("prohibited_coercions_materialized") == 0
        and serialization73.get("shared_egg_kept_out_of_normal_egg_table") is True
        and serialization73.get("reminder_kept_out_of_level_zero_rows") is True,
        "P03 Stage73 materialized/accounted/supply/table分離/除外勘定不正",
    )
    _require(
        breeding_owner73.get("canonical_species") == 24
        and breeding_owner73.get("light_ball_item") == 202
        and breeding_owner73.get("volt_tackle_move") == 344
        and breeding_owner73.get("source_route_count") == 1
        and breeding_owner73.get("runtime_owner") == "PARENT_BUILD_EGG_MOVESET"
        and breeding_instructions73.get("volt_tackle_build", {}).get("immediate") == 172
        and breeding_instructions73.get("volt_tackle_build", {}).get("shift") == 1
        and breeding_instructions73.get("volt_tackle_build", {}).get("result") == 344,
        "P03 Stage73 Pichu/Light Ball既存owner命令証拠不正",
    )
    parent74 = p03_stage74_config.get("parent_identity", {})
    supply74 = p03_stage74_config.get("supply_contract", {})
    runtime74 = p03_stage74_config.get("runtime", {})
    learnable74 = runtime74.get("build_learnable_moveset", {})
    preservation74 = learnable74.get("preservation_only", {})
    _require(
        p03_stage74_config.get("task")
        == "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME"
        and p03_stage74_config.get("stage") == 74
        and p03_stage74_config.get("status") == "STAGE73_IDENTITY_PINNED"
        and parent74.get("stage73_commit")
        == "1dd2a9ab8da73f7eb17dbd5b8fa8fcd96109443e"
        and parent74.get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/73_modernization_p03_consumer_runtime.gba"][1]
        and parent74.get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/73_modernization_p03_consumer_runtime.json"][1]
        and parent74.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/73_modernization_p03_consumer_runtime_allocation.json"
        ][1]
        and parent74.get("checkpoint", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p03_stage73_consumer_runtime_checkpoint.json"
        ][1]
        and parent74.get("route_audit", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p03_stage73_consumer_runtime_route_audit.json"
        ][1]
        and parent74.get("incremental_bps", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps"
        ][1]
        and parent74.get("policy")
        == "FAIL_CLOSED_EXACT_STAGE73_COMMIT_AND_SIX_ARTIFACT_IDENTITIES",
        "P03 Stage74 configのStage73 commit/6親identity不正",
    )
    _require(
        supply74.get("total_routes") == 26648
        and supply74.get("total_species_move_pairs") == 26648
        and supply74.get("duplicate_species_family_move_pairs") == 0
        and supply74.get("supply_required_set_sha256")
        == "5ef6be8c533e60c07ec1240c3ee8cc1e56c90c505689f3d41436719f338f7968"
        and supply74.get("machine", {}).get("routes") == 26279
        and supply74.get("machine", {}).get("set_sha256")
        == "c36479fe7ccca18a2f0861597d7e9667d0f30f2cc1a32d33dc32efea12e107fd"
        and supply74.get("machine", {}).get("max_rows_per_species") == 131
        and supply74.get("machine", {}).get("max_pages") == 4
        and supply74.get("tutor", {}).get("routes") == 369
        and supply74.get("tutor", {}).get("set_sha256")
        == "085379dc87fb5127e2f8f29d35d4f51805b138c7c86ecc022a68b5979da24f15"
        and supply74.get("tutor", {}).get("max_rows_per_species") == 12
        and supply74.get("existing_slot_projection", {})
        == {
            "routes": 29773,
            "machine": 29033,
            "tutor": 740,
            "set_sha256": "f4be2d83dae734c9339b790583d1e8c427daac49c964c87205b2f970b6deb3f1",
        }
        and supply74.get("selected_direct_partition")
        == {"total": 56421, "existing": 29773, "new": 26648}
        and supply74.get("cross_family_same_move_ids")
        == [173, 264, 304, 340, 352, 395, 700, 701, 702, 793]
        and supply74.get("same_species_cross_family_pair_count") == 0
        and supply74.get("completion_claim")
        == "DIRECT_MACHINE_TUTOR_SUPPLY_26648_COMPLETE_CHECKPOINT_NOT_FULL_P03_DONE",
        "P03 Stage74 config direct供給family分離/hash/accounting境界不正",
    )
    _require(
        runtime74.get("side_change_source_routes_excluded") == 159
        and runtime74.get("side_change_materialized") == 0
        and runtime74.get("prohibited_species_materialized") == 0
        and runtime74.get("candidate_capacity") == 40
        and learnable74.get("caller_capacity_u16") == 429
        and learnable74.get("maximum_runtime_buffer_entries_after_archive_append") == 238
        and learnable74.get("maximum_unique_entries_after_archive_append") == 234
        and learnable74.get("overflow_rows") == 0
        and preservation74 == {
            "selected_route_count_checked": 118369,
            "missing_path_count": 4014,
            "runtime_target_move_count": 2223,
            "species_count": 501,
            "max_rows_per_species": 22,
            "max_species": 576,
            "target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
            "ui_supply_routes_added": 0,
            "route_accounting_added": 0,
        }
        and runtime74.get("unlock", {}).get("required_flag") == "0x082C"
        and runtime74.get("unlock", {}).get("early_game_archive_available") is False
        and runtime74.get("economy", {}).get("price") == 0
        and runtime74.get("economy", {}).get("status") == "PROVISIONAL_REPLACEABLE"
        and runtime74.get("prohibited_coercions") == [
            "MACHINE_TO_EXISTING_TM_SLOT",
            "TUTOR_TO_EXISTING_TUTOR_SLOT",
            "MACHINE_OR_TUTOR_TO_LEVEL_ZERO",
            "MACHINE_OR_TUTOR_TO_EGG",
            "MACHINE_AND_TUTOR_TABLE_UNION",
        ],
        "P03 Stage74 config preservation/capacity/unlock/economy/除外境界不正",
    )
    checkpoint_preservation74 = p03_stage74.get("build_learnable_preservation", {})
    _require(
        p03_stage74.get("task") == "USER-MODERNIZATION-P03-STAGE74-SUPPLY-RUNTIME"
        and p03_stage74.get("stage") == 74
        and p03_stage74.get("status")
        == "CHECKPOINT_DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_FULL_P03_WITHHELD"
        and p03_stage74.get("completion_claim")
        == "DIRECT_MACHINE_TUTOR_SUPPLY_26648_COMPLETE_CHECKPOINT_NOT_FULL_P03_DONE"
        and p03_stage74.get("done") is False
        and p03_stage74.get("release_candidate") is False
        and p03_stage74.get("full_p03_done") is False
        and p03_stage74.get("parent_commit")
        == "1dd2a9ab8da73f7eb17dbd5b8fa8fcd96109443e"
        and p03_stage74.get("parent_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/73_modernization_p03_consumer_runtime.gba"][1]
        and p03_stage74.get("output_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.gba"][1]
        and str(p03_stage74.get("output_crc32", "")).upper() == "C9929F79"
        and p03_stage74.get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.json"][1]
        and p03_stage74.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/74_modernization_p03_supply_runtime_allocation.json"
        ][1]
        and p03_stage74.get("bps", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps"
        ][1]
        and p03_stage74.get("bps", {}).get("round_trip") is True
        and p03_stage74.get("route_audit", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "generated/runtime/modernization_p03_stage74_supply_route_audit.json"
        ][1]
        and p03_stage74.get("runtime_audit", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "generated/runtime/modernization_p03_stage74_supply_runtime_audit.json"
        ][1]
        and p03_stage74.get("symbols", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json"
        ][1],
        "P03 Stage74 checkpoint親/output/metadata/allocation/BPS/audit identity不正",
    )
    _require(
        p03_stage74.get("direct_supply_materialized_routes") == 26648
        and p03_stage74.get("direct_supply_species_family_move_pairs") == 26648
        and p03_stage74.get("cumulative_runtime_materialized_routes") == 83162
        and p03_stage74.get("cumulative_accounted_routes") == 118369
        and p03_stage74.get("remaining_direct_supply_routes") == 0
        and checkpoint_preservation74 == {
            "caller_capacity_u16": 429,
            "maximum_runtime_buffer_entries": 238,
            "missing_paths": 4014,
            "overflow_species_count": 0,
            "route_accounting_added": 0,
            "selected_routes_checked": 118369,
            "species": 501,
            "target_move_pairs": 2223,
            "target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
            "ui_supply_routes_added": 0,
        }
        and p03_stage74.get("economy") == "PROVISIONAL_REPLACEABLE"
        and p03_stage74.get("exclusions") == {
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "side_change_materialized": 0,
        }
        and p03_stage74.get("withheld_route_semantics") == {
            "count": 38,
            "direct_conversion": "FORBIDDEN",
            "scope": "OWN_TEMPO_ROCKRUFF_0744_01_CARRY_OWNER",
        }
        and p03_stage74.get("mgba") == "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "P03 Stage74 checkpoint scope/preservation/economy/Rockruff/未完了境界不正",
    )
    checkpoint_allocation74 = p03_stage74.get("allocation", {})
    _require(
        checkpoint_allocation74.get("inherited_layout_changes") == 0
        and checkpoint_allocation74.get("mutated_content_hash_sequences") == [33]
        and checkpoint_allocation74.get("new_sequence") == 77
        and checkpoint_allocation74.get("sequence33_parent_declared_content_sha256")
        == "f62631fbfabd7e1a3af77c0640140a0a27fab2cfe8f9076556aee7cab4cee40a"
        and checkpoint_allocation74.get("sequence33_parent_effective_rom_sha256")
        == "3b0e990853da8e4fa1a1f0c859ab624e7dbced767bf562891820f281bdb317af"
        and checkpoint_allocation74.get("sequence33_output_content_sha256")
        == "ac6a2008d9dc66c5ca8d4f224daa003ed752bcc4b6d92208dad83c62085cb53c"
        and checkpoint_allocation74.get("parent_declared_effective_known_diff_spans")
        == [
            {"start": 19726244, "end_exclusive": 19726246, "size": 2},
            {"start": 19726366, "end_exclusive": 19726370, "size": 4},
            {"start": 19726940, "end_exclusive": 19726941, "size": 1},
            {"start": 19728917, "end_exclusive": 19728921, "size": 4},
        ],
        "P03 Stage74 checkpoint allocation sequence33/77 lineage境界不正",
    )
    identity75 = {
        "ability_id": 20,
        "ability_slots": [20, 20, 20],
        "classification": "INTERNAL_CONDITIONAL_FORM",
        "collection_class": 4,
        "collection_weight": 0,
        "dusk_species_id": 1263,
        "form_key": "FORM_KEY_ROCKRUFF_OWN_TEMPO",
        "national_dex": 744,
        "normal_species_id": 1142,
        "reference_id": "scarletviolet:0744.01",
        "save_layout_changed": False,
        "species_id": 1670,
        "species_key": "SPECIES_KEY_ROCKRUFF_OWN_TEMPO",
    }
    save75 = {
        "existing_1142_preserved": True,
        "existing_1263_preserved": True,
        "layout_changed": False,
        "migration_required": False,
        "new_species_field_width": "existing_u16",
    }
    _require(
        p03_stage75_config.get("task") == "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75"
        and p03_stage75_config.get("stage") == 75
        and p03_stage75_config.get("identity") == identity75
        and p03_stage75_config.get("evolution", {}).get("row_u16") == [28, 25, 1263, 4372]
        and p03_stage75_config.get("p03", {}).get("withheld_carry_paths") == 38
        and p03_stage75_config.get("p03", {}).get("carry_resolution_counts")
        == {"reference_existing_slot": 21, "reference_stage74_archive": 17}
        and p03_stage75_config.get("p03", {}).get("route_accounting_delta") == 0
        and p03_stage75_config.get("inputs", {}).get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.gba"][1]
        and p03_stage75_config.get("inputs", {}).get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.json"][1]
        and p03_stage75_config.get("inputs", {}).get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime_allocation.json"][1]
        and p03_stage75_config.get("exclusions") == {
            "browt_pombon_gecqua_materialized": 0,
            "full_p03_done": False,
            "prohibited_coercions_materialized": 0,
            "side_change_materialized": 0,
            "side_change_project_move_id": 1063,
        },
        "P03 Stage75 config identity/evolution/38 carry/親/除外境界不正",
    )
    contract_p03_75 = p03_stage75_contract.get("p03", {})
    _require(
        p03_stage75_contract.get("task") == "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75"
        and p03_stage75_contract.get("stage") == 75
        and p03_stage75_contract.get("status") == "STAGE75_OWN_TEMPO_INTERNAL_FORM_CONTRACT"
        and p03_stage75_contract.get("identity") == identity75
        and p03_stage75_contract.get("save") == save75
        and p03_stage75_contract.get("table_contract", {}).get("old_species_count") == 1670
        and p03_stage75_contract.get("table_contract", {}).get("new_species_count") == 1671
        and p03_stage75_contract.get("table_contract", {}).get("pointer_consumers") == 310
        and p03_stage75_contract.get("table_contract", {}).get("count_consumers") == 19
        and contract_p03_75.get("pre_evolution_carry", {}).get("path_count") == 38
        and contract_p03_75.get("pre_evolution_carry", {}).get("missing_owner_path_count") == 0
        and contract_p03_75.get("pre_evolution_carry", {}).get("direct_conversion") == "FORBIDDEN"
        and contract_p03_75.get("source_route_clone", {}).get("route_count") == 60
        and contract_p03_75.get("accounting", {}).get("route_accounting_delta") == 0
        and contract_p03_75.get("accounting", {}).get("materialized_routes_after") == 83162
        and contract_p03_75.get("accounting", {}).get("selected_routes_after") == 118369,
        "P03 Stage75 contract species table/save/route accounting境界不正",
    )
    _require(
        p03_stage75.get("task") == "USER-MODERNIZATION-ROCKRUFF-OWN-TEMPO-STAGE75"
        and p03_stage75.get("stage") == 75
        and p03_stage75.get("status") == "ROM_MATERIALIZED_CHECKPOINT"
        and p03_stage75.get("done") is False
        and p03_stage75.get("release_candidate") is False
        and p03_stage75.get("p03", {}).get("full_p03_done") is False
        and p03_stage75.get("p03", {}).get("missing_owner_paths") == 0
        and p03_stage75.get("identity") == identity75
        and p03_stage75.get("save") == save75
        and p03_stage75.get("parent", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.gba"][1]
        and p03_stage75.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.gba"][1]
        and str(p03_stage75.get("output", {}).get("crc32", "")).upper() == "1511F429"
        and p03_stage75.get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.json"][1]
        and p03_stage75.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo_allocation.json"][1]
        and p03_stage75.get("allocation", {}).get("new_sequence") == 78
        and p03_stage75.get("allocation", {}).get("mutated_content_hash_sequences")
        == [25, 27, 33, 34, 44, 48, 61, 62, 66]
        and p03_stage75.get("bps", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps"][1]
        and p03_stage75.get("bps", {}).get("source_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/74_modernization_p03_supply_runtime.gba"][1]
        and p03_stage75.get("bps", {}).get("target_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.gba"][1]
        and p03_stage75.get("bps", {}).get("round_trip") is True
        and p03_stage75.get("mgba") == "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "P03 Stage75 checkpoint identity/allocation/BPS/未完了/mGBA境界不正",
    )
    expected_edges76 = {
        "eelevate_dedicated_switch": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
        "mega_sol_solar_charge_popup": "IMPLEMENT",
        "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
        "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
    }
    parent76 = p05_stage76_config.get("parent_identity", {})
    _require(
        p05_stage76_config.get("task") == "USER-MODERNIZATION-P05-STAGE76-EDGES"
        and p05_stage76_config.get("stage") == 76
        and p05_stage76_config.get("status") == "STAGE75_IDENTITY_PINNED"
        and parent76.get("stage75_commit") == STAGE75_IMPLEMENTATION_COMMIT
        and parent76.get("policy")
        == "FAIL_CLOSED_EXACT_STAGE75_IMPLEMENTATION_COMMIT_AND_FIVE_IDENTITIES"
        and parent76.get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.gba"][1]
        and parent76.get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.json"][1]
        and parent76.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo_allocation.json"][1]
        and parent76.get("tracked_config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_rockruff_own_tempo_stage75.json"][1]
        and parent76.get("checkpoint", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["content/modernization/rockruff_own_tempo_stage75_checkpoint.json"][1]
        and p05_stage76_config.get("edges") == expected_edges76
        and p05_stage76_config.get("edge_contract", {}).get("eelevate", {}).get("release_blocker") is True,
        "P05 Stage76 config Stage75 commit/5 identity/3実装+Eelevate pending境界不正",
    )
    for label, document, status in (
        ("contract", p05_stage76_contract, "THREE_P05_EDGES_MATERIALIZED_EELEVATE_PENDING"),
        ("checkpoint", p05_stage76, "THREE_EDGES_ROM_MATERIALIZED_EELEVATE_AND_MGBA_PENDING"),
    ):
        _require(
            document.get("task") == "USER-MODERNIZATION-P05-STAGE76-EDGES"
            and document.get("stage") == 76
            and document.get("status") == status
            and document.get("edges") == expected_edges76
            and document.get("done") is False
            and document.get("full_p05_done") is False
            and document.get("release_ready") is False
            and document.get("output", {}).get("sha256")
            == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
            and str(document.get("output", {}).get("crc32", "")).upper() == "0A78B46A"
            and document.get("bps", {}).get("sha256")
            == CANDIDATE_ARTIFACTS["build/patches/stage75-to-stage76-modernization-p05-edges.bps"][1]
            and document.get("bps", {}).get("source_sha256")
            == CANDIDATE_ARTIFACTS["build/stages/75_modernization_rockruff_own_tempo.gba"][1]
            and document.get("bps", {}).get("target_sha256")
            == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
            and document.get("bps", {}).get("round_trip") is True
            and document.get("allocation_lineage", {}).get("first79_all_fields_equal") is True
            and document.get("allocation_lineage", {}).get("parent_count") == 79
            and document.get("allocation_lineage", {}).get("new_count") == 80
            and document.get("allocation_lineage", {}).get("new_sequence") == 79
            and document.get("checks", {}).get("rom_diff_outside_payload_plus_four_patches") == 0
            and document.get("checks", {}).get("eelevate_unsafe_hooks_installed") == 0
            and document.get("checks", {}).get("mgba_runtime") == "NOT_RUN",
            f"P05 Stage76 {label} identity/allocation/BPS/Eelevate/未完了境界不正",
        )
    _require(
        p05_stage76.get("implemented_edge_count") == 3
        and p05_stage76.get("pending_edge_count") == 1
        and p05_stage76.get("parent", {}).get("commit") == STAGE75_IMPLEMENTATION_COMMIT
        and p05_stage76.get("rom_diff", {}).get("allowlist_interval_count") == 5
        and p05_stage76.get("rom_diff", {}).get("changed_bytes_inside_allowlist") == 2081
        and p05_stage76.get("rom_diff", {}).get("changed_bytes_outside_allowlist") == 0
        and p05_stage76.get("artifact_manifest", {}).get("artifact_count") == 9
        and p05_stage76.get("artifact_manifest", {}).get("all_paths_sizes_sha256_present") is True,
        "P05 Stage76 checkpoint 3/1 edge・allowlist・9成果境界不正",
    )
    expected_suppression77 = {
        "ordinary_suppression": {
            "gastro_acid": "ALREADY_SAFE_ACTIVE_ABILITY_MOVED_TO_SUPPRESSED_ABILITIES_AND_RAW_SET_NONE",
            "neutralizing_gas": "ALREADY_SAFE_ACTIVE_ABILITY_MOVED_TO_NEUTRALIZING_GAS_BLOCKED_AND_RAW_SET_NONE",
            "mold_breaker": "ALREADY_SAFE_ONLY_EELEVATE_FLAGGED_AND_IGNORED_ACTIVE_ABILITY_MOVED_TO_DISABLED_MOLD_BREAKER_AND_RAW_SET_NONE",
            "stage77_behavior": "NO_CHANGE",
        },
        "battle_circus_global": {
            "status": "IMPLEMENT",
            "battle_type_flags_address": "0x02022AAC",
            "battle_type_mask": "0x04000000",
            "circus_flags_address": "0x0203DFBC",
            "ability_suppression_mask": "0x80000000",
            "predicate": "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0",
            "suppressed_path": "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE",
            "normal_path": "TAIL_DELEGATE_STAGE72_WRAPPER",
            "unique_hook_count": 29,
            "ability_surface_occurrence_count": 33,
            "ability_hook_counts": {
                "Dragonize": 5,
                "Eelevate": 12,
                "Fire Mane": 1,
                "Mega Sol": 11,
                "Piercing Drill": 3,
                "Spicy Spray": 1,
            },
        },
        "exclusions": {
            "eelevate_dedicated_switch_ai": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
            "mgba_runtime": "DEFERRED_TO_SINGLE_CUMULATIVE_P05_SMOKE",
            "browt_pombon_gecqua_added": 0,
            "side_change_added": 0,
            "active_play_baseline_changed": False,
            "release_ready": False,
            "full_p05_done": False,
            "done": False,
        },
    }
    parent77 = p05_stage77_config.get("parent_identity", {})
    _require(
        p05_stage77_config.get("task")
        == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION"
        and p05_stage77_config.get("stage") == 77
        and p05_stage77_config.get("status") == "STAGE76_IDENTITY_PINNED"
        and parent77.get("stage76_commit") == STAGE76_IMPLEMENTATION_COMMIT
        and parent77.get("policy")
        == "FAIL_CLOSED_EXACT_STAGE76_COMMIT_AND_SIX_IDENTITIES"
        and parent77.get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
        and parent77.get("metadata", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.json"][1]
        and parent77.get("allocation", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/76_modernization_p05_edges_allocation.json"
        ][1]
        and parent77.get("checkpoint", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p05_stage76_edges_checkpoint.json"
        ][1]
        and parent77.get("tracked_config", {}).get("sha256")
        == PINNED_TRACKED_INPUTS["config/modernization_p05_stage76_edges.json"][1]
        and parent77.get("contract", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p05_stage76_edges_contract.json"
        ][1]
        and p05_stage77_config.get("suppression_contract")
        == expected_suppression77,
        "P05 Stage77 config Stage76 commit/6 identity/Circus suppression境界不正",
    )
    for label, document, status in (
        (
            "contract",
            p05_stage77_contract,
            "BATTLE_CIRCUS_SUPPRESSION_CONNECTED_NOT_P05_DONE",
        ),
        (
            "checkpoint",
            p05_stage77,
            "BATTLE_CIRCUS_GLOBAL_SUPPRESSION_MATERIALIZED_MGBA_AND_EELEVATE_SWITCH_PENDING",
        ),
    ):
        checks = document.get("checks", {})
        lineage = document.get("allocation_lineage", {})
        _require(
            document.get("task")
            == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION"
            and document.get("stage") == 77
            and document.get("status") == status
            and document.get("done") is False
            and document.get("full_p05_done") is False
            and document.get("release_ready") is False
            and document.get("suppression_contract") == expected_suppression77
            and document.get("parent", {}).get("commit")
            == STAGE76_IMPLEMENTATION_COMMIT
            and document.get("parent", {}).get("sha256")
            == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
            and document.get("output", {}).get("sha256")
            == CANDIDATE_ARTIFACTS[
                "build/stages/77_modernization_p05_circus_suppression.gba"
            ][1]
            and str(document.get("output", {}).get("crc32", "")).upper()
            == "F1CE0EAC"
            and document.get("bps", {}).get("sha256")
            == CANDIDATE_ARTIFACTS[
                "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps"
            ][1]
            and document.get("bps", {}).get("source_sha256")
            == CANDIDATE_ARTIFACTS["build/stages/76_modernization_p05_edges.gba"][1]
            and document.get("bps", {}).get("target_sha256")
            == CANDIDATE_ARTIFACTS[
                "build/stages/77_modernization_p05_circus_suppression.gba"
            ][1]
            and document.get("bps", {}).get("round_trip") is True
            and lineage.get("first80_all_fields_equal") is True
            and lineage.get("parent_count") == 80
            and lineage.get("new_count") == 81
            and lineage.get("new_sequence") == 80
            and checks.get("stage72_unique_hooks_repointed") == 29
            and checks.get("stage72_ability_surface_occurrences_guarded") == 33
            and checks.get("normal_path_delegates_stage72_wrapper") == "PASS"
            and checks.get("battle_circus_global_suppression_delegates_original")
            == "PASS"
            and checks.get("ordinary_gastro_neutralizing_gas_mold_breaker_semantics_unchanged")
            == "PASS"
            and checks.get("stage76_pointer_and_three_hooks_preserved") == "PASS"
            and checks.get("rom_diff_outside_payload_plus_29_hooks") == 0
            and checks.get("eelevate_unsafe_switch_hooks_installed") == 0
            and checks.get("side_change_added") == 0
            and checks.get("browt_pombon_gecqua_added") == 0
            and checks.get("mgba_runtime") == "NOT_RUN",
            f"P05 Stage77 {label} identity/allocation/BPS/Circus/通常経路/除外/未完了境界不正",
        )
    _require(
        p05_stage77.get("allocation_sequence") == 80
        and p05_stage77.get("rom_diff", {}).get("allowlist_interval_count") == 30
        and p05_stage77.get("rom_diff", {}).get("changed_bytes_inside_allowlist")
        == 1307
        and p05_stage77.get("rom_diff", {}).get("changed_bytes_outside_allowlist")
        == 0
        and p05_stage77.get("artifact_manifest", {}).get("artifact_count") == 9
        and p05_stage77.get("artifact_manifest", {}).get(
            "all_paths_sizes_sha256_present"
        )
        is True,
        "P05 Stage77 checkpoint allocation/allowlist/9成果境界不正",
    )
    _require(
        p04_stage70_config.get("status") == "STAGE70_ROM_MATERIALIZED"
        and p04_stage70_config.get("inputs", {}).get("rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/69_modernization_floette_gift.gba"][1]
        and p04_stage70_config.get("species_ids", {}).get("old_count") == 1621
        and p04_stage70_config.get("species_ids", {}).get("new_count") == 1670
        and p04_stage70_config.get("species_ids", {}).get("first_new_id") == 1621
        and p04_stage70_config.get("species_ids", {}).get("last_new_id") == 1669
        and p04_stage70_config.get("species_ids", {}).get("excluded_record_keys")
        == ["P04_SPECIES_BROWT", "P04_SPECIES_GECQUA", "P04_SPECIES_POMBON"],
        "P04 Stage70 config 49形態/3通常種除外境界不正",
    )
    _require(
        p04_stage70_contract.get("status") == "STAGE70_RUNTIME_CONTRACT"
        and p04_stage70_contract.get("species_count") == 1670
        and p04_stage70_contract.get("species_id_range") == [1621, 1669]
        and p04_stage70_contract.get("excluded_record_keys")
        == ["P04_SPECIES_BROWT", "P04_SPECIES_GECQUA", "P04_SPECIES_POMBON"]
        and p04_stage70_contract.get("parent_rom_sha256")
        == CANDIDATE_ARTIFACTS["build/stages/69_modernization_floette_gift.gba"][1]
        and p04_stage70_contract.get("output_rom_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/70_modernization_p04_species_runtime.gba"
        ][1]
        and p04_stage70.get("status") == "ROM_MATERIALIZED_CHECKPOINT"
        and p04_stage70.get("checks", {}).get("all_49_rows_materialized") == "PASS"
        and p04_stage70.get("checks", {}).get(
            "floette_eternal_species_id_1029_preserved"
        ) == "PASS"
        and p04_stage70.get("checks", {}).get("rom_outside_declared_spans_unchanged")
        == "PASS",
        "P04 Stage70 contract/checkpoint/除外/Floette保存境界不正",
    )
    _require(
        p04_stage71_config.get("status") == "STAGE70_IDENTITY_PINNED"
        and p04_stage71_config.get("inputs", {}).get("stage70_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/70_modernization_p04_species_runtime.gba"
        ][1]
        and p04_stage71_mapping.get("status")
        == "STAGE71_ROM_MATERIALIZED_STAGE72_EFFECTS_PENDING"
        and p04_stage71_mapping.get("counts", {}).get("mappings") == 49
        and p04_stage71_mapping.get("counts", {}).get("forward_entries") == 49
        and p04_stage71_mapping.get("counts", {}).get("reverse_entries") == 49
        and p04_stage71_mapping.get("special_form_guards", {}).get("floette_eternal")
        == "EXISTING_PRE_MEGA_SPECIES_1029"
        and p04_stage71.get("done") is False
        and p04_stage71.get("release_candidate") is False
        and p04_stage71.get("output", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/71_modernization_p04_mega_runtime.gba"][1]
        and p04_stage71.get("mapping", {}).get("sha256")
        == PINNED_TRACKED_INPUTS[
            "content/modernization/p04_mega_runtime_mapping.json"
        ][1]
        and p04_stage71.get("evolution_table", {}).get("forward_entries_added") == 49
        and p04_stage71.get("evolution_table", {}).get("reverse_entries_added") == 49
        and p04_stage71.get("validation", {}).get("exact_mgba_final_parent_once")
        == "NOT_RUN",
        "P04 Stage71 49 Mega forward/reverse/runtime未完了境界不正",
    )
    _require(
        p05_stage72_config.get("status") == "STAGE71_IDENTITY_PINNED"
        and p05_stage72_config.get("inputs", {}).get("stage71_rom", {}).get("sha256")
        == CANDIDATE_ARTIFACTS["build/stages/71_modernization_p04_mega_runtime.gba"][1]
        and p05_stage72.get("ability_ids") == list(range(312, 318))
        and p05_stage72.get("hook_count") == 29
        and p05_stage72.get("output_sha256")
        == CANDIDATE_ARTIFACTS[
            "build/stages/72_modernization_p05_ability_rom_runtime.gba"
        ][1]
        and p05_stage72.get("release_candidate") is False
        and p05_stage72.get("mgba") == "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE"
        and len(p05_stage72.get("release_blockers", [])) == 5
        and [row.get("id") for row in p05_stage72_surface.get("abilities", [])]
        == list(range(312, 318))
        and len(p05_stage72_surface.get("unconnected_surfaces", [])) == 5
        and p05_stage72_surface.get("release_candidate") is False,
        "P05 Stage72 6 Ability/29 hook/AI・UI・mGBA残件境界不正",
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
    p02_stage71 = documents[
        "content/modernization/p02_stage71_acceptance_checkpoint.json"
    ]
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
    p03_stage73 = documents[
        "content/modernization/p03_stage73_consumer_runtime_checkpoint.json"
    ]
    p03_stage73_routes = documents[
        "content/modernization/p03_stage73_consumer_runtime_route_audit.json"
    ]
    p03_stage74 = documents[
        "content/modernization/p03_stage74_supply_runtime_checkpoint.json"
    ]
    p03_stage75 = documents[
        "content/modernization/rockruff_own_tempo_stage75_checkpoint.json"
    ]
    p04 = documents["content/modernization/p04_candidate_manifest.json"]
    p04_import = documents["content/modernization/p04_asset_import_manifest.json"]
    p04_capacity = documents[
        "content/modernization/p04_capacity_allocation_manifest.json"
    ]
    mega_shop_checkpoint = documents["content/modernization/mega_shop_checkpoint.json"]
    mega_shop_mgba = documents[
        "content/modernization/mega_shop_mgba_runtime_gate.json"
    ]
    floette_checkpoint = documents[
        "content/modernization/floette_gift_checkpoint.json"
    ]
    floette_mgba = documents[
        "content/modernization/floette_gift_mgba_runtime_gate.json"
    ]
    p04_stage70 = documents[
        "content/modernization/p04_species_runtime_checkpoint.json"
    ]
    p04_stage71 = documents["content/modernization/p04_mega_runtime_checkpoint.json"]
    p05 = documents["content/modernization/p05_battle_content_contract.json"]
    p05_ability = documents["content/modernization/p05_ability_runtime_checkpoint.json"]
    p05_stage72 = documents[
        "content/modernization/p05_ability_rom_runtime_checkpoint.json"
    ]
    p05_stage76 = documents[
        "content/modernization/p05_stage76_edges_checkpoint.json"
    ]
    p05_stage77 = documents[
        "content/modernization/p05_stage77_suppression_checkpoint.json"
    ]
    p06 = documents["content/modernization/p06_species_adjustment_contract.json"]
    p06_projection = documents["content/modernization/p06_review_projection.json"]
    p07 = documents["content/modernization/p07_layered_learnset_contract.json"]

    _require(identity.get("status") == "PASS", "P01 identity contractがPASSではありません")
    norm = identity.get("target_normalization", {}).get("summary", {})
    _require(norm.get("changed_keys") == ["SPECIES_KEY_EGG", "SPECIES_KEY_CATERPIE"], "P01訂正key集合不一致")
    _require(
        candidate.get("completed_through") == "USER-MODERNIZATION-P01"
        and candidate.get("checkpointed_through")
        == "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION-CHECKPOINT"
        and candidate.get("release_ready") is False
        and candidate.get("active_play_baseline_changed") is False,
        "P01 completion evidenceとStage77 checkpoint境界不正",
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
    accounting73 = p03_stage73_routes.get("accounting", {})
    _require(
        p02_stage71.get("status") == "STOPPED_EXACT_UI_PENDING"
        and p02_stage71.get("claims", {}).get("p02_production_runtime_judged")
        is False
        and p02_stage71.get("claims", {}).get("full_evolution_acceptance")
        is False
        and p02_stage71.get("release_ready") is False,
        "P02 Stage71停止境界不正",
    )
    _require(
        p03_stage73.get("status")
        == "CHECKPOINT_FIVE_CONSUMER_BOUNDARY_CONNECTED_SUPPLY_DEPENDENCIES_REMAIN"
        and p03_stage73.get("done") is False
        and p03_stage73.get("release_candidate") is False
        and accounting73.get("new_runtime_materialized_routes") == 5363
        and accounting73.get("existing_owner_accounted_routes") == 35207
        and accounting73.get("consumer_boundary_accounted_routes") == 40570
        and accounting73.get("machine_tutor_upstream_supply_dependency") == 23595
        and p03_stage73_routes.get("remaining_full_p03_routes", {}).get("total")
        == 26648
        and p03_stage73_routes.get("side_change_materialized") == 0
        and p03_stage73_routes.get("browt_pombon_gecqua_materialized") == 0
        and p03_stage73_routes.get("prohibited_coercions_materialized") == 0,
        "P03 Stage73 consumer/accounting/除外境界不正",
    )
    _require(
        p03_stage74.get("status")
        == "CHECKPOINT_DIRECT_MACHINE_TUTOR_SUPPLY_CONNECTED_FULL_P03_WITHHELD"
        and p03_stage74.get("done") is False
        and p03_stage74.get("release_candidate") is False
        and p03_stage74.get("full_p03_done") is False
        and p03_stage74.get("direct_supply_materialized_routes") == 26648
        and p03_stage74.get("cumulative_runtime_materialized_routes") == 83162
        and p03_stage74.get("cumulative_accounted_routes") == 118369
        and p03_stage74.get("remaining_direct_supply_routes") == 0
        and p03_stage74.get("build_learnable_preservation", {}).get("missing_paths")
        == 4014
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "target_move_pairs"
        ) == 2223
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "ui_supply_routes_added"
        ) == 0
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "route_accounting_added"
        ) == 0
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "maximum_runtime_buffer_entries"
        ) == 238
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "caller_capacity_u16"
        ) == 429
        and p03_stage74.get("build_learnable_preservation", {}).get(
            "overflow_species_count"
        ) == 0
        and p03_stage74.get("economy") == "PROVISIONAL_REPLACEABLE"
        and p03_stage74.get("withheld_route_semantics", {}).get("count") == 38
        and p03_stage74.get("withheld_route_semantics", {}).get(
            "direct_conversion"
        ) == "FORBIDDEN"
        and all(value == 0 for value in p03_stage74.get("exclusions", {}).values()),
        "P03 Stage74 direct supply/preservation/capacity/economy/Rockruff境界不正",
    )
    _require(
        p03_stage75.get("status") == "ROM_MATERIALIZED_CHECKPOINT"
        and p03_stage75.get("stage") == 75
        and p03_stage75.get("done") is False
        and p03_stage75.get("release_candidate") is False
        and p03_stage75.get("full_p03_done", p03_stage75.get("p03", {}).get("full_p03_done")) is False
        and p03_stage75.get("identity", {}).get("species_id") == 1670
        and p03_stage75.get("identity", {}).get("ability_id") == 20
        and p03_stage75.get("identity", {}).get("dusk_species_id") == 1263
        and p03_stage75.get("p03", {}).get("missing_owner_paths") == 0
        and p03_stage75.get("p03", {}).get("accounting", {}).get("route_accounting_delta") == 0
        and p03_stage75.get("p03", {}).get("accounting", {}).get("materialized_routes_after") == 83162
        and p03_stage75.get("p03", {}).get("accounting", {}).get("selected_routes_after") == 118369
        and p03_stage75.get("save", {}).get("layout_changed") is False
        and p03_stage75.get("mgba") == "DEFERRED_TO_ROOT_FINAL_CUMULATIVE_ONCE",
        "P03 Stage75 Own Tempo/accounting/save/未完了境界不正",
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
    _require(
        mega_shop_checkpoint.get("stage") == 68
        and mega_shop_checkpoint.get("catalog", {}).get("entry_count") == 45
        and mega_shop_checkpoint.get("catalog", {}).get("prices_bp") == [16]
        and mega_shop_mgba.get("status") == "PASS"
        and mega_shop_mgba.get("runtime_result", {}).get("status") == "PASS",
        "P04 Stage68 Mega Stone shop runtime境界不正",
    )
    exact_floette = floette_mgba.get("exact_rom_confirmed", {})
    _require(
        floette_checkpoint.get("stage") == 69
        and floette_checkpoint.get("gift", {}).get("species_id") == 1029
        and floette_checkpoint.get("gift", {}).get("level") == 50
        and floette_mgba.get("status") == "PARTIAL_PASS_HARNESS_FIXTURE_BLOCKED"
        and exact_floette.get("party_delivery_species1029_level50") is True
        and exact_floette.get("full_party_pc_delivery_species1029_level50") is True
        and floette_mgba.get("not_yet_executed_exact_rom", {}).get(
            "fresh_core_standard_save_reload"
        ) == "PENDING",
        "P04 Stage69 Floette exact partial/runtime pending境界不正",
    )
    _require(
        p04_stage70.get("status") == "ROM_MATERIALIZED_CHECKPOINT"
        and p04_stage70.get("checks", {}).get("all_49_rows_materialized") == "PASS"
        and p04_stage70.get("checks", {}).get(
            "floette_eternal_species_id_1029_preserved"
        ) == "PASS"
        and p04_stage71.get("status") == "CHECKPOINT_STAGE72_ABILITY_EFFECTS_PENDING"
        and p04_stage71.get("done") is False
        and p04_stage71.get("release_candidate") is False
        and p04_stage71.get("evolution_table", {}).get("forward_entries_added") == 49
        and p04_stage71.get("evolution_table", {}).get("reverse_entries_added") == 49
        and p04_stage71.get("validation", {}).get("exact_mgba_final_parent_once")
        == "NOT_RUN",
        "P04 Stage70/71 49 Mega runtime checkpoint境界不正",
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
    _require(
        p05_stage72.get("status")
        == "CHECKPOINT_STATIC_RUNTIME_CONNECTED_MGBA_AND_DOCUMENTED_AI_UI_EDGES_PENDING"
        and p05_stage72.get("ability_ids") == list(range(312, 318))
        and p05_stage72.get("hook_count") == 29
        and p05_stage72.get("release_candidate") is False
        and len(p05_stage72.get("release_blockers", [])) == 5,
        "P05 Stage72 Ability ROM runtime checkpoint境界不正",
    )
    _require(
        p05_stage76.get("status") == "THREE_EDGES_ROM_MATERIALIZED_EELEVATE_AND_MGBA_PENDING"
        and p05_stage76.get("implemented_edge_count") == 3
        and p05_stage76.get("pending_edge_count") == 1
        and p05_stage76.get("edges", {}).get("eelevate_dedicated_switch")
        == "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT"
        and p05_stage76.get("done") is False
        and p05_stage76.get("full_p05_done") is False
        and p05_stage76.get("release_ready") is False
        and p05_stage76.get("checks", {}).get("mgba_runtime") == "NOT_RUN"
        and p05_stage76.get("checks", {}).get("side_change_added") == 0
        and p05_stage76.get("checks", {}).get("browt_pombon_gecqua_added") == 0,
        "P05 Stage76 3実装/Eelevate・mGBA pending/未完了境界不正",
    )
    circus77 = p05_stage77.get("suppression_contract", {}).get(
        "battle_circus_global", {}
    )
    _require(
        p05_stage77.get("status")
        == "BATTLE_CIRCUS_GLOBAL_SUPPRESSION_MATERIALIZED_MGBA_AND_EELEVATE_SWITCH_PENDING"
        and p05_stage77.get("stage") == 77
        and p05_stage77.get("done") is False
        and p05_stage77.get("full_p05_done") is False
        and p05_stage77.get("release_ready") is False
        and circus77.get("status") == "IMPLEMENT"
        and circus77.get("unique_hook_count") == 29
        and circus77.get("ability_surface_occurrence_count") == 33
        and circus77.get("predicate")
        == "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0"
        and circus77.get("normal_path") == "TAIL_DELEGATE_STAGE72_WRAPPER"
        and circus77.get("suppressed_path")
        == "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE"
        and p05_stage77.get("checks", {}).get(
            "ordinary_gastro_neutralizing_gas_mold_breaker_semantics_unchanged"
        )
        == "PASS"
        and p05_stage77.get("checks", {}).get(
            "stage76_pointer_and_three_hooks_preserved"
        )
        == "PASS"
        and p05_stage77.get("checks", {}).get("eelevate_unsafe_switch_hooks_installed")
        == 0
        and p05_stage77.get("checks", {}).get("side_change_added") == 0
        and p05_stage77.get("checks", {}).get("browt_pombon_gecqua_added") == 0
        and p05_stage77.get("checks", {}).get("mgba_runtime") == "NOT_RUN",
        "P05 Stage77 Circus 29 hook/33 surface/通常経路保持/Eelevate・mGBA pending境界不正",
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
            "phase": "P02", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["PASS", "CHECKPOINT", "PASS", "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX", "STOPPED_EXACT_UI_PENDING"],
            "adoption": {"static_contract_records": 1, "stage64_changed_evolution_rows": 1, "stage64_changed_rom_bytes": 2, "slot_priority_repaired_species": 6, "actual_consumer_case_count": 24, "actual_consumer_process_runs": 2, "hidden_ability_readback_verified": True, "hidden_ability_bit_mask": 16, "hidden_ability_observed_case_count": 24, "stage71_acceptance_status": "STOPPED_EXACT_UI_PENDING", "stage71_production_runtime": "UNJUDGED", "stage71_exact_ui_acceptance": False},
            "not_adopted": ["REVIEW_ONLY_BRANCHES", "FULL_EVOLUTION_RUNTIME_ACCEPTANCE", "STAGE71_EXACT_UI_ACCEPTANCE"],
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
                _gate("STAGE71_EXACT_UI_ACCEPTANCE", "STOPPED_PRODUCTION_UNJUDGED", ["content/modernization/p02_stage71_acceptance_checkpoint.json"]),
                _gate("FULL_EVOLUTION_ACCEPTANCE", "BLOCKED", ["content/modernization/p02_stage64_checkpoint.json"]),
            ],
            "blockers": ["EXACT_UI_ACCEPTANCE_PENDING", "PRODUCTION_RUNTIME_UNJUDGED", "FULL_EVOLUTION_ACCEPTANCE_FALSE"],
        },
        {
            "phase": "P03",
            "completion_state": "CHECKPOINT_NOT_DONE",
            "contract_statuses": [
                "PASS",
                "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS",
                "STAGE65_ANCESTOR_CHECKPOINT",
                "STAGE66_HISTORICAL_BULK_CHECKPOINT",
                "STAGE67_CONSUMER_CHECKPOINT",
                "STAGE73_FIVE_GROUP_CONSUMER_CHECKPOINT",
                "STAGE74_DIRECT_SUPPLY_CHECKPOINT",
                "STAGE75_OWN_TEMPO_ROCKRUFF_INTERNAL_FORM_CHECKPOINT",
                "STATIC_ONLY_FINAL_MGBA_PENDING",
            ],
            "adoption": {
                "reference_records": 1300,
                "source_routes": 118528,
                "runtime_selected_routes": 118369,
                "side_change_1063_source_routes": 159,
                "side_change_1063_excluded_routes": 159,
                "side_change_1063_adopted_routes": 0,
                "side_change_1063_replacement_move_key": None,
                "stage65_preserved_ancestor_routes": 4,
                "stage65_changed_rom_bytes": 17,
                "stage66_corrected_targets": 1300,
                "stage66_routes_materialized": 47548,
                "stage66_level_up_routes_materialized": 18515,
                "stage66_machine_existing_slot_routes_materialized": 29033,
                "stage66_changed_rom_bytes": 81693,
                "stage67_new_routes_materialized": 3603,
                "stage67_evolution_routes_materialized": 341,
                "stage67_tutor_existing_slot_routes_materialized": 740,
                "stage67_normal_egg_routes_materialized": 2522,
                "stage67_cumulative_routes_materialized": 51151,
                "stage73_new_runtime_materialized_routes": 5363,
                "stage73_existing_owner_accounted_routes": 35207,
                "stage73_consumer_boundary_accounted_routes": 40570,
                "stage73_historical_upstream_dependency_overlap_routes": 23595,
                "stage73_hook_count": 3,
                "stage74_direct_supply_materialized_routes": 26648,
                "stage74_direct_machine_routes": 26279,
                "stage74_direct_tutor_routes": 369,
                "stage74_hook_count": 2,
                "cumulative_routes_materialized": 83162,
                "cumulative_routes_accounted": 118369,
                "selected_routes_remaining": 0,
                "preservation_missing_paths": 4014,
                "preservation_target_move_pairs": 2223,
                "preservation_species": 501,
                "preservation_target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
                "preservation_ui_supply_routes_added": 0,
                "preservation_route_accounting_added": 0,
                "build_learnable_maximum_entries": 238,
                "build_learnable_capacity": 429,
                "build_learnable_overflow_species": 0,
                "archive_unlock_flag": "0x082C",
                "archive_economy": "PROVISIONAL_REPLACEABLE",
                "withheld_own_tempo_rockruff_routes": 38,
                "stage75_own_tempo_rockruff_species_id": 1670,
                "stage75_own_tempo_rockruff_ability_id": 20,
                "stage75_pre_evolution_carry_paths_resolved": 38,
                "stage75_missing_owner_paths": 0,
                "stage75_source_owner_clone_routes": 60,
                "stage75_route_accounting_delta": 0,
                "stage75_allocation_sequence": 78,
                "stage75_allocation_count": 79,
                "browt_pombon_gecqua_materialized": 0,
                "prohibited_coercions_materialized": 0,
                "stage67_changed_rom_bytes_from_overlay": 46455,
                "stage67_changed_rom_bytes_from_stage66": 46515,
                "stage67_future_tail_remaining_bytes": 62510,
            },
            "not_adopted": [
                "SIDE_CHANGE_1063_ALL_159_SOURCE_ROUTES_EXCLUDED_NO_REPLACEMENT",
                "BROWTPOMBONGECQUA_USER_EXCLUDED",
                "OWN_TEMPO_ROCKRUFF_0744_01_DIRECT_CONVERSION_FORBIDDEN_OWNER_FORM_CONNECTED",
                "FULL_CUMULATIVE_MGBA",
            ],
            "rom_reflection": {
                "reflected": True,
                "stage": 75,
                "ancestor_stage": 67,
                "scope": "STAGE67_DIRECT_CONSUMERS_PLUS_STAGE73_FIVE_GROUP_BOUNDARY_PLUS_STAGE74_DIRECT_SUPPLY_PLUS_STAGE75_OWN_TEMPO_OWNER_FORM",
            },
            "required_gates": [
                _gate("STREAMING_CONTRACT_AND_INDEX", "PASS", ["content/modernization/p03_learnset_contract.json", "content/modernization/p03_compiled_index.json"]),
                _gate("STAGE65_REPRESENTATIVE_RUNTIME", "PRESERVED_ANCESTOR_CHECKPOINT", ["content/modernization/p03_stage65_checkpoint.json", "content/modernization/p03_stage65_mgba_runtime_gate.json"]),
                _gate("STAGE66_BULK_RUNTIME", "INTEGRATED_CHECKPOINT_NOT_P03_DONE", ["content/modernization/p03_stage66_checkpoint.json", "content/modernization/p03_stage66_mgba_runtime_gate.json", "content/modernization/p03_stage66_bulk_route_audit.json", "content/modernization/p03_stage66_change_audit.json"]),
                _gate("STAGE67_CONSUMER_RUNTIME", "PASS_ALL_MATERIALIZED_DIRECT_CALLS_NOT_E2E", ["content/modernization/p03_stage67_checkpoint.json", "content/modernization/p03_stage67_mgba_runtime_gate.json", "content/modernization/p03_stage67_consumer_route_audit.json", "content/modernization/p03_stage67_change_audit.json"]),
                _gate("STAGE73_FIVE_GROUP_CONSUMER_RUNTIME", "STATIC_CONNECTED", ["content/modernization/p03_stage73_consumer_runtime_checkpoint.json", "content/modernization/p03_stage73_consumer_runtime_route_audit.json"]),
                _gate("STAGE74_DIRECT_MACHINE_TUTOR_SUPPLY", "PASS_STATIC_26648_ZERO_SILENT_DROP", ["config/modernization_p03_stage74_supply.json", "content/modernization/p03_stage74_supply_runtime_checkpoint.json"]),
                _gate("STAGE74_BUILD_LEARNABLE_PRESERVATION", "PASS_2223_PAIRS_CAPACITY_238_OF_429", ["content/modernization/p03_stage74_supply_runtime_checkpoint.json"]),
                _gate("STAGE75_OWN_TEMPO_ROCKRUFF", "PASS_INTERNAL_FORM_38_CARRY_PATHS_ZERO_ACCOUNTING_DELTA", ["content/modernization/rockruff_own_tempo_stage75_contract.json", "content/modernization/rockruff_own_tempo_stage75_checkpoint.json"]),
                _gate("SIDE_CHANGE_NON_ADOPTION", "PASS_EXCLUDED_159_NO_REPLACEMENT", ["config/modernization_adoption_decisions.json", "content/modernization/p03_runtime_handoff.json"]),
                _gate("FULL_SELECTED_ROUTE_SUPPLY", "PASS_DIRECT_SUPPLY_ZERO_REMAINING_NOT_FULL_P03", ["content/modernization/p03_stage74_supply_runtime_checkpoint.json"]),
            ],
            "blockers": [
                "ARCHIVE_ECONOMY_PROVISIONAL_REPLACEABLE",
                "FINAL_CUMULATIVE_MGBA_NOT_RUN",
            ],
        },
        {
            "phase": "P04", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CANDIDATE_MANIFEST_ONLY", "PRIVATE_USE_ASSETS_READY", "STAGE68_MEGA_STONE_SHOP_EXACT_RUNTIME_PASS", "STAGE69_FLOETTE_ETERNAL_EXACT_PARTY_PC_PARTIAL_PASS", "STAGE70_SPECIES_RUNTIME_CONNECTED", "STAGE71_MEGA_BATTLE_RUNTIME_CONNECTED_MGBA_PENDING"],
            "adoption": {
                "runtime_adopted_records": 49,
                "runtime_materialized_acquisition_routes": 46,
                "selected_candidate_records": 49,
                "held_records": 2,
                "mega_records": 49,
                "mega_form_battle_runtime_records": 49,
                "mega_form_species_runtime_materialized": True,
                "mega_form_battle_runtime_materialized": True,
                "mega_form_runtime_exact_mgba": False,
                "stone_records": 45,
                "stone_item_ids_materialized": 45,
                "stone_shop_entries_materialized": 45,
                "stone_shop_currency": "BP",
                "stone_shop_price_each": 16,
                "stone_shop_exact_runtime_gate": "PASS",
                "floette_eternal_existing_species_id": 1029,
                "floette_eternal_gift_level": 50,
                "floette_eternal_exact_party_pc_delivery": True,
                "floette_eternal_exact_full_and_fresh_reload": False,
                "new_species_reference_records": 3,
                "adopted_new_species_records": 0,
                "non_adopted_user_scope_records": 3,
                "asset_staging": {"mega_covered": 49, "mega_required": 49, "stones_covered": 45, "stones_required": 45, "palette_ready": 49, "palette_required": 49, "winds_waves_covered": 0, "winds_waves_required": 0, "missing_assets": 0, "payload_file_count": 670, "payload_total_bytes": 426648, "asset_set_sha256": "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c"},
                "capacity_reservation": {"capacity_basis_stage": 65, "species_form": [1621, 1669], "item": [999, 1043], "ability": [312, 317], "move": None, "move_append_count": 0, "fixed_table_count": 34, "fixed_table_delta_bytes": 19857, "aligned_bundle_bytes": 636392, "integration_modules_remaining_bytes": 1124296, "stage66_cross_check": {"allocation_region": "future_tail", "allocation_start": 33399368, "allocation_size": 60116, "allocation_end_exclusive": 33459484, "stage65_future_tail_remaining_bytes": 155064, "stage66_future_tail_remaining_bytes": 94948, "p04_candidate_region": "integration_modules", "p04_candidate_start": 21307984, "p04_candidate_end_exclusive": 23068672, "overlap": False}, "runtime_ready": False},
            },
            "not_adopted": ["WINDS_WAVES_NEW_SPECIES_3_USER_SCOPE", "PUBLIC_REDISTRIBUTION", "EXACT_MGBA_FINAL_RUNTIME_CLAIM"],
            "rom_reflection": {"reflected": True, "stage": 71, "ancestor_stage": 68, "scope": "45_MEGA_STONE_BP_SHOP_FLOETTE_ETERNAL_ACQUISITION_49_MEGA_SPECIES_AND_BATTLE_ROWS"},
            "required_gates": [
                _gate("OFFICIAL_SOURCE_AND_CANDIDATE_SET", "PASS", ["content/modernization/p04_candidate_manifest.json", "content/modernization/p04_official_sources.json"]),
                _gate("ASSET_IMPORTER", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY", ["content/modernization/p04_asset_import_manifest.json"]),
                _gate("ID_CAPACITY_RESERVATION", "INTEGRATED_CHECKPOINT_NOT_RUNTIME_READY", ["content/modernization/p04_capacity_allocation_manifest.json"]),
                _gate("MEGA_STONE_BP_SHOP", "PASS_EXACT_ROM_45_ITEMS_16_BP", ["content/modernization/mega_shop_checkpoint.json", "content/modernization/mega_shop_mgba_runtime_gate.json"]),
                _gate("FLOETTE_ETERNAL_ACQUISITION", "PASS_EXACT_PARTY_PC_FULL_RELOAD_PENDING", ["content/modernization/floette_gift_checkpoint.json", "content/modernization/floette_gift_mgba_runtime_gate.json"]),
                _gate("MEGA_FORM_SPECIES_RUNTIME", "PASS_STATIC_49_ROWS", ["content/modernization/p04_species_runtime_checkpoint.json"]),
                _gate("MEGA_FORM_BATTLE_RUNTIME", "PASS_STATIC_FORWARD_REVERSE_49_EXACT_MGBA_PENDING", ["content/modernization/p04_mega_runtime_checkpoint.json", "content/modernization/p04_mega_runtime_mapping.json"]),
            ],
            "blockers": ["FINAL_CUMULATIVE_MEGA_RUNTIME_MGBA_NOT_RUN", "FLOETTE_EXACT_FULL_PARTY_PC_AND_FRESH_RELOAD_GATE_PENDING"],
        },
        {
            "phase": "P05", "completion_state": "CHECKPOINT_NOT_DONE", "contract_statuses": ["CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS", "HOST_RUNTIME_VERIFIED", "STAGE72_ABILITY_ROM_RUNTIME_CONNECTED", "STAGE76_THREE_SAFE_AI_UI_EDGES_CONNECTED", "STAGE77_BATTLE_CIRCUS_29_HOOK_33_SURFACE_SUPPRESSION_CONNECTED_EELEVATE_MGBA_PENDING"],
            "adoption": {"performance_adjustments": 0, "data_only_patches": 0, "new_move_requirements": 0, "non_adopted_move_candidates": 1, "side_change_1063_adopted": False, "temporary_ability_assignments": 14, "existing_official_assignments": 29, "new_abilities": 6, "non_adopted_p04_records": 3, "ability_host_runtime_cases": 46, "ability_host_runtime_processes": 2, "ability_ids": [312, 313, 314, 315, 316, 317], "ability_rom_runtime_count": 6, "ability_rom_hook_count": 29, "ability_rom_linked": True, "ability_runtime_exact_mgba": False, "documented_ai_ui_edges_implemented": 3, "documented_ai_ui_edges_pending": 1, "stage76_allocation_sequence": 79, "stage76_allocation_count": 80, "stage76_changed_bytes": 2081, "stage76_allowlist_outside": 0, "stage77_battle_circus_suppression": True, "stage77_unique_hook_count": 29, "stage77_ability_surface_occurrence_count": 33, "stage77_ordinary_suppression_changed": False, "stage77_allocation_sequence": 80, "stage77_allocation_count": 81, "stage77_changed_bytes": 1307, "stage77_allowlist_outside": 0, "stage77_stage76_hooks_preserved": True},
            "not_adopted": ["SIDE_CHANGE_1063_RUNTIME_AND_ALLOCATION", "WINDS_WAVES_NEW_SPECIES_3_RUNTIME_AND_ALLOCATION", "EELEVATE_UNSAFE_SWITCH_AI", "FINAL_CUMULATIVE_MGBA"],
            "rom_reflection": {"reflected": True, "stage": 77, "ancestor_stage": 72, "scope": "ABILITY_312_317_FIXED_TABLES_AND_29_BATTLE_HOOKS_PLUS_THREE_SAFE_AI_UI_EDGES_PLUS_BATTLE_CIRCUS_GLOBAL_SUPPRESSION"},
            "required_gates": [
                _gate("BATTLE_CONTENT_CONTRACT", "PASS", ["content/modernization/p05_battle_content_contract.json"]),
                _gate("SIDE_CHANGE_1063_EXCLUSION", "PASS_NON_ADOPTED_NO_REPLACEMENT", ["config/modernization_adoption_decisions.json", "content/modernization/p05_runtime_handoff.json"]),
                _gate("WINDS_WAVES_NEW_SPECIES_EXCLUSION", "PASS_NON_ADOPTED_NO_ID_ASSET_RUNTIME", ["content/modernization/p04_candidate_manifest.json", "content/modernization/p04_capacity_allocation_manifest.json", "content/modernization/p05_runtime_handoff.json"]),
                _gate("P04_NEW_ABILITIES_HOST_RUNTIME", "PASS_46_CASES_X2", ["content/modernization/p05_ability_runtime_checkpoint.json"]),
                _gate("P04_NEW_ABILITIES_ROM_LINK", "PASS_STATIC_6_IDS_29_HOOKS", ["content/modernization/p05_ability_rom_runtime_checkpoint.json", "content/modernization/p05_ability_rom_runtime_surface_matrix.json"]),
                _gate("STAGE76_SAFE_AI_UI_EDGES", "PASS_HOST_STATIC_THREE_IMPLEMENTED_EELEVATE_PENDING", ["content/modernization/p05_stage76_edges_contract.json", "content/modernization/p05_stage76_edges_checkpoint.json"]),
                _gate("STAGE77_BATTLE_CIRCUS_SUPPRESSION", "PASS_HOST_STATIC_29_HOOKS_33_SURFACES_NORMAL_PATH_PRESERVED", ["content/modernization/p05_stage77_suppression_contract.json", "content/modernization/p05_stage77_suppression_checkpoint.json"]),
            ],
            "blockers": ["ABILITY_AND_STAGE77_FINAL_CUMULATIVE_MGBA_NOT_RUN", "EELEVATE_DEDICATED_SWITCH_AI_PENDING"],
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
        ("P02_STAGE71_EXACT_UI", "P02", "Stage71 exact ROM acceptance checkpoint", "tests/test_modernization_p02_stage71_acceptance.py", "STOPPED_EXACT_UI_PENDING_PRODUCTION_UNJUDGED"),
        ("P02_FULL_RUNTIME", "P02", "deferred runtime acceptance", "tests/test_modernization_p02_mgba.py", "BLOCKED"),
        ("P03_ORIGINAL_LEARNSETS", "P03", "streamed 1300/118528 contract", "tests/test_modernization_p03.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P03_STAGE65_SLICE", "P03", "Stage65 Caterpie 4-route ancestor checkpoint", "tests/test_modernization_p03_stage65.py", "PRESERVED_ANCESTOR_CHECKPOINT"),
        ("P03_STAGE66_BULK", "P03", "Stage66 47,548-route bulk ROM checkpoint", "tests/test_modernization_p03_stage66.py", "INTEGRATED_CHECKPOINT_NOT_P03_DONE"),
        ("P03_STAGE67_CONSUMERS", "P03", "Stage67 evolution/tutor/normal-egg 3,603-route consumer checkpoint", "tests/test_modernization_p03_stage67.py", "INTEGRATED_CHECKPOINT_NOT_P03_DONE"),
        ("P03_STAGE73_FIVE_GROUP_CONSUMERS", "P03", "Stage73 5-group consumer boundary 40,570 routes accounted", "tests/test_modernization_p03_stage73_runtime.py", "INTEGRATED_STATIC_MGBA_AND_SUPPLY_PENDING"),
        ("P03_STAGE74_DIRECT_SUPPLY", "P03", "Stage74 family-separated machine/tutor 26,648 direct routes + BuildLearnable preservation", "tests/test_modernization_p03_stage74_supply.py", "INTEGRATED_STATIC_ROCKRUFF_SEMANTICS_AND_MGBA_PENDING"),
        ("P03_STAGE75_OWN_TEMPO_ROCKRUFF", "P03", "Stage75 internal Species1670 Own Tempo owner + 38 carry paths", "tests/test_modernization_rockruff_own_tempo_stage75.py", "INTEGRATED_STATIC_FINAL_MGBA_PENDING"),
        ("P04_CANDIDATE_SCOPE", "P04", "49 Mega採用候補 + Winds/Waves 3種非採用 + 2 hold", "tests/test_modernization_p04_sources.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P04_ASSET_IMPORT", "P04", "private-use asset import manifest", "tests/test_modernization_p04_asset_importer.py", "INTEGRATED_STAGING_ONLY_NOT_ROM_READY"),
        ("P04_CAPACITY_RESERVATION", "P04", "49/45/6/0 append reservation + 34-table capacity audit", "tests/test_modernization_p04_capacity.py", "INTEGRATED_CHECKPOINT_NOT_RUNTIME_READY"),
        ("P04_MEGA_STONE_BP_SHOP", "P04", "Stage68 45 Mega Stone items + 16BP shop", "tests/test_modernization_mega_shop_mgba.py", "EXACT_ROM_RUNTIME_PASS"),
        ("P04_FLOETTE_ETERNAL_ACQUISITION", "P04", "Stage69 existing Species1029 Lv50 gift", "tests/test_modernization_floette_gift.py", "EXACT_PARTY_PC_PARTIAL_PASS_FULL_RELOAD_PENDING"),
        ("P04_STAGE70_SPECIES_RUNTIME", "P04", "49 Mega species/form table and asset rows", "tests/test_modernization_p04_species_runtime.py", "STATIC_RUNTIME_CONNECTED"),
        ("P04_STAGE71_MEGA_RUNTIME", "P04", "49 forward/reverse Mega battle rows", "tests/test_modernization_p04_mega_runtime.py", "STATIC_RUNTIME_CONNECTED_EXACT_MGBA_PENDING"),
        ("P05_MOVE_ABILITY", "P05", "Side Change/Winds・Waves 3種非採用 + battle content contract", "tests/test_modernization_p05.py", "CONTRACT_VERIFIED_RUNTIME_INCOMPLETE"),
        ("P05_ABILITY_HOST_RUNTIME", "P05", "6 Ability portable runtime", "tests/test_modernization_p05_ability_runtime.py", "HOST_VERIFIED_46_CASES_X2_HISTORICAL_PRE_ROM_CHECKPOINT"),
        ("P05_STAGE72_ABILITY_ROM_RUNTIME", "P05", "Ability 312..317 and 29 ROM hooks", "tests/test_modernization_p05_ability_rom_runtime.py", "STATIC_RUNTIME_CONNECTED_MGBA_AI_UI_EDGES_PENDING"),
        ("P05_STAGE76_SAFE_AI_UI_EDGES", "P05", "Mega Sol popup + Piercing Drill AI + Spicy Spray AI", "tests/test_modernization_p05_stage76_edges.py", "THREE_EDGES_CONNECTED_EELEVATE_AND_MGBA_PENDING"),
        ("P05_STAGE77_BATTLE_CIRCUS_SUPPRESSION", "P05", "29 Stage72 hooks / 33 ability surfaces with Battle Circus global suppression", "tests/test_modernization_p05_stage77_suppression.py", "SUPPRESSION_CONNECTED_NORMAL_PATH_PRESERVED_EELEVATE_AND_MGBA_PENDING"),
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
        root,
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
            "highest_pinned_candidate_stage": 77,
            "runtime_reflected_phase_count": 5,
            "release_ready": False,
        },
        "release_blockers": list(RELEASE_BLOCKERS),
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
    _require(
        isinstance(chain, Mapping)
        and chain.get("active_stage") == 62
        and chain.get("selected_checkpoint_stage") == 77
        and all(chain.get(f"stage{stage}_integrated") is True for stage in range(65, 78))
        and chain.get("release_candidate") is False,
        "P08候補Stage77 chain境界不正",
    )
    _require(
        chain.get("registry") == {
            "path": "config/modernization_candidate.json",
            "schema_version": 2,
            "status": "STAGE77_BATTLE_CIRCUS_SUPPRESSION_CHECKPOINT_NOT_RELEASE_CANDIDATE",
            "completed_through": "USER-MODERNIZATION-P01",
            "checkpointed_through": "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION-CHECKPOINT",
            "checkpoint_commit": SNAPSHOT_BASE_HEAD,
            "last_committed_checkpoint": SNAPSHOT_BASE_HEAD,
            "release_ready": False,
            "active_parent_stage": 62,
            "parent_stage": 76,
            "candidate_stage": 77,
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
    _require(
        chain.get("stage68_scope") == {
            "mega_stone_item_ids": [999, 1043],
            "mega_stone_item_count": 45,
            "shop_entry_count": 45,
            "currency": "BP",
            "price_each": 16,
            "mega_ring_gate_item_id": 580,
            "claim_flags": [0x14A0, 0x14CC],
            "exact_rom_runtime_gate": "PASS",
            "mega_form_battle_runtime_materialized": False,
            "full_p04_done": False,
        },
        "P04 Stage68 shop実装済み/Mega battle runtime未完了境界不正",
    )
    _require(
        chain.get("stage69_scope") == {
            "existing_species_id": 1029,
            "level": 50,
            "mega_ring_gate_item_id": 580,
            "claim_flag": 0x14CD,
            "canonical_collection_bit": 850,
            "exact_party_delivery": True,
            "exact_pc_delivery": True,
            "exact_full_and_fresh_reload": False,
            "host_full_rollback_reload": True,
            "runtime_gate": "PARTIAL_PASS_HARNESS_FIXTURE_BLOCKED",
            "full_p04_done": False,
        },
        "P04 Stage69 Floette exact partial/runtime pending境界不正",
    )
    _require(
        chain.get("stage70_scope") == {
            "mega_species_and_forms": 49,
            "existing_species_prefix_byte_exact": True,
            "floette_eternal_species_id_1029_preserved": True,
            "side_change_referenced": False,
            "new_normal_species": 0,
            "exact_mgba": False,
            "full_p04_done": False,
        }
        and chain.get("stage71_scope") == {
            "forward_entries_added": 49,
            "reverse_entries_added": 49,
            "existing_mega_entries_preserved": 80,
            "mega_form_battle_runtime_records": 49,
            "exact_mgba": False,
            "full_p04_done": False,
        },
        "P04 Stage70/71 49 Mega scope境界不正",
    )
    _require(
        chain.get("stage72_scope") == {
            "ability_ids": list(range(312, 318)),
            "ability_count": 6,
            "battle_hook_count": 29,
            "rom_linked": True,
            "documented_ai_ui_edges_pending": 4,
            "exact_mgba": False,
            "full_p05_done": False,
        },
        "P05 Stage72 Ability scope境界不正",
    )
    stage73 = chain.get("stage73_scope", {})
    _require(
        stage73 == {
            "new_runtime_materialized_routes": 5363,
            "existing_owner_accounted_routes": 35207,
            "consumer_boundary_accounted_routes": 40570,
            "cumulative_new_runtime_materialized_routes": 56514,
            "cumulative_consumer_boundary_accounted_routes": 91721,
            "machine_tutor_upstream_supply_dependency_routes": 23595,
            "remaining_direct_supply_routes": 26648,
            "hook_count": 3,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        }
        and stage73.get("new_runtime_materialized_routes")
        + stage73.get("existing_owner_accounted_routes")
        == stage73.get("consumer_boundary_accounted_routes")
        and chain.get("stage67_scope", {}).get("cumulative_materialized_routes")
        + stage73.get("new_runtime_materialized_routes")
        == stage73.get("cumulative_new_runtime_materialized_routes")
        and chain.get("stage67_scope", {}).get("cumulative_materialized_routes")
        + stage73.get("consumer_boundary_accounted_routes")
        == stage73.get("cumulative_consumer_boundary_accounted_routes")
        and chain.get("stage67_scope", {}).get("selected_routes")
        - stage73.get("cumulative_consumer_boundary_accounted_routes")
        == stage73.get("remaining_direct_supply_routes"),
        "P03 Stage73 materialized/accounted/supply/除外scope境界不正",
    )
    stage74 = chain.get("stage74_scope", {})
    _require(
        stage74 == {
            "direct_supply_materialized_routes": 26648,
            "direct_machine_routes": 26279,
            "direct_tutor_routes": 369,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "remaining_direct_supply_routes": 0,
            "preservation_missing_paths": 4014,
            "preservation_target_move_pairs": 2223,
            "preservation_species": 501,
            "preservation_target_move_set_sha256": "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
            "preservation_ui_supply_routes_added": 0,
            "preservation_route_accounting_added": 0,
            "build_learnable_maximum_entries": 238,
            "build_learnable_capacity": 429,
            "build_learnable_overflow_species": 0,
            "unlock_flag": "0x082C",
            "economy": "PROVISIONAL_REPLACEABLE",
            "withheld_own_tempo_rockruff_routes": 38,
            "hook_count": 2,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        }
        and stage73.get("cumulative_new_runtime_materialized_routes")
        + stage74.get("direct_supply_materialized_routes")
        == stage74.get("cumulative_runtime_materialized_routes")
        and stage74.get("cumulative_runtime_materialized_routes")
        + stage73.get("existing_owner_accounted_routes")
        == stage74.get("cumulative_accounted_routes")
        and stage74.get("cumulative_accounted_routes")
        == chain.get("stage67_scope", {}).get("selected_routes"),
        "P03 Stage74 supply/preservation/capacity/economy/除外scope境界不正",
    )
    _require(
        chain.get("stage75_scope") == {
            "internal_species_id": 1670,
            "normal_species_id": 1142,
            "dusk_species_id": 1263,
            "national_dex": 744,
            "ability_id": 20,
            "species_count": 1671,
            "pre_evolution_carry_paths": 38,
            "missing_owner_paths": 0,
            "source_owner_clone_routes": 60,
            "route_accounting_delta": 0,
            "cumulative_runtime_materialized_routes": 83162,
            "cumulative_accounted_routes": 118369,
            "save_layout_changed": False,
            "archive_economy": "PROVISIONAL_REPLACEABLE",
            "allocation_sequence": 78,
            "allocation_count": 79,
            "full_p03_done": False,
            "exact_mgba": False,
        },
        "P03 Stage75 Own Tempo/accounting/save/economy scope境界不正",
    )
    _require(
        chain.get("stage76_scope") == {
            "implemented_edge_count": 3,
            "pending_edge_count": 1,
            "edges": {
                "eelevate_dedicated_switch": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
                "mega_sol_solar_charge_popup": "IMPLEMENT",
                "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
                "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
            },
            "allocation_parent_count": 79,
            "allocation_count": 80,
            "allocation_sequence": 79,
            "parent_first79_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 5,
            "changed_bytes_inside_allowlist": 2081,
            "changed_bytes_outside_allowlist": 0,
            "eelevate_unsafe_hooks_installed": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
            "exact_mgba": False,
        },
        "P05 Stage76 3実装/1 pending/allocation/allowlist scope境界不正",
    )
    _require(
        chain.get("stage77_scope") == {
            "unique_hook_count": 29,
            "ability_surface_occurrence_count": 33,
            "battle_circus_global_fixed": True,
            "battle_type_mask": "0x04000000",
            "ability_suppression_mask": "0x80000000",
            "predicate": "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0",
            "normal_path": "TAIL_DELEGATE_STAGE72_WRAPPER",
            "suppressed_path": "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE",
            "ordinary_suppression_changed": False,
            "allocation_parent_count": 80,
            "allocation_count": 81,
            "allocation_sequence": 80,
            "parent_first80_rows_all_fields_preserved": True,
            "rom_diff_allowlist_interval_count": 30,
            "changed_bytes_inside_allowlist": 1307,
            "changed_bytes_outside_allowlist": 0,
            "stage76_pointer_and_three_hooks_preserved": True,
            "eelevate_unsafe_switch_hooks_installed": 0,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "full_p05_done": False,
            "release_ready": False,
            "exact_mgba": False,
        },
        "P05 Stage77 29 hook/33 surface/Circus/通常経路/allocation/除外scope境界不正",
    )
    inheritance = chain.get("inheritance")
    _require(
        inheritance == _candidate_inheritance(artifact_by_path),
        "P08 Stage62～77 inheritance role/ROM/parent chain不正",
    )
    latest_bps = chain.get("latest_incremental_bps")
    expected_latest_bps = [
        {
            "source": source,
            "patch": patch,
            "target": target,
            "status": "PASS_EXACT_APPLY",
        }
        for source, patch, target in LATEST_INCREMENTAL_BPS_PATHS
    ]
    _require(
        latest_bps == expected_latest_bps,
        "P08 Stage69～77 incremental BPS exact apply監査不正",
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
        ) == 24
        and by_phase["P02"].get("adoption", {}).get(
            "stage71_acceptance_status"
        ) == "STOPPED_EXACT_UI_PENDING"
        and by_phase["P02"].get("adoption", {}).get(
            "stage71_production_runtime"
        ) == "UNJUDGED"
        and by_phase["P02"].get("adoption", {}).get(
            "stage71_exact_ui_acceptance"
        ) is False,
        "P02 hidden ability readback/Stage71停止境界不正",
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
    p03_adoption = by_phase["P03"].get("adoption", {})
    _require(
        by_phase["P03"].get("rom_reflection", {}).get("stage") == 75
        and p03_adoption.get("stage65_preserved_ancestor_routes") == 4
        and p03_adoption.get("stage66_routes_materialized") == 47548
        and p03_adoption.get("runtime_selected_routes") == 118369
        and p03_adoption.get("side_change_1063_excluded_routes") == 159
        and p03_adoption.get("side_change_1063_adopted_routes") == 0
        and p03_adoption.get("side_change_1063_replacement_move_key") is None
        and p03_adoption.get("stage67_new_routes_materialized") == 3603
        and p03_adoption.get("stage73_new_runtime_materialized_routes") == 5363
        and p03_adoption.get("stage73_existing_owner_accounted_routes") == 35207
        and p03_adoption.get("stage73_consumer_boundary_accounted_routes") == 40570
        and p03_adoption.get("stage73_historical_upstream_dependency_overlap_routes")
        == 23595
        and p03_adoption.get("stage73_hook_count") == 3
        and p03_adoption.get("stage74_direct_supply_materialized_routes") == 26648
        and p03_adoption.get("stage74_direct_machine_routes") == 26279
        and p03_adoption.get("stage74_direct_tutor_routes") == 369
        and p03_adoption.get("stage74_hook_count") == 2
        and p03_adoption.get("cumulative_routes_materialized") == 83162
        and p03_adoption.get("cumulative_routes_accounted") == 118369
        and p03_adoption.get("selected_routes_remaining") == 0
        and p03_adoption.get("preservation_missing_paths") == 4014
        and p03_adoption.get("preservation_target_move_pairs") == 2223
        and p03_adoption.get("preservation_species") == 501
        and p03_adoption.get("preservation_target_move_set_sha256")
        == "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb"
        and p03_adoption.get("preservation_ui_supply_routes_added") == 0
        and p03_adoption.get("preservation_route_accounting_added") == 0
        and p03_adoption.get("build_learnable_maximum_entries") == 238
        and p03_adoption.get("build_learnable_capacity") == 429
        and p03_adoption.get("build_learnable_overflow_species") == 0
        and p03_adoption.get("archive_unlock_flag") == "0x082C"
        and p03_adoption.get("archive_economy") == "PROVISIONAL_REPLACEABLE"
        and p03_adoption.get("withheld_own_tempo_rockruff_routes") == 38
        and p03_adoption.get("stage75_own_tempo_rockruff_species_id") == 1670
        and p03_adoption.get("stage75_own_tempo_rockruff_ability_id") == 20
        and p03_adoption.get("stage75_pre_evolution_carry_paths_resolved") == 38
        and p03_adoption.get("stage75_missing_owner_paths") == 0
        and p03_adoption.get("stage75_source_owner_clone_routes") == 60
        and p03_adoption.get("stage75_route_accounting_delta") == 0
        and p03_adoption.get("stage75_allocation_sequence") == 78
        and p03_adoption.get("stage75_allocation_count") == 79
        and p03_adoption.get("browt_pombon_gecqua_materialized") == 0
        and p03_adoption.get("prohibited_coercions_materialized") == 0
        and 56514 + p03_adoption.get("stage74_direct_supply_materialized_routes")
        == p03_adoption.get("cumulative_routes_materialized")
        and p03_adoption.get("cumulative_routes_materialized")
        + p03_adoption.get("stage73_existing_owner_accounted_routes")
        == p03_adoption.get("cumulative_routes_accounted"),
        "P03 Stage74 supply/Stage75 Own Tempo checkpointの統合境界不正",
    )
    _require(
        by_phase["P05"].get("adoption", {}).get("new_move_requirements") == 0
        and by_phase["P05"].get("adoption", {}).get("non_adopted_move_candidates") == 1
        and by_phase["P05"].get("adoption", {}).get("side_change_1063_adopted") is False
        and by_phase["P05"].get("adoption", {}).get("new_abilities") == 6
        and by_phase["P05"].get("adoption", {}).get("non_adopted_p04_records") == 3
        and by_phase["P05"].get("adoption", {}).get("ability_host_runtime_cases") == 46
        and by_phase["P05"].get("adoption", {}).get("ability_host_runtime_processes") == 2
        and by_phase["P05"].get("adoption", {}).get("ability_ids")
        == list(range(312, 318))
        and by_phase["P05"].get("adoption", {}).get("ability_rom_runtime_count") == 6
        and by_phase["P05"].get("adoption", {}).get("ability_rom_hook_count") == 29
        and by_phase["P05"].get("adoption", {}).get("ability_rom_linked") is True
        and by_phase["P05"].get("adoption", {}).get("ability_runtime_exact_mgba")
        is False
        and by_phase["P05"].get("adoption", {}).get(
            "documented_ai_ui_edges_pending"
        ) == 1
        and by_phase["P05"].get("adoption", {}).get(
            "documented_ai_ui_edges_implemented"
        ) == 3
        and by_phase["P05"].get("adoption", {}).get("stage76_allocation_sequence") == 79
        and by_phase["P05"].get("adoption", {}).get("stage76_allocation_count") == 80
        and by_phase["P05"].get("adoption", {}).get("stage76_changed_bytes") == 2081
        and by_phase["P05"].get("adoption", {}).get("stage76_allowlist_outside") == 0
        and by_phase["P05"].get("adoption", {}).get(
            "stage77_battle_circus_suppression"
        )
        is True
        and by_phase["P05"].get("adoption", {}).get("stage77_unique_hook_count")
        == 29
        and by_phase["P05"].get("adoption", {}).get(
            "stage77_ability_surface_occurrence_count"
        )
        == 33
        and by_phase["P05"].get("adoption", {}).get(
            "stage77_ordinary_suppression_changed"
        )
        is False
        and by_phase["P05"].get("adoption", {}).get("stage77_allocation_sequence")
        == 80
        and by_phase["P05"].get("adoption", {}).get("stage77_allocation_count")
        == 81
        and by_phase["P05"].get("adoption", {}).get("stage77_changed_bytes")
        == 1307
        and by_phase["P05"].get("adoption", {}).get("stage77_allowlist_outside")
        == 0
        and by_phase["P05"].get("adoption", {}).get(
            "stage77_stage76_hooks_preserved"
        )
        is True
        and by_phase["P05"].get("rom_reflection") == {
            "reflected": True,
            "stage": 77,
            "ancestor_stage": 72,
            "scope": "ABILITY_312_317_FIXED_TABLES_AND_29_BATTLE_HOOKS_PLUS_THREE_SAFE_AI_UI_EDGES_PLUS_BATTLE_CIRCUS_GLOBAL_SUPPRESSION",
        },
        "P05 Side Change非採用/Stage72 ability/Stage76 edge/Stage77 Circus runtime境界不正",
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
        and by_phase["P04"].get("rom_reflection")
        == {"reflected": True, "stage": 71, "ancestor_stage": 68, "scope": "45_MEGA_STONE_BP_SHOP_FLOETTE_ETERNAL_ACQUISITION_49_MEGA_SPECIES_AND_BATTLE_ROWS"},
        "P04 asset/shop/Floette/49 Mega ROM reflection境界不正",
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
    _require(
        p04_adoption.get("runtime_adopted_records") == 49
        and p04_adoption.get("runtime_materialized_acquisition_routes") == 46
        and p04_adoption.get("stone_item_ids_materialized") == 45
        and p04_adoption.get("stone_shop_entries_materialized") == 45
        and p04_adoption.get("stone_shop_currency") == "BP"
        and p04_adoption.get("stone_shop_price_each") == 16
        and p04_adoption.get("stone_shop_exact_runtime_gate") == "PASS"
        and p04_adoption.get("floette_eternal_existing_species_id") == 1029
        and p04_adoption.get("floette_eternal_gift_level") == 50
        and p04_adoption.get("floette_eternal_exact_party_pc_delivery") is True
        and p04_adoption.get("floette_eternal_exact_full_and_fresh_reload") is False
        and p04_adoption.get("mega_form_battle_runtime_records") == 49
        and p04_adoption.get("mega_form_species_runtime_materialized") is True
        and p04_adoption.get("mega_form_battle_runtime_materialized") is True
        and p04_adoption.get("mega_form_runtime_exact_mgba") is False,
        "P04 Stage68～71取得経路/49 Mega runtime境界不正",
    )
    _require(all(row.get("required_gates") for row in phases), "必須gate一覧が欠落しています")
    trace = matrix.get("traceability")
    _require(isinstance(trace, list) and len(trace) >= 14, "要件→実装→test対応が不足しています")
    _require(all(row.get("requirement_key") and row.get("implementation_evidence") and row.get("test_evidence") and row.get("status") for row in trace), "traceability rowが不完全です")
    summary = matrix.get("integration_summary")
    _require(isinstance(summary, Mapping) and summary.get("completed_phase_count") == 1 and summary.get("completed_phases") == ["P01"] and summary.get("highest_pinned_candidate_stage") == 77 and summary.get("runtime_reflected_phase_count") == 5 and summary.get("release_ready") is False, "P08統合summaryがP01のみ完了/Stage77 checkpointと不一致です")
    _require(
        matrix.get("release_blockers") == list(RELEASE_BLOCKERS),
        "P08 release blocker集合/内容/順序不一致",
    )
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
        "candidate_stage": 77,
        "completed_phases": ["P01"],
        "not_completed_phases": ["P02", "P03", "P04", "P05", "P06", "P07", "P08"],
        "release_blockers": matrix["release_blockers"],
        "promotion": {
            "authorized": False,
            "active_play_baseline_changed": False,
            "reason": "P02～P07のruntime acceptance未完了。Stage77はStage75のOwn Tempo Rockruff内部フォームと38 carry経路、Stage76のMega Sol popup・Piercing Drill AI・Spicy Spray AI、Stage77のBattle Circus全29 hook・33 ability surface抑制を統合し通常経路を保持したが、P02 exact UI、暫定archive economy、最終累積mGBA、Floette full/fresh reload、Eelevate専用switch AIが残るためrelease candidateではない",
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
