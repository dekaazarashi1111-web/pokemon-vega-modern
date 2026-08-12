import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import project_status  # noqa: E402
import taskctl  # noqa: E402


def graph_task(task_id, dependencies=()):
    return {
        "id": task_id,
        "title": f"Task {task_id}",
        "lane": "test",
        "depends_on": list(dependencies),
        "file": f"tasks/{task_id}.md",
    }


class TemporaryTaskRepo:
    def __init__(self, test_case, queue_text, graph=None, mirror=None):
        self._temporary = tempfile.TemporaryDirectory()
        test_case.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)
        self.graph = graph or [graph_task("T00"), graph_task("T01", ["T00"])]

        (self.root / "design").mkdir(parents=True)
        (self.root / "tasks").mkdir(parents=True)
        (self.root / "state").mkdir(parents=True)
        (self.root / "design/tasks_next.md").write_bytes(queue_text.encode("utf-8"))
        (self.root / "tasks/task_graph.json").write_text(
            json.dumps({"tasks": self.graph}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for task in self.graph:
            dependencies = ", ".join(task["depends_on"]) or "none"
            (self.root / task["file"]).write_text(
                f"# {task['id']} — {task['title']}\n\n"
                f"- Lane: `{task['lane']}`\n"
                f"- Depends on: `{dependencies}`\n",
                encoding="utf-8",
            )

        if mirror is None:
            _, entries = taskctl.parse_task_queue(self.root / "design/tasks_next.md")
            entry_by_id = {entry.task_id: entry for entry in entries}
            mirror = {
                "tasks": {
                    task["id"]: {
                        "status": entry_by_id[task["id"]].status,
                        "summary": "",
                        "updated_at": "",
                    }
                    for task in self.graph
                }
            }
        (self.root / "state/task_status.json").write_text(
            json.dumps(mirror, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


class TaskQueueParserTest(unittest.TestCase):
    def test_parses_all_markers_and_preserves_exact_marker_offsets(self):
        text = (
            "# キュー\r\n"
            "- [ ] 未着手 <!-- id:T00 -->\r\n"
            "  - [>] 実行中 <!-- id:T01 -->\r\n"
            "- [x] 完了 <!-- id:USER-review -->\r\n"
            "- [!] 停止 <!-- id:INIT-1 -->\r\n"
        )

        entries = taskctl.parse_task_queue_text(text)

        self.assertEqual(
            [entry.status for entry in entries],
            ["PENDING", "IN_PROGRESS", "DONE", "BLOCKED"],
        )
        self.assertEqual(
            [entry.task_id for entry in entries],
            ["T00", "T01", "USER-review", "INIT-1"],
        )
        for entry in entries:
            self.assertEqual(text[entry.marker_offset], entry.marker)

    def test_only_user_and_init_ids_are_allowed_outside_graph(self):
        self.assertTrue(taskctl.is_auxiliary_task_id("USER-audit"))
        self.assertTrue(taskctl.is_auxiliary_task_id("INIT-1"))
        self.assertFalse(taskctl.is_auxiliary_task_id("USERLAND"))
        self.assertFalse(taskctl.is_auxiliary_task_id("T99"))


class ReadyTaskTest(unittest.TestCase):
    def test_ready_tasks_are_returned_in_stable_dag_order(self):
        graph = [
            graph_task("T03", ["T00"]),
            graph_task("T02", ["T00"]),
            graph_task("T00"),
            graph_task("T04", ["T02"]),
        ]
        statuses = {
            "T00": "DONE",
            "T02": "PENDING",
            "T03": "PENDING",
            "T04": "PENDING",
        }

        result = taskctl.ready(graph, statuses)

        self.assertEqual([task["id"] for task in result], ["T03", "T02"])

    def test_ready_accepts_legacy_mirror_shape(self):
        graph = [graph_task("T00")]
        mirror = {"tasks": {"T00": {"status": "PENDING"}}}
        self.assertEqual([task["id"] for task in taskctl.ready(graph, mirror)], ["T00"])

    def test_next_lines_distinguish_primary_parallel_prep_and_resume(self):
        graph = [
            graph_task("T00"),
            graph_task("T01", ["T00"]),
            graph_task("T02", ["T00"]),
        ]
        pending = taskctl.parse_task_queue_text(
            "- [x] T00 <!-- id:T00 -->\n"
            "- [ ] T01 <!-- id:T01 -->\n"
            "- [ ] T02 <!-- id:T02 -->\n"
        )
        self.assertEqual(
            [line.split()[0:2] for line in taskctl.next_task_lines(graph, pending)],
            [["PRIMARY", "T01"], ["PARALLEL_PREP", "T02"]],
        )

        active = taskctl.parse_task_queue_text(
            "- [x] T00 <!-- id:T00 -->\n"
            "- [>] T01 <!-- id:T01 -->\n"
            "- [ ] T02 <!-- id:T02 -->\n"
        )
        self.assertEqual(
            [line.split()[0:2] for line in taskctl.next_task_lines(graph, active)],
            [["RESUME", "T01"], ["PARALLEL_PREP", "T02"]],
        )

    def test_execution_waves_and_longest_chain_are_derived_from_dependencies(self):
        graph = [
            graph_task("T00"),
            graph_task("T01", ["T00"]),
            graph_task("T02", ["T00"]),
            graph_task("T03", ["T01", "T02"]),
        ]
        self.assertEqual(
            [[task["id"] for task in wave] for wave in taskctl.execution_waves(graph)],
            [["T00"], ["T01", "T02"], ["T03"]],
        )
        self.assertEqual(taskctl.longest_dependency_chain(graph), ["T00", "T01", "T03"])


class TaskTransitionTest(unittest.TestCase):
    def make_repo(self):
        queue = (
            "# tasks\r\n"
            "- [ ] Bootstrap 日本語 <!-- id:T00 -->\r\n"
            "- [ ] Dependent <!-- id:T01 -->\r\n"
            "- [ ] Independent <!-- id:T02 -->\r\n"
            "- [ ] Initial helper <!-- id:INIT-1 -->\r\n"
        )
        graph = [
            graph_task("T00"),
            graph_task("T01", ["T00"]),
            graph_task("T02"),
        ]
        return TemporaryTaskRepo(self, queue, graph)

    def test_transition_enforces_dependencies_and_one_active_task(self):
        repo = self.make_repo()
        with self.assertRaisesRegex(taskctl.TaskQueueError, "未完了の依存先"):
            taskctl.transition_task(repo.root, "start", "T01")
        with self.assertRaisesRegex(taskctl.TaskQueueError, "現在のPRIMARY: T00"):
            taskctl.transition_task(repo.root, "start", "T02")

        before = (repo.root / "design/tasks_next.md").read_bytes()
        status = taskctl.transition_task(
            repo.root,
            "start",
            "T00",
            summary="開始",
            now="2026-01-01T00:00:00+00:00",
        )
        after = (repo.root / "design/tasks_next.md").read_bytes()
        self.assertEqual(status, "IN_PROGRESS")
        self.assertEqual(len(before), len(after))
        self.assertEqual(sum(left != right for left, right in zip(before, after)), 1)
        self.assertIn(b"- [>] Bootstrap", after)
        self.assertIn(b"\r\n", after)

        mirror = json.loads((repo.root / "state/task_status.json").read_text(encoding="utf-8"))
        self.assertEqual(mirror["tasks"]["T00"]["status"], "IN_PROGRESS")
        self.assertEqual(mirror["tasks"]["T00"]["summary"], "開始")
        self.assertNotIn("INIT-1", mirror["tasks"])

        with self.assertRaisesRegex(taskctl.TaskQueueError, "実行中タスク"):
            taskctl.transition_task(repo.root, "start", "T02")

        taskctl.transition_task(repo.root, "done", "T00", summary="完了")
        taskctl.transition_task(repo.root, "start", "T01")
        taskctl.transition_task(repo.root, "block", "T01", summary="要確認")
        taskctl.transition_task(repo.root, "reset", "T01")
        with self.assertRaisesRegex(taskctl.TaskQueueError, "遷移できません"):
            taskctl.transition_task(repo.root, "done", "T01")

    def test_reset_done_dependency_rejects_non_pending_descendant(self):
        repo = self.make_repo()
        taskctl.transition_task(repo.root, "start", "T00")
        taskctl.transition_task(repo.root, "done", "T00")
        taskctl.transition_task(repo.root, "start", "T01")
        taskctl.transition_task(repo.root, "done", "T01")

        with self.assertRaisesRegex(taskctl.TaskQueueError, "後続タスク"):
            taskctl.transition_task(repo.root, "reset", "T00")

        taskctl.transition_task(repo.root, "reset", "T01")
        self.assertEqual(taskctl.transition_task(repo.root, "reset", "T00"), "PENDING")

    def test_auxiliary_task_can_transition_without_entering_mirror(self):
        repo = self.make_repo()
        taskctl.transition_task(repo.root, "start", "INIT-1")
        taskctl.transition_task(repo.root, "done", "INIT-1")
        mirror = json.loads((repo.root / "state/task_status.json").read_text(encoding="utf-8"))
        self.assertNotIn("INIT-1", mirror["tasks"])


class MirrorAndValidationTest(unittest.TestCase):
    def test_check_helpers_are_read_only(self):
        queue = "- [ ] Bootstrap <!-- id:T00 -->\n- [ ] Dependent <!-- id:T01 -->\n"
        repo = TemporaryTaskRepo(self, queue)
        paths = [
            repo.root / "design/tasks_next.md",
            repo.root / "tasks/task_graph.json",
            repo.root / "state/task_status.json",
        ]
        before = {path: path.read_bytes() for path in paths}

        self.assertEqual(taskctl.collect_consistency_errors(repo.root), [])
        project_status.status_lines(repo.root)

        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_sync_repairs_status_drift_and_preserves_summary(self):
        queue = (
            "- [x] Bootstrap <!-- id:T00 -->\n"
            "- [ ] Dependent <!-- id:T01 -->\n"
            "- [ ] Helper <!-- id:USER-audit -->\n"
        )
        mirror = {
            "tasks": {
                "T00": {"status": "PENDING", "summary": "old", "updated_at": "old-time"},
                "T01": {"status": "PENDING", "summary": "", "updated_at": ""},
            }
        }
        repo = TemporaryTaskRepo(self, queue, mirror=mirror)
        self.assertTrue(
            any("状態drift: T00" in error for error in taskctl.collect_consistency_errors(repo.root))
        )

        count = taskctl.sync_mirror(repo.root, now="2026-01-02T00:00:00+00:00")

        self.assertEqual(count, 2)
        synced = json.loads((repo.root / "state/task_status.json").read_text(encoding="utf-8"))
        self.assertEqual(synced["tasks"]["T00"]["status"], "DONE")
        self.assertEqual(synced["tasks"]["T00"]["summary"], "old")
        self.assertEqual(
            synced["tasks"]["T00"]["updated_at"], "2026-01-02T00:00:00+00:00"
        )
        self.assertNotIn("USER-audit", synced["tasks"])
        self.assertEqual(taskctl.collect_consistency_errors(repo.root), [])

    def test_validation_reports_missing_duplicate_unknown_and_drift(self):
        graph = [graph_task("T00"), graph_task("T01", ["T00"])]
        text = (
            "- [>] First <!-- id:T00 -->\n"
            "- [>] Duplicate <!-- id:T00 -->\n"
            "- [ ] Allowed <!-- id:INIT-1 -->\n"
            "- [ ] Unknown <!-- id:T99 -->\n"
        )
        entries = taskctl.parse_task_queue_text(text)
        mirror = {"tasks": {"T00": {"status": "DONE"}, "T99": {"status": "PENDING"}}}

        errors = taskctl.consistency_errors(graph, entries, mirror)
        joined = "\n".join(errors)

        self.assertIn("tasks_next.md のIDが重複", joined)
        self.assertIn("tasks_next.md にグラフタスクがありません: T01", joined)
        self.assertIn("task_graph.json にないタスクIDです: T99", joined)
        self.assertIn("IN_PROGRESSは最大1件", joined)
        self.assertIn("state/task_status.json にタスクがありません: T01", joined)
        self.assertIn("state/task_status.json に余分なタスクがあります: T99", joined)
        self.assertNotIn("task_graph.json にないタスクIDです: INIT-1", joined)

    def test_validation_reports_task_file_metadata_drift(self):
        queue = "- [ ] Bootstrap <!-- id:T00 -->\n- [ ] Dependent <!-- id:T01 -->\n"
        repo = TemporaryTaskRepo(self, queue)
        task_file = repo.root / "tasks/T01.md"
        task_file.write_text(
            "# T01 — Wrong title\n\n- Lane: `qa`\n- Depends on: `T00`\n",
            encoding="utf-8",
        )

        errors = taskctl.collect_consistency_errors(repo.root, check_task_files=True)
        joined = "\n".join(errors)
        self.assertIn("T01: task_graph.json と tasks/T01.md の title が不一致", joined)
        self.assertIn("T01: task_graph.json と tasks/T01.md の lane が不一致", joined)

    def test_validation_reports_queue_and_graph_order_drift(self):
        graph = [graph_task("T00"), graph_task("T01"), graph_task("T02")]
        entries = taskctl.parse_task_queue_text(
            "- [ ] T00 <!-- id:T00 -->\n"
            "- [ ] T02 <!-- id:T02 -->\n"
            "- [ ] T01 <!-- id:T01 -->\n"
        )

        errors = taskctl.consistency_errors(graph, entries)

        self.assertTrue(any("タスク順が不一致" in error for error in errors))

        repo = TemporaryTaskRepo(
            self,
            "- [ ] T00 <!-- id:T00 -->\n"
            "- [ ] T02 <!-- id:T02 -->\n"
            "- [ ] T01 <!-- id:T01 -->\n",
            graph,
        )
        with self.assertRaisesRegex(taskctl.TaskQueueError, "タスク順が不一致"):
            taskctl.transition_task(repo.root, "start", "T00")

    def test_validation_reports_non_topological_graph_array_order(self):
        graph = [graph_task("T01", ["T00"]), graph_task("T00")]
        entries = taskctl.parse_task_queue_text(
            "- [ ] T01 <!-- id:T01 -->\n- [ ] T00 <!-- id:T00 -->\n"
        )

        errors = taskctl.consistency_errors(graph, entries)

        self.assertTrue(any("配列順が依存順ではありません" in error for error in errors))

    def test_plan_view_validation_detects_index_and_master_dependency_drift(self):
        graph = [graph_task("T00"), graph_task("T01", ["T00"])]
        repo = TemporaryTaskRepo(
            self,
            "- [ ] T00 <!-- id:T00 -->\n- [ ] T01 <!-- id:T01 -->\n",
            graph,
        )
        (repo.root / "tasks/INDEX.md").write_text(
            "| ID | Task | Lane | Depends |\n"
            "|---|---|---|---|\n"
            "| [T00](T00.md) | Task T00 | test | — |\n"
            "| [T01](T01.md) | Task T01 | test | — |\n",
            encoding="utf-8",
        )
        (repo.root / "MASTER_PLAN.md").write_text(
            "| ID | タスク | 主レーン | 依存 | ゴール |\n"
            "|---|---|---|---|---|\n"
            "| T00 | zero | test | — | done |\n"
            "| T01 | one | test | — | done |\n",
            encoding="utf-8",
        )

        joined = "\n".join(taskctl.plan_view_errors(graph, repo.root))

        self.assertIn("T01: tasks/INDEX.md の depends", joined)
        self.assertIn("T01: MASTER_PLAN.md の依存", joined)

    def test_project_status_uses_queue_instead_of_stale_mirror(self):
        queue = "- [>] Bootstrap <!-- id:T00 -->\n- [ ] Dependent <!-- id:T01 -->\n"
        mirror = {
            "tasks": {
                "T00": {"status": "PENDING", "summary": "mirror summary", "updated_at": ""},
                "T01": {"status": "PENDING", "summary": "", "updated_at": ""},
            }
        }
        repo = TemporaryTaskRepo(self, queue, mirror=mirror)

        lines = project_status.status_lines(repo.root)

        self.assertEqual(lines[0], "PENDING=1 IN_PROGRESS=1 DONE=0 BLOCKED=0")
        self.assertIn("T00 IN_PROGRESS: mirror summary", lines)


if __name__ == "__main__":
    unittest.main()
