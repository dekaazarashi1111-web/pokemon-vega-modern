#!/usr/bin/env python3
"""採掘専用の実入力検証。写真/虫取りの受入済み main は呼ばない。"""
from pathlib import Path
import pr16_research_bug as prior
ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_mining.c'
CANDIDATE = prior.CANDIDATE
CASES = ('mining-missing-badge', 'mining-missing-move', 'mining-earn-cold-cap')

def generate(seed: bytes) -> bytes:
    source = prior.generate(seed).decode()
    token = 'int main(int argc,char**argv){'
    prior.need(source.count(token) == 1, 'unique inherited main')
    return (source.replace(token, 'int accepted_bug_main(int argc,char**argv){') + '\n' + (ROOT/C).read_text()).encode()

# 原本のdigestはローカル実測。受入時はfixtureから全台帳を独立再構成する。
import struct
need, identity, load, exact = prior.need, prior.identity, prior.load, prior.exact
RAW = 'content/modernization/pr16_research_mining_measurement.json'
LEDGERS = ('14674d7af0c4b8d32abefb5661603456d9cc2aff92b29538cccff936ab50a913',
           prior.LEDGERS[0], 'e99966043f6740bcac26ee3a88e1ee1676c1a9e31b897c4efefc323298ece0f8')
SCREENS = {
 'fixture-field':'4048c868091cc587cabaf1e9e503ec8fed6abd925da4991d4a9c7ed6e7a36ea6',
 'locked-prompt':'c2f5e0297c57f9eea6109b98ea1095fa7901da431aeddd391a81fce94641d554',
 'decline-prompt':'b46ad50b405d455456f84602fb7d334ed9236342696c673faa74b86b89d0d039',
 'earn-prompt':'b46ad50b405d455456f84602fb7d334ed9236342696c673faa74b86b89d0d039',
 'earn-outcome':'55f4908027e23a8b2ccd6ac6236ba0be2fb110a62b4250a93c9dc285e31d0155',
 'continued-field':'f39db8b929bb1f621b5a0e7db32409e1e6fb3021c0f86feece3abcb820ea1244',
 'cold_cap-prompt':'b46ad50b405d455456f84602fb7d334ed9236342696c673faa74b86b89d0d039',
 'cold_cap-outcome':'30d8316915742af8b4de5f6ba08414d09eae8bc5a58e74d2357fae7834b64e48'}


def physical(rom: bytes) -> dict:
    need(identity(rom)==CANDIDATE,'exact repaired ROM')
    def rd(a): return struct.unpack_from('<I',rom,a-0x08000000)[0]
    e=rd(0x092C2568);r=rd(e+4);s=rd(r+16)
    need((e,r,s)==(0x09413B40,0x0941397C,0x093C050C),'actual mining pointer chain')
    need(rom[e-0x08000000:e-0x08000000+20]==bytes.fromhex('110400017c394109143b410900000000343b4109'),'current 17 templates / four warps')
    need(rom[r-0x08000000:r-0x08000000+24]==bytes.fromhex('0c6000000100140003011100000000000c053c0900000000'),'local12 rock(1,20), flag0')
    model=load((ROOT/prior.photo.catalog.MODEL).read_bytes())
    row=model['activities'][4]
    need(row['activity']=='MINING' and row['points_awarded']==row['daily_cap']==10,'10RP daily mining policy')
    dialogues=[v for v in model['dialogue'] if v['binding_key']=='BINDING_KEY_ACTIVITY_MINING']
    need(len(dialogues)==4,'all four mining dialogues')
    for row in dialogues:
        a=row['runtime_address']-0x08000000;v=bytes.fromhex(row['encoded_hex'])
        need(rom[a:a+len(v)]==v,'exact native mining string')
    return dict(candidate=CANDIDATE,events=e,record=r,script=s,object_templates=17,
                dialogues=dialogues,rom_changes=0,natural_arrival_accepted=False,wild_tail_accepted=False)


def closing(case: str) -> dict:
    need(case in CASES,'closed mining cases');paid=case==CASES[2]
    return dict(status='PASS',case=case,candidate_sha256=CANDIDATE['sha256'],fresh_cores=3 if paid else 1,
        earned_rp=10 if paid else 0,transaction_saves=2 if paid else 0,manual_saves=0,guarded_host_writes=0,
        accepted_case_reruns=0,natural_arrival_accepted=False,all_activities_accepted=False,warnings_errors=0)


def expected_owner(paid: bool, minute: int) -> bytes:
    v=bytearray(64);v[0],v[1],v[6],v[7],v[36]=1,64,1,minute,1
    if paid:
        struct.pack_into('<H',v,4,10);struct.pack_into('<I',v,10,10)
        struct.pack_into('<H',v,22,10);v[27]=2;struct.pack_into('<I',v,36,2)
    return bytes(v)


def validate(raw: bytes, case: str, fixture: bytes | None = None) -> dict:
    need(type(raw) is bytes and 0<len(raw)<20000,'bounded original stdout');end=closing(case)
    rows=[load(line) for line in raw.splitlines()];paid=case==CASES[2]
    order=['setup','event','ledger_event','screen','screen','visit','event','ledger_event']
    if paid: order+=['screen','screen','visit','event','ledger_event','event','ledger_event','screen','reentry_fixture','event','ledger_event','screen','screen','visit','event','ledger_event']
    order+=['status']
    need(len(rows)==len(order) and all(type(r) is dict and k in r for k,r in zip(order,rows)),'closed row count/order')
    need(exact(rows[0],dict(setup='mining',events=0x09413B40,record=0x0941397C,script=0x093C050C,
        badge=0 if case==CASES[0] else 1,move=33 if case==CASES[1] else 249,party_count=1,progression_is_fixture=True,rp_injected=False)),'actual setup / fixture scope')
    need(exact(rows[-1],end),'closed terminal / no expanded acceptance')
    labels=['fixture','declined','earned','continued','reentered','cold_cap'] if paid else ['fixture','rejected']
    events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
    need([r['event'] for r in events]==labels and [r['ledger_event'] for r in ledgers]==labels,'ordered snapshots')
    bag='688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
    party='f55719006008d0c6f12da4c63bfd652637f5420240bf8cdb1f14222bc48fd5af' if case==CASES[1] else 'd87f63c3bf5fa33e6b0702923541fd5e502f8b19f8f1c30f527effe9388102bc'
    for i,(event,ledger) in enumerate(zip(events,ledgers)):
        earned=paid and i>=2;owner=expected_owner(earned,int(i>0))
        need(exact(event,dict(event=labels[i],counter=4 if earned else 2,item_quantity=0,inventory_sha256=bag,
            other_inventory_sha256=bag,party_sha256=party,party_count=1,owner=owner.hex())),'full party600 / Bag / owner64 / counter')
        need(exact(ledger,dict(ledger_event=labels[i],version=2,size=2048,checksum_valid=True,
            ledger_sha256=LEDGERS[2 if earned else int(i>0)],unrelated_ledger_sha256=prior.UNRELATED,
            migration_dirty=0,recovery_blocked=0)),'full ledger2048 / unrelated owners / checksum')
        if fixture is not None:
            need(type(fixture) is bytes and identity(fixture)=={'size':131072,'sha256':'434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'},'original-derived fixture identity')
            old=prior.photo.purchase.prior.prior.old;at=prior.photo.purchase.prior.prior.OFFSET
            v=bytearray(fixture[at:at+2048]);v[0x73f:0x77f]=owner;v=old.seal(v)
            need(identity(v)['sha256']==ledger['ledger_sha256'],'independent full-ledger reconstruction')
            rest=bytearray(v);rest[4:6]=bytes(2);rest[8:12]=bytes(4);rest[0x73f:0x77f]=bytes(64)
            need(identity(rest)['sha256']==prior.UNRELATED,'independent unrelated owners')
    visits=[r for r in rows if 'visit' in r];names=['decline','earn','cold_cap'] if paid else ['locked']
    need([v['visit'] for v in visits]==names,'all physical visits');frame=899
    for i,v in enumerate(visits):
        frame=prior.photo.catalog.integer(v['frame'],frame+1,10000);earned=paid and i>0
        want=dict(visit=names[i],confirmed=not(paid and i==0),eligible=paid,result=4 if paid and i==2 else 0,
                  rp=10 if earned else 0,counter=4 if earned else 2,rock_count=0 if earned else 1,frame=frame)
        if earned: want['stopped_before_wild_tail']=True
        need(exact(v,want),'actual move / result / scope before wild tail')
    reentry=[v for v in rows if 'reentry_fixture' in v]
    need(exact(reentry,[dict(reentry_fixture=True,stock_warps=2,rp_injected=False,natural_reentry_accepted=False)] if paid else []),'cap starts with explicit reentry fixture')
    names=['fixture-field','decline-prompt','earn-prompt','earn-outcome','continued-field','cold_cap-prompt','cold_cap-outcome'] if paid else ['fixture-field','locked-prompt']
    screens=[v for v in rows if 'screen' in v]
    need(exact(screens,[dict(screen='mining-'+n+'.ppm',sha256=SCREENS[n]) for n in names]),'reviewed four native dialogues / complete images')
    return dict(end,observations=events,ledger_observations=ledgers,visits=visits,screens=screens,stdout=identity(raw),
                wild_tail_accepted=False,natural_reentry_accepted=False)
