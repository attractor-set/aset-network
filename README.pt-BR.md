# ASET Network Extension

Status: **0.1.0-alpha.1 / núcleo de reconhecimento federado**

A extensão define uma camada de federação mínima e neutra em relação à implementação sobre o ASET Seed. Contexts independentes trocam artefatos endereçados por conteúdo sem transferir soberania e sem criar um supercontexto com autoridade superior.

## Regra central

Um Export remoto é evidência, não Authority.

```text
Export de origem -> Import Observation de destino -> resolução Seed local -> recibo de reconhecimento local
```

Participação na federação, ancestralidade, rota e aceitação na origem não criam autoridade no Context de destino. Até um `ACCEPT` local, o efeito permanece `BLOCKED`.

## Vínculo com Seed

- Canon: `ASET-SEED-RESOLUTION-CANON-0.2-ALPHA1`
- Versão: `0.2.0-alpha.1`
- Protocolo de conformidade: `ASET-SEED-RESOLUTION-CONFORMANCE-V1`
- SHA-256 do arquivo `CANON_PACKAGE.json`: `sha256:fb4638962eb3fbb19ca18f46066d28e97e037c709b1a4b99bceab68e32e523db`
- Digest interno do pacote Seed: `sha256:52862a9564a08cfb765ca1cc9d5551d439c75660f1fd11851e8d30d6ff7b1b8e`

O pacote normativo está em `extension/canonical/`. O modelo Python em `reference/` não tem precedência semântica.

Transporte, descoberta, consenso, armazenamento, provedor criptográfico, HE, reconciliação e disponibilidade permanecem fora desta versão alpha.
