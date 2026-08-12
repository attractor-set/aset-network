# ASET Network

Статус: **0.1.0-alpha.3 / минимальное ядро admission**

ASET Network задаёт минимальную технологически нейтральную границу, через которую чужой evidence становится локальным кандидатом для ASET Seed.

## Прямая топология репозиториев

- Вышестоящая спецификация: [ASET](https://github.com/attractor-set/ASET) — непосредственный нормативный родитель.
- Нижестоящая эталонная реализация: [ASET Network Python SQLite](https://github.com/attractor-set/aset-network-python-sqlite) — ненормативная эталонная реализация этого расширения.

Здесь перечисляются только непосредственные связи между репозиториями. Транзитивные связи обнаруживаются через их непосредственные родительские репозитории.

## Центральное правило

**Evidence may cross boundaries. Recognition does not.**

```text
foreign evidence -> ADMIT_IMPORT -> UNKNOWN/BLOCKED -> target-local Seed
```

У Network ровно одна структура семантического состояния — `imports` — и один изменяющий переход — `ADMIT_IMPORT`. Admission не создаёт Authority и не разрешает effect. Терминальные `ALLOW/BLOCK` принадлежат только локальному Seed.

Federation membership/routing и условная liveness — два отдельных опциональных профиля. Federation Profile владеет только federation lifecycle, Liveness Profile — только условными progress claims. Они компонуются без отношения parent/child; terminal-resolution progress остаётся в собственности target-local Seed.

## Привязка к Seed

- Seed: `seed-0.3.0-alpha.3`
- Commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

Network может усиливать ограничения Seed, но не ослаблять и не переопределять их.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` — самостоятельный опциональный dynamic profile. Он владеет состоянием федеративного lifecycle и переходами `FEDERATION_GENESIS`, `MEMBER_JOIN`, `ROUTE_GRANT`, `EXPORT_ARTIFACT`, `SUSPEND_ROUTE`, `MEMBER_WITHDRAW`. Все принадлежащие Federation артефакты находятся под `extension/canonical/profiles/federation/`. Его ненормативный oracle находится в `reference/profiles/federation.py`, а 10 нативных conformance cases — внутри того же profile-каталога.

Federation-переходы являются stutter относительно admission-состояния Network. Terminal recognition не является операцией Federation и остаётся исключительно в собственности target-local Seed.

## Liveness Profile

`ASET-NETWORK-LIVENESS-V1` — самостоятельный опциональный dynamic profile без собственного Network state и transition kinds. Он задаёт условные progress guarantees и required capabilities для отдельно компонуемого профиля. Текущая assurance-композиция связывает его с Federation Profile, но не делает один профиль родителем другого.

## Формальная проверка

Текущая core TLAPS-цепочка содержит canon->`NetworkExtension.tla` `3/3` и minimal Network->Seed `35/35`. Federation safety является profile-local assurance под `extension/canonical/profiles/federation/assurance/`. Liveness — отдельный профиль под `extension/canonical/profiles/liveness/`. Assurance их композиции вынесен в `extension/canonical/assurance/profile-compositions/federation-liveness/` и не создаёт parent/child отношения или переноса ownership.

Историческая совместимость старых релизов Network сохраняется Git history и immutable tags, а не переносится в текущий canon package и release gate.

Нормативным источником остаётся `extension/canonical/`; `reference/` — только ненормативный executable oracle.
