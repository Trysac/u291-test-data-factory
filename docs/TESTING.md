# Testing

## Running

```sh
uv run pytest tests/test_test_data_factory.py
```

The test suite is `tests/test_test_data_factory.py`, which imports the public names from `test_data_factory`: `Factory`, `FactoryError`, `Lazy` and `Sequence`.

## Policy

The tests assert public behavior: returned dataclass instances, generated field values, raised `FactoryError` codes and the effect of overrides. They do not use network access or external tools. Determinism is checked by comparing batches from separate `Factory` instances created with the same seed.

## Tiers

The repository contains a single pytest tier: the acceptance tests in `tests/test_test_data_factory.py`. The test functions in that file are:

- `test_acceptance_user_first_build`: checks the first `Factory(User, seed=42).build()` result (`User(id=640, name='name-1', active=True)`).
- `test_acceptance_user_second_build`: checks the second build uses the 1-based build counter and returns `User(id=275, name='name-2', active=True)`.
- `test_acceptance_deterministic_batch`: checks two `Factory(User, seed=42)` instances produce equal `build_batch` lists and `seed=43` produces a different list.
- `test_acceptance_override_consumes_draw`: checks `Factory(User, seed=42).build(id=7)` keeps the other fields equal to an unoverridden build because the overridden field still consumes its draw.
- `test_acceptance_sequence_and_lazy`: checks `Sequence` produces `user1@example.com`, `user2@example.com` and `Lazy` produces an uppercased label from a previous field.
- `test_acceptance_lazy_uses_generated_name`: checks `Lazy` receives the generated `name` value and produces the corresponding uppercase label.
- `test_acceptance_types`: checks generated values for `Enum`, `Literal['a', 'b']`, `Optional[int]`, `list[int]` (1 to 3 items), `date` (2026), `datetime` (UTC-aware, 2026), `Decimal`, `UUID` (version 4) and a nested dataclass.

The file also defines dataclasses used by the suite: `User`, `LabelUser`, `Node`, `BadNonOptionalNode`, `FrozenUser`, `InitFalseUser`, `KwOnlyUser`, `Color`, `Nested`, `AllTypes`, `RangeInt`, `BadRange`, `UseDefault`, `NotADataclass` and `Plain`.

## Layout

Tests live in `tests/test_test_data_factory.py`. The repository contents include no separate `tests/conftest.py`.
