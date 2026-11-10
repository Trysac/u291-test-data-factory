# test-data-factory

[![PyPI version](https://img.shields.io/pypi/v/trysac-test-data-factory)](https://pypi.org/project/trysac-test-data-factory/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-test-data-factory)](LICENSE)
[![CI](https://github.com/Trysac/u291-test-data-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u291-test-data-factory/actions/workflows/ci.yml)

Typed test data factories for Python dataclasses: values inferred from type hints, seeded and reproducible across Python versions, with sequences, lazy fields and ranges

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-test-data-factory
# or
uv add trysac-test-data-factory
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import test_data_factory

# normalize() trims surrounding whitespace and lower-cases the text.
print(test_data_factory.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    test_data_factory.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
