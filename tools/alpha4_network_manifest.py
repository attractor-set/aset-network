from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ManifestError(RuntimeError):
    pass


@dataclass(frozen=True)
class PairBinding:
    component_id: str
    transition: str
    formal_operator: str
    operational_operator: str
    pairing_theorem: str


@dataclass(frozen=True)
class CausalBinding:
    component_id: str
    causal_transition: str


@dataclass(frozen=True)
class ProofBinding:
    proof_id: str
    module: str
    final_theorem: str
    expected_obligations: int


@dataclass(frozen=True)
class SubjectBinding:
    name: str
    manifest: str
    header: tuple[str, ...]
    operational: str
    relational: str
    formal_reflection: str
    causal_model: str
    pairs: tuple[PairBinding, ...]
    causal_bindings: tuple[CausalBinding, ...]
    proofs: tuple[ProofBinding, ...]
    relations: tuple[tuple[str, str], ...]

    def relation_map(self) -> dict[str, str]:
        return dict(self.relations)


@dataclass(frozen=True)
class NetworkBindingPlan:
    subjects: tuple[SubjectBinding, ...]
    derivers: tuple[tuple[str, str], ...]

    def by_name(self) -> dict[str, SubjectBinding]:
        return {item.name: item for item in self.subjects}

    @property
    def all_proofs(self) -> tuple[ProofBinding, ...]:
        return tuple(proof for subject in self.subjects for proof in subject.proofs)


@dataclass(frozen=True)
class SubjectSchema:
    manifest: str
    header: tuple[str, ...]
    fixed_lines: tuple[str, ...]
    sources: tuple[str, str, str, str]
    pairs: tuple[PairBinding, ...]
    causal_bindings: tuple[CausalBinding, ...]
    proofs: tuple[ProofBinding, ...]
    relations: tuple[tuple[str, str], ...]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _pair(*values: str) -> PairBinding:
    return PairBinding(*values)


def _causal(component_id: str, transition: str) -> CausalBinding:
    return CausalBinding(component_id, transition)


def _proof(proof_id: str, module: str, theorem: str, obligations: int) -> ProofBinding:
    return ProofBinding(proof_id, module, theorem, obligations)


SCHEMAS: dict[str, SubjectSchema] = {
    "network": SubjectSchema(
        manifest="network/alpha4/NETWORK.aset",
        header=("ASET-NETWORK", "1", "ASET-NETWORK-ALPHA4", "alpha4"),
        fixed_lines=(
            "SEMANTIC-PRECEDENCE NONE",
            "ALPHA3-COMPATIBILITY NONE",
            "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA",
            "UPSTREAM-BINDING upstream/ASET_SEED_ALPHA4_BINDING.aset",
            "SEED-EXTENSION-BIND OPERATIONAL OBSERVE-UNKNOWN ADMIT-FRESH,ADMIT-REPLAY",
            "SEED-EXTENSION-BIND RELATIONAL ObserveUnknown AdmitFresh,AdmitReplay",
            "SEED-EXTENSION-BIND CAUSAL OBSERVE-UNKNOWN ADMIT-FRESH,ADMIT-REPLAY",
            "STATE IMPORTS SET-OF-EXACT-IMPORT-OBSERVATIONS",
            "TRANSITION ADMIT-IMPORT",
            "SEED-PROJECTION ADMIT-IMPORT OBSERVE-UNKNOWN",
            "SEED-RECOGNITION-OWNER TARGET-LOCAL-SEED",
            "EFFECT-PERMITTED-BY-NETWORK NEVER",
            "CHECK BINDING tools/validate_alpha4_network.py",
            "CHECK OPERATIONAL_RELATIONAL tools/alpha4_network_paired_expression.py",
            "CHECK ASSURANCE tools/alpha4_network_assurance.py",
            "CHECK TRIANGULATED_EXPRESSION tools/alpha4_network_triangulated_expression.py",
            "GATE tools/alpha4_network_gate.py",
        ),
        sources=(
            "network/alpha4/operational/components.forth",
            "network/alpha4/formal/NetworkRelations.tla",
            "network/alpha4/formal/RestrictedOperationalSemantics.tla",
            "network/alpha4/causal/components.petri",
        ),
        pairs=(
            _pair(
                "ASET-NETWORK-COMPONENT-ADMIT-FRESH",
                "ADMIT-IMPORT",
                "AdmitFresh",
                "OperationalAdmitFresh",
                "AdmitFreshPairing",
            ),
            _pair(
                "ASET-NETWORK-COMPONENT-ADMIT-REPLAY",
                "ADMIT-IMPORT",
                "AdmitReplay",
                "OperationalAdmitReplay",
                "AdmitReplayPairing",
            ),
            _pair(
                "ASET-NETWORK-COMPONENT-REJECT-CONFLICT",
                "ADMIT-IMPORT",
                "RejectConflict",
                "OperationalRejectConflict",
                "RejectConflictPairing",
            ),
        ),
        causal_bindings=(
            _causal("ASET-NETWORK-COMPONENT-ADMIT-FRESH", "ADMIT-FRESH"),
            _causal("ASET-NETWORK-COMPONENT-ADMIT-REPLAY", "ADMIT-REPLAY"),
            _causal("ASET-NETWORK-COMPONENT-REJECT-CONFLICT", "REJECT-CONFLICT"),
        ),
        proofs=(
            _proof(
                "OPERATIONAL_RELATIONAL_PAIRING",
                "network/alpha4/formal/OperationalRelationalPairingProofs.tla",
                "OperationalRelationalPairing",
                7,
            ),
            _proof(
                "SEED_BOUNDARY",
                "network/alpha4/formal/SeedBoundaryProofs.tla",
                "NetworkAdmissionPreservesSeedRecognitionBoundary",
                5,
            ),
        ),
        relations=(
            ("OPERATIONAL_CAUSAL_INTERFACE", "EXACT_STACK_CLOSED_WORLD_CAUSAL_CONTRACT"),
            ("OPERATIONAL_RELATIONAL", "BOUNDED_OPERATIONAL_RELATIONAL_CONGRUENCE"),
            ("OPERATIONAL_CAUSAL", "BOUNDED_OPERATIONAL_CAUSAL_CONGRUENCE"),
            ("RELATIONAL_CAUSAL", "BOUNDED_RELATIONAL_CAUSAL_CONGRUENCE"),
            ("TRIANGULATED", "THREE_WAY_BOUNDED_OBSERVATIONAL_CONGRUENCE"),
            ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
        ),
    ),
    "dynamic": SubjectSchema(
        manifest="network/alpha4/profiles/dynamic/DYNAMIC.aset",
        header=("ASET-NETWORK-PROFILE", "1", "ASET-NETWORK-DYNAMIC-ALPHA4", "alpha4"),
        fixed_lines=(
            "SEMANTIC-PRECEDENCE NONE",
            "PARENT-SUBJECT network/alpha4/NETWORK.aset",
            "PROFILE-KIND ACTIVATION-CONTRACT",
            "OPTIONAL TRUE",
            "NORMATIVE-WHEN-CLAIMED TRUE",
            "STATE-ADDED NONE",
            "TRANSITION-ADDED NONE",
            "NETWORK-STATE-CHANGE NEVER",
            "AUTHORITY-INHERITANCE NEVER",
            "OBJECT PROFILE-DEFINITION IMMUTABLE CONTENT-ADDRESSED",
            "OBJECT PROFILE-BINDING EXACT TARGET-LOCAL CONTENT-ADDRESSED",
            "ACTIVATION TARGET-LOCAL-SEED-ALLOW EXACT-PROFILE-BINDING",
            "ACTIVATION-BY-AVAILABILITY NEVER",
            "ACTIVATION-BY-VERIFICATION NEVER",
            "ACTIVATION-BY-REMOTE-RECOGNITION NEVER",
            "PREVIOUS-ALLOW-CARRIES-FORWARD NEVER",
        ),
        sources=(
            "network/alpha4/profiles/dynamic/operational/components.forth",
            "network/alpha4/profiles/dynamic/formal/DynamicProfileRelations.tla",
            "network/alpha4/profiles/dynamic/formal/DynamicRestrictedOperationalSemantics.tla",
            "network/alpha4/profiles/dynamic/causal/components.petri",
        ),
        pairs=(
            _pair(
                "ASET-NETWORK-DYNAMIC-APPLICABILITY",
                "PROFILE-APPLICABLE?",
                "ProfileApplicable",
                "OperationalProfileApplicable",
                "ProfileApplicablePairing",
            ),
            _pair(
                "ASET-NETWORK-DYNAMIC-NETWORK-STUTTER",
                "PROFILE-NETWORK-STUTTER?",
                "DynamicProfileNetworkProjection",
                "OperationalDynamicProfileNetworkProjection",
                "DynamicProfileNetworkProjectionPairing",
            ),
        ),
        causal_bindings=(
            _causal("ASET-NETWORK-DYNAMIC-APPLICABILITY", "PROFILE-APPLICABLE"),
            _causal("ASET-NETWORK-DYNAMIC-NETWORK-STUTTER", "PROFILE-NETWORK-STUTTER"),
        ),
        proofs=(
            _proof(
                "OPERATIONAL_RELATIONAL_PAIRING",
                "network/alpha4/profiles/dynamic/formal/DynamicOperationalRelationalPairingProofs.tla",
                "DynamicOperationalRelationalPairing",
                5,
            ),
            _proof(
                "BOUNDARY",
                "network/alpha4/profiles/dynamic/formal/DynamicProfileBoundaryProofs.tla",
                "DynamicProfilesPreserveNetworkAndLocalAuthority",
                5,
            ),
        ),
        relations=(
            ("OPERATIONAL_CAUSAL_INTERFACE", "EXACT_STACK_CLOSED_WORLD_CAUSAL_CONTRACT"),
            ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
        ),
    ),
    "federation": SubjectSchema(
        manifest="network/alpha4/profiles/federation/FEDERATION.aset",
        header=("ASET-NETWORK-PROFILE", "1", "ASET-NETWORK-FEDERATION-ALPHA4", "alpha4"),
        fixed_lines=(
            "SEMANTIC-PRECEDENCE NONE",
            "PARENT-SUBJECT network/alpha4/NETWORK.aset",
            "ACTIVATION-CONTRACT network/alpha4/profiles/dynamic/DYNAMIC.aset",
            "PROFILE-KIND STATEFUL-CAPABILITY",
            "OPTIONAL TRUE",
            "NORMATIVE-WHEN-CLAIMED TRUE",
            "STATE FEDERATION-ID",
            "STATE FEDERATION-EPOCH",
            "STATE MEMBERS",
            "STATE ROUTES",
            "STATE EXPORTS",
            "TRANSITION FEDERATION-GENESIS",
            "TRANSITION MEMBER-JOIN",
            "TRANSITION ROUTE-GRANT",
            "TRANSITION EXPORT-ARTIFACT",
            "TRANSITION SUSPEND-ROUTE",
            "TRANSITION MEMBER-WITHDRAW",
            "CAPABILITY RETAINED-EXPORT",
            "CAPABILITY DELIVERY",
            "CAPABILITY TARGET-OBSERVATION",
            "INVARIANT ROUTE-ENDPOINTS-DISTINCT",
            "INVARIANT ACTIVE-ROUTE-MEMBERS-ACTIVE",
            "INVARIANT MEMBER-WITHDRAWAL-REQUIRES-NO-ACTIVE-ROUTE",
            "INVARIANT EXPORT-PRESERVES-EXACT-ROUTE-BINDING",
            "INVARIANT NETWORK-IMPORTS-STUTTER-ON-PROFILE-TRANSITION",
            "INVARIANT AUTHORITY-INHERITANCE NEVER",
            "ASSURANCE SAFETY "
            "network/alpha4/profiles/federation/assurance/FederationProfile.tla "
            "network/alpha4/profiles/federation/assurance/FederationProfile.cfg",
        ),
        sources=(
            "network/alpha4/profiles/federation/operational/components.forth",
            "network/alpha4/profiles/federation/formal/FederationRelations.tla",
            "network/alpha4/profiles/federation/formal/FederationRestrictedOperationalSemantics.tla",
            "network/alpha4/profiles/federation/causal/components.petri",
        ),
        pairs=(
            _pair(
                "ASET-NETWORK-FEDERATION-GENESIS",
                "FEDERATION-GENESIS",
                "FederationGenesis",
                "OperationalFederationGenesis",
                "FederationGenesisPairing",
            ),
            _pair(
                "ASET-NETWORK-MEMBER-JOIN",
                "MEMBER-JOIN",
                "MemberJoin",
                "OperationalMemberJoin",
                "MemberJoinPairing",
            ),
            _pair(
                "ASET-NETWORK-ROUTE-GRANT",
                "ROUTE-GRANT",
                "RouteGrant",
                "OperationalRouteGrant",
                "RouteGrantPairing",
            ),
            _pair(
                "ASET-NETWORK-EXPORT-ARTIFACT",
                "EXPORT-ARTIFACT",
                "ExportArtifact",
                "OperationalExportArtifact",
                "ExportArtifactPairing",
            ),
            _pair(
                "ASET-NETWORK-SUSPEND-ROUTE",
                "SUSPEND-ROUTE",
                "SuspendRoute",
                "OperationalSuspendRoute",
                "SuspendRoutePairing",
            ),
            _pair(
                "ASET-NETWORK-MEMBER-WITHDRAW",
                "MEMBER-WITHDRAW",
                "MemberWithdraw",
                "OperationalMemberWithdraw",
                "MemberWithdrawPairing",
            ),
        ),
        causal_bindings=(
            _causal("ASET-NETWORK-FEDERATION-GENESIS", "FEDERATION-GENESIS"),
            _causal("ASET-NETWORK-MEMBER-JOIN", "MEMBER-JOIN"),
            _causal("ASET-NETWORK-ROUTE-GRANT", "ROUTE-GRANT"),
            _causal("ASET-NETWORK-EXPORT-ARTIFACT", "EXPORT-ARTIFACT"),
            _causal("ASET-NETWORK-SUSPEND-ROUTE", "SUSPEND-ROUTE"),
            _causal("ASET-NETWORK-MEMBER-WITHDRAW", "MEMBER-WITHDRAW"),
        ),
        proofs=(
            _proof(
                "OPERATIONAL_RELATIONAL_PAIRING",
                "network/alpha4/profiles/federation/formal/FederationOperationalRelationalPairingProofs.tla",
                "FederationOperationalRelationalPairing",
                13,
            ),
            _proof(
                "NETWORK_STUTTER",
                "network/alpha4/profiles/federation/formal/NetworkStutteringProofs.tla",
                "FederationTransitionsStutterOnNetworkImports",
                3,
            ),
        ),
        relations=(
            ("OPERATIONAL_CAUSAL_INTERFACE", "EXACT_STACK_CLOSED_WORLD_CAUSAL_CONTRACT"),
            ("OPERATIONAL_CAUSAL_RESULT", "OBSERVABLE_RESULT_CODE_CONGRUENCE"),
            ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
        ),
    ),
    "liveness": SubjectSchema(
        manifest="network/alpha4/profiles/liveness/LIVENESS.aset",
        header=("ASET-NETWORK-PROFILE", "1", "ASET-NETWORK-LIVENESS-ALPHA4", "alpha4"),
        fixed_lines=(
            "SEMANTIC-PRECEDENCE NONE",
            "PARENT-SUBJECT network/alpha4/NETWORK.aset",
            "ACTIVATION-CONTRACT network/alpha4/profiles/dynamic/DYNAMIC.aset",
            "PROFILE-KIND CONDITIONAL-PROGRESS-CONTRACT",
            "OPTIONAL TRUE",
            "NORMATIVE-WHEN-CLAIMED TRUE",
            "STATE-ADDED NONE",
            "TRANSITION-ADDED NONE",
            "AUTHORITY-INHERITANCE NEVER",
            "REQUIRES-CAPABILITY RETAINED-EXPORT",
            "REQUIRES-CAPABILITY DELIVERY",
            "REQUIRES-CAPABILITY TARGET-OBSERVATION",
            "ASSUMPTION EVENTUAL-DELIVERY-FOR-RETAINED-EXPORT",
            "ASSUMPTION EVENTUAL-TARGET-OBSERVATION",
            "ASSUMPTION TARGET-LOCAL-SEED-EVENTUAL-RESOLUTION",
            "ASSUMPTION NO-PERMANENT-TARGET-UNAVAILABILITY",
            "GUARANTEE EVENTUALLY-DELIVERED CONDITIONAL",
            "GUARANTEE EVENTUALLY-OBSERVED CONDITIONAL",
            "GUARANTEE EVENTUALLY-TARGET-LOCAL-SEED-RESOLVED CONDITIONAL",
            "SEED-RESOLUTION-OWNER TARGET-LOCAL-SEED",
            "SEED-TERMINAL-RESULT ALLOW",
            "SEED-TERMINAL-RESULT BLOCK",
            "EVENTUAL-ALLOW-REQUIRED FALSE",
        ),
        sources=(
            "network/alpha4/profiles/liveness/operational/components.forth",
            "network/alpha4/profiles/liveness/formal/LivenessContract.tla",
            "network/alpha4/profiles/liveness/formal/LivenessRestrictedOperationalSemantics.tla",
            "network/alpha4/profiles/liveness/causal/components.petri",
        ),
        pairs=(
            _pair(
                "ASET-NETWORK-LIVENESS-DELIVERY-CLAIM",
                "EVENTUALLY-DELIVERED-CLAIM?",
                "EventuallyDeliveredClaim",
                "OperationalEventuallyDeliveredClaim",
                "EventuallyDeliveredClaimPairing",
            ),
            _pair(
                "ASET-NETWORK-LIVENESS-OBSERVATION-CLAIM",
                "EVENTUALLY-OBSERVED-CLAIM?",
                "EventuallyObservedClaim",
                "OperationalEventuallyObservedClaim",
                "EventuallyObservedClaimPairing",
            ),
            _pair(
                "ASET-NETWORK-LIVENESS-RESOLUTION-CLAIM",
                "EVENTUALLY-RESOLVED-CLAIM?",
                "EventuallyTargetLocalSeedResolvedClaim",
                "OperationalEventuallyTargetLocalSeedResolvedClaim",
                "EventuallyTargetLocalSeedResolvedClaimPairing",
            ),
            _pair(
                "ASET-NETWORK-LIVENESS-TERMINAL-RESULT",
                "RESOLVED-RESULT-PERMITTED?",
                "ResolvedResultPermitted",
                "OperationalResolvedResultPermitted",
                "ResolvedResultPermittedPairing",
            ),
        ),
        causal_bindings=(
            _causal("ASET-NETWORK-LIVENESS-DELIVERY-CLAIM", "EVENTUALLY-DELIVERED-CLAIM"),
            _causal("ASET-NETWORK-LIVENESS-OBSERVATION-CLAIM", "EVENTUALLY-OBSERVED-CLAIM"),
            _causal("ASET-NETWORK-LIVENESS-RESOLUTION-CLAIM", "EVENTUALLY-RESOLVED-CLAIM"),
            _causal("ASET-NETWORK-LIVENESS-TERMINAL-RESULT", "RESOLVED-RESULT-PERMITTED"),
        ),
        proofs=(
            _proof(
                "OPERATIONAL_RELATIONAL_PAIRING",
                "network/alpha4/profiles/liveness/formal/LivenessOperationalRelationalPairingProofs.tla",
                "LivenessOperationalRelationalPairing",
                9,
            ),
            _proof(
                "BOUNDARY",
                "network/alpha4/profiles/liveness/formal/LivenessBoundaryProofs.tla",
                "LivenessPreservesOwnershipBoundary",
                7,
            ),
        ),
        relations=(
            ("OPERATIONAL_CAUSAL_INTERFACE", "EXACT_STACK_CLOSED_WORLD_CAUSAL_CONTRACT"),
            ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
        ),
    ),
    "federation-liveness": SubjectSchema(
        manifest="network/alpha4/profiles/composition/federation-liveness/FEDERATION_LIVENESS.aset",
        header=(
            "ASET-NETWORK-PROFILE-COMPOSITION",
            "1",
            "ASET-NETWORK-FEDERATION-LIVENESS-ALPHA4",
            "alpha4",
        ),
        fixed_lines=(
            "SEMANTIC-PRECEDENCE NONE",
            "PROFILE network/alpha4/profiles/federation/FEDERATION.aset",
            "PROFILE network/alpha4/profiles/liveness/LIVENESS.aset",
            "PROFILE-PARENT-RELATION FALSE",
            "STATE-OWNERSHIP-TRANSFER NONE",
            "TRANSITION-OWNERSHIP-TRANSFER NONE",
            "AUTHORITY-TRANSFER NONE",
            "PROVIDER FEDERATION",
            "PROVIDES RETAINED-EXPORT",
            "PROVIDES DELIVERY",
            "PROVIDES TARGET-OBSERVATION",
            "CONSUMER LIVENESS",
            "REQUIRES RETAINED-EXPORT",
            "REQUIRES DELIVERY",
            "REQUIRES TARGET-OBSERVATION",
            "TARGET-OBSERVATION-WITNESS ASSURANCE-WITNESS-FOR-NETWORK-ADMIT-IMPORT",
            "TARGET-LOCAL-RESOLUTION-WITNESS ASSURANCE-WITNESS-FOR-SEED-RESOLUTION",
            "ASSURANCE PROGRESS "
            "network/alpha4/profiles/composition/federation-liveness/assurance/"
            "FederationLivenessProgress.tla "
            "network/alpha4/profiles/composition/federation-liveness/assurance/"
            "FederationLivenessProgress.cfg",
        ),
        sources=(
            "network/alpha4/profiles/composition/federation-liveness/operational/components.forth",
            "network/alpha4/profiles/composition/federation-liveness/formal/FederationLivenessCompositionRelations.tla",
            "network/alpha4/profiles/composition/federation-liveness/formal/FederationLivenessRestrictedOperationalSemantics.tla",
            "network/alpha4/profiles/composition/federation-liveness/causal/components.petri",
        ),
        pairs=(
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-CAPABILITIES",
                "REQUIRED-CAPABILITIES-SATISFIED?",
                "ProvidesRequiredCapabilities",
                "OperationalProvidesRequiredCapabilities",
                "RequiredCapabilitiesPairing",
            ),
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-BOUNDARY",
                "COMPOSITION-BOUNDARY-PRESERVED?",
                "CompositionBoundaryPreserved",
                "OperationalCompositionBoundaryPreserved",
                "CompositionBoundaryPairing",
            ),
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-DELIVERY-WITNESS",
                "DELIVERY-WITNESS?",
                "DeliveryWitness",
                "OperationalDeliveryWitness",
                "DeliveryWitnessPairing",
            ),
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-OBSERVATION-WITNESS",
                "OBSERVATION-WITNESS?",
                "ObservationWitness",
                "OperationalObservationWitness",
                "ObservationWitnessPairing",
            ),
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-RESOLUTION-WITNESS",
                "RESOLUTION-WITNESS?",
                "ResolutionWitness",
                "OperationalResolutionWitness",
                "ResolutionWitnessPairing",
            ),
            _pair(
                "ASET-NETWORK-FEDERATION-LIVENESS-PROGRESS-WITNESS",
                "PROGRESS-WITNESS?",
                "ProgressWitness",
                "OperationalProgressWitness",
                "ProgressWitnessPairing",
            ),
        ),
        causal_bindings=(
            _causal(
                "ASET-NETWORK-FEDERATION-LIVENESS-CAPABILITIES", "REQUIRED-CAPABILITIES-SATISFIED"
            ),
            _causal("ASET-NETWORK-FEDERATION-LIVENESS-BOUNDARY", "COMPOSITION-BOUNDARY-PRESERVED"),
            _causal("ASET-NETWORK-FEDERATION-LIVENESS-DELIVERY-WITNESS", "DELIVERY-WITNESS"),
            _causal("ASET-NETWORK-FEDERATION-LIVENESS-OBSERVATION-WITNESS", "OBSERVATION-WITNESS"),
            _causal("ASET-NETWORK-FEDERATION-LIVENESS-RESOLUTION-WITNESS", "RESOLUTION-WITNESS"),
            _causal("ASET-NETWORK-FEDERATION-LIVENESS-PROGRESS-WITNESS", "PROGRESS-WITNESS"),
        ),
        proofs=(
            _proof(
                "OPERATIONAL_RELATIONAL_PAIRING",
                "network/alpha4/profiles/composition/federation-liveness/formal/FederationLivenessOperationalRelationalPairingProofs.tla",
                "FederationLivenessOperationalRelationalPairing",
                13,
            ),
            _proof(
                "CONTRACT",
                "network/alpha4/profiles/composition/federation-liveness/assurance/FederationLivenessContractProofs.tla",
                "FederationLivenessCompositionPreservesBoundaries",
                5,
            ),
        ),
        relations=(
            ("OPERATIONAL_CAUSAL_INTERFACE", "EXACT_STACK_CLOSED_WORLD_CAUSAL_CONTRACT"),
            ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
        ),
    ),
}

DERIVERS = (
    ("OPERATIONAL", "tools/alpha4_network_paired_expression.py"),
    ("RELATIONAL", "tools/alpha4_network_relational_expression.py"),
    ("CAUSAL", "tools/alpha4_network_causal_expression.py"),
)


def _read_tokens(path: Path) -> list[list[str]]:
    result: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped:
            result.append(stripped.split())
    return result


def _theorem_present(path: Path, theorem: str) -> bool:
    text = path.read_text(encoding="utf-8")
    return f"THEOREM {theorem}" in text or f"{theorem} ==" in text


def _parse_subject(root: Path, name: str, schema: SubjectSchema) -> SubjectBinding:
    path = root / schema.manifest
    require(path.is_file(), f"{name}: manifest missing: {schema.manifest}")
    token_lines = _read_tokens(path)
    require(token_lines, f"{name}: empty manifest")
    require(tuple(token_lines[0]) == schema.header, f"{name}: manifest header drift")

    fixed: list[str] = []
    sources: dict[str, str] = {}
    pairs: list[PairBinding] = []
    causal_bindings: list[CausalBinding] = []
    proofs: list[ProofBinding] = []
    relations: list[tuple[str, str]] = []
    derivers: list[tuple[str, str]] = []

    for tokens in token_lines[1:]:
        kind = tokens[0]
        if kind in {"OPERATIONAL", "RELATIONAL", "FORMAL-REFLECTION", "CAUSAL-MODEL"}:
            require(len(tokens) == 2, f"{name}: invalid {kind} source binding")
            require(kind not in sources, f"{name}: duplicate {kind} source binding")
            sources[kind] = tokens[1]
        elif kind == "PAIR":
            require(len(tokens) == 6, f"{name}: invalid PAIR binding")
            pairs.append(PairBinding(*tokens[1:]))
        elif kind == "CAUSAL-BIND":
            require(len(tokens) == 3, f"{name}: invalid CAUSAL-BIND")
            causal_bindings.append(CausalBinding(tokens[1], tokens[2]))
        elif kind == "PROOF":
            require(len(tokens) == 5, f"{name}: proof binding must pin obligation count")
            proofs.append(ProofBinding(tokens[1], tokens[2], tokens[3], int(tokens[4])))
        elif kind == "RELATION":
            require(len(tokens) == 3, f"{name}: invalid RELATION")
            relations.append((tokens[1], tokens[2]))
        elif kind == "DERIVER":
            require(len(tokens) == 3, f"{name}: invalid DERIVER")
            derivers.append((tokens[1], tokens[2]))
        else:
            fixed.append(" ".join(tokens))

    expected_sources = dict(
        zip(
            ("OPERATIONAL", "RELATIONAL", "FORMAL-REFLECTION", "CAUSAL-MODEL"),
            schema.sources,
            strict=True,
        )
    )
    require(sources == expected_sources, f"{name}: representation source binding drift")
    require(
        Counter(fixed) == Counter(schema.fixed_lines), f"{name}: closed-world declaration drift"
    )
    require(tuple(pairs) == schema.pairs, f"{name}: PAIR binding drift")
    require(tuple(causal_bindings) == schema.causal_bindings, f"{name}: CAUSAL-BIND drift")
    require(tuple(proofs) == schema.proofs, f"{name}: proof binding/scope drift")
    require(tuple(relations) == schema.relations, f"{name}: assurance relation binding drift")
    if name == "network":
        require(tuple(derivers) == DERIVERS, "network: deriver binding drift")
    else:
        require(not derivers, f"{name}: profile must inherit core deriver plan")

    require(
        len({item.component_id for item in pairs}) == len(pairs),
        f"{name}: duplicate pair component",
    )
    require(
        len({item.formal_operator for item in pairs}) == len(pairs),
        f"{name}: duplicate formal operator",
    )
    require(
        len({item.operational_operator for item in pairs}) == len(pairs),
        f"{name}: duplicate operational operator",
    )
    require(
        len({item.pairing_theorem for item in pairs}) == len(pairs),
        f"{name}: duplicate pairing theorem",
    )
    require(
        {item.component_id for item in causal_bindings} == {item.component_id for item in pairs},
        f"{name}: causal/pair component sets differ",
    )
    require(
        len({item.causal_transition for item in causal_bindings}) == len(causal_bindings),
        f"{name}: duplicate causal transition",
    )
    require(len({item.proof_id for item in proofs}) == len(proofs), f"{name}: duplicate proof id")
    require(len({key for key, _ in relations}) == len(relations), f"{name}: duplicate relation id")

    for relative in (*sources.values(), *(item.module for item in proofs)):
        bound = root / relative
        require(bound.is_file(), f"{name}: bound file missing: {relative}")
    for proof in proofs:
        require(
            _theorem_present(root / proof.module, proof.final_theorem),
            f"{name}: final theorem missing: {proof.final_theorem}",
        )
    for pair in pairs:
        relational_text = (root / sources["RELATIONAL"]).read_text(encoding="utf-8")
        reflection_text = (root / sources["FORMAL-REFLECTION"]).read_text(encoding="utf-8")
        pairing_texts = "\n".join(
            (root / proof.module).read_text(encoding="utf-8") for proof in proofs
        )
        require(
            f"{pair.formal_operator}(" in relational_text,
            f"{name}: relational operator missing: {pair.formal_operator}",
        )
        require(
            f"{pair.operational_operator}(" in reflection_text,
            f"{name}: operational reflection missing: {pair.operational_operator}",
        )
        require(
            pair.pairing_theorem in pairing_texts,
            f"{name}: pairing theorem missing: {pair.pairing_theorem}",
        )

    return SubjectBinding(
        name=name,
        manifest=schema.manifest,
        header=schema.header,
        operational=sources["OPERATIONAL"],
        relational=sources["RELATIONAL"],
        formal_reflection=sources["FORMAL-REFLECTION"],
        causal_model=sources["CAUSAL-MODEL"],
        pairs=tuple(pairs),
        causal_bindings=tuple(causal_bindings),
        proofs=tuple(proofs),
        relations=tuple(relations),
    )


def parse_network_manifests(root: Path = ROOT) -> NetworkBindingPlan:
    subjects = tuple(_parse_subject(root, name, schema) for name, schema in SCHEMAS.items())
    for _, path in DERIVERS:
        require((root / path).is_file(), f"bound deriver absent: {path}")
    return NetworkBindingPlan(subjects=subjects, derivers=DERIVERS)


def main() -> int:
    try:
        plan = parse_network_manifests(ROOT)
        pairs = sum(len(subject.pairs) for subject in plan.subjects)
        proofs = len(plan.all_proofs)
        obligations = sum(proof.expected_obligations for proof in plan.all_proofs)
        print(f"ALPHA4_NETWORK_MANIFEST_SUBJECTS={len(plan.subjects)}/{len(plan.subjects)} PASS")
        print(f"ALPHA4_NETWORK_MANIFEST_PAIRS={pairs}/{pairs} PASS")
        print(f"ALPHA4_NETWORK_MANIFEST_PROOFS={proofs}/{proofs} PASS")
        print(f"ALPHA4_NETWORK_MANIFEST_EXPECTED_TLAPS_OBLIGATIONS={obligations}")
        print("ALPHA4_NETWORK_BINDING_PLAN=PASS")
        return 0
    except (ManifestError, OSError, UnicodeError, ValueError) as error:
        print(f"ALPHA4_NETWORK_MANIFEST_ERROR={error}")
        print("ALPHA4_NETWORK_BINDING_PLAN=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
