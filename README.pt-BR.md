# ASET Network Extension

Status: **0.1.0-alpha.2 / núcleo de reconhecimento federado**

A extensão define uma camada de federação mínima e neutra em relação à implementação sobre o ASET Seed. Contexts independentes trocam artefatos endereçados por conteúdo sem transferir soberania e sem criar um supercontexto com autoridade superior.

## Regra central

Um Export remoto é evidência, não Authority.

```text
Export de origem -> Import Observation de destino -> resolução Seed local -> recibo de reconhecimento local
```

Participação na federação, ancestralidade, rota e aceitação na origem não criam autoridade no Context de destino. Até um `ACCEPT` local, o efeito permanece `BLOCKED`.

## Vínculo com Seed

- Release do Seed: `seed-0.3.0-alpha.3`
- Commit do Seed: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Versão do canon: `0.3.0-alpha.1`
- Digest do pacote canon: `sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31`
- Seed Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`
- Compatibility profile: `ASET-SEED-COMPATIBILITY-STANDARD-V1`
- Seed conformance kit: `sha256:5ecf9b93377a062b8772b4b4b44b4d76a0997d8ba98e8711e717456abbe583db`

O pacote normativo está em `extension/canonical/`. O modelo Python em `reference/` não tem precedência semântica.

Mecanismos concretos de transporte, descoberta, consenso, armazenamento, provedor criptográfico, HE, reconciliação e garantias incondicionais de disponibilidade permanecem fora desta versão alpha. Liveness é definido apenas condicionalmente por `ASET-NETWORK-LIVENESS-V1`.


## Verificação formal

O canon legível por máquina continua sendo a fonte normativa. `NetworkExtension.tla` é uma assurance projection verificada com TLC real. `NetworkExtensionSeedProjection.tla` define a projeção fail-closed de cada Context de destino para a álgebra de resolução do Seed. O refinement comportamental exato em relação ao `SeedResolution.tla` fixado permanece explicitamente uma obrigação TLAPS separada e ainda não é reivindicado.

O canon legível por máquina separa explicitamente o estado semântico da rede do histórico canônico de evidências. Ambos permanecem normativos: o estado semântico define a projeção de estado da rede, enquanto o histórico é um evidence trace append-only e, por si só, não confere Authority nem altera a elegibilidade de transições, salvo quando uma regra normativa referencia explicitamente uma transição anterior.

`ASET-NETWORK-LIVENESS-V1` é uma capability claim normativa opcional, e não um requisito do core `ASET-NETWORK-EXTENSION-CONFORMANCE-V1`. Quando reivindicado, exige eventual resolução local (`ACCEPT` ou `DENY`) apenas sob assumptions explícitas de fairness/ambiente; não exige eventual `ACCEPT` nem consenso global.

A ponte TLAPS para o `SeedResolution.tla` fixado é declarada em `NetworkExtensionSeedRefinement.tla` e `NetworkExtensionSeedRefinementProofs.tla`; o módulo upstream não é copiado para o canon e seu SHA-256 exato é verificado antes da prova. Até o proof gate passar, a relação não é marcada como provada.

## Relação entre repositórios

- Seed upstream: [ASET](https://github.com/attractor-set/ASET).
- Esta extensão normativa: [aset-network-extension](https://github.com/attractor-set/aset-network-extension).
- Implementação de referência do Seed: [aset-python-sqlite](https://github.com/attractor-set/aset-python-sqlite).
- Implementação de referência de rede: [aset-network-python-sqlite](https://github.com/attractor-set/aset-network-python-sqlite) — implementação não normativa desta extensão que compõe `aset-python-sqlite` como sua camada Seed.
