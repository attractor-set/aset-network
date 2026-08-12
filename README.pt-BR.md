# ASET Network

Status: **0.1.0-alpha.3 / núcleo mínimo de admissão**

ASET Network define a fronteira mínima e neutra de implementação pela qual evidência externa se torna candidata local para resolução pelo ASET Seed.

## Topologia direta dos repositórios

- Especificação upstream: [ASET](https://github.com/attractor-set/ASET) — pai normativo direto.
- Implementação de referência downstream: [ASET Network Python SQLite](https://github.com/attractor-set/aset-network-python-sqlite) — implementação de referência não normativa desta extensão.

Somente relações diretas entre repositórios são listadas aqui. Relações transitivas são descobertas por meio de seus repositórios-pai imediatos.

## Regra central

**Evidence may cross boundaries. Recognition does not.**

```text
foreign evidence -> ADMIT_IMPORT -> UNKNOWN/BLOCKED -> target-local Seed
```

O Network possui uma única estrutura de estado semântico, `imports`, e uma única transição mutável, `ADMIT_IMPORT`. A admissão não cria Authority nem autoriza efeitos. `ALLOW/BLOCK` terminais pertencem exclusivamente ao Seed local.

Federação/rotas e liveness condicional são dois perfis opcionais separados. O Federation Profile possui apenas o lifecycle federativo; o Liveness Profile possui apenas claims condicionais de progresso. Eles podem ser compostos sem relação parent/child, e o progresso de terminal-resolution continua sob o Seed local do alvo.

## Vínculo com Seed

- Seed: `seed-0.3.0-alpha.3`
- Commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

Network pode fortalecer as restrições de Seed, mas não enfraquecê-las nem substituí-las.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` é um dynamic profile opcional e autocontido. Ele possui o estado do ciclo de vida federativo e as transições `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. Todos os artefatos pertencentes à Federation ficam em `extension/canonical/profiles/federation/`. O oracle não normativo está em `reference/profiles/federation.py` e os 10 casos nativos de conformidade ficam no mesmo diretório de perfil.

As transições de Federation são stutter em relação ao estado de admission da Network. Terminal recognition não é uma operação de Federation e continua exclusivamente sob o Seed local do Context alvo.

## Liveness Profile

`ASET-NETWORK-LIVENESS-V1` é um dynamic profile opcional independente, sem estado ou transitions próprios da Network. Ele declara garantias condicionais de progresso e capacidades exigidas de um perfil composto separadamente. A composição atualmente verificada usa o Federation Profile sem tornar um perfil pai do outro.

## Verificação formal

A cadeia TLAPS do core contém canon->`NetworkExtension.tla` `3/3` e minimal Network->Seed `35/35`. A safety da Federation é assurance local ao perfil em `extension/canonical/profiles/federation/assurance/`. Liveness é um perfil separado em `extension/canonical/profiles/liveness/`. A assurance da composição fica em `extension/canonical/assurance/profile-compositions/federation-liveness/` e não cria relação parent/child nem transfere ownership.

A compatibilidade histórica de releases antigos da Network fica preservada no histórico Git e em tags imutáveis, não no canon package ou release gate atual.

A fonte normativa permanece `extension/canonical/`; `reference/` é apenas um oracle executável não normativo.
