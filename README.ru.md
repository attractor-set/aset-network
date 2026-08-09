# ASET Network Extension

Статус: **0.1.0-alpha.2 / ядро федеративного признания**

Расширение задаёт минимальный, технологически нейтральный сетевой слой над ASET Seed. Независимые Context обмениваются контентно-адресуемыми артефактами без передачи суверенитета и без образования надконтекста с верховной властью.

## Центральное правило

Удалённый Export является доказательственным материалом, а не Authority.

```text
Export источника -> Import Observation цели -> локальное разрешение Seed -> локальная запись признания
```

Членство в федерации, происхождение Context, маршрут и решение источника не создают полномочий в целевом Context. До локального `ACCEPT` действует `BLOCKED`.

## Привязка к Seed

- Релиз Seed: `seed-0.3.0-alpha.3`
- Commit Seed: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Версия canon: `0.3.0-alpha.1`
- Digest canon package: `sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31`
- Seed Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`
- Compatibility profile: `ASET-SEED-COMPATIBILITY-STANDARD-V1`
- Seed conformance kit: `sha256:5ecf9b93377a062b8772b4b4b44b4d76a0997d8ba98e8711e717456abbe583db`

Нормативным является пакет `extension/canonical/`. Python-модель в `reference/` не имеет семантического приоритета.

В alpha намеренно не определены конкретные транспорт, discovery, consensus, хранение, криптографический провайдер, HE, reconciliation и безусловные гарантии доступности. Liveness задаётся только условно профилем `ASET-NETWORK-LIVENESS-V1`.


## Формальная проверка

Machine-readable canon остаётся нормативным источником. `NetworkExtension.tla` является assurance projection и проверяется настоящим TLC. `NetworkExtensionSeedProjection.tla` задаёт fail-closed проекцию каждого целевого Context в алгебру разрешения Seed. Точное behavioral refinement к закреплённому `SeedResolution.tla` явно оставлено отдельным обязательством TLAPS и не заявляется преждевременно.

Machine-readable canon явно разделяет семантическое состояние сети и каноническую evidence history. Оба слоя остаются нормативными: semantic state задаёт сетевую state projection, а history является append-only evidence trace и сама по себе не создаёт Authority и не меняет допустимость перехода, если только нормативное правило явно не ссылается на предыдущий переход.

`ASET-NETWORK-LIVENESS-V1` — опциональное нормативное capability claim, а не требование core `ASET-NETWORK-EXTENSION-CONFORMANCE-V1`. При его заявлении требуется eventual local resolution (`ACCEPT` или `DENY`) только при явных fairness/environment assumptions; он не требует eventual `ACCEPT` или глобального согласия.

TLAPS-мост к закреплённому `SeedResolution.tla` объявлен в `NetworkExtensionSeedRefinement.tla` и `NetworkExtensionSeedRefinementProofs.tla`; upstream-модуль не копируется в канон и перед доказательством проверяется по точному SHA-256. До успешного proof gate связь не маркируется как доказанная.

## Связь репозиториев

- Вышестоящий Seed: [ASET](https://github.com/attractor-set/ASET).
- Это нормативное расширение: [aset-network-extension](https://github.com/attractor-set/aset-network-extension).
- Эталонная реализация Seed: [aset-python-sqlite](https://github.com/attractor-set/aset-python-sqlite).
- Сетевая эталонная реализация: [aset-network-python-sqlite](https://github.com/attractor-set/aset-network-python-sqlite) — ненормативная реализация этого расширения, композирующая `aset-python-sqlite` как Seed-слой.
