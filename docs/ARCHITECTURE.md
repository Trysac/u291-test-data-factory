# Architecture

## Purpose

`trysac-test-data-factory` is a small, dependency-free Python library: Typed test data factories for Python dataclasses: values inferred from type hints, seeded and reproducible across Python versions, with sequences, lazy fields and ranges

## Shape

```text
caller code --> test_data_factory (public API in __init__.py)
                    |
                    +-- Factory instances holding their own RNG stream and build counter
```

- **Public API**: the names listed in `__all__` of `src/test_data_factory/__init__.py`:
  `Factory(model, *, seed=0, overrides=None, max_depth=5)` with `build(**overrides)` and
  `build_batch(n, **overrides)` (n at most 10_000), plus `Sequence`, `Lazy` and `FactoryError`.
  Anything else is internal and may change without a major version.
- **Errors**: invalid input raises `FactoryError`, whose `code` is one of `unsupported_type`,
  `unknown_field`, `batch_too_large`, `invalid_range`, `recursion` or `not_a_dataclass`; the
  library never prints or exits.
- **State and determinism**: `Factory` instances hold a per-instance `random.Random(seed)` and a
  build counter; there is no module-level state. Only `random.Random.random()` is used, because
  CPython guarantees its sequence for a given seed across versions.
- **Side effects**: no I/O. If a feature needs I/O, isolate it in its own module behind a small
  interface and record the choice in an ADR.

## Quality contract

`scripts/check.py` is the single definition of the gates; `fabrica.json` tells the factory and CI
how to run it. See [TESTING.md](TESTING.md).

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
