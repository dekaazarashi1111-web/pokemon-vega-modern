import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.content.content_schema import (ContentError, build_outputs, emit_content,
    load_repository, validate_facility_doc, validate_repository, validate_trainer_rows)
from tools.content.v2_normalize import CHECK_IDS, audit_v2, normalization_diagnostics

ROOT=Path(__file__).resolve().parents[1]


def set_path(value,path,new_value):
    parts=path.split("."); target=value
    for part in parts[:-1]: target=target[int(part)] if isinstance(target,list) else target[part]
    last=parts[-1]
    if isinstance(target,list): target[int(last)]=new_value
    else: target[last]=new_value


class ContentSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=validate_repository(ROOT)
        cls.tables,cls.facility=load_repository(ROOT)
        cls.phases={r["unlock_key"]:r for r in cls.tables["progression"]}

    def test_repository_and_outputs_are_symbolic(self):
        outputs=build_outputs(ROOT)
        self.assertIn(b"59 / 59 PASS",outputs["reports/generated/content_schema.md"])
        self.assertEqual(len(outputs["content/normalized/shared_captures.csv"].decode().splitlines())-1,125)
        self.assertEqual(len(outputs["content/normalized/v2_family_coverage.csv"].decode().splitlines())-1,541)
        self.assertEqual(len(outputs["content/normalized/kanto_gym_rewards.csv"].decode().splitlines())-1,8)
        for rows in self.tables.values():
            for row in rows:
                for field,value in row.items():
                    if field.endswith("_key"): self.assertFalse(value.isdigit())

    def test_v2_checks_are_recomputed_and_raw_issues_fail(self):
        audit=audit_v2(ROOT)
        self.assertEqual(set(audit),CHECK_IDS); self.assertEqual(sum(audit.values()),59)
        norm=normalization_diagnostics(ROOT)
        self.assertEqual(norm["raw_validation"],"FAIL")
        self.assertGreater(norm["raw_semantic_duplicate_count"],0)
        self.assertGreater(norm["raw_decimal_national_id_count"],0)
        self.assertEqual(len(norm["raw_missing_evolution_item_references"]),4)
        self.assertEqual(norm["normalized_validation"],"PASS")

    def test_emit_requires_resolution_and_physical_binding(self):
        with self.assertRaisesRegex(ContentError,"requires --resolution"):
            emit_content(ROOT,None)
        with self.assertRaisesRegex(ContentError,"physical_maps"):
            emit_content(ROOT,{"ids":{},"physical_map_bindings":{}})
        required=set()
        for rows in self.tables.values():
            for row in rows:
                for field,value in row.items():
                    if field.endswith("_key") and value!="NONE" and field not in ("map_key","unlock_key","warning_key","safe_route_key"):
                        required.add(value)
        ids={key:index for index,key in enumerate(sorted(required),1)}
        maps={row["map_key"]:{"group":96,"map":index} for index,row in enumerate(self.tables["maps"])}
        emitted=json.loads(emit_content(ROOT,{"ids":ids,"physical_map_bindings":maps}))
        self.assertEqual(emitted["mode"],"PHYSICAL")

    def test_facility_fixtures(self):
        folder=ROOT/"tests/fixtures/facility_schema"
        for path in sorted(folder.glob("*.json")):
            spec=json.loads(path.read_text())
            doc=copy.deepcopy(self.facility)
            if "path" in spec: set_path(doc,spec["path"],spec["value"])
            if "append_from" in spec:
                source=doc
                for part in spec["append_from"].split("."): source=source[int(part)] if isinstance(source,list) else source[part]
                target=doc
                for part in spec["append_to"].split("."): target=target[int(part)] if isinstance(target,list) else target[part]
                target.append(copy.deepcopy(source))
            errors=validate_facility_doc(doc,self.result["registries"],set(self.phases))
            if spec["expect"]=="PASS": self.assertEqual(errors,[],path.name)
            else: self.assertTrue(any(spec["expect"] in error for error in errors),(path.name,errors))

    def test_trainer_fixtures(self):
        folder=ROOT/"tests/fixtures/trainer_difficulty_schema"
        for path in sorted(folder.glob("*.json")):
            spec=json.loads(path.read_text())
            row=copy.deepcopy(self.tables["trainers"][spec["row"]])
            if "field" in spec: row[spec["field"]]=spec["value"]
            errors=validate_trainer_rows([row],self.result["registries"],self.phases)
            if spec["expect"]=="PASS": self.assertEqual(errors,[],path.name)
            else: self.assertTrue(any(spec["expect"] in error for error in errors),(path.name,errors))


if __name__=="__main__": unittest.main()
