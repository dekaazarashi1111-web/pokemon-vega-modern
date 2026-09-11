"""Current-view contracts; synthetic metadata never claims native execution."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_refresh_current_view as m

class CurrentViewTests(unittest.TestCase):
    def original(self):
        text=(ROOT/m.GENERATOR).read_text()
        if m.AFTER in text:text=text.replace(m.AFTER,m.BEFORE,1)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),m.BEFORE_SHA)
        return text

    def test_hook_is_bounded_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/m.GENERATOR;p.parent.mkdir(parents=True);before=self.original();p.write_text(before)
            self.assertTrue(m.install_hook(root));self.assertFalse(m.install_hook(root))
            after=p.read_text();self.assertEqual(after.replace(m.AFTER,m.BEFORE,1),before)
            self.assertIn('if (root / completion_receipt).is_file():',after)

    def test_unrelated_generator_change_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/m.GENERATOR;p.parent.mkdir(parents=True);p.write_text(self.original()+'\n# unrelated change\n')
            before=p.read_bytes()
            with self.assertRaises(ValueError):m.install_hook(root)
            self.assertEqual(p.read_bytes(),before)

    def sample(self):
        return dict(final_integration={'source_path':'content/modernization/p08_final_candidate_acceptance.json','source_run_id':34477344071},
                    p06_adoption={'final_candidate_evidence':'content/modernization/p08_final_candidate_acceptance.json'},
                    p07_adoption={'normal_species_to_vega_move':0,'vega_species_to_normal_move':0},
                    repository_policy={'visibility':'public','owner_approved':True},
                    remaining_conditions=[{'id':'FINAL_NATIVE_ACCEPTANCE'},{'id':'P07_REMAINING_ROUTE_ACCEPTANCE'}],release_ready=False)

    def test_counts_roles_and_prior_run_survive_repeated_projection(self):
        before=self.sample()
        # Unit stub isolates projection labels, not actual acceptance validation.
        with patch.object(m.completion,'project',side_effect=lambda v,root:deepcopy(v)):
            after=m.current_view(before);twice=m.current_view(after)
        self.assertEqual(after,twice);self.assertEqual(before,self.sample())
        self.assertEqual(after['historical_stage84_integration']['source_run_id'],34477344071)
        self.assertEqual(after['final_integration']['new_native_processes_in_this_session'],7)
        self.assertEqual(after['final_integration']['source_runs']['repaired']['run_id'],34512326368)
        self.assertEqual(after['p07_adoption']['normal_species_to_vega_move'],499)
        self.assertEqual(after['p07_adoption']['vega_species_to_normal_move'],1073)
        self.assertEqual(after['repository_policy'],before['repository_policy'])
        self.assertFalse(after['p07_adoption']['decision_required']);self.assertFalse(after['release_ready'])
        self.assertEqual(after['p06_adoption']['final_candidate_evidence'],m.completion.RECEIPT)

if __name__=='__main__':unittest.main()
