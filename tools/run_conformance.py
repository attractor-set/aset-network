from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from reference.network_reference import execute_case as execute_core
from reference.legacy_network_reference import execute_case as execute_legacy
from tools.dynamic_profile_conformance import run_profile_conformance
C=ROOT/'extension/canonical/conformance'

def run_manifest(path, executor, label):
 p=json.loads(path.read_text()); failures=[]
 for item in p['cases']:
  case=json.loads((ROOT/item['path']).read_text()); _,actual=executor(case)
  if actual!=case['expected']: failures.append((case['case_id'],case['expected'],actual))
 if failures:
  for cid,e,a in failures: print(f'FAIL {label} {cid}: expected={e} actual={a}')
  return False,len(p['cases'])
 print(f'OK: {len(p["cases"])} {label} conformance cases'); return True,len(p['cases'])

def main():
 ok1,_=run_manifest(C/'conformance-profile.json',execute_core,'core')
 dyn=run_profile_conformance(); ok2=not dyn
 for cid,e,a in dyn: print(f'FAIL dynamic-profile {cid}: expected={e} actual={a}')
 if ok2: print('OK: dynamic-profile conformance cases')
 ok3,_=run_manifest(C/'federation-profile-conformance-profile.json',execute_legacy,'federation-profile')
 return 0 if ok1 and ok2 and ok3 else 1
if __name__=='__main__': raise SystemExit(main())
