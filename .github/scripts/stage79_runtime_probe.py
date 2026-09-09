#!/usr/bin/env python3
"""Diagnostic-only instrumentation; never commit runtime PASS evidence or a ROM."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    "p02": "tools/mgba_modernization_p02_stage71_acceptance_smoke.c",
    "floette": "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c",
    "battle_policy": "tools/mgba_battle_policy_smoke.c",
}


def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def instrument(domain, text):
    if domain == "p02":
        text = once(text, 'struct P02SScene {', '''static color_t *p02s_probe_video;
static void p02s_probe_image(unsigned frame)
{
    char path[160];
    snprintf(path, sizeof(path), ".local/stage79-runtime-probe/p02/frame-%u.ppm", frame);
    FILE *output = fopen(path, "wb");
    if (output == NULL || p02s_probe_video == NULL) exit(2);
    fprintf(output, "P6\\n240 160\\n255\\n");
    for (unsigned pixel = 0; pixel < 240U * 160U; ++pixel) {
        uint32_t value = p02s_probe_video[pixel];
        fputc(value & 255U, output);
        fputc((value >> 8) & 255U, output);
        fputc((value >> 16) & 255U, output);
    }
    if (fclose(output) != 0) exit(2);
}

struct P02SScene {''')
        text = text.replace('    core->setVideoBuffer(core, video, 240U);',
                            '    core->setVideoBuffer(core, video, 240U);\n    p02s_probe_video = video;')
        text = once(text, "    uint32_t species = source;\n", "    uint32_t species = source;\n    uint32_t previous_callback = UINT32_MAX;\n")
        text = once(text, "        if (callback == P02S_CB2_EVOLUTION_BEGIN) {", '''        if ((callback != previous_callback && frame < 1000U) || frame % 1200U == 0U) {
            fprintf(stderr, "P02_TRACE frame=%u cb=%08x species=%u started=%u begin=%u update=%u physical_b=%u level=%u held=%u special=%u usecb=%08x party=%08x/%08x/%08x\\n",
                    frame, callback, species, scene_started, trace.begin_seen,
                    trace.update_seen, trace.physical_b,
                    (unsigned)p02s_data(core, QOL_MON_DATA_LEVEL),
                    (unsigned)p02s_data(core, QOL_MON_DATA_HELD_ITEM),
                    read16(core, QOL_SPECIAL_VAR_ITEM), read32(core, QOL_ITEM_USE_CALLBACK),
                    read32(core, QOL_PARTY_MENU), read32(core, QOL_PARTY_MENU + 4U),
                    read32(core, QOL_PARTY_MENU + 8U));
            previous_callback = callback;
        }
        if (frame <= 300U && frame % 60U == 0U) p02s_probe_image(frame);
        if (callback == P02S_CB2_EVOLUTION_BEGIN) {''')
    elif domain == "floette":
        start = text.index('static uint32_t fg_call_thumb(')
        end = text.index('static uint32_t fg_call8(', start)
        call = text[start:end]
        call = once(call, "    uint64_t steps = 0U;\n", "    uint64_t steps = 0U;\n    uint64_t registration_calls = 0U;\n")
        call = once(call, "        if (++steps > FG_MAX_CALL_STEPS) {", '''        uint32_t trace_pc = (uint32_t)read_register(core, "pc");
        if (trace_pc == UINT32_C(0x092D1C32)) {
            ++registration_calls;
            if (registration_calls < 20U || registration_calls % 10000U == 0U)
                fprintf(stderr, "FG_REGISTER step=%" PRIu64 " call=%" PRIu64 " species=%u sp=%08x lr=%08x\\n",
                        steps, registration_calls, (unsigned)read_register(core, "r0"),
                        (unsigned)read_register(core, "sp"), (unsigned)read_register(core, "lr"));
        }
        if (steps % UINT64_C(1000000) == 0U)
            fprintf(stderr, "FG_TRACE function=%08x step=%" PRIu64 " pc=%08x original_sp=%08x sp=%08x cpsr=%08x r4=%08x r5=%08x r6=%08x r7=%08x\\n",
                    function, steps, trace_pc, (unsigned)original.registers[13],
                    (unsigned)read_register(core, "sp"), (unsigned)read_register(core, "cpsr"),
                    (unsigned)read_register(core, "r4"), (unsigned)read_register(core, "r5"),
                    (unsigned)read_register(core, "r6"), (unsigned)read_register(core, "r7"));
        if (++steps > FG_MAX_CALL_STEPS) {''')
        text = text[:start] + call + text[end:]
    elif domain == "battle_policy":
        text = once(text, "        uint8_t gate = 0;\n", '''        uint8_t gate = 0;
        if (frame % 300U == 0U)
            fprintf(stderr, "POLICY_TRACE frame=%u main=%08x controller=%08x exec=%08x cmd=%02x latched=%u shields=%u/%u turns=%u key=%04x\\n",
                    frame, main, controller, exec, command, latched_gate,
                    evidence->shield_breaks, evidence->initial_shields,
                    evidence->controller_turns, read16(core, UINT32_C(0x04000130)));
''')
    return text


def main():
    domain = sys.argv[1]
    path = ROOT / PATHS[domain]
    original = path.read_bytes()
    output = ROOT / ".local/stage79-runtime-probe" / domain
    output.mkdir(parents=True, exist_ok=True)
    cfgpath = ROOT / "config/modernization_stage79_cumulative_mgba.json"
    config = json.loads(cfgpath.read_text())
    rom = config["input_identity"]["rom"]
    before = hashlib.sha256((ROOT / rom["path"]).read_bytes()).hexdigest()
    assert before == rom["sha256"]
    result_code = 2
    try:
        path.write_text(instrument(domain, original.decode()))
        for row in config["domains"]:
            for record in [row["runner"], *row.get("dependencies", [])]:
                if record["path"] == PATHS[domain]:
                    raw = path.read_bytes()
                    record.update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        cfgpath.write_text(json.dumps(config, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        spec = importlib.util.spec_from_file_location("probe_stage79", ROOT / "scripts/run_modernization_stage79_cumulative_mgba.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.prepare()
        with (output / "helper.stdout.log").open("w") as out, (output / "helper.stderr.log").open("w") as err:
            result = subprocess.run([sys.executable, "scripts/run_modernization_stage79_github_domain.py", "run-domain", "--domain", domain,
                "--output-directory", str(output.relative_to(ROOT))], cwd=ROOT, stdout=out, stderr=err, timeout=1000, check=False)
        result_code = result.returncode
    except Exception:
        (output / "probe-error.log").write_text(traceback.format_exc())
        raise
    finally:
        unchanged = hashlib.sha256((ROOT / rom["path"]).read_bytes()).hexdigest() == before
        (output / "DIAGNOSTIC_ONLY.json").write_text(json.dumps({"domain": domain, "exit_code": result_code,
            "rom_unchanged": unchanged, "acceptance_evidence": False}, indent=2) + "\n")
        assert unchanged
    for name in ("helper.stderr.log", "runner.stderr.log"):
        log = output / name
        if log.exists():
            print(log.read_text())
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
