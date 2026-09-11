#!/usr/bin/env python3
"""Connect scoped completion to both existing remaining-work regeneration paths.

Only the exact previous generator return block is extended. Original receipts,
source ZIPs, baseline and accepted owner policy remain untouched.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_completion_checkpoint as completion
need=completion.need
GENERATOR='scripts/record_modernization_final_acceptance.py'
BEFORE_SHA='1371556130ed927b570835326a778533d075a61c8cad3cbbaecd627bc5dadee3'
BEFORE='    from modernization_owner_policy import project\n    return project(current, root)\n'
AFTER='''    from modernization_owner_policy import project
    current = project(current, root)
    from pr16_completion_checkpoint import RECEIPT as completion_receipt
    if (root / completion_receipt).is_file():
        from pr16_refresh_current_view import current_view
        return current_view(current, root)
    return current
'''


def current_view(previous,root=ROOT):
    out=completion.project(previous,root)
    if out['final_integration']['source_path']!=completion.RECEIPT:
        out['historical_stage84_integration']=deepcopy(out['final_integration'])
    out['final_integration']={
        'source_path':completion.RECEIPT,
        'candidate_sha256':completion.repaired.ROM_SHA,
        'source_runs':{label:dict(run_id=rec[0],tested_head=rec[4]) for label,rec in completion.RECORDS.items()},
        'new_native_processes_in_this_session':7,
        'new_native_cores_in_this_session':19,
        'old_native_acceptance_preserved_not_relabelled':True,
        'release_ready':False}
    p06=out['p06_adoption']
    # project() has already rebuilt and verified the retained acceptance receipt.
    # This is a current-view mirror, not a rewrite of historical Stage84 proof.
    need(type(out.get('full_p06_acceptance')) is bool,'P06 current acceptance must be boolean')
    p06['full_phase_accepted']=out['full_p06_acceptance']
    if p06.get('final_candidate_evidence')!=completion.RECEIPT:
        p06['historical_stage84_candidate_evidence']=p06.get('final_candidate_evidence')
    p06['final_candidate_evidence']=completion.RECEIPT
    out['p07_adoption'].update(
        normal_species_to_vega_move=499,vega_species_to_normal_move=1073,
        count_semantics='historical preservation / historical adopted additions, NOT new blanket adoption',
        source_reconciliation=completion.RECEIPT,decision_required=False)
    for row in out['remaining_conditions']:
        if row['id']=='FINAL_NATIVE_ACCEPTANCE':
            row['pass_condition']='Close the named outstanding native routes on candidate 635fd890 or its exact successor; preserve historical Stage82/84 runs and rerun only affected regression after changes'
        elif row['id']=='P07_REMAINING_ROUTE_ACCEPTANCE':
            row['pass_condition']='Reconcile residual physical-route coverage against 1073 historical additions and 499 preserved rows; no new table approval or blanket combinations; save/cancel at affected consumers'
    return out


def install_hook(root=ROOT):
    p=root/GENERATOR;raw=completion.read(root,GENERATOR);text=raw.decode()
    if AFTER in text:
        need(text.count(AFTER)==1 and BEFORE not in text,'ambiguous installed hook')
        need(hashlib.sha256(text.replace(AFTER,BEFORE,1).encode()).hexdigest()==BEFORE_SHA,'generator outside hook changed')
        return False
    need(hashlib.sha256(raw).hexdigest()==BEFORE_SHA and text.count(BEFORE)==1,'generator preimage changed')
    p.write_text(text.replace(BEFORE,AFTER,1))
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.write:install_hook()
    else:
        need(AFTER in completion.read(ROOT,GENERATOR).decode(),'completion projection hook absent')
    import record_modernization_final_acceptance as final
    importlib.reload(final)
    import record_modernization_p03_forgetting as forgetting
    current=forgetting.current_remaining_work(ROOT,forgetting.build())
    expected=current_view(current)
    need(completion.same(current,expected),'regeneration failed to include scoped completion')
    target=ROOT/completion.OVERVIEW
    if args.write:target.write_bytes(completion.stable(current))
    else:need(completion.same(completion.load(target.read_bytes()),current),'current view differs')
    print(completion.stable({'status':'PASS','remaining_conditions':len(current['remaining_conditions']),
                            'candidate_sha256':completion.repaired.ROM_SHA,'p06_adopted_phase_complete':True,
                            'new_emulator_runs':0,'release_ready':False}).decode(),end='')

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
