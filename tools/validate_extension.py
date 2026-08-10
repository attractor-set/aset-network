from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry,Resource
from dynamic_profile_conformance import run_profile_conformance,validate_wire_object
from verify_minimal_core_reduction import verify_profile_definition,verify_decomposition,verify_conformance_trace_projection
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/'extension/canonical'; S=C/'protocol/schemas'; UP=ROOT/'upstream/ASET_SEED_BINDING.json'
EXPECTED_SEED={'seed_release_tag':'seed-0.3.0-alpha.3','seed_release_commit':'633c130187b2a2bb42f24cfd66662d475de385d2','compatibility_standard':'ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3','compatibility_standard_profile':'ASET-SEED-COMPATIBILITY-STANDARD-V1'}
EXPECTED_TLAPM={'required_commit':'4600b24c6d95a25ff081ad37b63b2a01c29d43a5','required_version':'4600b24'}
EXPECTED_PROOF_COUNTS={'canon':3,'seed':35,'legacy':23}
def sha(p): return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cb(v): return (json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
def self_digest(path,field):
 d=json.loads(path.read_text()); declared=d.pop(field); actual='sha256:'+hashlib.sha256(cb(d)).hexdigest()
 if declared!=actual: raise SystemExit(f'self-digest mismatch: {path.relative_to(ROOT)}')
 d[field]=declared; return d
def registry():
 resources=[]; schemas={}
 for p in sorted(S.glob('*.json')):
  d=json.loads(p.read_text()); Draft202012Validator.check_schema(d); resources.append((d['$id'],Resource.from_contents(d))); schemas[p.name]=d
 return Registry().with_resources(resources),schemas
def main():
 package=self_digest(C/'CANON_PACKAGE.json','package_digest')
 if package['extension_version']!='0.1.0-alpha.3' or package['canon_id']!='ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3': raise SystemExit('package identity mismatch')
 for item in package['files']:
  p=ROOT/item['path']
  if not p.is_file() or sha(p)!=item['sha256']: raise SystemExit(f"package digest mismatch: {item['path']}")
 model=json.loads((C/'source/network-extension-model.json').read_text())
 if model['version']!='0.1.0-alpha.3' or model['status']!='MINIMAL_ADMISSION_CORE_ALPHA3_NORMATIVE_CUTOVER': raise SystemExit('minimal core identity mismatch')
 if model['state_partition']['semantic_state_fields']!=['imports'] or model['transition_kinds']!=['ADMIT_IMPORT']: raise SystemExit('minimal core must be imports + ADMIT_IMPORT')
 if 'recognitions' in model['state'] or any(x in model['transition_kinds'] for x in ['RECORD_RECOGNITION','FEDERATION_GENESIS','MEMBER_JOIN','ROUTE_GRANT']): raise SystemExit('legacy semantics leaked into core')
 b=json.loads(UP.read_text())
 for k,v in EXPECTED_SEED.items():
  if b.get(k)!=v: raise SystemExit(f'upstream Seed binding mismatch: {k}')
 if b.get('compatibility')!='STRICT_EXTENSION_NO_WEAKENING' or b.get('implementation_precedence')!='NONE': raise SystemExit('Seed compatibility boundary mismatch')
 rel=self_digest(C/'formal/canon-tla-relation.json','relation_digest')
 if rel['profile']!='ASET-NETWORK-CANON-TLA-PROJECTION-V3': raise SystemExit('formal relation profile mismatch')
 for sec in ['source_model','target_model','seed_projection','history_model']:
  item=rel[sec]; p=ROOT/item['path'];
  if sha(p)!=item['sha256']: raise SystemExit(f"formal relation digest mismatch: {item['path']}")
 cp=rel['canon_projection'];
 for key,dkey in [('path','sha256'),('proof_path','proof_sha256')]:
  if sha(ROOT/cp[key])!=cp[dkey]: raise SystemExit(f'canon projection relation digest mismatch: {key}')
 gen=subprocess.run([sys.executable,str(ROOT/'tools/generate_canon_tla_projection.py'),'--check'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if gen.returncode: raise SystemExit(gen.stdout)
 canon=json.loads((C/'assurance/canon-tla-refinement.json').read_text()); ce=json.loads((C/'assurance/canon-refinement-proof.json').read_text()); se=json.loads((C/'assurance/seed-refinement-proof.json').read_text()); le=json.loads((C/'assurance/legacy-admission-refinement-proof.json').read_text())
 for name,d in [('canon',ce),('seed',se),('legacy',le)]:
  gate=d['proof_gate']
  if d['status']!='MECHANICALLY_PROVED' or gate['verdict']!='MECHANICALLY_PROVED': raise SystemExit(f'{name} proof must be mechanically proved')
  if gate['obligations_proved']!=EXPECTED_PROOF_COUNTS[name]: raise SystemExit(f'{name} proof obligation count mismatch')
  if gate.get('materialization')!='REPRODUCED_WITH_PINNED_TLAPM': raise SystemExit(f'{name} proof materialization marker mismatch')
  if d['tlapm']!=EXPECTED_TLAPM: raise SystemExit(f'{name} TLAPM binding mismatch')
 for item in ce['network_artifacts'].values():
  if item['sha256']!=sha(ROOT/item['path']): raise SystemExit(f"canon proof artifact digest mismatch: {item['path']}")
 for item in se['network_artifacts'].values():
  if item['sha256']!=sha(ROOT/item['path']): raise SystemExit(f"Seed proof artifact digest mismatch: {item['path']}")
 for item in le['artifacts'].values():
  if item['sha256']!=sha(ROOT/item['path']): raise SystemExit(f"legacy proof artifact digest mismatch: {item['path']}")
 if canon['generated_projection']['profile']!='ASET-NETWORK-CANON-TLA-PROJECTION-V3' or canon['source_model']['sha256']!=sha(C/'source/network-extension-model.json') or canon['target_model']['sha256']!=sha(C/'formal/NetworkExtension.tla'): raise SystemExit('canon refinement binding mismatch')
 if canon['status']!='MECHANICALLY_PROVED' or canon['proof_evidence'].get('status')!='MECHANICALLY_PROVED' or canon['proof_evidence'].get('obligations_proved')!=3: raise SystemExit('canon refinement materialization mismatch')
 reduction=json.loads((C/'assurance/minimal-core-reduction.json').read_text())
 if reduction['verification'].get('legacy_tlaps_status')!='MECHANICALLY_PROVED' or reduction['verification'].get('legacy_tlaps_obligations_proved')!=23: raise SystemExit('minimal-core legacy proof materialization mismatch')
 if rel['canon_projection'].get('status')!='MECHANICALLY_PROVED' or rel['canon_projection'].get('obligations_proved')!=3: raise SystemExit('formal relation canon proof status/count mismatch')
 if rel['seed_refinement'].get('status')!='MECHANICALLY_PROVED' or rel['seed_refinement'].get('obligations_proved')!=35: raise SystemExit('formal relation Seed proof status/count mismatch')
 if rel['legacy_alpha2_refinement'].get('status')!='MECHANICALLY_PROVED' or rel['legacy_alpha2_refinement'].get('obligations_proved')!=23: raise SystemExit('formal relation legacy proof status/count mismatch')
 r,schemas=registry(); protocol=json.loads((C/'protocol/protocol-profile.json').read_text())
 actual={p.name:sha(p) for p in S.glob('*.json')}
 if protocol['schema_count']!=len(actual) or {x['name']:x['sha256'] for x in protocol['schemas']}!=actual: raise SystemExit('protocol schema catalogue mismatch')
 core=json.loads((C/'conformance/conformance-profile.json').read_text())
 if core['profile_id']!='ASET-NETWORK-EXTENSION-CONFORMANCE-V2' or core['case_count']!=4: raise SystemExit('core conformance identity/count mismatch')
 cv=Draft202012Validator(schemas['conformance-case.schema.json'],registry=r)
 for item in core['cases']:
  p=ROOT/item['path']; case=json.loads(p.read_text()); errs=list(cv.iter_errors(case))
  if errs: raise SystemExit(f"core conformance schema invalid: {item['case_id']}: {errs[0].message}")
  if item['sha256']!=sha(p): raise SystemExit(f"core conformance digest mismatch: {item['case_id']}")
 dyn=run_profile_conformance()
 if dyn: raise SystemExit(f'dynamic-profile conformance failed: {dyn[0][0]}')
 verify_profile_definition(); verify_decomposition(); legacy_count=verify_conformance_trace_projection()
 fed=json.loads((C/'conformance/federation-profile-conformance-profile.json').read_text())
 if fed['case_count']!=10: raise SystemExit('federation profile conformance count mismatch')
 for item in fed['cases']:
  if item['sha256']!=sha(ROOT/item['path']): raise SystemExit(f"federation legacy digest mismatch: {item['case_id']}")
 # exact ProfileDefinition remains valid after parent cutover
 fd=json.loads((C/'protocol/profiles/federation-profile-definition.json').read_text()); ok,code=validate_wire_object('PROFILE_DEFINITION',fd)
 if not ok: raise SystemExit(f'federation profile definition invalid after cutover: {code}')
 if fd['parent_contract_digest']!=sha(C/'source/network-extension-model.json'): raise SystemExit('federation profile parent digest mismatch')
 print(f"OK: package files={len(package['files'])}")
 print(f"OK: package digest={package['package_digest']}")
 print('OK: Seed compatibility binding exact')
 print('OK: normative Network core state_fields=1 transition_kinds=1')
 print('OK: canon-to-TLA alpha.3 relation exact')
 print(f"OK: canon TLAPS status={ce['status']}")
 print(f"OK: Seed TLAPS status={se['status']}")
 print(f"OK: legacy->minimal TLAPS status={le['status']}")
 print('OK: dynamic profiles add no Network state or transitions')
 print('OK: schemas valid')
 print('OK: core conformance cases=4')
 print('OK: dynamic-profile conformance cases=8')
 print('OK: federation-profile conformance cases=10')
 print(f'OK: legacy reduction conformance traces={legacy_count}')
 return 0
if __name__=='__main__': raise SystemExit(main())
