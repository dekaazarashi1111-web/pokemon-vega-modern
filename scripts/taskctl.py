from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:  # ``python scripts/taskctl.py`` と package import の両方を支える。
    from .common import repo_root
except ImportError:  # pragma: no cover - 実行方法で分岐するだけ
    from common import repo_root


VALID = {"PENDING", "IN_PROGRESS", "DONE", "BLOCKED"}
MARKER_TO_STATUS = {
    " ": "PENDING",
    ">": "IN_PROGRESS",
    "x": "DONE",
    "!": "BLOCKED",
}
STATUS_TO_MARKER = {status: marker for marker, status in MARKER_TO_STATUS.items()}

# The marker itself is captured separately so that an update can replace exactly
# one character without reformatting the Markdown file or changing line endings.
TASK_LINE_RE = re.compile(
    r"^[ \t]*-[ \t]*\[(?P<marker>[ >x!])\]"
    r"(?P<body>[^\r\n]*?)"
    r"<!--[ \t]*id[ \t]*:[ \t]*(?P<id>[^\s>]+)[ \t]*-->"
    r"[^\r\n]*\r?$",
    re.MULTILINE,
)
AUXILIARY_ID_RE = re.compile(r"^(?:USER|INIT)(?:[-_:].+)?$")
TASK_HEADER_RE = re.compile(r"^#[ \t]+(?P<id>T\d+)[ \t]+—[ \t]+(?P<title>.+?)\r?$", re.MULTILINE)
TASK_LANE_RE = re.compile(r"^-[ \t]+Lane:[ \t]+`(?P<lane>[^`]+)`[ \t]*\r?$", re.MULTILINE)
TASK_DEPENDS_RE = re.compile(
    r"^-[ \t]+Depends on:[ \t]+`(?P<depends>[^`]+)`[ \t]*\r?$", re.MULTILINE
)
INDEX_ROW_RE = re.compile(
    r"^\| \[(?P<id>T\d+)\]\((?P<file>[^)]+)\) \| (?P<title>.*?) \| "
    r"(?P<lane>.*?) \| (?P<depends>.*?) \|\r?$",
    re.MULTILINE,
)
MASTER_TASK_ROW_RE = re.compile(
    r"^\| (?P<id>T\d+) \| .*? \| .*? \| (?P<depends>.*?) \| .*? \|\r?$",
    re.MULTILINE,
)


class TaskQueueError(RuntimeError):
    """タスクキューを安全に操作できない場合のエラー。"""


@dataclass(frozen=True)
class QueueEntry:
    task_id: str
    status: str
    marker: str
    line_number: int
    marker_offset: int


def _read_utf8_exact(path: Path) -> str:
    """改行を変換せずUTF-8テキストを読む。"""

    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError as exc:
        raise TaskQueueError(f"ファイルがありません: {path}") from exc
    except UnicodeDecodeError as exc:
        raise TaskQueueError(f"UTF-8として読めません: {path}") from exc


def parse_task_queue_text(text: str) -> list[QueueEntry]:
    """tasks_next.md のチェックリスト行を出現順に解析する純関数。"""

    entries: list[QueueEntry] = []
    for match in TASK_LINE_RE.finditer(text):
        marker = match.group("marker")
        entries.append(
            QueueEntry(
                task_id=match.group("id"),
                status=MARKER_TO_STATUS[marker],
                marker=marker,
                line_number=text.count("\n", 0, match.start()) + 1,
                marker_offset=match.start("marker"),
            )
        )
    return entries


def parse_task_queue(path: Path) -> tuple[str, list[QueueEntry]]:
    text = _read_utf8_exact(path)
    return text, parse_task_queue_text(text)


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _entries_by_id(entries: Sequence[QueueEntry]) -> dict[str, QueueEntry]:
    duplicates = _duplicate_values([entry.task_id for entry in entries])
    if duplicates:
        raise TaskQueueError(f"tasks_next.md のIDが重複しています: {', '.join(duplicates)}")
    return {entry.task_id: entry for entry in entries}


def is_auxiliary_task_id(task_id: str) -> bool:
    """グラフ外で許可する直接作業用IDかを返す。"""

    return bool(AUXILIARY_ID_RE.fullmatch(task_id))


def load_graph(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(_read_utf8_exact(path))
    except json.JSONDecodeError as exc:
        raise TaskQueueError(f"JSONが不正です: {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise TaskQueueError(f"tasks配列がありません: {path}")

    tasks: list[dict[str, Any]] = []
    for index, raw_task in enumerate(data["tasks"]):
        if not isinstance(raw_task, dict):
            raise TaskQueueError(f"task_graph.json の tasks[{index}] がオブジェクトではありません")
        task_id = raw_task.get("id")
        dependencies = raw_task.get("depends_on")
        if not isinstance(task_id, str) or not task_id:
            raise TaskQueueError(f"task_graph.json の tasks[{index}].id が不正です")
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) and dependency for dependency in dependencies
        ):
            raise TaskQueueError(f"{task_id}: depends_on はID文字列の配列である必要があります")
        for key in ("title", "lane", "file"):
            if not isinstance(raw_task.get(key), str) or not raw_task[key]:
                raise TaskQueueError(f"{task_id}: {key} がありません")
        tasks.append(dict(raw_task))
    return tasks


def task_file_metadata(path: Path) -> dict[str, Any]:
    """T*.mdの先頭metadataを読み、DAGとのdrift検査用に正規化する。"""

    text = _read_utf8_exact(path)
    header = TASK_HEADER_RE.search(text)
    lane = TASK_LANE_RE.search(text)
    depends = TASK_DEPENDS_RE.search(text)
    missing = [
        label
        for label, match in (("header", header), ("Lane", lane), ("Depends on", depends))
        if match is None
    ]
    if missing:
        raise TaskQueueError(f"{path}: task metadataがありません: {', '.join(missing)}")
    assert header is not None and lane is not None and depends is not None
    raw_dependencies = depends.group("depends").strip()
    dependencies = (
        []
        if raw_dependencies.lower() == "none"
        else [item.strip() for item in raw_dependencies.split(",") if item.strip()]
    )
    return {
        "id": header.group("id").strip(),
        "title": header.group("title").strip(),
        "lane": lane.group("lane").strip(),
        "depends_on": dependencies,
    }


def _dependency_cell(cell: str) -> list[str]:
    value = cell.strip()
    if value.lower() in {"", "-", "—", "none"}:
        return []
    result: list[str] = []
    for item in (part.strip() for part in value.split(",")):
        range_match = re.fullmatch(r"T(?P<start>\d+)[–-]T(?P<end>\d+)", item)
        if range_match:
            start = int(range_match.group("start"))
            end = int(range_match.group("end"))
            width = max(len(range_match.group("start")), len(range_match.group("end")))
            result.extend(f"T{number:0{width}d}" for number in range(start, end + 1))
        elif item:
            result.append(item)
    return result


def plan_view_errors(graph: Sequence[Mapping[str, Any]], root: Path) -> list[str]:
    """DAGの手動表示であるINDEXとMASTER_PLANのdriftを検出する。"""

    errors: list[str] = []
    graph_ids = [str(task["id"]) for task in graph]
    index_path = root / "tasks/INDEX.md"
    if index_path.exists():
        rows = [match.groupdict() for match in INDEX_ROW_RE.finditer(_read_utf8_exact(index_path))]
        if [row["id"] for row in rows] != graph_ids:
            errors.append("tasks/INDEX.md のタスク順またはIDがtask_graph.jsonと不一致です")
        row_by_id = {row["id"]: row for row in rows}
        for task in graph:
            task_id = str(task["id"])
            row = row_by_id.get(task_id)
            if row is None:
                continue
            expected = {
                "file": Path(str(task["file"])).name,
                "title": str(task["title"]),
                "lane": str(task["lane"]),
                "depends": sorted(task["depends_on"]),
            }
            actual = {
                "file": row["file"].strip(),
                "title": row["title"].strip(),
                "lane": row["lane"].strip(),
                "depends": sorted(_dependency_cell(row["depends"])),
            }
            for key in expected:
                if actual[key] != expected[key]:
                    errors.append(
                        f"{task_id}: tasks/INDEX.md の {key} がtask_graph.jsonと不一致です: "
                        f"graph={expected[key]!r} index={actual[key]!r}"
                    )

    master_path = root / "MASTER_PLAN.md"
    if master_path.exists():
        rows = [
            match.groupdict()
            for match in MASTER_TASK_ROW_RE.finditer(_read_utf8_exact(master_path))
        ]
        if [row["id"] for row in rows] != graph_ids:
            errors.append("MASTER_PLAN.md のタスク順またはIDがtask_graph.jsonと不一致です")
        row_by_id = {row["id"]: row for row in rows}
        for task in graph:
            task_id = str(task["id"])
            row = row_by_id.get(task_id)
            if row is None:
                continue
            dependencies = sorted(_dependency_cell(row["depends"]))
            graph_dependencies = sorted(task["depends_on"])
            if dependencies != graph_dependencies:
                errors.append(
                    f"{task_id}: MASTER_PLAN.md の依存がtask_graph.jsonと不一致です: "
                    f"graph={graph_dependencies!r} master={dependencies!r}"
                )
    return errors


def graph_by_id(graph: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    duplicates = _duplicate_values([str(task["id"]) for task in graph])
    if duplicates:
        raise TaskQueueError(f"task_graph.json のIDが重複しています: {', '.join(duplicates)}")
    return {str(task["id"]): task for task in graph}


def topological_tasks(graph: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """JSON内の順序を同順位の安定順として、DAGのトポロジカル順を返す。"""

    by_id = graph_by_id(graph)
    order_index = {str(task["id"]): index for index, task in enumerate(graph)}
    dependencies: dict[str, set[str]] = {}
    dependents: dict[str, list[str]] = {task_id: [] for task_id in by_id}

    for task in graph:
        task_id = str(task["id"])
        task_dependencies = set(task["depends_on"])
        unknown = sorted(task_dependencies - by_id.keys())
        if unknown:
            raise TaskQueueError(f"{task_id}: 未知の依存先です: {', '.join(unknown)}")
        dependencies[task_id] = task_dependencies
        for dependency in task_dependencies:
            dependents[dependency].append(task_id)

    ready_ids = sorted(
        (task_id for task_id, deps in dependencies.items() if not deps),
        key=order_index.__getitem__,
    )
    result: list[Mapping[str, Any]] = []
    while ready_ids:
        task_id = ready_ids.pop(0)
        result.append(by_id[task_id])
        for dependent in sorted(dependents[task_id], key=order_index.__getitem__):
            dependencies[dependent].discard(task_id)
            if not dependencies[dependent] and dependent not in ready_ids:
                ready_ids.append(dependent)
        ready_ids.sort(key=order_index.__getitem__)

    if len(result) != len(graph):
        cyclic = sorted(
            (task_id for task_id, deps in dependencies.items() if deps),
            key=order_index.__getitem__,
        )
        raise TaskQueueError(f"task_graph.json に循環依存があります: {', '.join(cyclic)}")
    return result


def _status_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        status = value.get("status")
        return status if isinstance(status, str) else None
    return None


def ready(
    graph: Sequence[Mapping[str, Any]],
    status: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """依存がすべてDONEのPENDINGタスクをDAG順で返す。

    旧APIとの互換性のため、status は ``{"tasks": ...}`` とIDマップの
    どちらも受け付ける。
    """

    raw_statuses = status.get("tasks", status)
    if not isinstance(raw_statuses, Mapping):
        raise TaskQueueError("タスク状態マップが不正です")

    statuses = {str(task_id): _status_value(value) for task_id, value in raw_statuses.items()}
    result: list[Mapping[str, Any]] = []
    for task in topological_tasks(graph):
        task_id = str(task["id"])
        if statuses.get(task_id) != "PENDING":
            continue
        if all(statuses.get(str(dependency)) == "DONE" for dependency in task["depends_on"]):
            result.append(task)
    return result


def execution_waves(
    graph: Sequence[Mapping[str, Any]],
) -> list[list[Mapping[str, Any]]]:
    """依存段数から並列準備可能なwaveを導出する。"""

    wave_by_id: dict[str, int] = {}
    waves: list[list[Mapping[str, Any]]] = []
    for task in topological_tasks(graph):
        dependencies = [str(dependency) for dependency in task["depends_on"]]
        wave = 0 if not dependencies else max(wave_by_id[item] for item in dependencies) + 1
        task_id = str(task["id"])
        wave_by_id[task_id] = wave
        while len(waves) <= wave:
            waves.append([])
        waves[wave].append(task)
    return waves


def longest_dependency_chain(
    graph: Sequence[Mapping[str, Any]],
) -> list[str]:
    """DAG上で最長の依存鎖を安定順で1本返す。期間見積りではない。"""

    chains: dict[str, list[str]] = {}
    for task in topological_tasks(graph):
        task_id = str(task["id"])
        dependencies = [str(dependency) for dependency in task["depends_on"]]
        if not dependencies:
            chains[task_id] = [task_id]
            continue
        predecessor = max(dependencies, key=lambda item: len(chains[item]))
        chains[task_id] = chains[predecessor] + [task_id]
    return max(chains.values(), key=len, default=[])


def next_task_lines(
    graph: Sequence[Mapping[str, Any]], entries: Sequence[QueueEntry]
) -> list[str]:
    """再開対象、推奨PRIMARY、その他の依存READY候補を表示する。"""

    entry_by_id = _entries_by_id(entries)
    graph_index = graph_by_id(graph)
    status_map = {task_id: entry.status for task_id, entry in entry_by_id.items()}
    ready_tasks = ready(graph, status_map)
    in_progress = [entry for entry in entries if entry.status == "IN_PROGRESS"]
    if len(in_progress) > 1:
        raise TaskQueueError(
            "IN_PROGRESSは最大1件です: "
            + ", ".join(entry.task_id for entry in in_progress)
        )

    lines: list[str] = []
    if in_progress:
        active_id = in_progress[0].task_id
        active = graph_index.get(active_id)
        if active is None:
            lines.append(f"RESUME {active_id} [auxiliary]")
        else:
            lines.append(
                f"RESUME {active_id} [{active['lane']}] {active['title']} -> {active['file']}"
            )

    for index, task in enumerate(ready_tasks):
        current_label = "PARALLEL_PREP" if in_progress or index > 0 else "PRIMARY"
        lines.append(
            f"{current_label} {task['id']} [{task['lane']}] "
            f"{task['title']} -> {task['file']}"
        )
    return lines


def _load_json_detecting_duplicate_keys(path: Path) -> tuple[Any, list[str]]:
    duplicate_keys: list[str] = []

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicate_keys.append(key)
            result[key] = value
        return result

    try:
        data = json.loads(_read_utf8_exact(path), object_pairs_hook=pairs_hook)
    except json.JSONDecodeError as exc:
        raise TaskQueueError(f"JSONが不正です: {path}: {exc}") from exc
    return data, duplicate_keys


def load_mirror(path: Path) -> tuple[dict[str, Any], list[str]]:
    data, duplicate_keys = _load_json_detecting_duplicate_keys(path)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), dict):
        raise TaskQueueError(f"tasksオブジェクトがありません: {path}")
    return data, duplicate_keys


def _cycle_errors(graph: Sequence[Mapping[str, Any]]) -> list[str]:
    try:
        topological_tasks(graph)
    except TaskQueueError as exc:
        return [str(exc)]
    return []


def consistency_errors(
    graph: Sequence[Mapping[str, Any]],
    entries: Sequence[QueueEntry],
    mirror: Mapping[str, Any] | None = None,
    *,
    mirror_duplicate_keys: Sequence[str] = (),
    root: Path | None = None,
    check_task_files: bool = False,
) -> list[str]:
    """グラフ、キュー、互換ミラー間の不整合を列挙する純関数。"""

    errors: list[str] = []
    graph_ids_in_order = [str(task["id"]) for task in graph]
    graph_duplicates = _duplicate_values(graph_ids_in_order)
    for task_id in graph_duplicates:
        errors.append(f"task_graph.json のIDが重複しています: {task_id}")
    graph_ids = set(graph_ids_in_order)

    queue_ids_in_order = [entry.task_id for entry in entries]
    queue_duplicates = _duplicate_values(queue_ids_in_order)
    for task_id in queue_duplicates:
        errors.append(f"tasks_next.md のIDが重複しています: {task_id}")
    queue_ids = set(queue_ids_in_order)

    for task_id in sorted(graph_ids - queue_ids):
        errors.append(f"tasks_next.md にグラフタスクがありません: {task_id}")
    for task_id in sorted(queue_ids - graph_ids):
        if not is_auxiliary_task_id(task_id):
            errors.append(f"task_graph.json にないタスクIDです: {task_id}")
    queue_graph_order = [task_id for task_id in queue_ids_in_order if task_id in graph_ids]
    if (
        not graph_duplicates
        and not queue_duplicates
        and set(queue_graph_order) == graph_ids
        and queue_graph_order != graph_ids_in_order
    ):
        errors.append(
            "tasks_next.md と task_graph.json のタスク順が不一致です: "
            + " -> ".join(queue_graph_order)
        )

    if not graph_duplicates:
        errors.extend(_cycle_errors(graph))
        try:
            topological_order = [str(task["id"]) for task in topological_tasks(graph)]
        except TaskQueueError:
            topological_order = []
        if topological_order and topological_order != graph_ids_in_order:
            errors.append(
                "task_graph.json の配列順が依存順ではありません: "
                + " -> ".join(graph_ids_in_order)
            )
        by_id = {str(task["id"]): task for task in graph}
        for task in graph:
            task_id = str(task["id"])
            dependencies = list(task["depends_on"])
            for dependency in _duplicate_values(dependencies):
                errors.append(f"{task_id}: 依存先が重複しています: {dependency}")
            for dependency in dependencies:
                if dependency not in by_id:
                    errors.append(f"{task_id}: 未知の依存先です: {dependency}")
            if check_task_files and root is not None:
                task_file = root / str(task["file"])
                if not task_file.exists():
                    errors.append(f"{task_id}: タスクファイルがありません: {task['file']}")
                    continue
                try:
                    metadata = task_file_metadata(task_file)
                except TaskQueueError as exc:
                    errors.append(str(exc))
                    continue
                for key in ("id", "title", "lane", "depends_on"):
                    if metadata[key] != task[key]:
                        errors.append(
                            f"{task_id}: task_graph.json と {task['file']} の {key} が不一致です: "
                            f"graph={task[key]!r} file={metadata[key]!r}"
                        )

    in_progress = [entry.task_id for entry in entries if entry.status == "IN_PROGRESS"]
    if len(in_progress) > 1:
        errors.append(
            "IN_PROGRESSは最大1件です: " + ", ".join(in_progress)
        )

    if not queue_duplicates and not graph_duplicates:
        entry_by_id = {entry.task_id: entry for entry in entries}
        task_by_id = {str(task["id"]): task for task in graph}
        for task_id in graph_ids & queue_ids:
            entry = entry_by_id[task_id]
            if entry.status == "PENDING":
                continue
            missing_done = [
                dependency
                for dependency in task_by_id[task_id]["depends_on"]
                if dependency not in entry_by_id
                or entry_by_id[dependency].status != "DONE"
            ]
            if missing_done:
                errors.append(
                    f"{task_id}: {entry.status} ですが未完了の依存先があります: "
                    + ", ".join(missing_done)
                )

    if mirror is not None:
        for key in sorted(set(mirror_duplicate_keys)):
            errors.append(f"state/task_status.json のJSONキーが重複しています: {key}")
        mirror_tasks = mirror.get("tasks")
        if not isinstance(mirror_tasks, Mapping):
            errors.append("state/task_status.json にtasksオブジェクトがありません")
        else:
            mirror_ids = {str(task_id) for task_id in mirror_tasks}
            for task_id in sorted(graph_ids - mirror_ids):
                errors.append(f"state/task_status.json にタスクがありません: {task_id}")
            for task_id in sorted(mirror_ids - graph_ids):
                errors.append(f"state/task_status.json に余分なタスクがあります: {task_id}")
            if not queue_duplicates:
                entry_by_id = {entry.task_id: entry for entry in entries}
                for task_id in sorted(graph_ids & queue_ids & mirror_ids):
                    mirror_status = _status_value(mirror_tasks[task_id])
                    if mirror_status not in VALID:
                        errors.append(
                            f"state/task_status.json の状態が不正です: "
                            f"{task_id}={mirror_status!r}"
                        )
                    elif mirror_status != entry_by_id[task_id].status:
                        errors.append(
                            f"状態drift: {task_id} tasks_next={entry_by_id[task_id].status} "
                            f"mirror={mirror_status}"
                        )
    return errors


def collect_consistency_errors(root: Path, *, check_task_files: bool = False) -> list[str]:
    """実ファイルを読み、不整合を日本語メッセージで返す。"""

    errors: list[str] = []
    try:
        graph = load_graph(root / "tasks/task_graph.json")
    except TaskQueueError as exc:
        return [str(exc)]
    try:
        _, entries = parse_task_queue(root / "design/tasks_next.md")
    except TaskQueueError as exc:
        return [str(exc)]
    try:
        mirror, duplicate_keys = load_mirror(root / "state/task_status.json")
    except TaskQueueError as exc:
        errors.append(str(exc))
        mirror = None
        duplicate_keys = []

    errors.extend(
        consistency_errors(
            graph,
            entries,
            mirror,
            mirror_duplicate_keys=duplicate_keys,
            root=root,
            check_task_files=check_task_files,
        )
    )
    if check_task_files:
        errors.extend(plan_view_errors(graph, root))
    return errors


def _core_model(
    root: Path,
) -> tuple[list[dict[str, Any]], str, list[QueueEntry], dict[str, QueueEntry]]:
    graph = load_graph(root / "tasks/task_graph.json")
    # This verifies duplicate IDs, unknown dependencies and cycles before mutation.
    topological_order = [str(task["id"]) for task in topological_tasks(graph)]
    graph_ids_in_order = [str(task["id"]) for task in graph]
    if topological_order != graph_ids_in_order:
        raise TaskQueueError(
            "task_graph.json の配列順が依存順ではありません: "
            + " -> ".join(graph_ids_in_order)
        )
    for task in graph:
        duplicated_dependencies = _duplicate_values(list(task["depends_on"]))
        if duplicated_dependencies:
            raise TaskQueueError(
                f"{task['id']}: 依存先が重複しています: "
                + ", ".join(duplicated_dependencies)
            )
    text, entries = parse_task_queue(root / "design/tasks_next.md")
    entry_by_id = _entries_by_id(entries)
    graph_ids = {str(task["id"]) for task in graph}
    missing = sorted(graph_ids - entry_by_id.keys())
    if missing:
        raise TaskQueueError(
            "tasks_next.md にグラフタスクがありません: " + ", ".join(missing)
        )
    invalid_extra = sorted(
        task_id
        for task_id in entry_by_id.keys() - graph_ids
        if not is_auxiliary_task_id(task_id)
    )
    if invalid_extra:
        raise TaskQueueError(
            "task_graph.json にないタスクIDです: " + ", ".join(invalid_extra)
        )
    queue_graph_order = [entry.task_id for entry in entries if entry.task_id in graph_ids]
    if queue_graph_order != graph_ids_in_order:
        raise TaskQueueError(
            "tasks_next.md と task_graph.json のタスク順が不一致です: "
            + " -> ".join(queue_graph_order)
        )
    return graph, text, entries, entry_by_id


def _atomic_write_bytes(path: Path, data: bytes, *, expected: bytes | None = None) -> None:
    """同一ディレクトリの一時ファイルからos.replaceでatomicに更新する。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    if expected is not None:
        try:
            current = path.read_bytes()
        except FileNotFoundError as exc:
            raise TaskQueueError(f"更新直前にファイルが見つかりません: {path}") from exc
        if current != expected:
            raise TaskQueueError(f"別プロセスが更新したため中止しました: {path}")

    mode = path.stat().st_mode & 0o7777 if path.exists() else None
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _replace_status_character(
    path: Path,
    original_text: str,
    entry: QueueEntry,
    new_status: str,
) -> None:
    marker = STATUS_TO_MARKER[new_status]
    offset = entry.marker_offset
    if original_text[offset] != entry.marker:
        raise TaskQueueError(f"{entry.task_id}: 状態文字の位置を確認できません")
    updated_text = original_text[:offset] + marker + original_text[offset + 1 :]
    if len(original_text) != len(updated_text):
        raise TaskQueueError("内部エラー: 状態更新でファイル長が変わりました")
    if original_text[:offset] + original_text[offset + 1 :] != (
        updated_text[:offset] + updated_text[offset + 1 :]
    ):
        raise TaskQueueError("内部エラー: 状態文字以外が変わりました")
    _atomic_write_bytes(
        path,
        updated_text.encode("utf-8"),
        expected=original_text.encode("utf-8"),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _existing_mirror_tasks(path: Path) -> dict[str, Any]:
    try:
        mirror, _ = load_mirror(path)
    except TaskQueueError:
        return {}
    tasks = mirror.get("tasks")
    return dict(tasks) if isinstance(tasks, Mapping) else {}


def build_mirror(
    graph: Sequence[Mapping[str, Any]],
    entries: Sequence[QueueEntry],
    existing_tasks: Mapping[str, Any] | None = None,
    *,
    summary_updates: Mapping[str, str] | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """キュー状態からグラフ管理対象の互換ミラーを構築する純関数。"""

    existing_tasks = existing_tasks or {}
    summary_updates = summary_updates or {}
    timestamp = now or _utc_now()
    entry_by_id = _entries_by_id(entries)
    tasks: dict[str, Any] = {}
    for task in graph:
        task_id = str(task["id"])
        if task_id not in entry_by_id:
            raise TaskQueueError(f"tasks_next.md にグラフタスクがありません: {task_id}")
        new_status = entry_by_id[task_id].status
        old_item = existing_tasks.get(task_id)
        old_item = old_item if isinstance(old_item, Mapping) else {}
        old_status = _status_value(old_item)
        old_summary = old_item.get("summary", "")
        old_updated_at = old_item.get("updated_at", "")
        summary = summary_updates.get(
            task_id, old_summary if isinstance(old_summary, str) else ""
        )
        status_changed = old_status != new_status
        explicitly_updated = task_id in summary_updates
        updated_at = (
            timestamp
            if status_changed or explicitly_updated
            else old_updated_at if isinstance(old_updated_at, str) else ""
        )
        tasks[task_id] = {
            "status": new_status,
            "summary": summary,
            "updated_at": updated_at,
        }
    return {"tasks": tasks}


def sync_mirror(
    root: Path,
    *,
    summary_updates: Mapping[str, str] | None = None,
    now: str | None = None,
) -> int:
    graph, _, entries, _ = _core_model(root)
    mirror_path = root / "state/task_status.json"
    mirror = build_mirror(
        graph,
        entries,
        _existing_mirror_tasks(mirror_path),
        summary_updates=summary_updates,
        now=now,
    )
    encoded = (json.dumps(mirror, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _atomic_write_bytes(mirror_path, encoded)
    return len(graph)


def _descendants(
    graph: Sequence[Mapping[str, Any]], task_id: str
) -> list[str]:
    result: list[str] = []
    discovered = {task_id}
    changed = True
    while changed:
        changed = False
        for task in graph:
            candidate = str(task["id"])
            if candidate in discovered:
                continue
            if any(str(dependency) in discovered for dependency in task["depends_on"]):
                discovered.add(candidate)
                result.append(candidate)
                changed = True
    return result


def transition_task(
    root: Path,
    command: str,
    task_id: str,
    *,
    summary: str = "",
    now: str | None = None,
) -> str:
    """状態遷移を検証し、キュー1文字更新後にミラーを同期する。"""

    if command not in {"start", "done", "block", "reset"}:
        raise TaskQueueError(f"未知の操作です: {command}")
    graph, text, entries, entry_by_id = _core_model(root)
    if task_id not in entry_by_id:
        raise TaskQueueError(f"未知のタスクです: {task_id}")

    entry = entry_by_id[task_id]
    allowed_sources = {
        "start": {"PENDING"},
        "done": {"IN_PROGRESS"},
        "block": {"IN_PROGRESS"},
        "reset": {"IN_PROGRESS", "BLOCKED", "DONE"},
    }
    if entry.status not in allowed_sources[command]:
        expected = ", ".join(sorted(allowed_sources[command]))
        raise TaskQueueError(
            f"{task_id}: {entry.status} から {command} へ遷移できません"
            f"（必要な現在状態: {expected}）"
        )

    graph_index = graph_by_id(graph)
    if command == "start":
        in_progress = [
            other.task_id
            for other in entries
            if other.status == "IN_PROGRESS" and other.task_id != task_id
        ]
        if in_progress:
            raise TaskQueueError(
                f"{task_id}: 開始できません。実行中タスク: {', '.join(in_progress)}"
            )
        if task_id in graph_index:
            incomplete = [
                str(dependency)
                for dependency in graph_index[task_id]["depends_on"]
                if entry_by_id[str(dependency)].status != "DONE"
            ]
            if incomplete:
                raise TaskQueueError(
                    f"{task_id}: 未完了の依存先があります: {', '.join(incomplete)}"
                )

    if command == "reset" and entry.status == "DONE" and task_id in graph_index:
        active_descendants = [
            descendant
            for descendant in _descendants(graph, task_id)
            if entry_by_id[descendant].status != "PENDING"
        ]
        if active_descendants:
            raise TaskQueueError(
                f"{task_id}: 後続タスクを先にresetしてください: "
                + ", ".join(active_descendants)
            )

    new_status = {
        "start": "IN_PROGRESS",
        "done": "DONE",
        "block": "BLOCKED",
        "reset": "PENDING",
    }[command]
    queue_path = root / "design/tasks_next.md"
    _replace_status_character(queue_path, text, entry, new_status)
    try:
        sync_mirror(
            root,
            summary_updates={task_id: summary} if task_id in graph_index else None,
            now=now,
        )
    except Exception as exc:
        raise TaskQueueError(
            "tasks_next.md は更新しましたが、互換ミラーの同期に失敗しました。"
            f"`python3 scripts/taskctl.py sync` を実行してください: {exc}"
        ) from exc
    return new_status


def load(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """旧ヘルパー互換: 状態はmirrorではなくtasks_nextから組み立てる。"""

    graph, _, entries, entry_by_id = _core_model(root)
    existing = _existing_mirror_tasks(root / "state/task_status.json")
    tasks: dict[str, Any] = {}
    for task in graph:
        task_id = str(task["id"])
        old_item = existing.get(task_id)
        old_item = old_item if isinstance(old_item, Mapping) else {}
        tasks[task_id] = {
            "status": entry_by_id[task_id].status,
            "summary": old_item.get("summary", ""),
            "updated_at": old_item.get("updated_at", ""),
        }
    return graph, {"tasks": tasks}


def _print_list(
    graph: Sequence[Mapping[str, Any]], entries: Sequence[QueueEntry]
) -> None:
    entry_by_id = _entries_by_id(entries)
    graph_ids = {str(task["id"]) for task in graph}
    for task in graph:
        task_id = str(task["id"])
        print(
            f"{task_id} {entry_by_id[task_id].status:<11} "
            f"{str(task['lane']):<8} {task['title']}"
        )
    for entry in entries:
        if entry.task_id not in graph_ids:
            print(f"{entry.task_id} {entry.status:<11} auxiliary")


def _print_plan(
    graph: Sequence[Mapping[str, Any]], entries: Sequence[QueueEntry]
) -> None:
    lines = next_task_lines(graph, entries)
    print("現在の実行対象:")
    if lines:
        for line in lines:
            print(f"  {line}")
    else:
        print("  完了または開始可能タスクなし")

    entry_by_id = _entries_by_id(entries)
    print("並列準備wave（同じwaveは論理上並列、正本IN_PROGRESSは1件）:")
    for index, wave in enumerate(execution_waves(graph)):
        tasks = ", ".join(
            f"{task['id']}({entry_by_id[str(task['id'])].status})" for task in wave
        )
        print(f"  W{index}: {tasks}")
    print(
        "既定優先順（依存READYなら変更可）: "
        + " -> ".join(
            str(task["id"])
            for task in graph
            if entry_by_id[str(task["id"])].status != "DONE"
        )
    )
    chain = longest_dependency_chain(graph)
    print("最長依存鎖（期間見積りではない）: " + " -> ".join(chain))


def main() -> int:
    parser = argparse.ArgumentParser(description="tasks_next.md 正本のタスク状態管理")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("next")
    sub.add_parser("plan")
    sub.add_parser("sync")
    for name in ("start", "done", "block", "reset"):
        command_parser = sub.add_parser(name)
        command_parser.add_argument("task")
        command_parser.add_argument("--summary", default="")
    args = parser.parse_args()
    root = repo_root()

    try:
        if args.cmd == "sync":
            count = sync_mirror(root)
            print(f"互換ミラーを同期しました: {count}件")
            return 0

        graph, _, entries, entry_by_id = _core_model(root)
        if args.cmd == "list":
            _print_list(graph, entries)
            return 0
        if args.cmd == "next":
            lines = next_task_lines(graph, entries)
            if not lines:
                print("準備完了タスクはありません")
                return 0
            for line in lines:
                print(line)
            return 0
        if args.cmd == "plan":
            _print_plan(graph, entries)
            return 0

        new_status = transition_task(
            root,
            args.cmd,
            args.task,
            summary=args.summary,
        )
        print(f"{args.task}: {new_status}")
        return 0
    except TaskQueueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
