"""固定履歴入力だけの初回読取測定。現候補/native/保存は実行しない。"""
import io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_consumer_tutor as tutor
import pr16_dex_publication as publication
need,identity,write=prior.need,prior.identity,prior.write
BASE='afa090a1d28aa3776bc1f7c9875051cbbaa16439'
WF='.github/workflows/pr16-dex-hof-tutor-history.yml';SELF='scripts/pr16_dex_hof_tutor_history_actions.py';GUIDE='docs/PR16_DEX_HOF_TUTOR_HISTORY_JA.md'
CODE={WF,SELF,GUIDE,'scripts/pr16_dex_hof_consumer_tutor.py','tests/test_pr16_dex_hof_consumer_tutor.py'}
OUT=ROOT/'.local/pr16-dex-hof-tutor-history';PUBLIC=ROOT/'public-dex-hof-tutor-history';ARTIFACT='pr16-dex-hof-tutor-history-text-only'
FILES={'historical.json','host-tests.txt','receipt.json'}

def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/prior.STATE).read_bytes());need(not state['pending_runs']and prior.bindings(state['source_bindings'])==state['source_bindings'],'all prior accepted and pending state unchanged')

def run():
 import test_pr16_dex_hof_consumer_tutor as tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'fresh historical readonly scope');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  sources={}
  for path,sha in tutor.SOURCE_BLOBS.items():
   file=ROOT/path
   if file.is_file()and not file.is_symlink():raw=file.read_bytes()
   else:
    prefix='vendor/upstream/CFRU-JP/';need(path.startswith(prefix),'only fixed public upstream fallback')
    with urllib.request.urlopen('https://raw.githubusercontent.com/kapibarasan000/CFRU-JP/e24a16fe39e27ae162faf5b78596d1f3df18489d/'+path.removeprefix(prefix),timeout=90)as response:raw=response.read(2000000)
   need(tutor.blob(raw)==sha,'entire fixed source binding');sources[path]=raw
  stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));need(result.wasSuccessful()and not result.skipped and result.testsRun==16,'all16 new historical semantic refusal cases');(PUBLIC/'host-tests.txt').write_text(stream.getvalue())
  path=tutor.fetch_archive(OUT/'private',ROOT,sources);historical=tutor.archive_input(path,ROOT,sources);proof=tutor.historical_probe(historical,ROOT,sources)
  write(PUBLIC/'historical.json',proof)
  write(PUBLIC/'receipt.json',dict(status='PASS_EXACT_HISTORICAL_READONLY_INPUT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),historical_candidate=tutor.HISTORICAL,historical_identity=identity((PUBLIC/'historical.json').read_bytes()),test_identity=identity((PUBLIC/'host-tests.txt').read_bytes()),unit_tests=result.testsRun,source_bindings=prior.bindings(CODE),historical_reconstructions=0,current_reconstructions=0,native_processes=0,current_classifications=0,donor_leased=False,formal_rom_changed=False,formal_save_changed=False))
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc())
  msg=str(exc);safe=msg if msg.startswith('historical numeric consumer semantic mismatch at 0x')else type(exc).__name__
  print(json.dumps(dict(error_code='HISTORICAL_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',diagnostic=safe)))
  raise RuntimeError('HISTORICAL_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')from None

def export():
 publication.output(PUBLIC,success='receipt.json',failure=None)
 files={}
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in FILES and not p.name.startswith('.'),'closed regular historical text publication')
  raw=p.read_bytes();need(0<len(raw)<100000 and raw.endswith(b'\n')and b'\0'not in raw,'complete bounded historical text');raw.decode('utf8');files[p.name]=raw
 need(set(files)==FILES,'all complete historical outputs, never partial failure')
 m=json.loads(files['receipt.json']);h=json.loads(files['historical.json'])
 need(m['status']=='PASS_EXACT_HISTORICAL_READONLY_INPUT'and m['source_head']==os.environ['GITHUB_SHA']and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact source/run historical success')
 need(m['historical_identity']==identity(files['historical.json'])and m['test_identity']==identity(files['host-tests.txt'])and m['source_bindings']==prior.bindings(CODE),'whole proof/test/source envelopes')
 need(h['status']=='PASS_HISTORICAL_T09_NUMERIC_CONSUMER_ONLY'and h['historical_candidate']==tutor.HISTORICAL and h['historical_owner']==tutor.OWNER and h['hit']==tutor.HIT,'exact measured historical type only')
 need(m['unit_tests']==16 and all(m[k]==0 for k in('historical_reconstructions','current_reconstructions','native_processes','current_classifications'))and all(m[k]is False for k in('donor_leased','formal_rom_changed','formal_save_changed')),'no current/runtime promotion')
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','export'),'closed readonly historical workflow');globals()[sys.argv[1]]()
