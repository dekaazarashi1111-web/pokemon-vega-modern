#!/usr/bin/env python3
"""世代writerの下位sector本体を統合。counter/rotation選択を下位へ持ち込まない。"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_successor_source as prior
need=prior.need

CORE=r'''
/* normal、exact-old clone、Link source-recordの共通実writer。
 * planは上位で確定済み。ここで最新世代を再選択したりcounterを進めない。
 * mode=0 clone / 1 live normal / 2 Link source-record。後者は旧PCを保つ。
 * LinkFullの遅延署名はこの即commit経路へ入れない。 */
static __attribute__((noinline)) u8 stage61_generation_write_sector(
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *source,
    u16 id, u8 source_base, u8 target_sector, u32 target_counter,
    u8 inject_record, u8 mode, u32 *crc_out, u8 *live_out)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u16 size = chunks[id].size;
    u32 expected_crc, record_crc;
    u8 live;

    if (mode == 1u) {
        record_crc = stage61_state_crc();
        stage61_successor_prepare_live(section, id, size,
            chunks[id].data, target_counter);
        live = 1u;
        expected_crc = 0u;
    } else {
        (void)FN_READ_FLASH_SECTION(
            (u8)(source_base + source->physical_by_id[id]), (void *)section);
        size = sStage61SaveChunkSizes[id];
        if (!stage61_successor_footer_matches(section, id, size, source->counter)) {
            stage61_save_mark_damaged(target_sector);
            return STAGE61_SAVE_STATUS_ERROR;
        }
        if (mode == 0u)
            stage61_write32(section + STAGE61_SAVE_COUNTER_OFFSET, target_counter);
        /* source-recordは従来のCRC採取順序を保つ。cloneはinject後に採る。 */
        record_crc = mode == 2u ? stage61_state_crc() : 0u;
        if (inject_record != 0u && id == 13u)
            stage61_state_inject_tail(section, id, size);
        if (mode == 0u)
            record_crc = stage61_state_crc();
        live = (u8)(id == 13u && stage61_state_tail_matches_live_crc(
            section, id, size, record_crc) != 0u);
        if (mode == 2u && live == 0u) {
            stage61_save_mark_damaged(target_sector);
            return STAGE61_SAVE_STATUS_ERROR;
        }
        expected_crc = stage61_save_section_crc32(section);
    }
    if (mode != 0u)
        stage61_save_mark_damaged(target_sector);
    if (stage61_successor_program_committed(erase_sector, program_byte,
            target_sector, section, (u8)(mode == 1u)) != STAGE61_SAVE_STATUS_OK) {
        if (mode == 0u)
            stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    if (mode == 1u) {
        live = stage61_save_readback_matches_prepared(section, id, size,
            chunks[id].data, target_counter, record_crc, (u8)STAGE61_SAVE_SIGNATURE);
    } else {
        live = (u8)(stage61_save_section_crc32(section) == expected_crc
            && stage61_successor_footer_matches(section, id, size, target_counter)
            && (live == 0u || stage61_state_tail_matches_live_crc(
                section, id, size, record_crc) != 0u));
    }
    if (live == 0u) {
        /* source-record失敗時は旧backupを保護。元の失敗mask契約を維持。 */
        if (mode != 2u)
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    if (crc_out != (void *)0) {
        *crc_out = expected_crc;
        /* cloneの元のexpected-liveはprogram前の画像で判定済み。成功readbackは
         * 同一全像なので再計算しても意味は同じでflash callbackは増えない。 */
        *live_out = (u8)(id == 13u && stage61_state_tail_matches_live_crc(
            section, id, size, record_crc) != 0u);
    }
    stage61_save_clear_damaged(target_sector);
    return STAGE61_SAVE_STATUS_OK;
}
'''

def generated_source(host=False):
    source=prior.generated_source(host=host)
    anchor='/* Copy one exact sector from the selected generation into the inactive slot.'
    need(source.count(anchor)==1,'one lower writer insertion')
    source=source.replace(anchor,CORE+'\n'+anchor)
    name='stage61_save_clone_record_sector';a,b,z=prior.previous.function_span(source,name);body=source[a:z]
    begin=body.index('    (void)FN_READ_FLASH_SECTION(source_sector, (void *)section);')
    body=body[:begin]+'''    return stage61_generation_write_sector(chunks, selected, id, source_base,
        target_sector, target_counter, inject_record, 0u,
        expected_crc_out, expected_live_record_out);
}'''
    for line in ('    u16 size;\n','    u32 expected_section_crc;\n','    u32 live_record_crc;\n','    u8 expected_live_record;\n'):body=body.replace(line,'')
    source=source[:a]+body+source[z:]
    name='stage61_save_write_normal_live_sector';a,b,z=prior.previous.function_span(source,name);body=source[a:z]
    begin=body.index('    data = chunks[id].data;')
    body=body[:begin]+'''    return stage61_generation_write_sector(chunks, (const void *)0, id, 0u,
        target_sector, target_counter, 0u, 1u, (void *)0, (void *)0);
}'''
    for line in ('    volatile u8 *data;\n','    u16 size;\n','    u32 record_crc;\n'):body=body.replace(line,'')
    source=source[:a]+body+source[z:]
    name='stage61_save_rewrite_source_record_sector';a,b,z=prior.previous.function_span(source,name);body=source[a:z]
    begin=body.index('    size = sStage61SaveChunkSizes[13];')
    body=body[:begin]+'''    return stage61_generation_write_sector(chunks, selected, 13u, source_base,
        source_sector, selected->counter, 1u, 2u, (void *)0, (void *)0);
}'''
    for line in ('    u16 size;\n','    u32 record_crc;\n','    u32 expected_section_crc;\n'):body=body.replace(line,'')
    source=source[:a]+body+source[z:]
    need(source.count('stage61_successor_program_committed(erase_sector, program_byte,')==1,'one shared lower commit call')
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
