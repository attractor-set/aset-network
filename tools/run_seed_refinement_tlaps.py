#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FORMAL=ROOT/'extension/canonical/formal'; PROOF=FORMAL/'NetworkExtensionSeedRefinementProofs.tla'; BRIDGE=FORMAL/'NetworkExtensionSeedRefinement.tla'; EVID=ROOT/'extension/canonical/assurance/seed-refinement-proof.json'; BIND=ROOT/'upstream/ASET_SEED_BINDING.json'
VER='4600b24'; COMMIT='4600b24c6d95a25ff081ad37b63b2a01c29d43a5'; SEED_COMMIT='633c130187b2a2bb42f24cfd66662d475de385d2'; SEED_SHA='1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926'; THEOREMS=['NetworkExtensionRefinesSeedSafetySpec','NetworkProjectionMatchesSeedResolution']
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--tlapm',type=Path,required=True); ap.add_argument('--seed-root',type=Path,default=Path.home()/'ASET'); ap.add_argument('--output',type=Path,default=ROOT/'dist/network-seed-refinement-proof.json'); ap.add_argument('--timeout-seconds',type=int,default=900); a=ap.parse_args(); tl=a.tlapm.expanduser().resolve(); sf=a.seed_root.expanduser().resolve()/'seed/canonical/formal'; seed=sf/'SeedResolution.tla'; errs=[]; e=json.loads(EVID.read_text()); b=json.loads(BIND.read_text())
 if b['seed_release_commit']!=SEED_COMMIT: errs.append('Seed release mismatch')
 if not seed.is_file() or h(seed)!=SEED_SHA: errs.append('SeedResolution.tla digest mismatch')
 if e['proof_gate']['final_theorems']!=THEOREMS: errs.append('theorem set mismatch')
 for p,key in [(BRIDGE,'mapping'),(PROOF,'proof')]:
  if e['network_artifacts'][key]['sha256']!='sha256:'+h(p): errs.append(f'{key} digest mismatch')
 if not tl.is_file() or not os.access(tl,os.X_OK): errs.append(f'missing executable TLAPM: {tl}')
 vo=''; out=''; rc=None
 if not errs:
  vr=subprocess.run([str(tl),'--version'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); vo=vr.stdout.strip();
  if vo!=VER: errs.append(f'unexpected TLAPM version: {vo!r}')
 if not errs:
  shutil.rmtree(ROOT/'.tlacache',ignore_errors=True); rr=subprocess.run([str(tl),'-I',str(FORMAL),'-I',str(sf),str(PROOF)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=a.timeout_seconds); out=rr.stdout; rc=rr.returncode; print(out,end='' if out.endswith('\n') else '\n');
  if rc: errs.append(f'TLAPM returned {rc}')
 m=re.findall(r'All ([0-9]+) obligations? proved\.',out); obligations=int(m[-1]) if m else None
 if not errs and obligations is None: errs.append('TLAPM success summary missing')
 if not errs and e['status']=='MECHANICALLY_PROVED' and (e['proof_gate'].get('verdict')!='MECHANICALLY_PROVED' or obligations!=e['proof_gate'].get('obligations_proved')): errs.append('materialized Seed proof count/verdict mismatch')
 verdict='PASS' if not errs else 'FAIL'; report={'document_type':'aset-network-seed-tlaps-refinement-report','schema_version':1,'tlapm_commit':COMMIT,'tlapm_version':vo,'seed_release_commit':SEED_COMMIT,'seed_resolution_sha256':'sha256:'+h(seed) if seed.is_file() else None,'bridge_sha256':'sha256:'+h(BRIDGE),'proof_sha256':'sha256:'+h(PROOF),'final_theorems':THEOREMS,'obligations_proved':obligations,'returncode':rc,'errors':errs,'verdict':verdict}; op=a.output if a.output.is_absolute() else ROOT/a.output; op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(f'NETWORK_SEED_TLAPS_VERDICT={verdict}');
 for x in errs: print(f'NETWORK_SEED_TLAPS_ERROR={x}')
 return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
