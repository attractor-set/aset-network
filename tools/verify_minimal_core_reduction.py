from __future__ import annotations
import copy, json, sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from reference.legacy_network_reference import apply_transition
from tools.dynamic_profile_conformance import validate_wire_object
CANON=ROOT/'extension/canonical'
REDUCTION=CANON/'assurance/minimal-core-reduction.json'
FED=CANON/'protocol/federation-profile.json'
FED_DEF=CANON/'protocol/profiles/federation-profile-definition.json'
LEGACY=CANON/'conformance/legacy-alpha2-cases'

def project(state:dict[str,Any]|None)->dict[str,Any]:
    return {'imports': copy.deepcopy((state or {}).get('imports',{}))}

def verify_profile_definition():
    d=json.loads(FED_DEF.read_text()); ok,code=validate_wire_object('PROFILE_DEFINITION',d)
    if not ok: raise SystemExit(f'federation profile definition invalid: {code}')

def verify_decomposition():
    r=json.loads(REDUCTION.read_text()); f=json.loads(FED.read_text())
    if r['candidate']['semantic_state_fields']!=['imports'] or r['candidate']['transition_kinds']!=['ADMIT_IMPORT']:
        raise SystemExit('normative minimal core is not imports + ADMIT_IMPORT')
    if r.get('normative') is not True or r.get('status')!='NORMATIVE_CUTOVER_ALPHA3':
        raise SystemExit('minimal-core reduction is not normative cutover')
    e=f['extraction_semantics']
    if e['normative_core_changed_by_this_slice'] is not True or e['phase']!='NORMATIVE_PROFILE_AFTER_CORE_CUTOVER':
        raise SystemExit('federation profile is not post-cutover')
    if e['network_admission_state_retained']!=['imports'] or e['seed_derived_legacy_state_fields']!=['recognitions']:
        raise SystemExit('federation cutover ownership mismatch')

def verify_conformance_trace_projection()->int:
    r=json.loads(REDUCTION.read_text()); fed=set(r['decomposition']['federation_profile_transition_kinds']); seed=set(r['decomposition']['seed_derived_transition_kinds'])
    count=success=0
    for p in sorted(LEGACY.rglob('*.json')):
        c=json.loads(p.read_text()); state=copy.deepcopy(c['initial_state'])
        for tr in c['steps']:
            before=project(state); state,res=apply_transition(state,tr); after=project(state); kind=tr['kind']
            if kind=='OBSERVE_IMPORT':
                if res['accepted'] and res['state_changed']:
                    if len(set(after['imports'])-set(before['imports']))!=1: raise SystemExit(f"{c['case_id']}: admission projection not append")
                    success+=1
                elif after!=before: raise SystemExit(f"{c['case_id']}: rejected/replay observe changed projection")
            elif kind in fed or kind in seed:
                if after!=before: raise SystemExit(f"{c['case_id']}: {kind} must stutter")
            else: raise SystemExit(f"{c['case_id']}: unclassified legacy transition {kind}")
            if not res['accepted']: break
        count+=1
    if success==0: raise SystemExit('legacy traces exercised no successful admission')
    return count

def main():
    verify_profile_definition(); verify_decomposition(); n=verify_conformance_trace_projection()
    print('OK: federation profile definition is valid dynamic-profile evidence')
    print('OK: normative minimal core state_fields=1 transition_kinds=1')
    print(f'OK: legacy reduction conformance traces={n}')
    print('OK: federation/Seed-derived legacy transitions stutter under admission projection')
    return 0
if __name__=='__main__': raise SystemExit(main())
