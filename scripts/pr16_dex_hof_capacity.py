#!/usr/bin/env python3
"""現source/owner容量の読取専用contract。ROM断片やsave本文は不要。"""
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
 'overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c': '7ad33b6b00aacb30088b7a0cc528a7fb41c947a709bb4006ab225d82d4e271bf',
 'overlays/dex_owner/dex_owner.h': '9b6458882cfa70129fbc4e0a489b0dfacdfa587dcde6272e0d0c3c80a6d8a2d9',
 'overlays/qol_production/qol_production.c': '6a07635ca20dcd37365a2393910eb610d4f9c5a682585149ecb1243738cce23a',
 'content/modernization/pr16_dex_storage_audit.json': 'a21526808be34928098119fd3bec57185e1ce1edc1663a21608ee37eec3568f7',
 'content/modernization/pr16_dex_loadchain_audit.json': '92cb84f0fd1a26e04dec3f26d424c4b8ed5b3bbdcc412e65137dbd985e6505d6',
}
CP = 'content/modernization/pr16_dex_hof_main_checkpoint.json'
CANDIDATE = '88be88116bd452bd70cffaf2a820d5c6c6b6b7410fa603a9a0228b694725d5de'


def identity(raw):
 return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def need(condition, message):
 if not condition: raise ValueError(message)


def audit(root=ROOT):
 bindings = {}
 for path, sha in SOURCES.items():
  raw = (root / path).read_bytes(); bindings[path] = identity(raw)
  need(bindings[path]['sha256'] == sha, 'complete fixed source retained: ' + path)
 source = (root / next(iter(SOURCES))).read_text()
 block = re.search(r'static const u16 sStage61SaveChunkSizes\[STAGE61_SAVE_SLOT_SECTORS\] = \{(.*?)\};', source, re.S)
 need(block is not None, 'one exact main size table')
 sizes = [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]+)u', block[1])]
 need(sizes == [0xF24, 0xF80, 0xF80, 0xF80, 0xEC0] + [0xF80]*8 + [0x7D0], '14 logical payload sizes')
 spare = sum(0xFF0 - size for size in sizes[:13])
 need(spare == 1740 and 0x7D0 + 0x616 + 522 == 0xFF0, 'main tail capacity excludes fully owned logical13')
 cp = json.loads((root / CP).read_bytes()); bindings[CP] = identity((root / CP).read_bytes())
 need(cp['candidate']['sha256'] == CANDIDATE and len(cp['current_build']['placement']['allocation']['allocations']) == 115, 'exact candidate and115 owners')
 need(len(cp['current_scheduler_subowners']) == 43 and cp['current_scheduler_free_bytes'] == 186 and sum(r['size'] for r in cp['current_scheduler_free_subspans']) == 186, 'current43 subowners and186 actual bytes')
 old = json.loads((root / 'content/modernization/pr16_dex_storage_audit.json').read_bytes())
 need(old['flash_size'] == 131072 and old['existing_sector31_free_candidate']['size'] == 1100, 'historical capacity source')
 return dict(status='PASS_SOURCE_BOUND_CAPACITY_REFUSAL_NOT_ROM_ACCEPTANCE', candidate=cp['candidate'],
  flash_bytes=131072, flash_sectors=32, main_banks=2, main_sectors_per_bank=14,
  hof_payload_bytes=7936, hof_current_sectors=2, other_current_sectors=[30,31],
  simple_dual_hof_required_sectors=34, simple_dual_hof_deficit_bytes=8192,
  main_tail_potential_bytes_per_bank=spare, main_tail_new_owner_authorized=False,
  logical13_available_bytes=0, sector31_historical_candidate_bytes=1100,
  sector31_mdx_shadow_bytes=522, sector31_remaining_candidate_bytes=578,
  sector31_new_owner_authorized=False, sector30_unowned_claim=False,
  current_rom_owners=115, current_scheduler_subowners=43, current_scheduler_free_bytes=186,
  runtime_generation_binding=False, runtime_cross_store_atomicity=False,
  source_bindings=bindings, rom_reads=0, save_reads=0, rom_writes=0, save_writes=0)


if __name__ == '__main__':
 print(json.dumps(audit(), ensure_ascii=False, indent=2))
