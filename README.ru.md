# ASET Network Extension

Статус: **0.1.0-alpha.3 / минимальное ядро admission**

ASET Network Extension задаёт минимальную технологически нейтральную границу, через которую чужой evidence становится локальным кандидатом для ASET Seed.

## Центральное правило

**Evidence may cross boundaries. Recognition does not.**

```text
foreign evidence -> ADMIT_IMPORT -> UNKNOWN/BLOCKED -> target-local Seed
```

У Network ровно одна структура семантического состояния — `imports` — и один изменяющий переход — `ADMIT_IMPORT`. Admission не создаёт Authority и не разрешает effect. Терминальные `ALLOW/BLOCK` принадлежат только локальному Seed.

Федеративное членство, маршруты, экспортный lifecycle и условная transport-liveness вынесены в опциональные профили.

## Привязка к Seed

- Seed: `seed-0.3.0-alpha.3`
- Commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

Network может усиливать ограничения Seed, но не ослаблять и не переопределять их.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` теперь владеет бывшими alpha.2 операциями `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. `RECORD_RECOGNITION` туда не переносится: terminal recognition остаётся Seed-owned.

## Формальная проверка

Alpha.3 изменяет нормативный canon, поэтому доказательства alpha.2 намеренно не переиспользуются. Три новых proof-модуля реально прогнаны закреплённым TLAPM и материализованы как `MECHANICALLY_PROVED`: canon->TLA `3/3`, minimal Network->Seed `35/35`, legacy alpha.2->minimal `23/23`. TLC и conformance остаются отдельными assurance surfaces и не подменяют TLAPS.

Нормативным источником остаётся `extension/canonical/`; `reference/` — только ненормативный executable oracle.
