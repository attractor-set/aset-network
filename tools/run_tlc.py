from __future__ import annotations
import argparse, os, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FORMAL=ROOT/'extension/canonical/formal'; DEFAULT_JAR=ROOT/'.tooling/tla2tools.jar'; META=ROOT/'.tooling/tlc'
MODELS={
 'safety':('NetworkExtensionTLC.tla','NetworkExtensionTLC.cfg'),
 'admission-alias':('NetworkAdmissionCore.tla','NetworkAdmissionCore.cfg'),
 'history':('NetworkHistory.tla','NetworkHistory.cfg'),
 'legacy-safety':('NetworkLegacyAlpha2.tla','NetworkLegacyAlpha2.cfg'),
 'federation-liveness':('NetworkLegacyAlpha2.tla','NetworkLegacyAlpha2Liveness.cfg'),
}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('model',choices=[*MODELS,'all'],nargs='?',default='all'); ap.add_argument('--jar',type=Path); a=ap.parse_args(); jar=(a.jar or Path(os.environ.get('TLA2TOOLS_JAR',DEFAULT_JAR))).expanduser().resolve()
 if not jar.is_file(): raise SystemExit(f'tla2tools.jar not found: {jar}; run python tools/bootstrap_tla.py or set TLA2TOOLS_JAR')
 selected=list(MODELS) if a.model=='all' else [a.model]; META.mkdir(parents=True,exist_ok=True)
 for name in selected:
  module,config=MODELS[name]; md=META/name
  if md.exists(): shutil.rmtree(md)
  cmd=['java','-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC','-workers','1','-metadir',str(md),'-config',config,module]
  print(f'TLC_MODEL={name.upper()}'); r=subprocess.run(cmd,cwd=FORMAL,check=False)
  if r.returncode: print(f'TLC_{name.upper()}=FAIL'); return r.returncode
  print(f'TLC_{name.upper()}=PASS')
 print('TLC_NETWORK_EXTENSION=PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
