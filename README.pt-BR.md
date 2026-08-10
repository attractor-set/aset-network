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

`ASET-NETWORK-FEDERATION-PROFILE-V1` passa a possuir as operações alpha.2 `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. `RECORD_RECOGNITION` não é transferido: reconhecimento terminal continua Seed-owned.

## Verificação formal

Alpha.3 altera o canon normativo, portanto a evidência de prova alpha.2 não é reutilizada. Os três novos módulos de prova foram executados com o TLAPM fixado e materializados como `MECHANICALLY_PROVED`: canon->TLA `3/3`, minimal Network->Seed `35/35`, legacy alpha.2->minimal `23/23`. TLC e conformance continuam superfícies de assurance separadas e não substituem TLAPS.

A fonte normativa permanece `extension/canonical/`; `reference/` é apenas um oracle executável não normativo.
