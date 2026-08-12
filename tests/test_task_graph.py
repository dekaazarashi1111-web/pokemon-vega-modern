import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TaskGraphTest(unittest.TestCase):
    def test_dependencies_exist_and_graph_is_acyclic(self):
        tasks = json.loads((ROOT/'tasks/task_graph.json').read_text(encoding='utf-8'))['tasks']
        by_id = {t['id']: t for t in tasks}
        for task in tasks:
            self.assertTrue((ROOT/task['file']).exists())
            for dep in task['depends_on']:
                self.assertIn(dep, by_id)
        visiting, visited = set(), set()
        def visit(node):
            self.assertNotIn(node, visiting)
            if node in visited:
                return
            visiting.add(node)
            for dep in by_id[node]['depends_on']:
                visit(dep)
            visiting.remove(node)
            visited.add(node)
        for node in by_id:
            visit(node)

if __name__ == '__main__':
    unittest.main()
