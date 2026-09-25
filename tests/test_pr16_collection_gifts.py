"""Only new collection-route contracts. Synthetic records are never acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_collection_gifts as c


def model():
    forms=[];gifts=[];bit=0
    for i in range(18):
        fixed=i in (5,11,17);kind='FIXED' if fixed else 'RESEARCH_EGG'
        forms.append(dict(target_species=i+1,method='FIXED_GIFT' if fixed else kind))
        gifts.append(dict(form_index=i,kind=kind,kind_id=int(not fixed),claim_bit=bit if fixed else 0,
                          unlock_id=1,display_name='synthetic-'+str(i)))
        if fixed:bit+=1
    return dict(forms=forms,gifts=gifts)


def case():
    return c.vectors(model(),{i:[(33,1),(45,1)] for i in range(1,19)},{33:35,45:40})[0]


def owner(bits, generation):
    raw=bytearray(512);struct.pack_into('<IIHH',raw,0,0x31565343,0xcea9acbc,1,512)
    struct.pack_into('<I',raw,16,generation);raw[80]=bits
    struct.pack_into('<I',raw,12,zlib.crc32(raw)&0xffffffff)
    return bytes(raw)


def synthetic(v=None):
    v=v or case();geo=dict(script=0x093a0200)
    r=dict(schema_version=1,status='PASS',scope=c.SCOPE,case=v['name'],candidate_sha256=c.CANDIDATE['sha256'],
           gift_index=v['gift_index'],species=v['species'],level=v['level'],is_egg=v['is_egg'],
           moves=v['moves'],pp=v['pp'],npc_script=geo['script'],fresh_cores=2,denied_host_write_apis=7,
           guarded_phases=4,party_preserved_bytes=200,initial_party_map_unlock_claim_are_fixtures=True,
           story_acquisition_verified=False,egg_hatch_verified=False,all_owners_accepted=False,
           issue19_complete=False,release_ready=False,warnings_errors=0,
           witness=dict(boundary=1,root=2,list=3,selected=4,claimed=5,returned=7,saved=8,continued=9,revisited=10,cancelled=11),
           save_counters=[2,4,5,5,5],native_save_steps=2)
    bit=0 if v['is_egg'] else 1<<v['claim_bit'];r['owner_claim_bits']=[0,bit,bit,bit,bit]
    old=bytes([17])*100;child=bytearray(100)
    struct.pack_into('<H',child,32,v['species']);child[84]=v['level']
    struct.pack_into('<4H',child,44,*v['moves']);child[52:56]=bytes(v['pp']);struct.pack_into('<HH',child,86,30,35)
    lines=[]
    for i,stage in enumerate(('fixture','claimed','saved','continued','cancelled')):
        data=old if i==0 else old+child
        lines.append(f'CF_PARTY stage={stage} counter={r["save_counters"][i]} hex={data.hex()}')
        lines.append(f'CF_OWNER stage={stage} hex={owner(r["owner_claim_bits"][i],1 if i==0 else 2).hex()}')
    lines += [f'CF_MON stage={s} species={v["species"]} level={v["level"]} egg={v["is_egg"]} hp=30 max=35' for s in ('claimed','continued','cancelled')]
    lines += ['CF_SAVE frame=5 before=2 after=3 count=1 lock=1','CF_SAVE frame=6 before=3 after=4 count=2 lock=1',
              'original core destroyed; new core boot and normal Continue']
    return r, ('\n'.join(lines)+'\n').encode(), v, geo


class CollectionGiftsTests(unittest.TestCase):
    def check(self,r,e,v,g):return c.validate(json.dumps(r).encode(),e,v,g)
    def test_all_18_source_vectors_and_fixed_first(self):
        values=c.vectors(model(),{i:[(33,1),(45,1)] for i in range(1,19)},{33:35,45:40})
        self.assertEqual(len(values),18);self.assertEqual([x['gift_index'] for x in values[:3]],[5,11,17])
        self.assertTrue(all(x['level']==1 for x in values[3:]));self.assertEqual(values[0]['moves'],[33,45,0,0])
    def test_raw_last_four_precedes_dedup(self):
        rows={i:[(33,1),(45,1),(52,1),(55,1),(55,1)] for i in range(1,19)}
        values=c.vectors(model(),rows,{33:35,45:40,52:25,55:25})
        self.assertEqual(values[0]['moves'],[45,52,55,0])
    def test_unknown_original_owner_rejected(self):
        with self.assertRaises(ValueError):c.vectors(model(),{}, {33:35})
    def test_duplicate_owner_rejected(self):
        d=model();d['forms'][1]['target_species']=1
        with self.assertRaises(ValueError):c.vectors(d,{i:[(33,1)] for i in range(1,19)},{33:35})
    def test_bad_kind_or_claim_rejected(self):
        for mutate in (lambda d:d['gifts'][0].update(kind_id=0),lambda d:d['gifts'][5].update(claim_bit=2)):
            d=model();mutate(d)
            with self.assertRaises(ValueError):c.vectors(d,{i:[(33,1)] for i in range(1,19)},{33:35})
    def test_bad_pp_rejected(self):
        with self.assertRaises(ValueError):c.vectors(model(),{i:[(33,1)] for i in range(1,19)},{33:0})
    def test_synthetic_fixed_record_consistent(self):
        r,e,v,g=synthetic();self.assertEqual(self.check(r,e,v,g)['status'],'PASS')
    def test_synthetic_research_record_consistent(self):
        values=c.vectors(model(),{i:[(33,1)] for i in range(1,19)},{33:35})
        r,e,v,g=synthetic(values[3]);self.assertEqual(self.check(r,e,v,g)['is_egg'],1)
    def test_duplicate_json_and_extra_key_rejected(self):
        r,e,v,g=synthetic();raw=json.dumps(r).encode()
        with self.assertRaises(ValueError):c.validate(raw[:-1]+b',"status":"PASS"}',e,v,g)
        r['unknown']=1
        with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_scope_escalation_rejected(self):
        for key in ('egg_hatch_verified','all_owners_accepted','issue19_complete','release_ready','story_acquisition_verified'):
            r,e,v,g=synthetic();r[key]=True
            with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_non_integer_witness_rejected(self):
        r,e,v,g=synthetic();r['witness']['boundary']=True
        with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_reordered_chronology_rejected(self):
        r,e,v,g=synthetic();r['witness']['selected']=6
        with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_missing_or_changed_party_rejected(self):
        r,e,v,g=synthetic()
        for bad in (e.replace(b'CF_PARTY stage=saved',b'OMITTED stage=saved'),e.replace(b'CF_PARTY stage=saved counter=5 hex=11',b'CF_PARTY stage=saved counter=5 hex=22')):
            with self.assertRaises(ValueError):self.check(r,bad,v,g)
    def test_move_and_pp_claims_cannot_override_raw(self):
        r,e,v,g=synthetic();r['moves'][0]=52;v=deepcopy(v);v['moves'][0]=52
        with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_raw_owner_crc_rejected(self):
        r,e,v,g=synthetic();e=e.replace(b'CF_OWNER stage=saved hex=43',b'CF_OWNER stage=saved hex=42')
        with self.assertRaises(ValueError):self.check(r,e,v,g)
    def test_missing_getter_or_wrong_egg_rejected(self):
        r,e,v,g=synthetic()
        for bad in (e.replace(b'CF_MON stage=continued',b'OMITTED stage=continued'),e.replace(b'egg=0',b'egg=1')):
            with self.assertRaises(ValueError):self.check(r,bad,v,g)
    def test_counter_jump_or_missing_native_save_rejected(self):
        r,e,v,g=synthetic()
        for bad in (e.replace(b'before=2 after=3',b'before=2 after=4'),e.replace(b'CF_SAVE frame=6',b'OMITTED frame=6')):
            with self.assertRaises(ValueError):self.check(r,bad,v,g)
    def test_missing_new_core_and_warnings_rejected(self):
        r,e,v,g=synthetic()
        for bad in (e.replace(b'original core destroyed;',b'missing;'),e+b'mGBA[warning]\n'):
            with self.assertRaises(ValueError):self.check(r,bad,v,g)
    def test_accepted_case_excluded_and_drift_rejected(self):
        contracts={'a':{'candidate':1},'b':{'candidate':1}}
        accepted={'a':dict(contract={'candidate':1},result=dict(status='PASS'))}
        self.assertEqual(c.pending(accepted,contracts),['b'])
        contracts['a']['candidate']=2
        with self.assertRaises(ValueError):c.pending(accepted,contracts)
    def test_geometry_uses_actual_object_and_native_script(self):
        rom=bytearray(0x56000)
        def ptr(at,to):struct.pack_into('<I',rom,at,0x08000000+to)
        ptr(0x54b0c,0x100);ptr(0x104,0x200);ptr(0x20c,0x300);ptr(0x304,0x400)
        rom[0x400]=1;ptr(0x404,0x500);rom[0x500]=7
        struct.pack_into('<HH',rom,0x504,21,3);ptr(0x510,0x600)
        rom[0x600:0x60b]=b'\x6a\x16\x04\x80\x00\x00\x23'+struct.pack('<I',0x08007001)
        config=dict(physical_hosts=[dict(service='GIFT',map_group=1,map_num=3,x=21,y=3)])
        geo=c.geometry(rom,config);self.assertEqual((geo['local_id'],geo['x'],geo['y']),(7,21,4))
        rom[0x600]=0
        with self.assertRaises(ValueError):c.geometry(rom,config)
    def test_controller_barriers_and_no_testgift_execution(self):
        source=(c.ROOT/c.C).read_text();body=source.split('cf_t.boundary=b_frames;',1)[1]
        self.assertEqual(source.count('a_guard(c);'),4)
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'TestGift(', 'test_mode=1'):
            self.assertNotIn(forbidden,body)
        self.assertIn('cf_watching=true',body);self.assertIn('b_restart(c,',body)
        self.assertIn('cf_raw(c,"continued"',body);self.assertIn('cf_check(c,"cancelled"',body)
    def test_header_only_original_vectors(self):
        v=case();geo={k:1 for k in ('group','number','x','y','host_index','local_id','script')}
        h=c.header([v],geo);self.assertIn(v['name'],h);self.assertIn('{33U,45U,0U,0U}',h)
        self.assertNotIn('test_mode',h)


if __name__=='__main__':unittest.main()
