#!/usr/bin/env python3
"""固定save ABIを維持する後継source。配置済みROMや旧generatorは変更しない。

重複するsector生成・footer検査・program・最終世代検証だけを共通化する。
HT controllerの有効化は別段階であり、本生成物から呼び出したとは主張しない。
Linkのsource c、backup c+1、同じrotationという契約を維持する。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import pr16_dex_scheduler as previous

need = previous.need


def _body(source: str, name: str, body: str) -> str:
    """既存の宣言・公開section名を保持し、関数本体を一意に置換する。"""
    start, brace, end = previous.function_span(source, name)
    need(start < brace < end, "後継関数境界 " + name)
    return source[:brace] + "{\n" + body.strip() + "\n}" + source[end:]


COMMON = r"""
/* sourceは従来と同じstock footerで検査する。MDXの全世代検査は既存
 * validate_slotに残し、S61Eのlegacy互換ロード方針も変更しない。 */
static __attribute__((noinline)) u8 stage61_successor_footer_matches(
    const volatile u8 *section, u16 id, u16 size, u32 counter)
{
    return (u8)(stage61_read16(section + STAGE61_SAVE_ID_OFFSET) == id
        && stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
            == STAGE61_SAVE_SIGNATURE
        && stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET) == counter
        && stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
            == FN_SAVE_CHECKSUM((const void *)section, size));
}

/* 呼出側がdescriptorを検査してから使う。全4096byteの生成規則は
 * WriteSector/ReplaceSector/normalで共通。LinkFullの署名commitは含めない。 */
static __attribute__((noinline)) void stage61_successor_prepare_live(
    volatile u8 *section, u16 id, u16 size,
    const volatile u8 *data, u32 counter)
{
    u32 index;
    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index)
        section[index] = 0u;
    for (index = 0u; index < size; ++index)
        section[index] = data[index];
    stage61_write16(section + STAGE61_SAVE_ID_OFFSET, id);
    stage61_write16(section + STAGE61_SAVE_CHECKSUM_OFFSET,
        FN_SAVE_CHECKSUM((const void *)data, size));
    stage61_write32(section + STAGE61_SAVE_SIGNATURE_OFFSET,
        STAGE61_SAVE_SIGNATURE);
    stage61_write32(section + STAGE61_SAVE_COUNTER_OFFSET, counter);
    stage61_state_inject_tail(section, id, size);
}

/* 書込順を共有するだけでreadback責任は各呼出側に残す。
 * erase/body失敗時は従来どおり即座に停止。normalだけ署名失敗をinvalidate。
 * driver pointerは呼出側で取得済みの値を渡し、callbackで再取得しない。 */
static __attribute__((noinline)) u8 stage61_successor_program_committed(
    EraseFlashSectorFn erase_sector, ProgramFlashByteFn program_byte,
    u8 sector, volatile u8 *section, u8 reject_signature_failure)
{
    if (erase_sector(sector) != 0u
            || !stage61_dex_program_body(program_byte, sector, section))
        return STAGE61_SAVE_STATUS_ERROR;
    if (program_byte(sector, STAGE61_SAVE_SIGNATURE_OFFSET,
            reject_signature_failure != 0u ? (u8)STAGE61_SAVE_SIGNATURE
                : section[STAGE61_SAVE_SIGNATURE_OFFSET]) != 0u) {
        if (reject_signature_failure != 0u)
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    (void)FN_READ_FLASH_SECTION(sector, (void *)section);
    return STAGE61_SAVE_STATUS_OK;
}

/* 書込完了後の全14sector readback。normalはlive全像とのbyte比較、cloneは
 * sourceから準備した全像CRCとlive tail条件を使う。二つを混同しない。
 * targetのfirst/counterは明示引数で、ここで「最新世代」を選び直さない。 */
static __attribute__((noinline)) u8 stage61_successor_verify_generation(
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *source,
    u8 target_base, u8 target_first, u32 target_counter,
    const u32 *expected_crc, const u8 *expected_live,
    EraseFlashSectorFn erase_sector, ProgramFlashByteFn program_byte)
{
    struct Stage61SaveSlotValidation written;
    volatile u8 *section = G_FAST_SAVE_SECTION;
    u8 record_sector = (u8)(target_base
        + (u8)((target_first + 13u) % STAGE61_SAVE_SLOT_SECTORS));
    u16 id;
    u32 record_crc;

    stage61_save_validate_slot(target_base, chunks, &written);
    if (written.status != STAGE61_SAVE_STATUS_OK
            || written.counter != target_counter
            || written.valid_mask != STAGE61_SAVE_FULL_MASK
            || written.first_save_sector != target_first) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, record_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    record_crc = stage61_state_crc();
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        u8 sector = (u8)(target_base + written.physical_by_id[id]);
        u8 position = source != (const void *)0
            ? source->physical_by_id[id]
            : (u8)((target_first + id) % STAGE61_SAVE_SLOT_SECTORS);
        u8 reject = source != (const void *)0 ? sector : record_sector;
        u16 size = source != (const void *)0
            ? sStage61SaveChunkSizes[id] : chunks[id].size;
        u8 matches;

        if (written.physical_by_id[id] != position) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, reject);
            return STAGE61_SAVE_STATUS_ERROR;
        }
        (void)FN_READ_FLASH_SECTION(sector, (void *)section);
        if (source == (const void *)0) {
            matches = stage61_save_readback_matches_prepared(
                section, id, size, chunks[id].data, target_counter,
                record_crc, (u8)STAGE61_SAVE_SIGNATURE);
        } else {
            matches = (u8)(stage61_save_section_crc32(section)
                    == expected_crc[id]
                && stage61_successor_footer_matches(
                    section, id, size, target_counter)
                && (expected_live[id] == 0u
                    || stage61_state_tail_matches_live_crc(
                        section, id, size, stage61_state_crc())));
        }
        if (matches == 0u) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, reject);
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }
    return STAGE61_SAVE_STATUS_OK;
}
"""


def generated_source(host: bool = False) -> str:
    """旧source identity検査を通ったsourceだけを後継へ変換する。"""
    source = previous.generated_source(host=host)
    anchor = "STAGE61_EXPORT(DexImpl_Stage61State_HandleWriteSector)"
    need(source.count(anchor) == 1, "固定save export前の共通helper挿入")
    source = source.replace(anchor, COMMON + "\n" + anchor)

    # 三つのlive画像builderを、同じ全byte規則のhelperへ置き換える。
    for name in (
        "DexImpl_Stage61State_HandleWriteSector",
        "DexImpl_Stage61State_HandleReplaceSector",
        "stage61_save_write_normal_live_sector",
    ):
        a, b, z = previous.function_span(source, name)
        body = source[a:z]
        begin = body.index("    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE;")
        finish = body.index("    stage61_state_inject_tail(section, id, size);", begin)
        finish += len("    stage61_state_inject_tail(section, id, size);")
        counter = "target_counter" if name.startswith("stage61_save_") else "G_SAVE_COUNTER"
        replacement = "    stage61_successor_prepare_live(section, id, size, data, " + counter + ");"
        if name.endswith("HandleReplaceSector"):
            replacement = "    record_crc = stage61_state_crc();\n" + replacement
        body = body[:begin] + replacement + body[finish:]
        body = body.replace("    u32 index;\n", "")
        if name.startswith("stage61_save_"):
            body = body.replace("    u16 checksum;\n", "")
            body = body.replace("    checksum = FN_SAVE_CHECKSUM((const void *)data, size);\n", "")
        source = source[:a] + body + source[z:]

    # clone/rewriteの読出footer検証を共通化する。各経路の損傷bitと失敗先は維持。
    for name, sid in (
        ("stage61_save_clone_record_sector", "id"),
        ("stage61_save_rewrite_source_record_sector", "13u"),
    ):
        a, b, z = previous.function_span(source, name)
        body = source[a:z]
        begin = body.index("    if (stage61_read16(section + STAGE61_SAVE_ID_OFFSET)")
        finish = body.index(" {", begin)
        body = body[:begin] + ("    if (!stage61_successor_footer_matches(section, "
            + sid + ", size, selected->counter))") + body[finish:]
        begin = body.index("            || stage61_read16(section + STAGE61_SAVE_ID_OFFSET)")
        finish = body.index("            || ", begin + len("            || "))
        finish = body.index("            || ", finish + len("            || "))
        finish = body.index("            || ", finish + len("            || "))
        finish = body.index("            || ", finish + len("            || "))
        counter = "target_counter" if sid == "id" else "selected->counter"
        body = body[:begin] + ("            || !stage61_successor_footer_matches(section, "
            + sid + ", size, " + counter + ")\n") + body[finish:]
        source = source[:a] + body + source[z:]

    # 署名lastの書込とreadback開始を共通化し、比較内容は各経路にそのまま残す。
    for name, sector, normal, clone in (
        ("stage61_save_write_normal_live_sector", "target_sector", True, False),
        ("stage61_save_clone_record_sector", "target_sector", False, True),
        ("stage61_save_rewrite_source_record_sector", "source_sector", False, False),
    ):
        a, b, z = previous.function_span(source, name)
        body = source[a:z]
        begin = body.index("    if (erase_sector(" + sector + ") != 0u)")
        read = "    (void)FN_READ_FLASH_SECTION(" + sector + ", (void *)section);"
        finish = body.index(read, begin) + len(read)
        replacement = ("    if (stage61_successor_program_committed(erase_sector, program_byte,\n"
            + "            " + sector + ", section, " + ("1u" if normal else "0u")
            + ") != STAGE61_SAVE_STATUS_OK) {\n")
        if clone:
            replacement += "        stage61_save_mark_damaged(" + sector + ");\n"
        replacement += "        return STAGE61_SAVE_STATUS_ERROR;\n    }"
        body = body[:begin] + replacement + body[finish:]
        source = source[:a] + body + source[z:]

    # cloneの全世代validatorと後続readbackを同じhelperへ収束させる。
    name = "stage61_save_clone_complete_generation"
    a, b, z = previous.function_span(source, name)
    body = source[a:z]
    begin = body.index("    stage61_save_validate_slot(target_base, chunks, &written);")
    body = body[:begin] + r"""    return stage61_successor_verify_generation(
        chunks, selected, target_base, selected->first_save_sector,
        target_counter, expected_crc, expected_live_record,
        erase_sector, program_byte);
}"""
    body = body.replace("    struct Stage61SaveSlotValidation written;\n", "")
    source = source[:a] + body + source[z:]

    # normalのrollback値とno-main分岐を保持したまま、完了検証だけを共有する。
    name = "stage61_save_normal_copy_on_write"
    a, b, z = previous.function_span(source, name)
    body = source[a:z]
    begin = body.index("    stage61_save_validate_slot(target_base, live_chunks, &written);")
    finish = body.index("    G_SAVE_COUNTER = target_counter;", begin)
    body = body[:begin] + r"""    if (stage61_successor_verify_generation(
            live_chunks, (const void *)0, target_base, target_first_sector,
            target_counter, (const void *)0, (const void *)0,
            erase_sector, program_byte)
            != STAGE61_SAVE_STATUS_OK) {
        G_SAVE_COUNTER = rollback_counter;
        G_FIRST_SAVE_SECTOR = rollback_first_sector;
        return STAGE61_SAVE_STATUS_ERROR;
    }

""" + body[finish:]
    body = body.replace("    struct Stage61SaveSlotValidation written;\n", "")
    body = body.replace("    u32 record_crc;\n", "")
    source = source[:a] + body + source[z:]

    # ABIや未統合controllerの暗黙有効化を検出する簡潔な生成時不変条件。
    for name in previous.EXPORTS:
        previous.function_span(source, "DexImpl_" + name)
    need("HT_Normal(" not in source and "HT_Commit(" not in source,
         "未検証runtime接続を生成しない")
    need("source_counter = original_counter;" in source
         and "rollback_first_sector = original_first_sector;" in source,
         "no valid mainの従来初回saveを保持")
    return source


def integration_contract() -> dict:
    """配置/ABI/RAMの受入と、source refactorの実装状態を明確に分ける。"""
    return {
        "schema_version": 1,
        "status": "SOURCE_REFACTOR_ONLY_NOT_RUNTIME_INTEGRATED",
        "fixed_export_names": list(previous.EXPORTS),
        "source_generator": "scripts/pr16_dex_scheduler.py",
        "current_save_owner_total_bytes": 9560,
        "rom_placed": False,
        "capacity_reclaimed_bytes": None,
        "arm_measurement_required": True,
        "no_main_behavior": "既存normalのoriginal_counter/firstによる初回生成を保持",
        "link_generation": {
            "preflight": "source cを同じfirstのc+1へexact-old clone。RAMはcのまま",
            "stock": "cのlogical0..4だけ更新",
            "source_record": "cのid13のstock 0x7D0を保持しlive S61E/MDXのみ更新",
            "postflight": "検証済みcを同じfirstのc+1へcloneし、最後にRAMを昇格",
            "ht_normal_compatible": False,
        },
        "controller_blockers_ja": [
            "全14source SHAと既存owner検証を維持するcallback統合が未完",
            "HT_Workspace本体+4096+7936byteの実save中RAM/heap所有証明が未完",
            "INITIALのhas-records/loader absence証明が未完",
            "HT_Normalはno-mainを受理せず、初回normal生成の明示経路が必要",
            "Linkには最新selectorを使わないsource/target/first明示writerが必要",
            "全save mode、LinkFull遅延署名、HOF-only loadのjournal gateが未接続",
            "固定8entry veneerと既存mode3五sectionの参照監査・配置は別工程",
        ],
    }


DIFFERENTIAL_CASES = r"""
/* 合成媒体だけを使い、旧/新sourceの全flash・selector・callback数を比較する。 */
static uint64_t successor_hash(uint64_t h, const void *v, unsigned length)
{
    const uint8_t *bytes = v;
    for (unsigned n = 0; n < length; ++n) {
        h ^= bytes[n]; h *= UINT64_C(1099511628211);
    }
    return h;
}
static void successor_sample(unsigned number, unsigned result)
{
    uint64_t h = UINT64_C(1469598103934665603);
    unsigned state[] = {result, G_SAVE_COUNTER, G_FIRST_SAVE_SECTOR,
        G_DAMAGED_SAVE_SECTORS, reads, erases, programs, stock_calls,
        updates, serializes};
    h = successor_hash(h, flash_bytes, sizeof(flash_bytes));
    h = successor_hash(h, (const void *)DEX_LIVE, VEGA_DEX_OWNER_SIZE);
    h = successor_hash(h, state, sizeof(state));
    printf("%u:%016llx\n", number, (unsigned long long)h);
}
static void successor_differential(void)
{
    static const unsigned boundaries[] = {
        1, 2, 120, 522, 0x7D0, 0xDE6, 0xFF8, 0xFFF, 0x1000,
        0x1001, 0x1FF8, 0x8000, 0xDFF8, 0xE000, 0x12FF8, 0x1DFF8
    };
    unsigned number = 0;
    for (unsigned mode = 0; mode < 3; ++mode) {
        for (unsigned first = 0; first < 14; ++first) {
            reset(); G_FIRST_SAVE_SECTOR = first;
            G_SAVE_COUNTER = first & 1 ? UINT32_MAX - 1 : 0;
            successor_sample(number++, DexImpl_Stage61State_HandleSavingData(mode));
            reset(); G_FIRST_SAVE_SECTOR = first;
            G_SAVE_COUNTER = first & 1 ? UINT32_MAX - 1 : 0;
            saved(); access(1205, VEGA_DEX_SET_CAUGHT);
            memset((void *)(G_POKEMON_STORAGE_PTR + 0x7C00), 0xA9, 0x7D0);
            successor_sample(number++, DexImpl_Stage61State_HandleSavingData(mode));
        }
        for (unsigned fault = 0; fault < 2; ++fault) {
            for (unsigned b = 0; b < sizeof(boundaries)/sizeof(boundaries[0]); ++b) {
                reset(); saved(); access(1205, VEGA_DEX_SET_SEEN);
                if (fault == 0) fail_after = (int)(programs + boundaries[b]);
                else lie_after = (int)(programs + boundaries[b]);
                successor_sample(number++, DexImpl_Stage61State_HandleSavingData(mode));
            }
        }
    }
    /* EMPTYだけでなく、破損bankしかない既存normalの明示経路も保持する。 */
    for (unsigned corruption = 0; corruption < 3; ++corruption) {
        reset(); saved();
        if (corruption == 0) flash_bytes[record_sector()][0xDE6] ^= 1;
        if (corruption == 1) flash_bytes[record_sector()][0xFF8] = 0;
        if (corruption == 2) flash_bytes[record_sector()][0xFF6] ^= 1;
        successor_sample(number++, DexImpl_Stage61State_HandleSavingData(0));
    }
    printf("differential_cases=%u\n", number);
}
"""


def verify_synthetic_host() -> dict:
    """ROM/saveを使わず、既存合成20caseと旧/新source差分183caseを検証する。"""
    harness = (ROOT / "tools/pr16_dex_scheduler_host.c").read_text()
    harness = previous.once(harness, "int main(void)", DIFFERENTIAL_CASES + "\nint main(void)")
    harness = previous.once(harness, "all_banks();invalid_live();linkfull();partial_link();torn();",
        "all_banks();invalid_live();linkfull();partial_link();torn();successor_differential();")
    outputs = []
    with tempfile.TemporaryDirectory(prefix="vega-hof-successor-") as temporary:
        folder = Path(temporary)
        harness_path = folder / "host.c"
        harness_path.write_text(harness)
        for label, make_source in (("prior", previous.generated_source), ("successor", generated_source)):
            source = make_source(host=True)
            for name in previous.placement.EXPORTS:
                source, count = re.subn(r"#define DEX_ENTRY_" + name + r" 0x[0-9a-f]+u",
                    "#define DEX_ENTRY_" + name + " ((uintptr_t)&" + name + ")", source)
                need(count == 1, "合成dex関数binding " + name)
            block = ("static volatile u8 *host_save1,*host_save2,*host_storage;\n"
                "#undef G_SAVE_BLOCK1_PTR\n#define G_SAVE_BLOCK1_PTR host_save1\n"
                "#undef G_SAVE_BLOCK2_PTR\n#define G_SAVE_BLOCK2_PTR host_save2\n"
                "#undef G_POKEMON_STORAGE_PTR\n#define G_POKEMON_STORAGE_PTR host_storage\n")
            for name, function in (("FN_READ_FLASH_SECTION", "host_read"),
                ("FN_SAVE_CHECKSUM", "host_checksum"), ("FN_TRY_WRITE_SECTOR", "host_try"),
                ("FN_UPDATE_SAVE_ADDRESSES", "host_update"),
                ("FN_SAVE_SERIALIZED_GAME", "host_serialize"),
                ("FN_STOCK_HANDLE_SAVING_DATA", "host_stock")):
                block += "#undef " + name + "\n#define " + name + " " + function + "\n"
            source = previous.once(source, "static u8 stage61_factory_prepare_fault_is_armed",
                block + "\nstatic u8 stage61_factory_prepare_fault_is_armed")
            source_path = folder / (label + ".c")
            source_path.write_text(source)
            program = folder / label
            command = ["cc", *[x for x in previous.proof()["compile_argv_canonical"] if x.startswith("-D")],
                "-std=c11", "-O0", "-g", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                "-Wno-unused-const-variable", "-Wno-unused-parameter", "-I" + str(ROOT / "overlays/dex_owner"),
                '-DSCHEDULER_SOURCE="' + str(source_path) + '"', str(harness_path),
                *[str(ROOT / x) for x in previous.placement.SOURCES], "-o", str(program)]
            compiled = subprocess.run(command, capture_output=True, text=True)
            need(compiled.returncode == 0 and not compiled.stdout and not compiled.stderr,
                "strict合成host compile " + label + ": " + compiled.stderr[-2000:])
            tested = subprocess.run([str(program)], capture_output=True, text=True)
            need(tested.returncode == 0 and not tested.stderr,
                "合成host実行 " + label + ": " + tested.stderr[-2000:])
            outputs.append(tested.stdout)
    need(outputs[0] == outputs[1], "全合成媒体・selector・callback数の旧新一致")
    match = re.search(r"differential_cases=(\d+)", outputs[1])
    need(match is not None, "差分case数が記録済み")
    return {
        "status": "PASS_SYNTHETIC_HOST_SUCCESSOR_EQUIVALENCE",
        "existing_scheduler_cases_per_source": 20,
        "differential_cases": int(match.group(1)),
        "full_output_sha256": hashlib.sha256(outputs[1].encode()).hexdigest(),
        "host_compiles": 2,
        "native_game_runs": 0,
        "real_rom_or_save_inputs": 0,
        "arm_capacity_reclaimed_bytes": None,
        "runtime_controller_integrated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--host", action="store_true")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--verify-host", action="store_true")
    args = parser.parse_args()
    if args.verify_host:
        print(json.dumps(verify_synthetic_host(), ensure_ascii=False, indent=2))
    elif args.contract:
        print(json.dumps(integration_contract(), ensure_ascii=False, indent=2))
    else:
        output = generated_source(host=args.host)
        if args.output is None:
            print(output, end="")
        else:
            need(not args.output.exists(), "新規生成先のみ許可")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output)


if __name__ == "__main__":
    main()
