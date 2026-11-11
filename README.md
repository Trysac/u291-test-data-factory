# test-data-factory

[![PyPI version](https://img.shields.io/pypi/v/trysac-test-data-factory)](https://pypi.org/project/trysac-test-data-factory/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-test-data-factory)](LICENSE)
[![CI](https://github.com/Trysac/u291-test-data-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u291-test-data-factory/actions/workflows/ci.yml)

Typed test data factories for Python dataclasses: values inferred from type hints, seeded and reproducible across Python versions, with sequences, lazy fields and ranges

## Problem

Tests build domain objects by hand with copy-pasted literals, so every new required field breaks dozens of tests and nobody knows which values matter. Factory libraries help but need a hand-written declaration per model and often draw values that change between library or Python versions. This library infers a factory from a dataclass's type hints, draws every value from a seeded `random()` stream with documented formulas, and lets tests override only what they care about.

## Install

```sh
pip install trysac-test-data-factory
# or
uv add trysac-test-data-factory
```

Requires Python 3.10 or newer. No runtime dependencies (standard library only).

## Usage

```python
from dataclasses import dataclass
from test_data_factory import Factory, Sequence


@dataclass
class User:
    id: int
    email: str


factory = Factory(User, seed=42, overrides={"email": Sequence(lambda n: f"user{n}@example.com")})
print(factory.build())  # User(id=640, email='user1@example.com')
```

## Public API

`Factory(model, *, seed=0, overrides=None, max_depth=5)` builds instances of a dataclass `model`. `build(**overrides)` returns one instance; `build_batch(n, **overrides)` returns a list of `n` instances and rejects `n > 10_000` with `FactoryError.code == "batch_too_large"`.

- `Sequence(fn)` receives the 1-based build counter of the factory. `Lazy(fn)` receives the field values computed so far and is evaluated after all non-lazy fields, in declaration order.
- `overrides` on the factory and per-build keyword arguments replace generated values. An overridden field still consumes the random draws its type would use, so other fields keep the same values.
- Supported field types: `bool`, `int`, `float`, `str`, `Decimal`, `date`, `datetime`, `uuid.UUID`, `enum.Enum` subclasses, `Literal`, `Optional[T]`, `list[T]` and nested dataclasses. Unsupported types (`set`, `dict`, `tuple`, a `Union` of two non-`None` types, plain classes, `Any`) raise `FactoryError.code == "unsupported_type"` at `Factory` construction, naming the field.
- `field(metadata={"factory": {"min": x, "max": y}})` changes the bounds for `int`, `float` and `Decimal`; `min > max` raises `FactoryError.code == "invalid_range"`. Metadata `{"factory": {"use_default": True}}` uses the dataclass default or `default_factory` instead of generating a value.
- `Optional` self references stop with `None` at `max_depth` (default `5`); a non-optional self reference raises `FactoryError.code == "recursion"`.
- Determinism: each `Factory` owns one `random.Random(seed)` and uses only its `random()` method. A given seed therefore produces the same `random()` sequence across Python versions.
- Errors: `FactoryError.code` is one of `unsupported_type`, `unknown_field`, `batch_too_large`, `invalid_range`, `recursion` or `not_a_dataclass`.

## Why not factory_boy

factory_boy requires a hand-written declaration per model. This library derives a factory from the dataclass type hints and uses only `random.Random.random()`, so a given seed produces the same values across Python versions. It does not model ORM persistence or realistic fake data; use a dedicated data library for those.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
