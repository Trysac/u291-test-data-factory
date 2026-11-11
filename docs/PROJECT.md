# Project record

## Objective

Typed test data factories for Python dataclasses: values inferred from type hints, seeded and reproducible across Python versions, with sequences, lazy fields and ranges.

## Scope

In scope:

- `Factory(model, *, seed=0, overrides=None, max_depth=5)` with `build(**overrides)` and `build_batch(n, **overrides)` (n at most 10,000).
- `Sequence(fn)`, `Lazy(fn)` and `FactoryError(code)`.
- Values inferred from dataclass type hints for `bool`, `int`, `float`, `str`, `Decimal`, `date`, `datetime`, `uuid.UUID`, `enum.Enum`, `Literal`, `Optional[T]`, `list[T]` and nested dataclasses.
- Range metadata `{"factory": {"min": x, "max": y}}` for `int`, `float` and `Decimal`, and `{"factory": {"use_default": True}}` for defaults.
- Determinism through one `random.Random(seed)` per factory and only its `random()` method.
- Tests in `tests/test_test_data_factory.py`.

Out of scope:

- ORMs and saving to databases.
- pydantic models.
- attrs classes.
- realistic fake names or addresses (use a dedicated data library).
- hypothesis strategies.
- runtime dependencies; the package is standard library only.
- I/O.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 1889118 / 99589 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1303 |

## Factory run u291 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1689 | 25635 | 0 | 3200 | 0.0519 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 33338 | 19393 | 0 | 904064 | 0.0193 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 5992 | 1139 | 0 | 19840 | 0.0016 |
| 2026-11-10 | audit | deepseek-flash | no | 32579 | 37463 | 0 | 688000 | 0.0294 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 9867 | 4464 | 0 | 78976 | 0.0044 |
| 2026-11-10 | docs | deepseek-flash | no | 111317 | 11495 | 0 | 256 | 0.0236 |

Total: $0.1303. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
