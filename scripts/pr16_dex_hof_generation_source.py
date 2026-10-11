#!/usr/bin/env python3
"""exact-source generation writerを統合。live normal/LinkFullは固有barrierを保つ。"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_successor_source as prior
need=prior.need

def generated_source(host=False):
    source=prior.generated_source(host=host)
    name='stage61_save_clone_record_sector'
    a,b,z=prior.previous.function_span(source,name);body=source[a:z]
    body=body.replace('    u8 expected_live_record;','    u8 expected_live_record;\n    u8 rewrite = (u8)(source_base == target_base);')
    body=body.replace('            || expected_crc_out == (u32 *)0\n            || expected_live_record_out == (u8 *)0)','            || (rewrite == 0u && (expected_crc_out == (u32 *)0\n                || expected_live_record_out == (u8 *)0))\n            || (rewrite != 0u && (id != 13u || inject_record == 0u\n                || selected->status != STAGE61_SAVE_STATUS_OK\n                || selected->valid_mask != STAGE61_SAVE_FULL_MASK\n                || selected->counter != G_SAVE_COUNTER\n                || target_counter != selected->counter)))')
    body=body.replace('    if (source_base == target_base || source_sector == target_sector) {',
        '    if (rewrite == 0u && source_sector == target_sector) {')
    body=body.replace('    stage61_write32(\n        section + STAGE61_SAVE_COUNTER_OFFSET, target_counter\n    );','    if (rewrite == 0u)\n        stage61_write32(section + STAGE61_SAVE_COUNTER_OFFSET, target_counter);\n    live_record_crc = rewrite != 0u ? stage61_state_crc() : 0u;')
    body=body.replace('    live_record_crc = stage61_state_crc();',
        '    if (rewrite == 0u) live_record_crc = stage61_state_crc();')
    body=body.replace('    expected_section_crc = stage61_save_section_crc32(section);',
        '    if (rewrite != 0u && expected_live_record == 0u) {\n        stage61_save_mark_damaged(target_sector);\n        return STAGE61_SAVE_STATUS_ERROR;\n    }\n    expected_section_crc = stage61_save_section_crc32(section);\n    if (rewrite != 0u) stage61_save_mark_damaged(target_sector);')
    body=body.replace('        (void)stage61_save_reject_written_target_sector(\n            erase_sector, program_byte, target_sector\n        );','        if (rewrite == 0u)\n            (void)stage61_save_reject_written_target_sector(\n                erase_sector, program_byte, target_sector);')
    body=body.replace('    *expected_crc_out = expected_section_crc;\n    *expected_live_record_out = expected_live_record;','    if (rewrite == 0u) {\n        *expected_crc_out = expected_section_crc;\n        *expected_live_record_out = expected_live_record;\n    }')
    source=source[:a]+body+source[z:]
    name='stage61_save_rewrite_source_record_sector'
    a,b,z=prior.previous.function_span(source,name)
    # private wrapperのみ。public8entry、normal、LinkFull署名gateは保持。
    wrapper=source[a:b].replace('__attribute__((noinline)) ','')+'{\n    if (selected == (const void *)0) return STAGE61_SAVE_STATUS_ERROR;\n    return stage61_save_clone_record_sector(chunks, selected, 13u,\n        source_base, source_base, selected->counter, 1u, (void *)0, (void *)0);\n}'
    source=source[:a]+wrapper+source[z:]
    need(source.count('stage61_save_rewrite_source_record_sector(')==2,'one definition and one private caller')
    return source

def verify_host():
    old=prior.generated_source
    try:
        # freeze predecessor before injecting source dependency, avoiding recursion.
        base={x:old(host=x) for x in (False,True)}
        def generated(host=False):
            original=prior.generated_source
            try:
                prior.generated_source=lambda host=False:base[host]
                return generated_source(host=host)
            finally:prior.generated_source=original
        prior.generated_source=generated
        result=prior.verify_synthetic_host()
    finally:prior.generated_source=old
    result['status']='PASS_EXPLICIT_GENERATION_LOWER_WRITER_EQUIVALENCE'
    return result
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--verify-host':print(json.dumps(verify_host(),indent=2))
    else:print(generated_source(),end='')
