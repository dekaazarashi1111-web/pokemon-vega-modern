#!/usr/bin/env python3
"""保存済みJP計測原本とActions終端だけを照合。ROM/nativeを再実行しない。"""
import json
from pathlib import Path
import pr16_dex_hof_jp_consumer_probe as probe
ROOT=Path(__file__).resolve().parents[1]
CP='content/modernization/pr16_dex_hof_jp_consumer_probe_terminal.json'
EVIDENCE='content/modernization/pr16_dex_hof_jp_consumer_probe_evidence'
HEAD='dd69e1253b7705ad2fc5ebe9c69723b3308e114a'
MEASURED={'size':49671,'sha256':'c800071446877641d8745054163d5f67040dbfec5c442feb588c858cfc954436'}
TESTS={'size':94,'sha256':'23ff586778bb4d645430ad8925f2727bd73b083d9ab3dd04b83fbf8d5227bb82'}
need=probe.need


def validate(receipt,raw,tests_raw):
    need(probe.identity(raw)==MEASURED and probe.identity(tests_raw)==TESTS,'取得artifact内の全文原本identity')
    report=json.loads(raw);probe.validate_report(report)
    need(receipt['source_head']==report['source_head']==HEAD and receipt['run_id']==report['run_id']==37688855091 and receipt['run_attempt']==1 and receipt['conclusion']=='success','初回終端と測定source')
    need(receipt['measurement_path']==EVIDENCE+'/measurement.json' and receipt['tests_path']==EVIDENCE+'/probe-tests.json' and receipt['measurement_identity']==MEASURED and receipt['tests_identity']==TESTS,'保存先とproducer原本')
    job=receipt['job'];steps=job['steps']
    need(job['id']==113023572648 and job['run_id']==37688855091 and job['status']=='completed' and job['conclusion']=='success' and len(steps)==10 and all(s['status']=='completed' and s['conclusion']=='success' for s in steps),'全10step終端')
    artifact=receipt['artifact']
    need(artifact['id']==11512656180 and artifact['name']=='pr16-jp-consumer-probe-text-only' and artifact['size_in_bytes']==7863 and artifact['digest']=='sha256:30abe9cfde2d7e69f3eb25566110a78a264ee9f59967f363860ddef22121f8fc' and artifact['workflow_run']['id']==37688855091 and artifact['workflow_run']['head_sha']==HEAD and artifact['expired'] is False,'取得時artifact完全identity')
    need(json.loads(tests_raw)==dict(status='PASS_NEW_SYNTHETIC_TESTS',tests=59,failures=0,errors=0,skipped=0),'新59試験終端原本')
    for key in ('classified','unclassified','newly_classified','native_processes','all_api_arguments_proven','serializer_execution_proven','formal_rom_changed','formal_save_changed','donor_eligible','current_rom_reconstructions','current_owner_count','unit_tests'):
        need(type(receipt[key]) is type(report[key]) and receipt[key]==report[key],'原本scope保持 '+key)
    need(receipt['status']=='RECORDED_CURRENT_JP_LEXICAL_AND_POINTER_OBSERVATION_ONLY','型受入へ昇格しない')
    need(receipt['registered_cells_verified']==sum(c['matches_expected'] for c in report['cells'])==2,'実2cell')
    need(receipt['lexical_eos_extents']==[t['size']for t in report['texts'].values()]==[30,27,24,38],'実字句EOS extent')
    need(receipt['explored_function_entries']==len(report['functions'])==14 and receipt['explored_instructions']==sum(f['instruction_count']for f in report['functions'].values())==653 and receipt['explored_contiguous_windows']==sum(len(f['windows'])for f in report['functions'].values())==28,'限定CFG観測の計数')
    need(all([r['owners'][0]['role']for r in hit['byte_roles']]==['pause_until_press','pause_until_press','eos','glyph'] and all(len(r['owners'])==1 for r in hit['byte_roles']) for hit in report['hits']),'両4byteの観測境界partition')
    return dict(status='PASS_RETAINED_JP_CANDIDATE_MEASUREMENT_ONLY',newly_classified=0,native_processes=0)


def main():
    result=validate(json.loads((ROOT/CP).read_bytes()),(ROOT/EVIDENCE/'measurement.json').read_bytes(),(ROOT/EVIDENCE/'probe-tests.json').read_bytes())
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
