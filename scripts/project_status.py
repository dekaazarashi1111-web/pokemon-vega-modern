from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

try:  # ``python scripts/project_status.py`` と package import の両方を支える。
    from .common import repo_root
    from .taskctl import (
        TaskQueueError,
        collect_consistency_errors,
        load_graph,
        load_mirror,
        parse_task_queue,
    )
except ImportError:  # pragma: no cover - 実行方法で分岐するだけ
    from common import repo_root
    from taskctl import (
        TaskQueueError,
        collect_consistency_errors,
        load_graph,
        load_mirror,
        parse_task_queue,
    )


STATUSES = ("PENDING", "IN_PROGRESS", "DONE", "BLOCKED")


def _mirror_summaries(path: Path) -> dict[str, str]:
    try:
        mirror, _ = load_mirror(path)
    except TaskQueueError:
        return {}
    tasks = mirror.get("tasks")
    if not isinstance(tasks, Mapping):
        return {}
    summaries: dict[str, str] = {}
    for task_id, item in tasks.items():
        if isinstance(item, Mapping) and isinstance(item.get("summary"), str):
            summaries[str(task_id)] = item["summary"]
    return summaries


def status_lines(root: Path) -> list[str]:
    """表示内容を組み立てる。状態値は必ずtasks_next.mdから取得する。"""

    graph = load_graph(root / "tasks/task_graph.json")
    _, entries = parse_task_queue(root / "design/tasks_next.md")
    summaries = _mirror_summaries(root / "state/task_status.json")
    graph_ids = {str(task["id"]) for task in graph}

    counts = {status: 0 for status in STATUSES}
    for entry in entries:
        counts[entry.status] = counts.get(entry.status, 0) + 1

    lines = [" ".join(f"{key}={value}" for key, value in counts.items())]
    for entry in entries:
        if entry.status not in {"IN_PROGRESS", "BLOCKED"}:
            continue
        summary = summaries.get(entry.task_id, "") if entry.task_id in graph_ids else ""
        suffix = f": {summary}" if summary else ""
        lines.append(f"{entry.task_id} {entry.status}{suffix}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="プロジェクトのタスク状態を表示する")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = repo_root()

    try:
        for line in status_lines(root):
            print(line)
    except TaskQueueError as exc:
        print(f"ERROR: {exc}")
        return 1 if args.check else 0

    errors = collect_consistency_errors(root)
    if errors:
        label = "ERROR" if args.check else "WARNING"
        for error in errors:
            print(f"{label}: {error}")
        if args.check:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
