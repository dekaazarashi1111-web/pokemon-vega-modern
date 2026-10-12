#!/usr/bin/env python3
"""独立したtype1読取範囲の新scope検査。過去のPCM/28試験等は呼び出さない。"""
from __future__ import annotations
import contextlib
import json
import os
from pathlib import Path
import sys
import traceback

import pr16_selected_compressed_asset as m
import pr16_selected_asset_provenance_actions as previous

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".local/pr16-selected-compressed-asset"
PUBLIC = WORK / "public"
PHASE = "preflight"
REPO = "dekaazarashi1111-web/pokemon-vega-modern"
BRANCH = "codex/modernization-followup-20260908"
SOURCE = "https://raw.githubusercontent.com/pret/pokefirered/" + m.DPCM_SOURCE["commit"] + "/" + m.DPCM_SOURCE["path"]


def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def write(name, value):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC/name).write_bytes(m.encode(value))


def run():
    global PHASE
    m.need(os.environ.get("GITHUB_REPOSITORY") == REPO
           and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
           and os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "固定branch/初回")
    m.need(not WORK.exists(), "測定scope重複拒否")
    PUBLIC.mkdir(parents=True)
    PHASE = "fixed-source-check"
    source = previous.old.download(SOURCE, 100000)
    m.need(previous.old.m.blob(source) == m.DPCM_SOURCE["git_blob"], "固定ARM source blob")
    m.verify_decoder_source(source.decode("utf-8"))
    PHASE = "saved-lineage-and-asset-ledger"
    provenance = load("content/modernization/pr16_selected_asset_provenance_evidence/provenance.json")
    sound = load("content/modernization/pr16_selected_sound_roots_evidence/sound-roots.json")
    placement = load("content/modernization/pr16_dex_hof_generation_writer_checkpoint.json")
    supply = load("content/modernization/pr16_learnset_supply_checkpoint.json")
    align = load("content/modernization/pr16_learnset_supply_alignment_checkpoint.json")
    ledger = m.owner_lineage(provenance, placement, supply, align)
    PHASE = "one-new-scope-reconstruction"
    import pr16_dex_hof_capacity_actions as builder
    builder.OUT = WORK/"candidate"
    builder.OUT.mkdir()
    with (WORK/"private-reconstruction.log").open("w") as private, contextlib.redirect_stdout(private), contextlib.redirect_stderr(private):
        rom, checkpoint = builder.reconstruct()
    m.need(checkpoint["candidate"] == m.CANDIDATE, "現代化候補全SHA")
    PHASE = "only-saved-type1-tones"
    proof = m.inspect_saved_bank_wave_types(rom, sound, provenance)
    proof["owner_lineage"] = ledger
    proof["fixed_arm_source_identity"] = m.identity(source)
    proof["accepted_pcm_measurements_replayed"] = 0
    proof["accepted_provenance_measurements_replayed"] = 0
    proof["candidate_reconstructions"] = 1
    proof["native_processes"] = 0
    write("compressed-asset.json", proof)
    m.need(load(".local/pr16-selected-compressed-asset/public/compressed-asset.json") == proof, "evidence readback")
    summary = {
        "status": "TYPE1_DECLARED_EXTENT_MEASURED_READER_PENDING",
        "match_count": proof["match_count"], "matched_targets": proof["matched_targets"],
        "unique_type1_waves": proof["unique_type1_waves"], "stats": proof["stats"],
        "source_blob": m.DPCM_SOURCE["git_blob"], "formal_classified": 789,
        "formal_unclassified": 85, "donor_safe_bytes": 0, "actual_reader_proven": False,
    }
    write("result.json", summary)
    print("RESULT=DONE TASK=USER-20261012-COMPRESSED-ASSET VERIFY=PASS COMMIT=-")
    print("TYPE1_SUMMARY=" + json.dumps(summary, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        failure = {"status": "NOT_ACCEPTED", "phase": PHASE, "exception_type": type(exc).__name__,
                   "frames": [{"file": f.filename.rsplit("/", 1)[-1], "line": f.lineno} for f in traceback.extract_tb(exc.__traceback__) if "/scripts/" in f.filename],
                   "accepted_pcm_measurements_replayed": 0}
        write("failure.json", failure)
        print("RESULT=BLOCKED TASK=USER-20261012-COMPRESSED-ASSET VERIFY=FAIL TYPE=" + type(exc).__name__)
        sys.exit(1)
