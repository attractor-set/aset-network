# ASET Network Extension

Статус: **0.1.0-alpha.3 / минимальное ядро admission**

ASET Network Extension задаёт минимальную технологически нейтральную границу, через которую чужой evidence становится локальным кандидатом для ASET Seed.

## Центральное правило

**Evidence may cross boundaries. Recognition does not.**

```text
foreign evidence -> ADMIT_IMPORT -> UNKNOWN/BLOCKED -> target-local Seed
```

У Network ровно одна структура семантического состояния — `imports` — и один изменяющий переход — `ADMIT_IMPORT`. Admission не создаёт Authority и не разрешает effect. Терминальные `ALLOW/BLOCK` принадлежат только локальному Seed.

Федеративное членство, маршруты, экспортный lifecycle и условная liveness вынесены в опциональные профили. Любая terminal-resolution liveness явно остаётся в собственности target-local Seed.

## Привязка к Seed

- Seed: `seed-0.3.0-alpha.3`
- Commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

Network может усиливать ограничения Seed, но не ослаблять и не переопределять их.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` — самостоятельный опциональный dynamic profile. Он владеет состоянием федеративного lifecycle и переходами `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. Его ненормативный oracle находится в `reference/federation_profile_reference.py`, а 10 нативных conformance cases — в `extension/canonical/conformance/federation-profile-cases/`.

Federation-переходы являются stutter относительно admission-состояния Network. Terminal recognition не является операцией Federation и остаётся исключительно в собственности target-local Seed.

## Формальная проверка

Текущая TLAPS-цепочка содержит два механически доказанных отношения: canon->`NetworkExtension.tla` `3/3` и minimal Network->Seed `35/35`. Для Federation Profile отдельно существуют bounded TLC safety и composition-liveness модели `FederationProfile.tla` и `FederationCompositionLiveness.tla`. `Resolve(e)` в liveness-модели — только assurance witness прогресса target-local Seed и не создаёт Network/Federation recognition state.

Историческая совместимость старых релизов Network сохраняется Git history и immutable tags, а не переносится в текущий canon package и release gate.

Нормативным источником остаётся `extension/canonical/`; `reference/` — только ненормативный executable oracle.
