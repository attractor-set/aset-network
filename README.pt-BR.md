# ASET Network

Status: **representação pública atual Alpha4 / evidência predecessora Alpha3 congelada**

ASET Network define a fronteira mínima e neutra de implementação pela qual evidência externa se torna candidata local para resolução pelo ASET Seed.

## Alpha4 paired admission

A superfície Alpha4 atual fica em `network/alpha4/`. `network/CURRENT.aset` a seleciona como a representação atual do projeto sem adquirir precedência semântica. Ela define um único subject pertencente ao Network: observações de importação exatas e a única operação `ADMIT-IMPORT`. A expressão restricted-Forth e uma expressão relacional TLA+ independente são ligadas por uma prova de pairing. `SeedBoundaryProofs.tla` fixa a fronteira: uma admissão aceita projeta somente `UNKNOWN` no Seed local do alvo e nunca autoriza um efeito por si só.

`upstream/ASET_SEED_ALPHA4_BINDING.aset` liga o Network à superfície semântica atual do ASET Seed 0.4alpha por SHA-256 de conteúdo, e não por uma implementação privilegiada. O `extension/canonical/**` existente permanece como evidência predecessora Alpha3 byte-frozen e material de regressão.

## Topologia direta dos repositórios

- Especificação upstream: [ASET Seed](https://github.com/attractor-set/aset-seed) — pai normativo direto.

Somente relações diretas entre repositórios são listadas aqui. Relações transitivas são descobertas por meio de seus repositórios-pai imediatos.

## Perfis opcionais Alpha4

A representação Alpha4 atual possui uma superfície de perfis separada em `network/alpha4/profiles/`, sem alterar `network/alpha4/NETWORK.aset`:

- Dynamic — ativação exata por `ALLOW` do Seed local, sem novo estado ou transições de Network;
- Federation — ciclo de vida próprio da federação, com 5 campos de estado e 6 transições que comprovadamente fazem stutter sobre `IMPORTS`;
- Liveness — apenas garantias condicionais de progresso, sem estado ou transições de Network e sem exigir `ALLOW` eventual;
- Federation+Liveness — composição de assurance sem relação pai, transferência de estado, transições ou Authority.

Cada objeto semântico de perfil Alpha4 possui agora expressões operacional e relacional pareadas. Federation pareia seu grafo de transições Forth/TLA; Dynamic pareia a relação de ativação por binding exato; Liveness pareia predicates condicionais de claim/result sem criar uma máquina de transições; e Federation+Liveness pareia o predicate de composição de capabilities/boundaries. TLAPS prova os pairings e as fronteiras, enquanto TLC continua responsável por safety de Federation e pelo progresso temporal Federation+Liveness.

## Expressões operacionais pertencem ao objeto semântico

Uma expressão operacional pertence ao **objeto semântico**, e não necessariamente a uma máquina de estados ou a um grafo de transições. Portanto, ownership de estado e ownership de transições são ortogonais à existência de uma expressão restricted-Forth.

A forma da expressão operacional segue o tipo do objeto semântico:

- subjects de transição usam evaluators de transição;
- subjects relacionais usam predicates operacionais;
- subjects de propriedade usam claim predicates;
- subjects de trace usam reconhecedores de witnesses finitos;
- subjects de composição usam composition predicates.

Dynamic e Liveness demonstram diretamente essa fronteira: nenhum dos dois possui estado de Network nem define transições de Network, mas ambos possuem expressões operacionais restricted-Forth pareadas com expressões relacionais TLA independentes. Federation continua sendo o perfil stateful; sua expressão Forth avalia o lifecycle transition graph pertencente ao perfil.

```text
semantic object
    ├── operational expression   (restricted Forth)
    └── relational expression    (TLA)
             ↕
          pairing

state ownership        independent
transition ownership   independent
```

Consequentemente, `operational expression` não implica `state ownership`, `transition ownership` nem semântica de máquina de estados. O contrato machine-readable de perfis fixa isso por meio de `OPERATIONAL-EXPRESSION-REQUIRES-STATE NEVER` e `OPERATIONAL-EXPRESSION-REQUIRES-TRANSITION NEVER`.

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

A cadeia de assurance Alpha4 atual vive em `network/alpha4/**`: pairing Forth/TLA do core, prova da fronteira com Seed, pairings/fronteiras locais dos perfis e TLC para safety de Federation e progresso temporal Federation+Liveness. O gate principal da representação atual é `python -m tools.alpha4_network_gate`.

`extension/canonical/**` e as ferramentas Alpha3 associadas de proof/conformance permanecem como evidência regressiva do predecessor congelado. Elas não definem mais a representação atual do Network. `reference/` continua sendo apenas um oracle histórico não normativo.
