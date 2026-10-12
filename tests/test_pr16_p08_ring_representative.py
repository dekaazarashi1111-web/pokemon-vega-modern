"""新しいcandidate contextだけを拒否検査。nativeケース自体は再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p08_ring_representative as m


def fixture():
    # 既受入resultを合成test inputへコピーするだけ。実行証拠としては保存しない。
    old=json.loads((ROOT/m.OLD).read_text())['native']
    row=copy.deepcopy(next(x['native_result'] for x in old['results'] if x['case']==m.CASE))
    row['rom_sha256']=m.impact.TARGET['sha256']
    audit=copy.deepcopy(old['oracle']);audit['candidate']=m.impact.TARGET
    stderr=(f"RING_ENCOUNTER species={row['enemy_species']} level={row['enemy_level']} flags=00000004 mode=1 used=0 frame={row['witness']['encounter']}\n").encode()
    return row,stderr,dict(returncode=0,timed_out=False,spawn_error=None),audit


class ContextTests(unittest.TestCase):
    def check(self,row,err,proc,audit):return m.validate_result(m.s.stable(row),err,proc,audit)
    def reject(self,change):
        args=fixture();change(*args)
        with self.assertRaises((ValueError,KeyError)):self.check(*args)
    def test_context_copy_is_explicit_and_old_module_unchanged(self):
        import pr16_ring_policy_native as old
        result=self.check(*fixture());self.assertEqual(result['rom_sha256'],m.impact.TARGET['sha256'])
        self.assertEqual(old.SHA,m.OLD_SHA);self.assertFalse(result['ordinary_battle_accepted'])
    def test_header_only_sha_changes(self):
        original=('/* 固定候補のNPCと歩行経路。Ring/NEXTのfixtureなし。 */\n#define RP_SHA "'+m.OLD_SHA+'"\n'
            '#define RP_GROUP 96U\n#define RP_MAP 17U\n#define RP_LOCAL_ID 4U\n#define RP_X 12U\n'
            '#define RP_Y 39U\n#define RP_ORDINARY_ACTIVE_FLAGS 4U\n').encode()
        self.assertEqual(m.adapt_header(original).replace(m.impact.TARGET['sha256'].encode(),m.OLD_SHA.encode()),original)
        with self.assertRaises(ValueError):m.adapt_header(original.replace(b'FLAGS 4U',b'FLAGS 0U'))
    def test_header_rejects_extra_code(self):
        with self.assertRaises(ValueError):m.adapt_header(b'#define RP_SHA "'+m.OLD_SHA.encode()+b'"\n')
    def test_old_candidate_rejected(self):self.reject(lambda r,e,p,a:r.update(rom_sha256=m.OLD_SHA))
    def test_old_oracle_rejected(self):self.reject(lambda r,e,p,a:a.update(candidate=dict(size=33554432,sha256=m.OLD_SHA)))
    def test_other_case_rejected(self):self.reject(lambda r,e,p,a:r.update(case='ring-unowned'))
    def test_returncode_bool_rejected(self):self.reject(lambda r,e,p,a:p.update(returncode=False))
    def test_timeout_rejected(self):self.reject(lambda r,e,p,a:p.update(timed_out=True))
    def test_spawn_error_rejected(self):self.reject(lambda r,e,p,a:p.update(spawn_error='failed'))
    def test_nonzero_returncode_rejected(self):self.reject(lambda r,e,p,a:p.update(returncode=1))
    def test_ring_fixture_rejected(self):self.reject(lambda r,e,p,a:r.update(ring_is_fixture=True))
    def test_policy_fixture_rejected(self):self.reject(lambda r,e,p,a:r.update(policy_is_fixture=True))
    def test_guard_count_rejected(self):self.reject(lambda r,e,p,a:r.update(host_write_barriers=6))
    def test_fresh_continue_count_rejected(self):self.reject(lambda r,e,p,a:r.update(fresh_cores=2))
    def test_no_native_pp_spend_rejected(self):self.reject(lambda r,e,p,a:r.update(pp_after=r['pp_before']))
    def test_reward_or_spend_contamination_rejected(self):self.reject(lambda r,e,p,a:r.update(bp_after=r['bp_before']+9))
    def test_uncaptured_save_rejected(self):self.reject(lambda r,e,p,a:r.update(save_after=r['save_before']+1))
    def test_chronology_rejected(self):self.reject(lambda r,e,p,a:r['witness'].update(mega=r['witness']['spent']+1))
    def test_ordinary_acceptance_not_premature(self):self.reject(lambda r,e,p,a:r.update(ordinary_battle_accepted=True))
    def test_warning_rejected(self):
        r,e,p,a=fixture()
        with self.assertRaises(ValueError):self.check(r,e+b'mGBA[warning]',p,a)
    def test_missing_natural_encounter_rejected(self):
        r,e,p,a=fixture()
        with self.assertRaises(ValueError):self.check(r,b'',p,a)
    def test_final_release_not_inherited(self):self.reject(lambda r,e,p,a:r.update(release_ready=True))


if __name__=='__main__':unittest.main()
