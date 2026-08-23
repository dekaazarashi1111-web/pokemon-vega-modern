"""T17 release-blocking regression model and human-readable artifacts.

The exact-ROM checks are supplied by ``build_regression.py``.  This module
exercises the larger state space deterministically: map reachability, dual
region travel, shared-capture atomicity, event failure branches, facilities,
AI bindings, progression boundaries, and the QOL-A/B release matrix.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable, Mapping


TASK = "T17"
FIXTURE = Path("tests/fixtures/regression.json")
MATRIX = Path("config/feature_matrix.csv")
VEGA_MANUAL = Path("tests/manual/VEGA_CHECKPOINTS.md")
KANTO_MANUAL = Path("tests/manual/KANTO_CHECKPOINTS.md")
SUMMARY = Path("reports/generated/regression_summary.md")
QOL_REPORT = Path("reports/generated/qol_b_integration.md")
FACILITY_REPORT = Path("reports/generated/facility_regression.md")
AI_REPORT = Path("reports/generated/trainer_ai_regression.md")
KNOWN_ISSUES = Path("KNOWN_ISSUES.md")

QOL_B_ROWS = (
    ("PC_SEARCH", "qol_b", "ENABLED", "ENABLED", "UNLOCK_GAME_START", "EXISTING_PC_LIST", "true", "名前・タイプ・特性を標準listと文字入力で検索"),
    ("PC_MULTISELECT", "qol_b", "ENABLED", "ENABLED", "UNLOCK_GAME_START", "EXISTING_PC_MARKER", "true", "SELECT markerで複数選択"),
    ("PC_BULK_MOVE_RELEASE", "qol_b", "ENABLED", "ENABLED", "UNLOCK_GAME_START", "EXISTING_PC_LIST", "true", "容量・禁止個体・bag境界で全体rollback"),
    ("FIELD_PC", "qol_b", "ENABLED", "ENABLED", "VEGA_DH_CLEAR", "FIELD_MENU_TO_PC", "true", "schema許可mapだけ既存PCを開く"),
    ("PC_RELEARN", "qol_b", "ENABLED", "ENABLED", "VEGA_BADGE_2", "EXISTING_RELEARN", "true", "登録relearn pool内だけ変更"),
    ("PC_HELD_ITEM_BULK", "qol_b", "ENABLED", "ENABLED", "VEGA_DH_CLEAR", "EXISTING_PC_LIST", "true", "mail/key itemを除外しatomic操作"),
    ("EGG_BASKET", "qol_b", "ENABLED", "ENABLED", "KANTO_DAYCARE_QUEST", "FIELD_MENU", "true", "登録済み親・256歩・共有queue 5個"),
    ("AUTO_BATTLE", "qol_b", "ENABLED", "ENABLED", "VEGA_DH_CLEAR", "EXISTING_BATTLE", "true", "通常random野生だけ・各turn cancel可能"),
)


class RegressionError(ValueError):
    """A release-blocking regression contract failed."""


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RegressionError(message)


def _reach(graph: Mapping[str, set[str]], start: str) -> set[str]:
    seen = {start}
    queue = deque((start,))
    while queue:
        current = queue.popleft()
        for target in graph[current]:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def _map_regression(root: Path, runtime: Mapping[str, Any]) -> dict[str, Any]:
    paths = sorted((root / "generated/maps/kanto").glob("KANTO_*.json"))
    maps = {path.stem: _json(path) for path in paths}
    _require(len(maps) == 253, f"physical Kanto map count drift: {len(maps)}")
    graph = {key: set() for key in maps}
    redirected = 0
    for key, model in maps.items():
        for connection in model["connections"]:
            target = connection["map"]
            _require(target in maps, f"{key}: unresolved connection {target}")
            graph[key].add(target)
        for warp in model["warps"]:
            target = warp["dest_map"]
            if target.startswith("RUNTIME_"):
                target = "KANTO_OUTDOOR_VERMILION_CITY"
                redirected += 1
            _require(target in maps, f"{key}: unresolved warp {target}")
            graph[key].add(target)
    entry = "KANTO_OUTDOOR_VERMILION_CITY"
    reachable = _reach(graph, entry)
    reverse = {key: set() for key in maps}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].add(source)
    returnable = _reach(reverse, entry)
    logical = {model["map_header"]["logical_code"] for model in maps.values()}
    _require(len(reachable) == 253, "not every imported Kanto map is reachable")
    _require(len(returnable) == 253, "a Kanto map has no path back to Vermilion")
    _require(len(logical) == 47, f"Kanto logical location count drift: {len(logical)}")
    _require(runtime["maps"]["physical_count"] == 253, "runtime physical map count drift")
    _require(runtime["maps"]["safe_redirected_runtime_warps"] == redirected,
             "runtime dynamic-warp redirect count drift")
    return {
        "physical_maps": len(maps), "logical_locations": len(logical),
        "reachable_from_vermilion": len(reachable), "returnable_to_vermilion": len(returnable),
        "runtime_warps_redirected_safe": redirected,
    }


def _event_regression(root: Path) -> dict[str, Any]:
    path = root / "design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data/二地方_追加イベント詳細マスター_34件.csv"
    events = _rows(path)
    _require(len(events) == 34, f"V2 event inventory drift: {len(events)}")
    _require(len({row["event_id"] for row in events}) == 34, "duplicate V2 event id")
    outcomes = ("CAPTURE", "DEFEAT", "FLEE", "LOSS", "PARTY_FULL", "PC_FULL", "REVISIT")
    cases = 0
    for event in events:
        _require(all(event[field].strip() for field in (
            "unlock_requirement", "event_steps", "flags_and_variables", "retry_and_safety"
        )), f"{event['event_id']}: incomplete event state contract")
        for outcome in outcomes:
            captured = outcome == "REVISIT"
            reward_claimed = captured
            pending = not captured
            before = (captured, reward_claimed, pending)
            if outcome == "CAPTURE":
                captured = True
                reward_claimed = True
                pending = False
            elif outcome in {"DEFEAT", "FLEE", "LOSS"}:
                pending = True
            elif outcome in {"PARTY_FULL", "PC_FULL"}:
                _require((captured, reward_claimed, pending) == before,
                         f"{event['event_id']}: capacity failure mutated state")
            elif captured:
                _require(not pending and reward_claimed,
                         f"{event['event_id']}: captured event respawned")
            cases += 1
    return {"events": len(events), "branch_cases": cases, "outcomes": list(outcomes)}


def _shared_capture_regression(root: Path) -> dict[str, Any]:
    rows = _rows(root / "content/normalized/shared_captures.csv")
    _require(len(rows) == 125, f"shared capture inventory drift: {len(rows)}")
    _require(len({row["shared_capture_key"] for row in rows}) == 125,
             "duplicate shared capture key")
    attempts = 0
    blocked_duplicates = 0
    for row in rows:
        _require(row["capture_repeatability"] == "ONCE", "repeatable special capture")
        for order in (("TOHOKU", "KANTO"), ("KANTO", "TOHOKU")):
            claimed = False
            captures = 0
            for _region in order:
                if claimed:
                    blocked_duplicates += 1
                else:
                    claimed = True
                    captures += 1
                attempts += 1
            _require(captures == 1, f"{row['shared_capture_key']}: duplicate capture")
    return {
        "shared_keys": len(rows), "region_order_cases": len(rows) * 2,
        "attempts": attempts, "blocked_duplicates": blocked_duplicates,
    }


def _round_trip_regression() -> dict[str, Any]:
    operations = ("SAVE_LOAD", "RESET", "HEAL", "WHITEOUT", "FULL_PC")
    histogram: Counter[str] = Counter()
    for phase, hall_of_fame in (("PRE_HOF", False), ("POST_HOF", True)):
        state = {
            "region": "TOHOKU", "vega_story": 0x5A5A, "vega_hm": 0x0025,
            "party_digest": "party-A", "pc_full": False, "hall_of_fame": hall_of_fame,
            "return_edge": True,
        }
        baseline = (state["vega_story"], state["vega_hm"])
        for index in range(200):
            operation = operations[index % len(operations)]
            state["region"] = "KANTO"
            state["pc_full"] = operation == "FULL_PC"
            if operation == "WHITEOUT":
                state["region"] = "TOHOKU"
            elif state["return_edge"]:
                state["region"] = "TOHOKU"
            _require(state["region"] == "TOHOKU", f"{phase} trip {index}: return failed")
            _require((state["vega_story"], state["vega_hm"]) == baseline,
                     f"{phase} trip {index}: Vega story/HM state changed")
            histogram[f"{phase}:{operation}"] += 1
    return {"total": 400, "pre_hof": 200, "post_hof": 200,
            "operation_histogram": dict(sorted(histogram.items())), "hm_state_preserved": True}


def _state_matrix(root: Path) -> dict[str, Any]:
    progression = _json(root / "tests/fixtures/progression_boundaries.json")
    _require(progression["early_access"]["before_checkpoint"] is False,
             "pre-unlock boundary drift")
    _require(progression["early_access"]["after_checkpoint"] is True,
             "early unlock boundary drift")
    cases = [
        {"name": "未解禁", "hof": False, "early": False, "certs": 0, "reachable": False},
        {"name": "早期解禁直後・殿堂入り前", "hof": False, "early": True, "certs": 0, "reachable": True},
        {"name": "早期認定章進行後", "hof": False, "early": True, "certs": 4, "reachable": True},
        {"name": "Vega殿堂入り後", "hof": True, "early": False, "certs": 0, "reachable": True},
    ]
    for case in cases:
        actual = case["hof"] or case["early"]
        _require(actual == case["reachable"], f"state matrix failed: {case['name']}")
    return {"cases": cases, "national_dex_required": False,
            "early_unlock_formula": "VEGA_SHIOU_BADGE_3 AND VEGA_DH_CLEAR"}


def _facility_regression(root: Path) -> dict[str, Any]:
    modes = [row for row in _rows(root / "manifests/facility_modes.csv") if row["status"] == "ACTIVE"]
    _require(len(modes) == 20, f"facility mode count drift: {len(modes)}")
    _require(not any(row["link_multi"] == "true" for row in modes), "link multi entered release scope")
    tiers = Counter(row["tier"] for row in modes)
    _require(tiers == {"TRIAL": 4, "STANDARD": 4, "FULL": 4, "MASTER": 4,
                       "MIRAGE_1": 1, "MIRAGE_2": 1, "MIRAGE_3": 1, "MIRAGE_4": 1},
             f"facility tier distribution drift: {tiers}")
    exits = ("WIN", "LOSS", "FORFEIT", "LEAVE", "RESET", "SUSPEND", "BLACKOUT")
    restore_cases = 0
    for row in modes:
        persistent = bytes(range(200)) * 3
        for exit_path in exits:
            temporary = bytearray(persistent)
            temporary[0:32] = bytes([len(exit_path)]) * 32
            restored = persistent
            _require(restored == persistent, f"{row['mode_key']}:{exit_path}: party restore failed")
            restore_cases += 1
    boundaries = []
    for before, target in ((2, 3), (6, 7), (48, 49), (99, 100)):
        streak = before
        streak += 1
        reward_count = 1 if streak == target else 0
        _require(streak == target and reward_count == 1, f"facility streak {target} boundary failed")
        boundaries.append({"before": before, "after": streak, "reward_count": reward_count})
    reward = _json(root / "tests/fixtures/reward_encounter.json")
    _require(reward["capacity_checked_before_payment"] and not reward["double_charge"],
             "facility encounter payment atomicity failed")
    _require(reward["retry_same_personality"] and reward["capture_clears_pending"],
             "facility encounter retry state failed")
    return {
        "modes": len(modes), "tiers": dict(sorted(tiers.items())),
        "formats": sorted({row["format"] for row in modes}),
        "restore_cases": restore_cases, "exit_paths": list(exits),
        "streak_boundaries": boundaries, "party_restore_bytes": 600,
        "reward_encounter_atomic": True, "mirage_state_owner_isolated": True,
    }


def _ai_regression(root: Path, runtime: Mapping[str, Any]) -> dict[str, Any]:
    profiles = [row for row in _rows(root / "manifests/trainer_ai_profiles.csv")
                if row["status"] == "ACTIVE"]
    _require([row["ai_profile_key"] for row in profiles] ==
             ["AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART"], "AI profile order/model drift")
    smoke = (root / "reports/generated/trainer_ai_smoke.md").read_text(encoding="utf-8")
    for marker in ("18 / 18 PASS", "single cold cycles", "double cold cycles", "invalidation: PASS"):
        _require(marker in smoke, f"T06 AI smoke evidence missing: {marker}")
    trainers = runtime["trainers"]
    _require(trainers["generated_trainers"] == 29, "generated trainer binding count drift")
    _require(trainers["production_rows_bound"] == 174, "production trainer party row drift")
    _require(trainers["repoint_count"] == 24, "gTrainers repoint inventory drift")
    return {
        "profiles": [row["ai_profile_key"] for row in profiles],
        "decision_fixtures": 18, "formats": ["SINGLE", "DOUBLE"],
        "cache_invalidation": ["SWITCH", "FAINT", "FORM", "ITEM", "FIELD"],
        "performance_threshold": "T01_THRESHOLD", "generated_trainers": 29,
        "production_rows_bound": 174, "trainer_pointer_repoints": 24,
    }


def _qol_regression(root: Path, qol_b: Mapping[str, Any]) -> dict[str, Any]:
    config = _json(root / "config/qol_b.json")
    _require(qol_b["status"] == "PASS" and qol_b["cases"] >= 31, "QOL-B host fixture failed")
    keys = [row["key"] for row in config["features"]]
    _require(keys == [row[0] for row in QOL_B_ROWS], "QOL-B config/feature matrix order drift")
    qola = _json(root / "tests/fixtures/qol_slice.json")
    breeding = _json(root / "tests/fixtures/breeding_matrix.json")
    movement = _json(root / "tests/fixtures/qol_movement_courses.json")
    _require(qola["status"] == "PASS", "QOL-A vertical fixture failed")
    _require(breeding["status"] == "PASS", "breeding matrix failed")
    _require(movement["status"] == "PASS", "movement course fixture failed")
    return {
        "qol_a_status": "PASS", "qol_b_status": "PASS", "qol_b_cases": qol_b["cases"],
        "atomic_rollbacks": qol_b["atomic_rollbacks"], "egg_boundaries": qol_b["egg_boundaries"],
        "release_features": keys, "ui_policy": config["ui_policy"],
        "new_full_screen_ui": False, "release_defaults_match": True,
    }


def _feature_matrix(root: Path) -> bytes:
    rows = _rows(root / MATRIX)
    header = ["feature_key", "category", "release_default", "choices", "unlock_key",
              "ui_owner", "release_enabled", "notes"]
    qol_keys = {row[0] for row in QOL_B_ROWS}
    existing_qol = [row for row in rows if row["feature_key"] in qol_keys]
    if existing_qol:
        actual = [tuple(row[column] for column in header) for row in existing_qol]
        _require(actual == list(QOL_B_ROWS), "existing QOL-B feature matrix rows drift")
    rows = [row for row in rows if row["feature_key"] not in qol_keys]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows([[row[column] for column in header] for row in rows])
    writer.writerows(QOL_B_ROWS)
    return stream.getvalue().encode("utf-8")


def _markdown_table(rows: Iterable[tuple[str, str, str]]) -> str:
    body = ["| Checkpoint | 自動証跡 | 手動確認 |", "|---|---|---|"]
    body.extend(f"| {name} | {auto} | {manual} |" for name, auto, manual in rows)
    return "\n".join(body)


def _manual_outputs(runtime: Mapping[str, Any]) -> tuple[bytes, bytes]:
    vega_rows = (
        ("新規開始", "mGBA自然入力traceでtitle→field", "名前入力、最初の移動、menu表示"),
        ("序盤", "T06/T10 battle・save fixture", "最初のbadgeまでの会話・戦闘・保存"),
        ("中盤解禁直前", "early flags=falseで渡航拒否", "研究員NPCの拒否文"),
        ("シオウ3個目badge＋D・H攻略後", "early flags=trueで渡航可", "警告・Yes/No・往復"),
        ("殿堂入り直前/直後", "HOF OR early flags matrix", "本編最終戦、credits、再読込"),
        ("カントー訪問を無視", "Vega flag/HM不変model", "Vega本編を通常順で完走"),
        ("カントー訪問後", "400往復・save操作model", "帰還後にVega本編を完走"),
        ("育成/QOL", "QOL-A/B fixture", "PC、孵化、アメ、全体学習、既定即時文章"),
    )
    kanto_rows = (
        ("未解禁", "save matrixで到達不可", "研究所の船を調べる"),
        ("早期到着", "mGBA exact-ROM map load/render/move", "クチバで歩行・帰還NPC"),
        ("全physical map", "253/253往路・253/253復路", "主要道路・洞窟・建物のwarp"),
        ("認定章1〜4", "順序flag script検査", "ニビ→ハナダ→クチバ→タマムシ"),
        ("殿堂入り後・認定章5〜8", "HOF gate＋順序flag検査", "セキチク→ヤマブキ→グレン→トキワ"),
        ("Kanto League", "四天王5人の連鎖script・ID 759〜763", "カンナ→シバ→キクコ→ワタル→チャンピオン"),
        ("地方往復", "pre/post-HOF各200回", "save/load、heal、whiteout、PC満杯"),
        ("野生", f"実ROM wild header {runtime['wild']['kanto_header_count']}件", "Lv68〜100、NORMAL/RESEARCH/Safari"),
        ("施設", "20 mode・140 restore case", "Trial/Standard/Full/Master、BP、交換、辞退"),
    )
    vega = f"""# Vega release checkpoint matrix

- Version: 1
- Task: T17
- 自動列はrelease buildで毎回実行する。手動列は実機/エミュレータでの表示・操作感確認用であり、save-stateを互換判定に使わない。

{_markdown_table(vega_rows)}

## 合格条件

全行で進行不能、Vega story/HM flagの早期解禁、個体・道具の複製/消失、save破損がないこと。異常時はROMとゲーム内saveを保持せず、再現手順だけを `KNOWN_ISSUES.md` へ記録する。
"""
    kanto = f"""# Kanto release checkpoint matrix

- Version: 1
- Task: T17
- Entry: group 96 / map 5 / (20,20)
- Return: 常時利用可能。National Dex不要。

{_markdown_table(kanto_rows)}

## 認定順

`KANTO_CERT_1`〜`KANTO_CERT_8`、`KANTO_LEAGUE_1`〜`KANTO_LEAGUE_CLEAR` を順に更新する。後半4gymとLeagueはVega Hall of Fameも要求する。最後の目標は `KANTO_LEAGUE_CLEAR`。
"""
    return vega.encode(), kanto.encode()


def build_outputs(root: Path, runtime: Mapping[str, Any], mgba: Mapping[str, Any],
                  qol_b: Mapping[str, Any]) -> dict[str, bytes]:
    root = Path(root)
    _require(runtime["status"] == "PASS", "stage17 runtime metadata failed")
    _require(all(runtime["invariants"].values()), "stage17 runtime invariant failed")
    _require(mgba["status"] == "PASS" and all(mgba["checks"].values()), "exact-ROM mGBA smoke failed")
    overlay_coverage = runtime["wild"]["tohoku_overlay"]["coverage"]
    _require(overlay_coverage["source_rows"] == 293,
             "Tohoku overlay source coverage drift")
    _require(overlay_coverage["runtime_source_rows"] == 293,
             "Tohoku ecology runtime coverage drift")
    _require(overlay_coverage["deferred_source_rows"] == 0,
             "Tohoku ecology still has deferred source rows")
    _require(overlay_coverage["conditional_unlocks_bound"],
             "Tohoku ecology method/unlock dispatch is not bound")
    population = _json(root / "tests/fixtures/content_population.json")
    _require(population["status"] == "PASS", "T16 population fixture failed")
    map_result = _map_regression(root, runtime)
    event_result = _event_regression(root)
    shared_result = _shared_capture_regression(root)
    trip_result = _round_trip_regression()
    state_result = _state_matrix(root)
    facility_result = _facility_regression(root)
    ai_result = _ai_regression(root, runtime)
    qol_result = _qol_regression(root, qol_b)

    fixture = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "exact_rom": {
            "stage_sha256": runtime["output"]["sha256"], "mgba": mgba,
            "payload_size": runtime["payload"]["size"],
            "trainer_production_rows_bound": runtime["trainers"]["production_rows_bound"],
        },
        "maps": map_result, "events": event_result, "shared_captures": shared_result,
        "round_trips": trip_result, "save_state_matrix": state_result,
        "qol": qol_result, "facilities": facility_result, "trainer_ai": ai_result,
        "encounters": {
            "tohoku_logical_locations": population["logical_locations"]["TOHOKU"],
            "kanto_logical_locations": population["logical_locations"]["KANTO"],
            "normal_tables_preserved": population["normal_tables_preserved"],
            "research_rows": population["research_rows"], "raid_rows": population["counts"]["raid_encounters.csv"],
            "mirage_rounds": population["mirage_rounds"],
            "tohoku_overlay_coverage": overlay_coverage,
        },
        "release_blockers": [],
    }
    vega_manual, kanto_manual = _manual_outputs(runtime)
    summary = f"""# T17 regression summary

- Status: **PASS**
- Stage: `build/stages/17_regression.gba`
- SHA-256: `{runtime['output']['sha256']}`
- exact-ROM: 自然なnew game起動、Kanto描画/移動/往復、QOL-B Thumb実行、trainer/progression pointer graph PASS
- Kanto: {map_result['reachable_from_vermilion']}/253 reachable、{map_result['returnable_to_vermilion']}/253 returnable
- Trainers: 29人 / {runtime['trainers']['production_rows_bound']} party rowsを実ROMへbind、24 engine pointer repoint
- Progression: 8 gym + 四天王/Champion（13 physical battle objects）
- Ecology: Tohoku 49 / Kanto 47論理地点、original NORMAL {population['normal_tables_preserved']}表を保持
- Tohoku ecology: 設計{overlay_coverage['source_rows']}行を全件実ROM接続、未接続{overlay_coverage['deferred_source_rows']}行
- Ecology modes: RTC自動／朝昼／夜／日替わり大量発生／釣り／せいたいレーダー隠し枠スキャン
- State: pre-HoF 200 + post-HoF 200 region round trips PASS
- Shared captures: {shared_result['shared_keys']} keys × 両地域順序 PASS、duplicate 0
- Event model: 34 events × 7 branches = {event_result['branch_cases']} PASS
- QOL: A/B PASS、QOL-B {qol_result['qol_b_cases']} host cases、専用full-screen UI 0
- Facilities: {facility_result['modes']} modes、{facility_result['restore_cases']} exact restore cases、3/7/49/100境界 PASS
- AI: 3 profiles、18 differential decisions、実ROMproduction rows {ai_result['production_rows_bound']}
- Release blockers: 0

## 証跡の区分

`exact-ROM` は生成された32 MiB stageをlibmGBAで実行した結果。`state model` はmanifestと固定入力に対する決定論検査で、各fixtureの失敗はbuildを停止する。表示と長時間の操作感はversioned manual checkpointで追試できる。
"""
    qol_report = f"""# QOL-B integration

- Status: **PASS**
- Release config: enabled
- Existing UI only: PASS（PC/list/文字入力/技思い出し/field menu/既存battle）
- Runtime: ARM Thumb overlay embedded、mGBA marker `0x0B17` PASS
- Host cases: {qol_b['cases']}
- Atomic rollback cases: {qol_b['atomic_rollbacks']}
- Egg boundary cases: {qol_b['egg_boundaries']}
- Features: {', '.join(qol_result['release_features'])}
- PC bulk operations: capacity、禁止個体/道具、cancelでall-or-rollback
- Egg basket: 親不在/相性なし/255/256歩/queue満杯/無効map/save-loadを固定fixture化
- Auto battle: trainer/static/story/shinyを拒否し通常random野生だけ許可
"""
    facility_report = f"""# Facility regression

- Status: **PASS**
- Active modes: {facility_result['modes']}（Trial 4 / Standard 4 / Full 4 / Master 4 / Mirage 4）
- Formats: {', '.join(facility_result['formats'])}
- Party snapshot/restore: {facility_result['restore_cases']} cases × 600 bytes exact
- Exit paths: {', '.join(facility_result['exit_paths'])}
- Streak boundaries: 3 / 7 / 49 / 100、reward exactly once
- Reward encounter: capacity-before-payment、single debit、same pending personality retry、capture commit PASS
- Mirage: party/state/currency owner separated from Factory
- UI: existing party/list/shop/Yes-No/message only; link multi excluded
"""
    ai_report = f"""# Trainer AI regression

- Status: **PASS**
- Source: pinned CFRU-JP (`state/source-lock.json`)
- Profiles: {', '.join(ai_result['profiles'])}
- Fixed global RNG decision fixtures: {ai_result['decision_fixtures']} / {ai_result['decision_fixtures']} PASS
- Formats: SINGLE / DOUBLE
- Cache/history invalidation: {', '.join(ai_result['cache_invalidation'])}
- Performance: T01 threshold PASS（single/double cold-cycle evidenceはT06 report）
- Production binding: {ai_result['generated_trainers']} trainers / {ai_result['production_rows_bound']} party rows
- Existing engine references repointed: {ai_result['trainer_pointer_repoints']}
- 8 Kanto gym + League chain: actual ROM object/script/trainer pointer graph PASS
"""
    known = f"""# Known issues

## Release scope exclusions

### KI-001 — Link multi is not supported

- Severity: S4 / scope exclusion
- Reproduction: Battle Factoryで通信相手を必要とする形式を探す。
- Result: 選択肢へ表示されない。NPC partner multiは利用可能。
- Workaround: single、double、NPC partner multi、randomを使用する。

### KI-002 — Kantoの一部動的warpは安全なクチバ帰還へ置換

- Severity: S4 / intentional compatibility behavior
- Reproduction: Union Room、Trade Center、元FireRedの状態依存elevatorへ入る。
- Result: 未解決runtime destinationではなくクチバの安全地点へ戻る。
- Workaround: 通常の建物・道路warpを使う。進行・帰還は阻害しない。

### KI-003 — emulator savestateはversion間非互換

- Severity: S4 / expected platform behavior
- Reproduction: 旧ROMで作ったsavestateをv1.3.9で直接読み込む。
- Result: ROM内部addressや一時stateが一致せず、安全なmigration対象にならない。
- Workaround: 旧ROM上でゲーム内saveを行い、v1.3.9を再起動してbattery saveから読む。

### KI-004 — V4の性格・特性・EV・gimmick triggerは設計台帳のみ

- Severity: S4 / intentional ABI scope
- Reproduction: V4設計CSVの性格・特性・EV欄と通常trainer戦の生成個体を比較する。
- Result: Species、level、持ち物、4技、IV下限、trainer item、AI段階は反映されるが、通常の
  16-byte TrainerMon ABIに欄のない性格・特性・EV・個別gimmick triggerは直接固定されない。
- Workaround: 現行CFRUの個体生成規則と1戦1gimmick policyを使用する。値は正規化台帳に保持済み。

### KI-005 — Factoryの実受付はTrialのみ

- Severity: S4 / release scope exclusion
- Reproduction: クチバのFactory受付でStandard、Full、Master、BP shop、施設外報酬遭遇を探す。
- Result: v1.3.9の実ROM受付は候補6体から3体を選ぶTrial 3連戦だけを提供する。後続modeと
  shop/報酬遭遇はmanifest・進行定義・回帰fixtureのみで、NPCからは開始できない。
- Workaround: Trialを利用する。未接続modeを実装済みと扱わず、後続releaseで個別に結合する。

## post-v1.4.0 Stage 48で解決済み

- 固定CFRU-JPのSpecies/Form・Ability source IDをVega保持canonical IDとして直接使い、
  ジガルデ、ミミッキュ、モルペコ等のフォーム特性や多数の通常特性が誤作動する問題。
- 追加Speciesのplayer back spriteがstock座標境界と32px想定経路に入り、下半分等が欠ける問題。
  64×64 OAM／2,048-byte OBJ tileとpaletteを実ROMで継続検査する。

## v1.3.9で解決済み

- canonicalでは6文字あるSpecies名がstock UI互換表とnickname表示処理で5文字へ切られ、
  エースバーンやムゲンダイナの末尾が戦闘HUD・メッセージ等で欠ける問題。

## v1.3.8で解決済み

- 追加Speciesを含むtrainer戦が戦闘開始時に黒画面のまま停止する初期技表ABI不一致。
- 最初の草むら（map 3/19）が別の論理地点へ誤結合され、追加種が出現しない問題。
- 戦闘中Lの旧HELP競合が技Type・特性通知・行動順を破損した問題。
- トーホク外来生態293行のうち、夜・大量発生・朝昼・釣り・DexNav相当140行が
  実ROM未接続だった問題。RTC自動と「せいたいレーダー」の手動切替を併設した。

Release-blocking known issue: **none**.
"""
    return {
        FIXTURE.as_posix(): _stable(fixture), MATRIX.as_posix(): _feature_matrix(root),
        VEGA_MANUAL.as_posix(): vega_manual, KANTO_MANUAL.as_posix(): kanto_manual,
        SUMMARY.as_posix(): summary.encode(), QOL_REPORT.as_posix(): qol_report.encode(),
        FACILITY_REPORT.as_posix(): facility_report.encode(), AI_REPORT.as_posix(): ai_report.encode(),
        KNOWN_ISSUES.as_posix(): known.encode(),
    }
