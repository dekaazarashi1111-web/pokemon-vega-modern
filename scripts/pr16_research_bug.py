#!/usr/bin/env python3
"""実虫取りNPCの新規2ケース専用oracle。写真/保存viewの受入は再実行しない。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_research_photo as photo
import pr16_research_map_view as view
need, identity, load, exact = photo.need, photo.identity, photo.load, photo.exact
ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_bug.c'
RAW = 'content/modernization/pr16_research_bug_measurement.json'
CANDIDATE = {'size':33554432,'sha256':'26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da'}
CASES = ('bug-missing-type-rejected','bug-earn-duplicate-cold')
UNRELATED = 'f94facc9b8c3ff8c744aab1065f7662b386e5ab8d78646d17d60f495ff26884e'
LEDGERS = ('bdaae0a71b80b9dd0f133c1633bf13863fd6d42a9f3364c557e2db0ea12356ce',
           '8e0b80cf4c77cb4a2abea07a01e82f9ec6011330003c3aa99899ba7c0a29abc5')
SCREENS = {
 'fixture-field':'bb80ac0ad5087bcb7a1649028774db491260cbd878ecaa90dd6bf09ac5db19dd',
 'missing-prompt':'17cf28de2d43489a99a1403b4a429cb484a3b90e7ef5c2614eb8d0d53bd09979',
 'missing-outcome':'dd1ebc4de9b91f40d4a4d036b03b88421ba80d18216a47811aeb7de996bd4c70',
 'decline-prompt':'17cf28de2d43489a99a1403b4a429cb484a3b90e7ef5c2614eb8d0d53bd09979',
 'earn-prompt':'17cf28de2d43489a99a1403b4a429cb484a3b90e7ef5c2614eb8d0d53bd09979',
 'earn-outcome':'15e649906e0d9887ee2bf437114d92f1e81522624ab4375d8747730515528437',
 'duplicate-prompt':'17cf28de2d43489a99a1403b4a429cb484a3b90e7ef5c2614eb8d0d53bd09979',
 'duplicate-outcome':'b6118da2d12d7f3ae43ffdf9f06315429045c20de01a41ed4b296b4f676c68af',
 'continued-field':'762524118ccf2705c63c171510b932a8b1749862934d19e9e83344c17c800c30',
 'cold_duplicate-prompt':'17cf28de2d43489a99a1403b4a429cb484a3b90e7ef5c2614eb8d0d53bd09979',
 'cold_duplicate-outcome':'b6118da2d12d7f3ae43ffdf9f06315429045c20de01a41ed4b296b4f676c68af'}


def generate(seed: bytes) -> bytes:
    need(exact(load((ROOT/view.RECIPE).read_bytes())['candidate'],CANDIDATE),'accepted successor recipe')
    source=photo.generate(seed).decode();token='int main(int argc,char**argv){'
    need(source.count(token)==1 and source.count(photo.CANDIDATE['sha256'])==1,'unique inherited main/identity')
    source=source.replace(token,'int accepted_photo_main(int argc,char**argv){').replace(photo.CANDIDATE['sha256'],CANDIDATE['sha256'])
    return (source+'\n'+(ROOT/C).read_text()).encode()


def physical(rom: bytes) -> dict:
    need(identity(rom)==CANDIDATE,'exact repaired ROM')
    def rd(a):return struct.unpack_from('<I',rom,a-0x08000000)[0]
    e=rd(0x092C0B80);record=rd(e+4)+24*10;script=rd(record+16)
    need((e,record,script)==(0x09413968,0x09413854,0x093C048C),'physical NPC chain')
    need(rom[record-0x08000000:record-0x08000000+24]==bytes.fromhex('0b1400002b000600030d1100000000008c043c0900000000'),'NPC local11 (43,6), flag0')
    root=rd(0x080001BC);types={i:list(rom[root-0x08000000+32*i+6:root-0x08000000+32*i+8]) for i in (1,39)}
    need(types=={1:[12,12],39:[6,6]},'actual Vega IDs, not National Dex inference')
    model=load((ROOT/photo.catalog.MODEL).read_bytes());row=model['activities'][3]
    need(row['activity']=='BUG_CATCHING' and row['points_awarded']==8 and row['daily_cap']==8,'fixed bug reward policy')
    dialogues=[r for r in model['dialogue'] if r['binding_key']=='BINDING_KEY_ACTIVITY_BUG']
    need(len(dialogues)==4,'all four bug dialogues')
    for r in dialogues:
        data=bytes.fromhex(r['encoded_hex']);a=r['runtime_address']-0x08000000
        need(rom[a:a+len(data)]==data,'candidate bug dialogue bytes')
    need('RESEARCH_RESULT_LOCKED = 3' in (ROOT/'overlays/research_economy_v1/research_economy_v1.h').read_text(),'native locked result enum')
    return dict(candidate=CANDIDATE,events=e,record=record,script=script,species_types=types,dialogues=dialogues,rom_changes=0)


def closing(case: str) -> dict:
    need(case in CASES,'closed new cases');earned=case==CASES[1]
    return dict(status='PASS',case=case,candidate_sha256=CANDIDATE['sha256'],fresh_cores=2 if earned else 1,
        earned_rp=8 if earned else 0,transaction_saves=2 if earned else 0,manual_saves=0,guarded_host_writes=0,
        accepted_case_reruns=0,natural_arrival_accepted=False,all_activities_accepted=False,warnings_errors=0)


def expected_owner(earned: bool) -> bytes:
    owner=bytearray(64);owner[0],owner[1],owner[6],owner[7],owner[36]=1,64,1,1,1
    if earned:owner[4]=owner[10]=owner[20]=8;owner[27]=1;owner[36]=2
    return bytes(owner)


def validate(raw: bytes, case: str, fixture: bytes | None = None) -> dict:
    """Goldenは実測digest。fixture指定時は独立に全2048byteを再構成する。"""
    need(type(raw) is bytes and 0<len(raw)<20000,'bounded native transcript');end=closing(case)
    rows=[load(line) for line in raw.splitlines()];earned=case==CASES[1]
    order=['setup','event','ledger_event','screen','screen']
    if earned:
        order+=['visit','event','ledger_event','screen','screen','visit','event','ledger_event','screen','screen','visit','event','ledger_event','event','ledger_event','screen','screen','screen','visit','event','ledger_event','status']
    else:order+=['screen','visit','event','ledger_event','status']
    need(len(rows)==len(order) and all(k in r for k,r in zip(order,rows)),'complete ordered transcript')
    need(exact(rows[0],dict(setup='bug',events=0x09413968,record=0x09413854,script=0x093C048C,species=39 if earned else 1,type1=6 if earned else 12,type2=6 if earned else 12,party_count=1,progression_is_fixture=True,rp_injected=False)),'fixture and physical root scope')
    need(exact(rows[-1],end),'closed terminal scope')
    labels=['fixture','declined','earned','duplicate','continued','cold_duplicate'] if earned else ['fixture','rejected']
    events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
    need([r['event'] for r in events]==labels and [r['ledger_event'] for r in ledgers]==labels,'stage order')
    bag='688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
    party='d9ea926f94efa66d166cebc959320a2ba49844469d4dc86d895b47f8a9a6aa0a' if earned else '76b3ec7e9dbf2fa0291f2eb5435d614c195c48d24ca957023bec32d8418eedbb'
    for i,(event,ledger) in enumerate(zip(events,ledgers)):
        paid=earned and i>=2;owner=expected_owner(paid)
        need(exact(event,dict(event=labels[i],counter=4 if paid else 2,item_quantity=0,inventory_sha256=bag,other_inventory_sha256=bag,party_sha256=party,party_count=1,owner=owner.hex())),'full party/Bag/owner/counter invariant')
        need(exact(ledger,dict(ledger_event=labels[i],version=2,size=2048,checksum_valid=True,ledger_sha256=LEDGERS[int(paid)],unrelated_ledger_sha256=UNRELATED,migration_dirty=0,recovery_blocked=0)),'full ledger checksums and unrelated owners')
        if fixture is not None:
            need(len(fixture)==131072,'complete original-derived fixture')
            old=photo.purchase.prior.prior.old;at=photo.purchase.prior.prior.OFFSET
            b=bytearray(fixture[at:at+2048]);b[0x73f:0x77f]=owner;b=old.seal(b)
            need(identity(b)['sha256']==ledger['ledger_sha256'],'independent full-ledger reconstruction')
            rest=bytearray(b);rest[4:6]=bytes(2);rest[8:12]=bytes(4);rest[0x73f:0x77f]=bytes(64)
            need(identity(rest)['sha256']==UNRELATED,'independent unrelated-ledger hash')
    visits=[r for r in rows if 'visit' in r];vl=['decline','earn','duplicate','cold_duplicate'] if earned else ['missing']
    need([r['visit'] for r in visits]==vl,'all physical visits');frame=899
    for i,row in enumerate(visits):
        f=photo.catalog.integer(row['frame'],frame+1,10000);frame=f
        result=(0 if i<2 else 4) if earned else 3
        need(exact(row,dict(visit=vl[i],confirmed=not(earned and i==0),result=result,rp=8 if earned and i>0 else 0,counter=4 if earned and i>0 else 2,frame=f)),'native result/credit/source order')
    names=['fixture-field','decline-prompt','earn-prompt','earn-outcome','duplicate-prompt','duplicate-outcome','continued-field','cold_duplicate-prompt','cold_duplicate-outcome'] if earned else ['fixture-field','missing-prompt','missing-outcome']
    screens=[r for r in rows if 'screen' in r]
    need(exact(screens,[dict(screen='bug-'+n+'.ppm',sha256=SCREENS[n]) for n in names]),'all independently reviewed native screens')
    return dict(end,observations=events,ledger_observations=ledgers,visits=visits,screens=screens,stdout=identity(raw))
