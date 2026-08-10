# ASET Network Extension

Status: **0.1.0-alpha.3 / núcleo mínimo de admissão**

ASET Network Extension define a fronteira mínima e neutra de implementação pela qual evidência externa se torna candidata local para resolução pelo ASET Seed.

## Regra central

**Evidence may cross boundaries. Recognition does not.**

```text
foreign evidence -> ADMIT_IMPORT -> UNKNOWN/BLOCKED -> target-local Seed
```

O Network possui uma única estrutura de estado semântico, `imports`, e uma única transição mutável, `ADMIT_IMPORT`. A admissão não cria Authority nem autoriza efeitos. `ALLOW/BLOCK` terminais pertencem exclusivamente ao Seed local.

Federação, rotas, ciclo de exportação e liveness condicional são perfis opcionais. Qualquer garantia de terminal-resolution permanece explicitamente sob o Seed local do alvo.

## Vínculo com Seed

- Seed: `seed-0.3.0-alpha.3`
- Commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

Network pode fortalecer as restrições de Seed, mas não enfraquecê-las nem substituí-las.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` é um dynamic profile opcional e autocontido. Ele possui o estado do ciclo de vida federativo e as transições `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. O oracle não normativo está em `reference/federation_profile_reference.py` e os 10 casos nativos de conformidade estão em `extension/canonical/conformance/federation-profile-cases/`.

As transições de Federation são stutter em relação ao estado de admission da Network. Terminal recognition não é uma operação de Federation e continua exclusivamente sob o Seed local do Context alvo.

## Verificação formal

A cadeia TLAPS atual contém duas relações mecanicamente provadas: canon->`NetworkExtension.tla` `3/3` e minimal Network->Seed `35/35`. O Federation Profile possui modelos TLC separados de safety e composition-liveness: `FederationProfile.tla` e `FederationCompositionLiveness.tla`. `Resolve(e)` no modelo de liveness é apenas um witness de assurance do progresso do Seed local e não cria estado de recognition da Network/Federation.

A compatibilidade histórica de releases antigos da Network fica preservada no histórico Git e em tags imutáveis, não no canon package ou release gate atual.

A fonte normativa permanece `extension/canonical/`; `reference/` é apenas um oracle executável não normativo.
