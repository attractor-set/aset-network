# ASET Network

Статус: **Alpha4 paired-admission candidate / Alpha3 frozen predecessor evidence**

ASET Network задаёт минимальную технологически нейтральную границу, через которую чужой evidence становится локальным кандидатом для ASET Seed.

## Alpha4 paired admission

Кандидатная Alpha4-поверхность находится в `network/alpha4/` и задаёт один Network-owned subject: точные import observations и единственную операцию `ADMIT-IMPORT`. Restricted-Forth expression и независимая TLA+ relational expression связываются отдельным pairing proof. `SeedBoundaryProofs.tla` фиксирует границу: успешная admission проецируется только в target-local Seed `UNKNOWN` и никогда сама не разрешает effect.

`upstream/ASET_SEED_ALPHA4_BINDING.aset` связывает Network с текущей семантической поверхностью ASET Seed 0.4alpha по SHA-256 содержимого, а не через привилегированную реализацию. Существующий `extension/canonical/**` остаётся byte-frozen Alpha3 predecessor evidence на время миграции.

## Прямая топология репозиториев

- Вышестоящая спецификация: [ASET Seed](https://github.com/attractor-set/aset-seed) — непосредственный нормативный родитель.

Здесь перечисляются только непосредственные связи между репозиториями. Транзитивные связи обнаруживаются через их непосредственные родительские репозитории.

## Опциональные профили Alpha4

Alpha4-кандидат теперь содержит отдельную профильную поверхность `network/alpha4/profiles/`, не изменяя `network/alpha4/NETWORK.aset`:

- Dynamic — точная активация через локальный Seed `ALLOW`, без нового состояния и переходов Network;
- Federation — собственный жизненный цикл федерации: 5 полей состояния и 6 переходов, которые доказуемо stutter относительно Network `IMPORTS`;
- Liveness — только условные гарантии прогресса, без состояния и переходов Network и без требования eventual `ALLOW`;
- Federation+Liveness — assurance-композиция без parent relation, передачи состояния, переходов или Authority.

Профиль Federation имеет paired Forth/TLA expression; границы профилей проверяются TLAPS, а safety/liveness-композиция — отдельным TLC harness.

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
