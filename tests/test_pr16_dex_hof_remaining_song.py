"""ROM再モデル化を行わず、保存・有限root guardの拒否条件を検査する。"""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(Path(__file__).resolve().parent)]
import pr16_dex_hof_remaining_song as candidate
import pr16_dex_hof_reference_chain as chain


class PreservationGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent=chain.parent((ROOT/chain.BASELINE).read_bytes(),(ROOT/chain.PARENT).read_bytes())
        cp=json.loads((ROOT/'content/modernization/pr16_dex_hof_reference_gaps_checkpoint.json').read_bytes())
        child=chain.read_measured((ROOT/'content/modernization/pr16_dex_hof_reference_gaps_evidence/reference-chain.json').read_bytes(),cp['delta_identity'],parent)
        cls.inherited=chain.materialize(parent,child)
        cls.witnesses=candidate.retained_sample_witnesses(cls.inherited)
        cls.regions=[SimpleNamespace(kind=w.get('kind',w.get('codec')),evidence=dict(asset=w['asset']))for w in cls.witnesses]
        cls.songs=[dict(id=i)for i in range(132)]
        cls.expected={i:[]for i in range(132)}
        cls.raw=bytes(range(64));cls.base=candidate.prior.base.BASE

    def window(self,start,size):
        return dict(address=self.base+start,size=size,sha256=hashlib.sha256(self.raw[start:start+size]).hexdigest())

    def test_01_exact49_including_immediate_parent_two(self):
        self.assertEqual(len(self.witnesses),49)
        candidate.preserve_assets(self.regions,self.witnesses)
        parent_assets=[r['evidence']['asset']for r in self.inherited['reference_chain']['witnesses']if r['kind']in('pcm8','dpcm4')]
        self.assertEqual(len(parent_assets),2)
        self.assertEqual([w['asset']for w in self.witnesses[-2:]],parent_assets)

    def test_02_original43_loss_rejected(self):
        value=copy.deepcopy(self.inherited)
        value['song_extension']['asset_witnesses'].pop()
        with self.assertRaisesRegex(ValueError,'all43'):candidate.retained_sample_witnesses(value)

    def test_03_each_immediate_parent_loss_and_extra_rejected(self):
        for removed in (0,1):
            value=copy.deepcopy(self.inherited)
            rows=value['reference_chain']['witnesses'];indices=[i for i,r in enumerate(rows)if r['kind']in('pcm8','dpcm4')]
            del rows[indices[removed]]
            with self.subTest(missing_parent_asset=removed),self.assertRaisesRegex(ValueError,'reference_chain'):
                candidate.retained_sample_witnesses(value)
        value=copy.deepcopy(self.inherited);rows=value['reference_chain']['witnesses']
        rows.append(copy.deepcopy(next(r for r in rows if r['kind']in('pcm8','dpcm4'))))
        with self.assertRaisesRegex(ValueError,'reference_chain'):candidate.retained_sample_witnesses(value)

    def test_04_duplicate49th_identity_rejected(self):
        value=copy.deepcopy(self.inherited)
        rows=[r for r in value['reference_chain']['witnesses']if r['kind']in('pcm8','dpcm4')]
        rows[1]['evidence']['asset']=copy.deepcopy(rows[0]['evidence']['asset'])
        rows[1]['kind']=rows[0]['kind']
        with self.assertRaisesRegex(ValueError,'distinct'):candidate.retained_sample_witnesses(value)

    def test_05_each_of49_missing_modeled_assets_rejected(self):
        for i in range(49):
            with self.subTest(missing_asset=i),self.assertRaisesRegex(ValueError,'every prior49'):
                candidate.preserve_assets(self.regions[:i]+self.regions[i+1:],self.witnesses)

    def test_06_asset_hash_size_address_or_kind_change_rejected(self):
        for key,value in [('sha256','0'*64),('size',1),('address',self.base)]:
            regions=copy.deepcopy(self.regions);regions[-1].evidence['asset'][key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):candidate.preserve_assets(regions,self.witnesses)
        regions=copy.deepcopy(self.regions);regions[-1].kind='unknown'
        with self.assertRaises(ValueError):candidate.preserve_assets(regions,self.witnesses)

    def test_07_exact132_set_accepted(self):
        candidate.exact_song_set(self.songs,self.expected)

    def test_08_lost_or_wrong_expected_song_rejected(self):
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs[:-1],self.expected)
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs,{i:[]for i in range(131)})

    def test_09_duplicate_song_row_rejected(self):
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs+[self.songs[-1]],self.expected)
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs[:-1]+[self.songs[0]],self.expected)

    def test_10_changed_or_new_zero_hit_song_rejected(self):
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs[:-1]+[dict(id=999)],self.expected)
        with self.assertRaises(ValueError):candidate.exact_song_set(self.songs+[dict(id=999)],{**self.expected,999:[]})

    def test_11_new_root_sample_overlap_rejected_boundaries_allowed(self):
        regions=[SimpleNamespace(start=self.base+20,end=self.base+40)]
        candidate.protect_root_roles(self.raw,regions,[self.window(16,4),self.window(40,4)])
        for start,size in [(19,2),(20,1),(39,2),(16,28)]:
            with self.subTest(start=start,size=size),self.assertRaisesRegex(ValueError,'sound payloads disjoint'):
                candidate.protect_root_roles(self.raw,regions,[self.window(start,size)])

    def test_12_new_root_signature_zero_extent_or_outside_rejected(self):
        wrong=self.window(0,4);wrong['sha256']='0'*64
        for w in [wrong,self.window(0,0),self.window(64,1)]:
            with self.subTest(window=w),self.assertRaises(ValueError):candidate.protect_root_roles(self.raw,[],[w])

    def test_13_current_whole_sha_and_parent_candidate_guard(self):
        with self.assertRaisesRegex(ValueError,'strict whole current'):candidate.song_regions(b'not current',self.inherited,{}, {})
        value=copy.deepcopy(self.inherited);value['candidate']['sha256']='0'*64
        with patch.object(candidate,'identity',return_value=candidate.prior.base.CANDIDATE),self.assertRaisesRegex(ValueError,'strict whole current'):
            candidate.song_regions(b'test only',value,{}, {})

    def test_14_frontier_exact661_213_guard_without_model(self):
        for classified,unknown in [(660,214),(661,214),(662,212)]:
            value=dict(self.inherited,classified=classified,unclassified=unknown)
            with self.subTest(frontier=(classified,unknown)),patch.object(candidate,'identity',return_value=candidate.prior.base.CANDIDATE),patch.object(candidate,'measured_regions')as measured,self.assertRaisesRegex(ValueError,'exact immediate accepted frontier'):
                candidate.song_regions(b'test only',value,{}, {})
            measured.assert_not_called()
        with patch.object(candidate,'identity',return_value=candidate.prior.base.CANDIDATE),patch.object(candidate,'measured_regions',return_value=([],{}))as measured:
            self.assertEqual(candidate.song_regions(b'test only',self.inherited,{}, {}),([],{}))
            measured.assert_called_once()

    def test_15_no_new_selected_audio_region(self):
        candidate.no_new_audio([])
        with self.assertRaisesRegex(ValueError,'no newly classified audio'):candidate.no_new_audio([object()])


if __name__=='__main__':unittest.main(verbosity=2)
