#!/usr/bin/env python3
"""一回だけ候補ROMを非公開復元し、対象11siteの新命令形だけ公開する。"""
from __future__ import annotations
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import subprocess
import pr16_ips_dpe_instruction_probe as probe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/pr16-ips-dpe-instruction-extent"
PUBLIC = OUT / "public"
PHASE = "start"

def need(ok, message):
    if not ok:
        raise ValueError(message)

def put(name, value):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC/name).write_bytes(probe.serialize(value))

def run():
    global PHASE
    need(os.environ.get("GITHUB_REPOSITORY")=="dekaazarashi1111-web/pokemon-vega-modern" and
         os.environ.get("GITHUB_REF")=="refs/heads/codex/modernization-followup-20260908" and
         os.environ.get("GITHUB_RUN_ATTEMPT")=="1", "正本branch初回のみ")
    need(not OUT.exists(), "同scope二重復元なし")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    need(head==os.environ["GITHUB_SHA"],"実HEAD固定")
    state=json.loads((ROOT/"content/modernization/pr16_wiki_first_execution_plan.json").read_text())
    need(state["next_action"]["id"]=="SAVE_CAPACITY_IPS_AND_DPE_ASSET_READERS","固定next")
    lane=state["owner_execution_plan"]["technical_lanes"]["save_capacity"]
    need([lane[k] for k in ("classified","unclassified","selected_unknown_origins","donor_safe_bytes")]==[789,85,6,0],"受領正式数を保持")
    OUT.mkdir(parents=True)
    PHASE="candidate-exact-once"
    import pr16_dex_hof_capacity_actions as builder
    builder.OUT=OUT/"candidate"
    builder.OUT.mkdir()
    put("attempt.json", {"candidate_reconstructions_started":1,"native_processes":0,"accepted_test_reruns":0})
    with (OUT/"private-reconstruction.log").open("w") as private, contextlib.redirect_stdout(private),contextlib.redirect_stderr(private):
        raw,cp=builder.reconstruct()
    need(probe.identity(raw)==probe.CANDIDATE and cp["candidate"]==probe.CANDIDATE, "既存同SHA全候補")
    PHASE="new-instruction-and-output-extent"
    saved=json.loads((ROOT/probe.XREFS).read_text())
    evidence=probe.probe(raw,saved)
    cache_root=ROOT/"build/upstream-cache"
    chain=json.loads((ROOT/probe.CHAIN).read_text())
    candidates=[]
    if cache_root.is_dir() and not cache_root.is_symlink():
        candidates=sorted(p for p in cache_root.rglob("output.bin") if p.is_file() and "dpe" in (part.lower() for part in p.parts))
        need(len(candidates)<=16,"DPE未選定候補過多")
    evidence["dpe_output_probe"]=probe.dpe_extent(raw,candidates,chain)
    evidence.update(source_head=head, actions_run_id=int(os.environ["GITHUB_RUN_ID"]),
                    accepted_test_reruns=0,native_processes=0,candidate_reconstructions_for_this_scope=1)
    put("instruction-extent.json",evidence)
    need(json.loads((PUBLIC/"instruction-extent.json").read_bytes())==evidence,"保存後同値")
    PHASE="taskgraph"
    r=subprocess.run(["python3","-B","scripts/validate_task_graph.py"],cwd=ROOT,capture_output=True,text=True)
    need(r.returncode==0,"task graph fail")
    put("result.json", {"task":"USER-20261012-IPS-DPE-INSTRUCTION-EXTENT",
          "status":"LIMITED_MEASUREMENT_NOT_FORMAL_CLASSIFICATION",
          "source_head":head,"saved_first_level_references":11,"unaligned_sites":9,
          "rom_reconstructions":1,"new_unit_tests":11,"native_processes":0,"accepted_test_reruns":0,
          "actual_reader_accepted":False, "full_ci_green_claimed":False})
    print("INSTRUCTION_SITES=11")
    print("UNALIGNED_SITES=9")
    print("DPE_OUTPUT_CANDIDATES="+str(len(candidates)))
    print("RESULT=DONE TASK=USER-20261012-IPS-DPE-INSTRUCTION-EXTENT VERIFY=PASS COMMIT=-")

if __name__=="__main__":
    try:
        run()
    except Exception as exc:
        put("failure.json",{"status":"NOT_ACCEPTED","phase":PHASE,"exception_type":type(exc).__name__,
              "frames":[{"name":Path(f.filename).name,"line":f.lineno} for f in traceback.extract_tb(exc.__traceback__) if "/scripts/" in f.filename],
              "candidate_reconstructions_maybe_started": PHASE != "start",
              "native_processes":0})
        print("RESULT=BLOCKED TASK=USER-20261012-IPS-DPE-INSTRUCTION-EXTENT VERIFY=FAIL PHASE="+PHASE+" TYPE="+type(exc).__name__)
        sys.exit(1)
