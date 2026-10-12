#!/usr/bin/env python3
"""成功済みtype1限定Actionsをbyte受領。再測定せず引継ぎとlogへ単親非force反映。"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import traceback
from pathlib import Path

import pr16_selected_compressed_asset as m
import pr16_selected_asset_provenance_actions as prior

a, old, publication = prior.a, prior.old, prior.publication
ROOT, STATE, GUIDE, BRANCH, LOGS = prior.ROOT, prior.STATE, prior.GUIDE, prior.BRANCH, prior.LOGS
read, load, write, snapshot = prior.read, prior.load, prior.write, prior.snapshot
TASK = "USER-20261012-COMPRESSED-ASSET-CLOSEOUT"
SOURCE_HEAD = "5962b1bcd96a82d0734d3434a174e4f73806b6b6"
MEASUREMENT_RUN = 38200881853
ARTIFACT_ID = 11725131506
ARTIFACT_SHA256 = "ab4317e233916b697eadbacdb611ffa61f4c578a016a32c8552901df9d23747f"
ARTIFACT_SIZE = 2009
FAILED_RUN = 38200730808
REPORT = "content/modernization/pr16_selected_compressed_asset_checkpoint.json"
EVIDENCE = "content/modernization/pr16_selected_compressed_asset_evidence"
CODE = {
    "scripts/pr16_selected_compressed_asset_closeout.py",
    ".github/workflows/pr16-selected-compressed-asset-closeout.yml",
}
MEASUREMENT_CODE = {
    "scripts/pr16_selected_compressed_asset.py",
    "scripts/pr16_selected_compressed_asset_actions.py",
    "tests/test_pr16_selected_compressed_asset.py",
    ".github/workflows/pr16-selected-compressed-asset.yml",
}
WORK = ROOT / ".local/pr16-selected-compressed-closeout"
PUBLIC = WORK / "public"
PHASE = "preflight"


def public(name, value):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def receive_measurement():
    completion = publication.accepted_run(
        MEASUREMENT_RUN, SOURCE_HEAD,
        ["新しいtype1境界試験のみ", "軽量task graph",
         "保存済み73bankのtype1のみ新範囲測定", "Run actions/upload-artifact@v4"])
    meta = a.fetch("actions/artifacts/" + str(ARTIFACT_ID))
    m.need(meta["name"] == "pr16-selected-compressed-asset-public-text" and not meta["expired"]
           and meta["workflow_run"]["id"] == MEASUREMENT_RUN
           and meta["workflow_run"]["head_sha"] == SOURCE_HEAD
           and meta["size_in_bytes"] == ARTIFACT_SIZE
           and meta["digest"] == "sha256:" + ARTIFACT_SHA256, "成功原本ZIP identity")
    raw = a.fetch("actions/artifacts/" + str(ARTIFACT_ID) + "/zip", binary=True)
    m.need(m.identity(raw) == dict(size=ARTIFACT_SIZE, sha256=ARTIFACT_SHA256), "ZIP bytes")
    members = old.zip_members(raw)
    m.need(set(members) == {"compressed-asset.json", "result.json"}, "限定公開2member")
    proof = json.loads(members["compressed-asset.json"])
    result = json.loads(members["result.json"])
    m.need(proof["candidate"] == m.CANDIDATE
           and proof["scope"] == "SAVED_73_BANKS_TYPE1_ONLY_WITHOUT_PCM_REPLAY"
           and proof["match_count"] == result["match_count"] == 0
           and proof["matches"] == [] and proof["matched_targets"] == []
           and proof["unique_type1_waves"] == result["unique_type1_waves"] == 0
           and proof["stats"] == result["stats"]
           and proof["stats"]["saved_tone_records_checked"] == 13194
           and proof["fixed_dpcm_source"] == m.DPCM_SOURCE
           and proof["formal_classified"] == 789 and proof["formal_unclassified"] == 85
           and proof["selected_unknown_origins"] == 6 and proof["donor_safe_bytes"] == 0
           and proof["actual_asset_reader_proven"] is False
           and proof["accepted_pcm_measurements_replayed"] == 0
           and proof["accepted_provenance_measurements_replayed"] == 0
           and proof["candidate_reconstructions"] == 1
           and proof["native_processes"] == 0, "成功測定の有限0件・不再走・型未受入")
    original = load(prior.EVIDENCE + "/provenance.json")
    saved = load("content/modernization/pr16_selected_sound_roots_evidence/sound-roots.json")
    m.need(proof["input_provenance_identity"] == m.identity(m.encode(original))
           and proof["input_sound_identity"] == m.identity(m.encode(saved)),
           "保存音声・系譜原本を束縛")
    m.need(proof["owner_lineage"]["source_image_identity"]
           == dict(sha256="499714cc04fd43ecb59ac45d8d23dad6badbc013c46d13", size=21383),
           "保存PLA1のarchive identity")
    completion.update(
        artifact={k: meta[k] for k in ("id", "name", "digest", "size_in_bytes")},
        published_source_commit=SOURCE_HEAD,
        result=result,
        artifact_members={name: m.identity(blob) for name, blob in members.items()},
        prior_failure_preserved={"run_id": FAILED_RUN, "reason": "initial runner lacked ARM toolchain",
                                 "rewritten_as_success": False},
        accepted_measurement_reruns=0, accepted_test_reruns=0,
        additional_rom_reconstructions=0)
    return proof, completion


def run():
    global PHASE
    m.need(os.environ.get("GITHUB_REPOSITORY") == a.REPO
           and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
           and os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "branch/first attempt")
    m.need(not WORK.exists() and not (ROOT / REPORT).exists(), "同scope記録の重複禁止")
    PUBLIC.mkdir(parents=True)
    head = a.git("rev-parse", "HEAD").decode().strip()
    m.need(head == os.environ["GITHUB_SHA"] and
           set(a.git("diff", "--name-only", SOURCE_HEAD, head).decode().splitlines()) == CODE
           and not a.git("status", "--porcelain", "--untracked-files=no").strip(),
           "今回closeout source2件の改変のみ")
    m.need(not a.git("ls-files", "--", *[p + "/AGENTS.md" for p in (
        "scripts", "tests", "docs", "design", "content", "content/modernization",
        ".github", ".github/workflows")]).strip(), "nested AGENTS not read")
    state = load(STATE)
    lane = state["owner_execution_plan"]["technical_lanes"]["save_capacity"]
    m.need(state["next_action"]["id"] == "SAVE_CAPACITY_SELECTED_COMPRESSED_ASSET_READER"
           and [lane[k] for k in ("classified", "unclassified", "selected_unknown_origins", "donor_safe_bytes")]
           == [789, 85, 6, 0], "固定next/分類/安全容量")
    owner = m.encode({k: state["owner_execution_plan"][k] for k in (
        "wiki", "wiki_readability", "owner_review", "scope")})
    parent = load(prior.REPORT)
    protected = {prior.REPORT, "content/modernization/pr16_selected_sound_roots_checkpoint.json",
                 "content/modernization/pr16_selected_sound_roots_evidence/sound-roots.json",
                 "content/modernization/pr16_selected_asset_provenance_evidence/provenance.json",
                 "content/modernization/pr16_dex_hof_generation_writer_checkpoint.json",
                 "content/modernization/pr16_learnset_supply_checkpoint.json",
                 "content/modernization/pr16_learnset_supply_alignment_checkpoint.json"}
    for key in ("source_bindings", "evidence_bindings", "preserved_inputs"):
        for name, expected in parent[key].items():
            m.need(m.identity(read(name)) == expected, "受入済み原本SHA/size: " + name)
            protected.add(name)
    baseline = snapshot(protected)
    PHASE = "receive-success-run-and-zip"
    proof, completion = receive_measurement()
    PHASE = "record-only"
    data = {
        EVIDENCE + "/compressed-asset.json": m.encode(proof),
        EVIDENCE + "/actions-completion.json": m.encode(completion),
    }
    for name, body in data.items():
        write(name, body)
    m.need(load(EVIDENCE + "/compressed-asset.json") == proof and
           load(EVIDENCE + "/actions-completion.json") == completion and
           baseline == snapshot(protected), "readback/accepted-originals")
    summary = ("保存済み音声73bank・13194 recordのtype1だけを、新しいDPCM 64sample/33byte"
               "消費境界で照合。妥当なtype1 WaveData 0件、選定3地点との全4byte一致0件。"
               "旧PCM測定/旧28試験/旧map・LZ・逆参照・Wiki再走0。"
               "0x095FE848はarchive-image.bin SHAと現PLA1(owner_offset 17232)が"
               "既存台帳・115owner配置と一致。実caller/readerは未証明。")
    goal = ("保存73bankのtype1は一致0件（type1不在の全域証明ではない）。"
            "次はpr16_supply_pla1のarchive-image.bin内+17232(0x095FE848)を"
            "現代化learnset供給consumerの具体的ABI/読取命令へ束縛し、"
            "0x0880FA64のIPS記録11873に由来する実asset境界と"
            "0x09673660の未所有配置元も個別に調べる。"
            "形/所有者だけで正式型・安全容量に昇格しない。"
            "今回22境界試験/type1新1計測と受入済み音声/系譜/map/LZ/Wikiを"
            "無変更再走しない。正式789/85・選定残6・安全容量0。"
            "保存統合/窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。")
    status = "SELECTED_TYPE1_ZERO_MATCH_PLA1_LEDGER_BOUND_READER_PENDING"
    observed = a.live(head)
    report = dict(schema_version=1, task=TASK, status=status, source_head=head,
                  measurement_source_head=SOURCE_HEAD, measurement_run_id=MEASUREMENT_RUN,
                  measurement_completion_confirmed=True, failed_run_id=FAILED_RUN,
                  candidate=m.CANDIDATE, match_count=0, unique_type1_waves=0,
                  new_unit_tests=22, newly_measured_type1_scopes=1,
                  additional_rom_reconstructions=0, measured_rom_reconstructions=1,
                  native_processes=0, accepted_test_reruns=0,
                  accepted_pcm_measurement_reruns=0,
                  actual_asset_reader_proven=False, formal_classified=789,
                  formal_unclassified=85, selected_unknown_origins=6, donor_safe_bytes=0,
                  source_bindings={n: m.identity(read(n)) for n in sorted(CODE | MEASUREMENT_CODE)},
                  evidence_bindings={n: m.identity(read(n)) for n in sorted(data)},
                  preserved_inputs={n: val[0] for n, val in baseline.items()},
                  read_only_check_passed=True, task_graph_passed=True,
                  observed_head_checks=observed, next_ja=goal)
    write(REPORT, report)
    lane.update(status=status, checkpoint_path=REPORT, next_ja=goal)
    state["next_action"] = {
        "id": "SAVE_CAPACITY_SELECTED_PLA1_AND_IPS_ACTUAL_READER",
        "goal_ja": goal,
        "read_paths": [GUIDE, REPORT, EVIDENCE + "/compressed-asset.json",
                       EVIDENCE + "/actions-completion.json",
                       prior.REPORT, prior.EVIDENCE + "/provenance.json",
                       "content/modernization/pr16_learnset_supply_checkpoint.json",
                       "content/modernization/pr16_learnset_supply_alignment_checkpoint.json"],
        "done_ja": "3地点の具体的なbyte境界/consumer readerを全4byteで立証した場合のみ正式分類を更新。"
    }
    state["observed_head_checks"] = observed
    state["recording"]["last_execution"] = dict(
        task=TASK, source_head=head, measurement_run_id=MEASUREMENT_RUN,
        measurement_source_head=SOURCE_HEAD, actions_run_id=int(os.environ["GITHUB_RUN_ID"]),
        actions_completion_confirmed=True, new_unit_tests=22,
        measured_rom_reconstructions=1, new_rom_reconstructions=0,
        accepted_test_reruns=0, accepted_pcm_measurement_reruns=0,
        type1_matches=0, read_only_check_passed=True, task_graph_passed=True)
    state["recording"].update(
        task=TASK, status=status, source_head=head,
        selected_compressed_asset_checkpoint=REPORT,
        received_selected_compressed_actions_completion=EVIDENCE + "/actions-completion.json")
    text = read("CHATGPT_RESUME.md").decode("utf-8")
    left, rest = text.split("## 次の未完作業\n", 1)
    _, right = rest.split("\n所有者が閲覧版で", 1)
    text = (left + "## 次の未完作業\n\n現在の next_action は "
            "SAVE_CAPACITY_SELECTED_PLA1_AND_IPS_ACTUAL_READER。" + goal
            + " 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で" + right)
    write("CHATGPT_RESUME.md", text.encode("utf-8"))
    state["bindings"]["CHATGPT_RESUME.md"] = dict(
        git_blob_sha=old.m.blob(text.encode("utf-8")), **m.identity(text.encode("utf-8")))
    m.need(owner == m.encode({k: state["owner_execution_plan"][k] for k in (
        "wiki", "wiki_readability", "owner_review", "scope")}),
        "承認/Wiki/安全境界を一切変更しない")
    write(STATE, state)
    guide = read(GUIDE).decode("utf-8").replace("## 次の未完作業", "## 以前の停止点（履歴）")
    guide += ("\n## 保存音声type1 DPCMの0件測定とPLA1台帳照合\n\n"
              + summary + "\n\n[checkpoint](../" + REPORT
              + ") / [type1測定](../" + EVIDENCE + "/compressed-asset.json"
              + ") / [完了run受領](../" + EVIDENCE + "/actions-completion.json"
              + ")。失敗run38200730808はARM compiler未導入による未受入原本のまま保持。"
              "成功run38200881853の22試験/task graph/候補復元1/静的type1計測1を"
              "新scopeとして受領し、受入済みPCM測定・系譜28試験の再走0。"
              "CI全体greenや正式分類の受入を主張しない。\n\n"
              "## 次の未完作業\n\n" + goal + "\n")
    write(GUIDE, guide.encode("utf-8"))
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    log_block = (
        "\n## " + stamp + "\n- Timestamp: " + stamp
        + "\n- Task: " + TASK + " / type1静的消費範囲とPLA1出典の受領"
        + "\n- Version: selected-compressed-asset-v1"
        + "\n- Status: DONE（限定type1照合0件を受領。実reader/保存統合は未完）"
        + "\n- Summary: " + summary
        + "\n- Files changed: 新DPCM限定検査器・22境界試験・専用Actionsと"
          "toolchain訂正、成功run受領器・公開証拠/checkpoint・固定入口MD/状態JSON・両ログ。"
        + "\n- Verify: 新22試験とtask graph PASS、成功run38200881853全必須steps、"
          "2009byte ZIP SHA256 ab4317e233916b697eadbacdb611ffa61f4c578a016a32c8552901df9d23747f、"
          "公開2member全照合、保存provenance/sound原本hash・現PLA1台帳一致、"
          "保存読戻し/受入既存130証拠byte・mtime不変。全体guard既存失敗と一般CIの既存状態は別扱い。"
        + "\n- Scope: 73保存bank/13194 toneのtype1限定。初回run38200730808"
          "失敗を成功に書替えない。計測時だけ新候補復元1、受領時再構成0、"
          "旧PCM/音声/系譜/record/base/逆参照/map/ARM/LZ/Wiki再走0。"
          "正式789/85・選定残6・安全容量0。"
        + "\n- Next: " + goal
        + "\n- Commit: 両ログを含む単親通常commit。実SHAはActions result/Git履歴。"
        + "\n- Network: 同repo固定Actions/artifact読取と同branch非force pushのみ。"
          "ROM/IPS/Save/private原本はGit追加なし。\n")
    for name in LOGS:
        original = read(name)
        m.need(("- Task: " + TASK + " /").encode() not in original, "同task log重複禁止")
        write(name, original + log_block.encode("utf-8"))
    PHASE = "final-scoped-index-and-nonforce-push"
    allowed = set(data) | set(LOGS) | {
        REPORT, STATE, GUIDE, "CHATGPT_RESUME.md"}
    publication.final_index(head, allowed, REPORT)
    m.need(baseline == snapshot(protected), "受入済み130証拠byte/mtime不変")
    m.need(a.git("ls-remote", "origin", "refs/heads/" + BRANCH).decode().split()[0] == head,
           "push直前lease")
    a.git("config", "user.name", "github-actions[bot]")
    a.git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    a.git("commit", "-m", TASK + ": type1の0件証拠とPLA1配置元・固定引継ぎを記録")
    a.git("push", "origin", "HEAD:" + BRANCH)
    pushed = a.git("rev-parse", "HEAD").decode().strip()
    m.need(a.git("ls-remote", "origin", "refs/heads/" + BRANCH).decode().split()[0] == pushed,
           "push後HEAD")
    for name in allowed:
        m.need(a.git("show", "HEAD:" + name) == read(name), "push後公開blob " + name)
    public("result.json", dict(status="DONE", task=TASK, commit=pushed, source_head=head,
                               measurement_run=MEASUREMENT_RUN, match_count=0,
                               formal_classified=789, formal_unclassified=85,
                               selected_unknown_origins=6, donor_safe_bytes=0))
    print("RESULT=DONE TASK=" + TASK + " VERIFY=PASS COMMIT=" + pushed)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        public("failure.json", dict(status="NOT_ACCEPTED", phase=PHASE,
                                    type=type(exc).__name__,
                                    frames=[{"file": x.filename.rsplit("/", 1)[-1], "line": x.lineno}
                                            for x in traceback.extract_tb(exc.__traceback__)
                                            if "/scripts/" in x.filename]))
        print("RESULT=BLOCKED TASK=" + TASK + " VERIFY=FAIL PHASE=" + PHASE
              + " TYPE=" + type(exc).__name__)
        sys.exit(1)
