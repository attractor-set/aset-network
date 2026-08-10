#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "extension/canonical/source/network-extension-model.json"
OUTPUT_PATH = ROOT / "extension/canonical/formal/NetworkCanonProjection.tla"
EXPECTED_VERSION = "0.1.0-alpha.3"
EXPECTED_STATUS = "MINIMAL_ADMISSION_CORE_ALPHA3_NORMATIVE_CUTOVER"
EXPECTED_TRANSITIONS = ["ADMIT_IMPORT"]
EXPECTED_FIELDS = ["imports"]
PROFILE = "ASET-NETWORK-CANON-TLA-PROJECTION-V3"


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate(model):
    if model.get("version") != EXPECTED_VERSION:
        raise SystemExit("ERROR: unsupported extension version")
    if model.get("status") != EXPECTED_STATUS:
        raise SystemExit("ERROR: unsupported extension status")
    if model.get("transition_kinds") != EXPECTED_TRANSITIONS:
        raise SystemExit("ERROR: unsupported transition catalogue")
    if model.get("state_partition", {}).get("semantic_state_fields") != EXPECTED_FIELDS:
        raise SystemExit("ERROR: unsupported semantic-state partition")
    if model.get("state_partition", {}).get("evidence_history_fields") != ["history"]:
        raise SystemExit("ERROR: unsupported history partition")


def render(model):
    source_sha = sha(MODEL_PATH.read_bytes())
    return f"""---------------------- MODULE NetworkCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/network-extension-model.json
Source SHA-256: {source_sha}
Projection profile: {PROFILE}
***************************************************************************)

CONSTANTS Contexts, Artifacts
ASSUME /\\ Contexts # {{}}
       /\\ Artifacts # {{}}

CanonObservation(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
CanonObservationUniverse == [source : Contexts, target : Contexts, artifact : Artifacts]

VARIABLE imports
CanonVars == <<imports>>
CanonInit == imports = {{}}

CanonAdmitImport(o) ==
  /\\ o \\in CanonObservationUniverse
  /\\ o \\notin imports
  /\\ imports' = imports \\cup {{o}}

CanonNetworkAction == \\E o \\in CanonObservationUniverse : CanonAdmitImport(o)
CanonSafetySpec == CanonInit /\\ [][CanonNetworkAction]_CanonVars

CanonTypeOK == imports \\subseteq CanonObservationUniverse
CanonProjectedStatus(o) == IF o \\in imports THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
CanonProjectedEnforcement(o) == IF o \\in imports THEN "BLOCKED" ELSE "NOT_APPLICABLE"
CanonAdmissionFailClosed ==
  \\A o \\in imports :
    /\\ CanonProjectedStatus(o) = "UNKNOWN"
    /\\ CanonProjectedEnforcement(o) = "BLOCKED"
CanonNoTerminalRecognitionState == TRUE
CanonNoRemoteAuthorityState == TRUE
CanonNetworkDoesNotWeakenSeedBoundary ==
  /\\ CanonNoTerminalRecognitionState
  /\\ CanonNoRemoteAuthorityState
  /\\ CanonAdmissionFailClosed

=============================================================================
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    model = json.loads(MODEL_PATH.read_text())
    validate(model)
    expected = render(model)
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != expected:
            raise SystemExit("NETWORK_CANON_PROJECTION_CHECK=FAIL")
        print(f"NETWORK_CANON_PROJECTION={OUTPUT_PATH.relative_to(ROOT)}")
        print(f"NETWORK_CANON_PROJECTION_SHA256={sha(OUTPUT_PATH.read_bytes())}")
        print("NETWORK_CANON_PROJECTION_CHECK=PASS")
        return 0
    OUTPUT_PATH.write_text(expected)
    print(f"NETWORK_CANON_PROJECTION={OUTPUT_PATH.relative_to(ROOT)}")
    print(f"NETWORK_CANON_PROJECTION_SHA256={sha(OUTPUT_PATH.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
