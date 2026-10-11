import unittest
from scripts import pr16_supply_closeout_ref_guard as r

class RefGuardTests(unittest.TestCase):
    def setUp(self):
        self.head='1'*40;self.parent='2'*40
        self.pr={'state':'open','draft':True,'merged':False,
                 'head':{'ref':r.BRANCH,'sha':self.parent,'repo':{'full_name':r.REPO}},
                 'base':{'ref':'main','repo':{'full_name':r.REPO}}}
        self.ref={'ref':'refs/heads/'+r.BRANCH,'object':{'type':'commit','sha':self.head}}
        self.allowed={self.head,self.parent}
    def check(self):return r.check_remote(self.pr,self.ref,self.head,self.allowed)
    def test_exact_and_known_ancestor(self):
        self.assertTrue(self.check()['pr_head_display_lag'])
        self.pr['head']['sha']=self.head;self.assertFalse(self.check()['pr_head_display_lag'])
    def test_live_ref_mismatch(self):
        self.ref['object']['sha']=self.parent
        with self.assertRaises(ValueError):self.check()
    def test_nonancestor_pr_head(self):
        self.pr['head']['sha']='3'*40
        with self.assertRaises(ValueError):self.check()
    def test_foreign_repository(self):
        self.pr['head']['repo']['full_name']='other/repo'
        with self.assertRaises(ValueError):self.check()
    def test_foreign_branch(self):
        self.pr['head']['ref']='other'
        with self.assertRaises(ValueError):self.check()
    def test_merged_pr(self):
        self.pr['merged']=True
        with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
