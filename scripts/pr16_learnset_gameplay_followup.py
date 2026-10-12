#!/usr/bin/env python3
"""新規UI検証の早すぎるpage入力を修復。最初の失敗/20試験を保存継承。"""
from __future__ import annotations
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import pr16_learnset_gameplay as m
from pr16_wiki_reconcile import fetch
RUN=35830398856
HEAD='a906a09cc8537c04f9e6d1dd760634301bef9b3c'
ARTIFACT={'id':10737350300,'name':'pr16-learnset-gameplay-proof','size_in_bytes':39464,
          'digest':'sha256:deb89bccb9878ffe0a80fa1fd0e46f18e7cee9e51cc3b792b5f70f8e99473a8d'}
EXTRA={'scripts/pr16_learnset_gameplay_followup.py','tests/test_pr16_learnset_gameplay_followup.py'}
ORIGINAL_RUN=m.run


def replace_once(text, old, new):
    m.need(text.count(old)==1,'UI source anchor absent/duplicated')
    return text.replace(old,new)


def render(text):
    text=replace_once(text,'if(menu>1 && menu<6 && !t.page_menu)t.page_menu=stamp;',
        'if(menu>1 && menu<6 && !t.page_menu){t.page_menu=stamp;fprintf(stderr,"PAGE_OPEN frame=%u count=%u mode=%u\\n",stamp,menu,read8(c,A_MODE));}')
    text=replace_once(text,'if(!t.page_choice){if(action==5)',
        '/* Task data becomes visible before cursor initialization completes. */\n'
        '                if(stamp-t.page_menu<60U){key=0;}\n'
        '                else if(!t.page_choice){fprintf(stderr,"PAGE_INPUT frame=%u count=%u down_sent=%u target=%u mode=%u\\n",stamp,menu,page_down,page,read8(c,A_MODE));if(action==5)')
    text=replace_once(text,'if((state==4 || state==6) && !t.list){a_list(c,p,count,moves);t.list=stamp;}',
        'if((state==4 || state==6) && !t.list){\n'
        '            fprintf(stderr,"PAGE_RESULT frame=%u family=%u page=%u mode=%u count=%u expected=%u\\n",stamp,family,page,read8(c,A_MODE),read8(c,p+0x1a),count+1);\n'
        '            if(family==3)a_require(read8(c,A_MODE)==3U+page,"physical page selection differs");\n'
        '            a_list(c,p,count,moves);t.list=stamp;}')
    return text


def inherit():
    run=fetch('actions/runs/'+str(RUN))
    m.need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure','prior run boundary')
    meta=fetch('actions/artifacts/'+str(ARTIFACT['id']))
    m.need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired'] and meta['workflow_run']['head_sha']==HEAD,'prior artifact metadata')
    raw=fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
    m.need(m.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'prior artifact digest')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m.need(len(z.namelist())==len(set(z.namelist())) and sum(x.file_size for x in z.infolist())<2000000,'prior ZIP bounds')
        import json
        proof=json.loads(z.read('verification.json'))
        m.need(proof['status']=='FAIL' and proof['source_head']==HEAD and proof['new_unit_tests']==20
               and proof['cases']==[] and proof['new_native_processes']==1
               and proof['active_case']=='machine-page4-replace','prior successful-prefix boundary')
        for name in ('unit.stderr.txt','unit.stdout.txt','machine-page4-replace.stderr.txt','verification.json'):
            data=z.read(name)
            if name!='verification.json':m.need(m.identity(data)==proof['proof_bindings'][name],'prior member hash')
            (m.PROOF/('first-'+name)).write_bytes(data)
        unit=z.read('unit.stderr.txt')
        m.need(unit.count(b' ... ok\n')==20 and b'Ran 20 tests' in unit and unit.rstrip().endswith(b'OK'),'prior unit pass')
        for name in ('tests/test_pr16_learnset_gameplay.py','tools/mgba_pr16_learnset_gameplay.c'):
            m.need(m.identity((m.ROOT/name).read_bytes())==proof['source_bindings'][name],'prior tested contract source')
        old=subprocess.check_output(['git','show',HEAD+':scripts/pr16_learnset_gameplay.py'],cwd=m.ROOT).decode()
        expected=old.replace("SCOPE = 'ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE'", "ARCHIVE_TRANSFORM = lambda text: text\nSCOPE = 'ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE'")
        expected=expected.replace("archive=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()", "archive=ARCHIVE_TRANSFORM((ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text())")
        m.need((m.ROOT/'scripts/pr16_learnset_gameplay.py').read_text()==expected,'20-test semantic source unchanged except explicit transform hook')
    m.write(m.PROOF/'inherited-unit.json',{'source_head':HEAD,'run_id':RUN,'artifact':ARTIFACT,
        'inherited_tests':20,'tests_rerun':0,'prior_native_accepted':False,
        'prior_stop':'first raw page4 selected mode5 before candidate list assertion; no accepted cases',
        'original_conclusion':'failure','contract_source_changes':'only explicit generated UI transform hook'})


def command(args,name,timeout=240):
    if name=='unit':
        inherit()
        m.need(args[1:]==['-B','-m','unittest','tests.test_pr16_learnset_gameplay','-v'],'old suite invocation')
        args=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_gameplay_followup','-v']
    return ORIGINAL_RUN(args,name,timeout)


def execute():
    m.ARCHIVE_TRANSFORM=render;m.run=command
    try:m.execute()
    finally:
        p=m.PROOF/'verification.json'
        if p.exists():
            v=m.load(p);v['inherited_unit_tests']=20;v['previous_failed_run']=RUN
            v['ui_followup']='page Task initialization settles for 60 frames before physical inputs; selected mode asserted'
            m.write(p,v)


def install_hook():
    # Exact two-line tracked edit; the same run records its bytes and commits it.
    import importlib
    p=m.ROOT/'scripts/pr16_learnset_gameplay.py'
    old=subprocess.check_output(['git','show',HEAD+':scripts/pr16_learnset_gameplay.py'],cwd=m.ROOT).decode()
    expected=old.replace("SCOPE = 'ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE'", "ARCHIVE_TRANSFORM = lambda text: text\nSCOPE = 'ISSUE19_ORDINARY_BAG_SAVE_CONTINUE_WITH_INITIAL_FIXTURE'")
    expected=expected.replace("archive=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()", "archive=ARCHIVE_TRANSFORM((ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text())")
    m.need(p.read_text() in (old,expected),'unexpected runner before explicit two-line hook edit')
    if p.read_text()==old:p.write_text(expected)
    importlib.reload(m)


if __name__=='__main__':
    install_hook()
    m.CODE|=EXTRA
    actions={'execute':execute,'record':m.record,'guard':m.guard,'paths':lambda:print('\n'.join(sorted(m.owned()|m.CODE)))}
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required')
    actions[sys.argv[1]]()
