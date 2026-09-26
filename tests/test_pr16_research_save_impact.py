"""Synthetic contract tests only; these fixtures are never native evidence."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_save_impact as m


def packed(rows):return ('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n').encode()


def fixture(op='existing-earn',phase=0):
    kind=m.OPS.index(op)+1;rows=[];saves=[2,0,1,1][phase];recovery=int(phase>1)
    for i,stage in enumerate(m.EVENTS):
        b=bytearray(64);b[0]=1;b[1]=64;b[6]=1
        fields={4:500,36:1};applied=i>0 and phase!=1 and (phase==0 or (i==1 and phase==3) or (i>1 and kind==1))
        if i and phase!=1:fields[36]=2
        if applied:
            fields[4]=500+{1:3,2:10,3:-100,4:0}[kind]
            if kind in (1,2):fields[10]={1:3,2:10}[kind];fields[{1:18,2:22}[kind]]=fields[10]
            if kind==1:fields[40]=0x52450001
            if kind==2:b[27]=2
            if kind==3:b[28]=1
            if kind==4:b[26]=1
        if i==1 and phase==2:
            key,aux,amount=[(2,0,3),(4,2,10),(14,1,100),(0,5,4)][kind-1]
            fields[44]=0x52450001 if kind==1 else 1;b[48:52]=bytes((kind,1,key,aux));fields[52]=amount;fields[54]=500
        for offset,value in fields.items():struct.pack_into('<I' if offset in (10,36,40,44) else '<H',b,offset,value)
        b[7]=int(i>=2)
        added=({3:1,4:5}.get(kind,0)) if applied else 0
        rows.append({'event':stage,'counter':3+(saves if i else 0)+(recovery if i>1 else 0),'item_quantity':added,
                     'inventory_sha256':('b' if added else 'a')*64,'other_inventory_sha256':'c'*64,
                     'party_sha256':'d'*64,'party_count':1,'owner':b.hex()})
    rows.append({'status':'PASS','scope':'RESEARCH_SHARED_SAVE_SCHEDULED_FLASH_RECOVERY','candidate_sha256':m.repair.CANDIDATE['sha256'],
                 'operation':op,'phase':phase,'result':(0,13,13,0xFFFFFFFF)[phase],'transaction_calls':1,'delegate_saves':saves,
                 'delegate_loads':0,'phase1':1,'phase2':int(phase!=1),'fresh_cores':3,'host_write_barriers':7,'recovery_saves':recovery,
                 'test_mode':False,'normal_transaction_ui_accepted':False,'second_continue_idempotent':True,'warnings_errors':0,'steps':1000000})
    return rows


class NativeContract(unittest.TestCase):
    def reject(self,rows,op='existing-earn',phase=0):
        with self.assertRaises((ValueError,KeyError,TypeError)):m.native_result(packed(rows),op,phase)
    def test_all_sixteen_contracts(self):
        for op in m.OPS:
            for phase in range(4):
                with self.subTest(op=op,phase=phase):self.assertEqual(m.native_result(packed(fixture(op,phase)),op,phase)['phase'],phase)
    def test_missing_observation(self):self.reject(fixture()[1:])
    def test_duplicate_observation(self):a=fixture();a.insert(0,a[0]);self.reject(a)
    def test_event_order(self):a=fixture();a[0],a[1]=a[1],a[0];self.reject(a)
    def test_old_candidate(self):a=fixture();a[-1]['candidate_sha256']=m.repair.PARENT['sha256'];self.reject(a)
    def test_simulated_services(self):a=fixture();a[-1]['test_mode']=True;self.reject(a)
    def test_ui_overclaim(self):a=fixture();a[-1]['normal_transaction_ui_accepted']=True;self.reject(a)
    def test_wrong_load_delegate(self):a=fixture();a[-1]['delegate_loads']=1;self.reject(a)
    def test_missing_actual_saves(self):a=fixture();a[-1]['delegate_saves']=0;self.reject(a)
    def test_multiple_target_entries(self):a=fixture();a[-1]['transaction_calls']=2;self.reject(a)
    def test_boolean_counter(self):a=fixture();a[-1]['transaction_calls']=True;self.reject(a)
    def test_one_core_reused(self):a=fixture();a[-1]['fresh_cores']=1;self.reject(a)
    def test_missing_guard_api(self):a=fixture();a[-1]['host_write_barriers']=6;self.reject(a)
    def test_warning(self):a=fixture();a[-1]['warnings_errors']=1;self.reject(a)
    def test_unknown_field(self):a=fixture();a[-1]['accepted']=True;self.reject(a)
    def test_bad_cpu_limit(self):a=fixture();a[-1]['steps']=0;self.reject(a)
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):m.load('{"x":1,"x":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(ValueError):m.load('{"x":NaN}')
    def test_all_owner_bytes_checked(self):
        for offset in range(64):
            if offset==7:continue
            with self.subTest(offset=offset):
                a=fixture();b=bytearray.fromhex(a[2]['owner']);b[offset]^=1;a[2]['owner']=b.hex();self.reject(a)
    def test_recovery_cannot_duplicate_earn(self):a=fixture(phase=2);b=bytearray.fromhex(a[2]['owner']);struct.pack_into('<H',b,4,506);a[2]['owner']=b.hex();self.reject(a,phase=2)
    def test_spend_does_not_complete_reservation_on_reload(self):a=fixture('spend',3);a[2]['item_quantity']=1;self.reject(a,'spend',3)
    def test_rank_cannot_duplicate_bag_reward(self):a=fixture('rank');a[3]['item_quantity']=10;self.reject(a,'rank',0)
    def test_cut_not_success_return(self):a=fixture(phase=3);a[-1]['result']=0;self.reject(a,phase=3)
    def test_fault1_not_persisted(self):a=fixture(phase=1);a[1]['counter']+=1;self.reject(a,phase=1)
    def test_fault2_pending_kind(self):a=fixture(phase=2);b=bytearray.fromhex(a[1]['owner']);b[48]=3;a[1]['owner']=b.hex();self.reject(a,phase=2)
    def test_wrong_recovery_save_count(self):a=fixture(phase=2);a[2]['counter']+=1;self.reject(a,phase=2)
    def test_inventory_unrelated_change(self):a=fixture();a[2]['other_inventory_sha256']='e'*64;self.reject(a)
    def test_party_change(self):a=fixture();a[2]['party_sha256']='e'*64;self.reject(a)
    def test_party_count_change(self):a=fixture();a[2]['party_count']=2;self.reject(a)
    def test_unchanged_inventory_digest_after_reward(self):a=fixture('rank');a[2]['inventory_sha256']=a[0]['inventory_sha256'];self.reject(a,'rank',0)
    def test_second_continue_time_changed(self):a=fixture();b=bytearray.fromhex(a[3]['owner']);b[7]=2;a[3]['owner']=b.hex();self.reject(a)
    def test_digest_syntax(self):a=fixture();a[0]['party_sha256']='not-a-hash';self.reject(a)


class PublicationContract(unittest.TestCase):
    def test_unchanged_allowed_files_not_mandatory(self):self.assertEqual(m.guard_scope({'a','b'},{'a'},{'a'}),{'a'})
    def test_missing_mandatory(self):
        with self.assertRaises(ValueError):m.guard_scope({'a','b'},{'a'},{'b'})
    def test_unowned_staged_file(self):
        with self.assertRaises(ValueError):m.guard_scope({'a'},{'a','private.gba'},{'a'})
    def test_extra_zip_member(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            for path in m.MEMBERS:z.writestr(path,b'{}')
            z.writestr('../private.gba',b'no')
        with self.assertRaises(ValueError):m.unpack(b.getvalue())
    def test_missing_zip_member(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('measurement.json',b'{}')
        with self.assertRaises(ValueError):m.unpack(b.getvalue())
    def test_thumb_bl_exact(self):self.assertEqual(m.thumb_bl(bytes.fromhex('fff7befb'),0x08000000),0x07FFF780)
    def test_thumb_non_call_rejected(self):
        with self.assertRaises(ValueError):m.thumb_bl(b'\x00'*4,0x08000000)
    def test_nonterminal_run(self):
        run={'head_sha':m.SOURCE,'head_branch':'codex/modernization-followup-20260908','repository':{'full_name':'dekaazarashi1111-web/pokemon-vega-modern'},'event':'push','path':m.WF,'status':'in_progress','conclusion':None,'run_attempt':1}
        with self.assertRaises(ValueError):m.terminal(run,{},m.SOURCE,m.WF,'native')
    def test_non_success_step(self):
        run={'id':1,'head_sha':m.SOURCE,'head_branch':'codex/modernization-followup-20260908','repository':{'full_name':'dekaazarashi1111-web/pokemon-vega-modern'},'event':'push','path':m.WF,'status':'completed','conclusion':'success','run_attempt':1}
        job={'run_id':1,'head_sha':m.SOURCE,'name':'native','status':'completed','conclusion':'success','steps':[{'status':'completed','conclusion':'failure','name':'Run actions/upload-artifact@v4'}]}
        with self.assertRaises(ValueError):m.terminal(run,{'total_count':1,'jobs':[job]},m.SOURCE,m.WF,'native')


def item_fixture(op='spend',phase=0):
    rows=fixture(op,1 if phase==4 else phase)
    rows[-1]['candidate_sha256']=m.bag.CANDIDATE['sha256']
    if phase==4:
        rows[-1].update(phase=4,result=15,phase1=0)
        for row in rows[:4]:row['item_quantity']=999
    return rows


def bundle_fixture(items=False):
    # Synthetic process receipts, never published or treated as Actions proof.
    sources=m.ITEM_SOURCES if items else m.SOURCES
    source=m.ITEM_SOURCE if items else m.SOURCE;run=36229762846 if items else 36229142708
    texts={p:('synthetic:'+p).encode() for p in sources}
    texts[m.C]=(m.ROOT/m.C).read_bytes()
    bindings={p:m.identity(b) for p,b in texts.items()}
    files={p:b'' for p in (m.ITEM_MEMBERS if items else m.MEMBERS)}
    def write(path,value):files[path]=json.dumps(value).encode()
    inputs={'source_head':source,'run_id':run,'candidate':m.bag.CANDIDATE if items else m.repair.CANDIDATE,'seed':m.SEED,'source_bindings':bindings,'artifacts':m.ARTIFACT_INPUTS}
    if items:
        files['generated-items.c']=m.bag.item_runner(texts[m.C]);inputs.update(generated_harness=m.identity(files['generated-items.c']),canonical_source_after=m.bag.SOURCE_AFTER)
        write('invocation.json',{'source_head':source,'run_id':run})
        write('bag-repair.json',{'parent':m.bag.PARENT,'candidate':m.bag.CANDIDATE,'changed_bytes':2,'rollback_verified':True,'outside_declared_changes':0,'source_before':m.bag.SOURCE_BEFORE,'source_after':m.bag.SOURCE_AFTER})
    else:inputs['prior_terminal']={'id':36221094800,'head_sha':'e6135fb6cd22abbd9a25d3712a7a7b389d71042a','status':'completed','conclusion':'success'}
    write('inputs.json',inputs)
    write('repair.json',{'parent':m.repair.PARENT,'candidate':m.repair.CANDIDATE,'changed_bytes':1,'rollback_verified':True,'arm_compiles':0})
    write('compile.json',{'source_bindings':bindings,'returncode':0,'executable':{'size':50000,'sha256':'e'*64},'command':['cc','/synthetic/generated-items.c' if items else m.C,'-lmgba','-Werror']})
    guards={}
    for g in m.GUARDS:
        files[f'guard-{g}.stderr.txt']=m.DENIED;guards[g]={'returncode':1,'stdout':m.identity(b''),'stderr':m.identity(m.DENIED)}
    write('guards.json',guards)
    cases={};failures={}
    for key in (m.ITEM_CASES if items else m.CASES):
        op,p=key.rsplit('-',1);p=int(p);failed=not items and op in ('spend','rank')
        rows=item_fixture(op,p) if items else fixture(op,p)
        out=packed(rows[:1] if failed else rows);err=m.STDERR+(b'research-save-impact: transaction result\n' if failed else b'')
        if items:
            v=rows[-1];err+=f"item boundary result={v['result']} saves={v['delegate_saves']} loads=0 phases=0/{v['phase1']}/{v['phase2']}\n".encode()
        files[key+'.stdout.txt']=out;files[key+'.stderr.txt']=err
        process={'returncode':int(failed),'timeout':False,'source_head':source,'seed':m.SEED,'stdout':m.identity(out),'stderr':m.identity(err),'private_final_save':{'size':131088,'sha256':'f'*64}}
        cases[key]=process;write(key+'.process.json',process)
        if failed:failures[key]=process
    write('measurement.json',{'source_head':source,'run_id':run,'failures':failures,'cases':cases,'native_processes':len(cases),'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,'normal_transaction_ui_accepted':False,'status':'MEASURED_NOT_YET_ACCEPTED'})
    return files,source,run,texts


class BagAndBundleContract(unittest.TestCase):
    def verify(self,parts,items=False):
        f,s,r,t=parts;return m.validate_bundle(f,s,r,lambda p:t[p],items)
    def mutate(self,items,name,field,value):
        parts=bundle_fixture(items);row=json.loads(parts[0][name]);row[field]=value;parts[0][name]=json.dumps(row).encode()
        with self.assertRaises((ValueError,KeyError,TypeError)):self.verify(parts,items)
    def test_old_partial_bundle_not_relabelled(self):
        r=self.verify(bundle_fixture());self.assertEqual(r['accepted_cases'],8);self.assertEqual(len(r['failures']),8)
    def test_item_bundle_ten_cases(self):self.assertEqual(self.verify(bundle_fixture(True),True)['accepted_cases'],10)
    def test_all_item_contracts(self):
        for op in ('spend','rank'):
            for phase in range(5):
                with self.subTest(op=op,phase=phase):m.native_result(packed(item_fixture(op,phase)),op,phase,m.bag.CANDIDATE)
    def test_full_stack_no_debit(self):
        a=item_fixture(phase=4);b=bytearray.fromhex(a[2]['owner']);struct.pack_into('<H',b,4,400);a[2]['owner']=b.hex()
        with self.assertRaises(ValueError):m.native_result(packed(a),'spend',4,m.bag.CANDIDATE)
    def test_full_stack_no_save(self):
        a=item_fixture(phase=4);a[-1]['delegate_saves']=1
        with self.assertRaises(ValueError):m.native_result(packed(a),'spend',4,m.bag.CANDIDATE)
    def test_full_stack_requires_native_quantity(self):
        a=item_fixture(phase=4);a[0]['item_quantity']=1
        with self.assertRaises(ValueError):m.native_result(packed(a),'spend',4,m.bag.CANDIDATE)
    def test_absent_item_not_workaround_seed(self):
        a=item_fixture();a[0]['item_quantity']=1
        with self.assertRaises(ValueError):m.native_result(packed(a),'spend',0,m.bag.CANDIDATE)
    def test_full_stack_not_old_candidate(self):
        with self.assertRaises(ValueError):m.native_result(packed(item_fixture(phase=4)),'spend',4)
    def test_old_failures_cannot_be_cleared(self):self.mutate(False,'measurement.json','failures',{})
    def test_no_inherited_ui_acceptance(self):self.mutate(True,'measurement.json','normal_transaction_ui_accepted',True)
    def test_wrong_input_artifact(self):self.mutate(True,'inputs.json','artifacts',[])
    def test_wrong_input_run(self):self.mutate(True,'inputs.json','run_id',1)
    def test_source_bindings_closed(self):self.mutate(True,'inputs.json','source_bindings',{})
    def test_source_changed_after_measurement(self):
        p=bundle_fixture(True);p[3][m.C]+=b'\n'
        with self.assertRaises(ValueError):self.verify(p,True)
    def test_failed_host_compile_rejected(self):self.mutate(True,'compile.json','returncode',1)
    def test_boolean_host_compile_return_rejected(self):self.mutate(True,'compile.json','returncode',False)
    def test_compile_warning_rejected(self):
        p=bundle_fixture(True);p[0]['compile.stderr.txt']=b'warning'
        with self.assertRaises(ValueError):self.verify(p,True)
    def test_generated_runner_changed(self):
        p=bundle_fixture(True);p[0]['generated-items.c']+=b'\n'
        with self.assertRaises(ValueError):self.verify(p,True)
    def test_missing_item_evidence(self):
        p=bundle_fixture(True);del p[0]['rank-4.stdout.txt']
        with self.assertRaises(ValueError):self.verify(p,True)
    def test_native_failure_cannot_be_overwritten(self):
        p=bundle_fixture();p[0]['spend-0.stdout.txt']=packed(fixture('spend'))
        with self.assertRaises(ValueError):self.verify(p)
    def test_bad_guard_output_rejected(self):
        p=bundle_fixture(True);p[0]['guard-raw8.stderr.txt']=b'wrong'
        with self.assertRaises(ValueError):self.verify(p,True)
    def test_wrong_recipe_parent_rejected(self):
        with self.assertRaises(ValueError):m.bag.apply(b'not a ROM')
    def test_wrong_recipe_source_rejected(self):
        with self.assertRaises(ValueError):m.bag.correct_source(b'not the canonical source')
    def test_frozen_harness_generation(self):
        raw=(m.ROOT/m.C).read_bytes();generated=m.bag.item_runner(raw)
        self.assertIn(m.bag.CANDIDATE['sha256'].encode(),generated)
        self.assertNotIn(m.bag.PARENT['sha256'].encode(),generated)
        self.assertIn(b'kind==3||kind==4',generated)
        self.assertIn(b'full stack: ownership but no real capacity',generated)
        self.assertIn(b'absent item: no ownership but real capacity',generated)
    def test_unfrozen_harness_rejected(self):
        with self.assertRaises(ValueError):m.bag.item_runner((m.ROOT/m.C).read_bytes()+b'\n')
    def test_canonical_source_fix_only_one_macro(self):
        raw=(m.ROOT/m.bag.SOURCE).read_bytes()
        if m.identity(raw)==m.bag.SOURCE_AFTER:raw=raw.replace(b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099A09u)',b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099949u)')
        out=m.bag.correct_source(raw);self.assertEqual(m.identity(out),m.bag.SOURCE_AFTER)
        self.assertEqual(raw.replace(b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099949u)',b'#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099A09u)'),out)
    def test_source_fix_fails_closed_on_unrelated_edit(self):
        with self.assertRaises(ValueError):m.bag.correct_source((m.ROOT/m.bag.SOURCE).read_bytes()+b'\n')


if __name__=='__main__':unittest.main()
