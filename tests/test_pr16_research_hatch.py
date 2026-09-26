"""研究孵化の新境界だけを検査。既受入native/旧unitは実行しない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_hatch as r


def sample():
    raw=bytearray(200);child=100
    struct.pack_into('<II',raw,child,12345,67890)
    struct.pack_into('<H',raw,child+32,1201);raw[child+84]=1;raw[child+41]=50
    struct.pack_into('<4H',raw,child+44,33,39,0,0);raw[child+52:child+56]=bytes([35,30,0,0])
    struct.pack_into('<HH',raw,child+86,5,10)
    owner=bytearray(512);struct.pack_into('<IIHH',owner,0,0x31565343,0xcea9acbc,1,512)
    struct.pack_into('<I',owner,12,zlib.crc32(owner)&0xffffffff)
    case=dict(name='research-egg-1201',species=1201,level=1,is_egg=1,original_rows=[[33,1],[39,1],[84,4]],moves=[33,39,0,0],pp=[35,30,0,0])
    accepted=dict(contract=dict(candidate=r.CANDIDATE,case=case),result=dict(status='PASS',party_identity=r.identity(raw)),run_id=99,source_head='a'*40)
    labels=['fixture','claimed','saved','continued','cancelled'];lines=[]
    for i,label in enumerate(labels):
        lines.append(f'CF_PARTY stage={label} counter={i if i<2 else 2} hex={(raw[:100] if i==0 else raw).hex()}')
        lines.append(f'CF_OWNER stage={label} hex={owner.hex()}')
    stderr=('\n'.join(lines)+'\n').encode();fixture=r.fixture(accepted,stderr)
    return accepted,stderr,fixture


def observed():
    accepted,source,c=sample();raw=bytes.fromhex(c['party']);hatched=bytearray(raw);hatched[141]=70
    # 同行個体のなつき度は通常歩行で変わり得る。
    hatched[41]=60;hatched[28]=123
    t=dict(boundary=1,hatch_begin=500000,nickname=500100,hatch_end=500200,saved=501000,continued=503000)
    out=dict(schema_version=1,status='PASS',scope=r.SCOPE,case=c['name'],candidate_sha256=r.CANDIDATE['sha256'],species=1201,level=1,
             moves=c['moves'],pp=c['pp'],cycles=50,fresh_cores=2,host_write_barriers=7,guarded_phases=3,native_hatch_saves=1,manual_saves=1,saved_party_bytes=200,
             reconstructed_individual_fixture=True,continuous_gift_save_claimed=False,gift_reruns=0,issue19_complete=False,release_ready=False,warnings_errors=0,
             clock_start=0,steps=13055,hatch_frames=200,hatch_state_mask=(1<<6)|(1<<10),total_frames=503000,save_counters=[2,3,4,4],witness=t)
    lines=[]
    for i,(label,frame) in enumerate(zip(('fixture','hatched','saved','continued'),(0,500200,501000,503000))):
        lines.append(f'RH_PARTY stage={label} frame={frame} counter={out["save_counters"][i]} hex={(raw if i==0 else hatched).hex()}')
    for i,label in enumerate(('fixture','hatched','continued')):
        lines.append(f'RH_MON stage={label} species=1201 level=1 egg={int(i==0)} hp=5 max=10 pid=12345 ot=67890 cycles={50 if i==0 else 70}')
    for step in range(1,13056,256):
        lines.append(f'BREED research-hatch-walk map=35/0 xy=3,5 party=2 queue=0 clock=1 steps={step} frame={step*32} cb=08000001')
    lines.append('original core destroyed; new core boot and normal Continue')
    return out,('\n'.join(lines)+'\n').encode(),c


class ResearchHatchTests(unittest.TestCase):
    def test_accepted_fixture_binding(self):
        a,err,c=sample();self.assertEqual(c['cycles'],50);self.assertEqual(len(bytes.fromhex(c['party'])),200)
        self.assertFalse(c['gift_reexecuted']);self.assertFalse(c['genuine_saved_game_continuation'])
    def test_explicit_fifteen_owners(self):
        self.assertEqual(len(r.SPECIES),15);self.assertEqual(len(set(r.SPECIES)),15);self.assertNotIn(1281,r.SPECIES)
    def test_original_window_then_duplicate_removal(self):
        self.assertEqual(r.initial([[1,1],[2,1],[3,1],[2,1],[4,1]]),[2,3,4,0])
    def test_original_unsorted_rejected(self):
        with self.assertRaises(ValueError):r.initial([[33,2],[39,1]])
    def test_original_sidechange_rejected(self):
        with self.assertRaises(ValueError):r.initial([[1063,1]])
    def test_empty_initial_rejected(self):
        with self.assertRaises(ValueError):r.initial([[33,2]])
    def test_original_bool_rejected(self):
        with self.assertRaises(ValueError):r.initial([[True,1]])
    def test_nonlearning_owner_rejected(self):
        a,err,_=sample();a['contract']['case'].update(species=1281,name='research-egg-1281')
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_wrong_candidate_rejected(self):
        a,err,_=sample();a['contract']['candidate']=dict(r.CANDIDATE,sha256='0'*64)
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_original_span_mismatch_rejected(self):
        a,err,_=sample();a['contract']['case']['original_rows'][1][0]=40
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_zero_pp_rejected(self):
        a,err,_=sample();a['contract']['case']['pp'][0]=0
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_raw_party_hash_rejected(self):
        a,err,_=sample();a['result']['party_identity']={'size':200,'sha256':'0'*64}
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_missing_source_stage_rejected(self):
        a,err,_=sample();err=b'\n'.join(x for x in err.split(b'\n') if not x.startswith(b'CF_PARTY stage=saved'))
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_duplicate_source_stage_rejected(self):
        a,err,_=sample();err+=next(x+b'\n' for x in err.splitlines() if x.startswith(b'CF_PARTY'))
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_owner_crc_rejected(self):
        a,err,_=sample();err=err.replace(b'CF_OWNER stage=continued hex=43535631',b'CF_OWNER stage=continued hex=43535630')
        with self.assertRaises(ValueError):r.fixture(a,err)
    def test_header_contains_original_bytes(self):
        _,_,c=sample();s=r.header([c]);self.assertIn('1201U,50U',s);self.assertIn('party[200],owner[512]',s)
    def test_validator_pass_with_natural_friendship(self):
        out,err,c=observed();v=r.validate(json.dumps(out),err,c);self.assertEqual(v['steps'],13055)
    def test_shortened_walking_rejected(self):
        out,err,c=observed();out['steps']=255
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_missing_callback_state_rejected(self):
        out,err,c=observed();out['hatch_state_mask']=1<<6
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_counter_injection_rejected(self):
        out,err,c=observed();out['save_counters']=[2,2,3,3]
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_bool_counter_rejected(self):
        out,err,c=observed();out['clock_start']=False
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_nickname_order_rejected(self):
        out,err,c=observed();out['witness']['nickname']=500200
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_raw_counter_disagreement_rejected(self):
        out,err,c=observed();err=err.replace(b'stage=continued frame=503000 counter=4',b'stage=continued frame=503000 counter=3')
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_hatched_egg_still_set_rejected(self):
        out,err,c=observed();err=err.replace(b'stage=hatched species=1201 level=1 egg=0',b'stage=hatched species=1201 level=1 egg=1')
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_individual_change_rejected(self):
        out,err,c=observed();err=err.replace(b'pid=12345 ot=67890',b'pid=12346 ot=67890')
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_missing_walk_prefix_rejected(self):
        out,err,c=observed();err=b'\n'.join(x for x in err.split(b'\n') if b'steps=257 ' not in x)
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_duplicate_json_rejected(self):
        out,err,c=observed();raw=json.dumps(out).replace('"schema_version": 1','"schema_version": 1,"schema_version": 1')
        with self.assertRaises(ValueError):r.validate(raw,err,c)
    def test_scope_promotion_rejected(self):
        out,err,c=observed();out['continuous_gift_save_claimed']=True
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_host_write_rejected(self):
        out,err,c=observed();err+=b'host write after observation barrier\n'
        with self.assertRaises(ValueError):r.validate(json.dumps(out),err,c)
    def test_pending_never_repeats_success(self):
        contracts={n:{'identity':n} for n in r.NAMES};a={r.NAMES[0]:dict(contract=contracts[r.NAMES[0]],result={'status':'PASS'})}
        self.assertNotIn(r.NAMES[0],r.pending(a,contracts))
    def test_accepted_input_change_needs_review(self):
        contracts={n:{'identity':n} for n in r.NAMES};a={r.NAMES[0]:dict(contract={'changed':True},result={'status':'PASS'})}
        with self.assertRaises(ValueError):r.pending(a,contracts)
    def test_native_boundary_has_no_fixture_writes(self):
        source=(r.ROOT/r.C).read_text();observed_part=source.split('struct mCore saved=*c;a_guard(c);',1)[1]
        self.assertNotIn('write8(',observed_part);self.assertNotIn('set_mon_data',observed_part)
        self.assertEqual(observed_part.count('a_guard(c)'),2);self.assertIn('c->reset(c);saved=*c;a_guard(c)',observed_part)
        self.assertNotIn('rh_unused_daycare_main(',source)


if __name__=='__main__':unittest.main()
