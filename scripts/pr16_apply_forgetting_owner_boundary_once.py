#!/usr/bin/env python3
"""Apply the PR16 forgetting-recorder owner-boundary repair exactly once."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/record_modernization_p03_forgetting.py"
TEST = ROOT / "tests/test_modernization_p08_forgetting_evidence.py"

SOURCE_OLD = """def current_remaining_work(root, forgetting):
    # Compose current adoption only after validating immutable historical evidence.
    overview = remaining_work(root, forgetting)
    receipt = root/'content/modernization/p08_final_candidate_acceptance.json'
    need(not receipt.is_symlink(), 'symlink final receipt')
    if receipt.exists():
        import record_modernization_final_acceptance as integration
        overview = integration.project_overview(overview, root)
    sys.path.insert(0, str(root/'tools'))
    from modernization_owner_policy import project
    return project(overview, root)
"""

SOURCE_NEW = """def validate_current_remaining_work(overview, forgetting):
    \"\"\"Validate only the fields owned by the forgetting acceptance recorder.\"\"\"
    need(type(overview) is dict, 'remaining-work root must be an object')
    need(overview.get('schema_version') == 1, 'remaining-work schema changed')
    need(overview.get('historical_snapshot_is_current_backlog') is False,
         'historical snapshot was relabelled as current backlog')
    reports = overview.get('accepted_scoped_reports')
    need(type(reports) is list, 'accepted scoped reports must be a list')
    matches = [row for row in reports
               if type(row) is dict and row.get('source_path') == MANIFEST]
    need(len(matches) == 1, 'forgetting accepted report link differs')
    fields(matches[0], dict(
        label='native forgetting and cold Save/Continue',
        source_path=MANIFEST,
        source_run_id=RUN,
        cases=12,
        candidate_rom=forgetting['candidate_rom']))
    bindings = overview.get('source_bindings')
    need(type(bindings) is dict,
         'remaining-work source bindings must be an object')
    manifest_raw = (json.dumps(forgetting, ensure_ascii=False,
                               sort_keys=True, indent=2) + '\\n').encode()
    need(same(bindings.get(MANIFEST), identity(manifest_raw)),
         'forgetting manifest binding differs')


def current_remaining_work(root, forgetting):
    # Later P03/P05/P07/P08 recorders share this canonical overview.  Preserve
    # it verbatim and validate only the links owned by this recorder.
    summary = root/OVERVIEW
    need(not any(path.is_symlink() for path in (summary, *summary.parents)),
         'unsafe remaining-work overview')
    if summary.exists():
        need(summary.is_file(), 'remaining-work overview is not a file')
        overview = load(summary.read_bytes())
        validate_current_remaining_work(overview, forgetting)
        return overview

    # Bootstrap only when no canonical overview has ever been recorded.
    overview = remaining_work(root, forgetting)
    receipt = root/'content/modernization/p08_final_candidate_acceptance.json'
    need(not receipt.is_symlink(), 'symlink final receipt')
    if receipt.exists():
        import record_modernization_final_acceptance as integration
        overview = integration.project_overview(overview, root)
    sys.path.insert(0, str(root/'tools'))
    from modernization_owner_policy import project
    overview = project(overview, root)
    validate_current_remaining_work(overview, forgetting)
    return overview
"""

TEST_IMPORT_OLD = "import sys\nimport unittest\n"
TEST_IMPORT_NEW = "import sys\nimport tempfile\nimport unittest\n"
TEST_MARKER = "\nif __name__=='__main__':unittest.main()\n"
TEST_SENTINEL = "class CurrentRemainingWorkOwnershipTests(unittest.TestCase):"
TEST_ADDITION = r'''

class CurrentRemainingWorkOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acceptance = record.build()
        cls.tracked = record.load((ROOT/record.OVERVIEW).read_bytes())

    def test_current_snapshot_preserves_later_checkpoint_fields(self):
        current = record.current_remaining_work(ROOT, self.acceptance)
        self.assertTrue(record.same(current, self.tracked))
        self.assertIn('p03_form_route_inventory', current)
        self.assertIn('p05_native_supply_reconciliation', current)
        self.assertIn('p05_native_supply_evidence_map', current)
        self.assertEqual(current['p07_remaining_route_count'], 0)

    def test_unknown_future_fields_survive_unchanged(self):
        future = copy.deepcopy(self.tracked)
        future['future_owner_projection'] = {'sentinel': True}
        future['remaining_conditions'][0]['future_owner_field'] = 'kept'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/record.OVERVIEW
            target.parent.mkdir(parents=True)
            target.write_bytes((json.dumps(future, ensure_ascii=False,
                                           sort_keys=True, indent=2) + '\n').encode())
            actual = record.current_remaining_work(root, self.acceptance)
        self.assertTrue(record.same(actual, future))

    def test_missing_owned_report_is_rejected(self):
        broken = copy.deepcopy(self.tracked)
        broken['accepted_scoped_reports'] = [
            row for row in broken['accepted_scoped_reports']
            if row.get('source_path') != record.MANIFEST
        ]
        with self.assertRaisesRegex(
                ValueError, 'forgetting accepted report link differs'):
            record.validate_current_remaining_work(broken, self.acceptance)

    def test_changed_owned_binding_is_rejected(self):
        broken = copy.deepcopy(self.tracked)
        broken['source_bindings'][record.MANIFEST]['sha256'] = '0' * 64
        with self.assertRaisesRegex(
                ValueError, 'forgetting manifest binding differs'):
            record.validate_current_remaining_work(broken, self.acceptance)
'''


def replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text()
    count = text.count(old)
    if count == 1:
        path.write_text(text.replace(old, new))
        return True
    if count == 0 and new in text:
        return False
    raise SystemExit(f"{path}: expected exactly one replacement point, found {count}")


def update_test() -> bool:
    text = TEST.read_text()
    changed = False
    if TEST_IMPORT_OLD in text:
        if text.count(TEST_IMPORT_OLD) != 1:
            raise SystemExit("test import replacement point is ambiguous")
        text = text.replace(TEST_IMPORT_OLD, TEST_IMPORT_NEW)
        changed = True
    elif TEST_IMPORT_NEW not in text:
        raise SystemExit("test import replacement point is absent")

    if TEST_SENTINEL not in text:
        if text.count(TEST_MARKER) != 1:
            raise SystemExit("test insertion marker is absent or ambiguous")
        text = text.replace(TEST_MARKER, TEST_ADDITION + TEST_MARKER)
        changed = True

    if changed:
        TEST.write_text(text)
    return changed


def main() -> int:
    source_changed = replace_once(SOURCE, SOURCE_OLD, SOURCE_NEW)
    test_changed = update_test()
    print({"source_changed": source_changed, "test_changed": test_changed})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
