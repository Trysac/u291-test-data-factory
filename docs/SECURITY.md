# Security notes

## Threat model

`trysac-test-data-factory` is a pure library: it has no runtime dependencies, no network access and no I/O. It is not a sandbox.

Defended:

- `Factory` construction rejects non-dataclasses with `FactoryError.code == "not_a_dataclass"`.
- Type validation rejects unsupported field types (`set`, `dict`, `tuple`, two non-`None` union members, plain classes, `Any`) with `FactoryError.code == "unsupported_type"`, naming the field.
- Range validation rejects `min > max` for `int`, `float` and `Decimal` with `FactoryError.code == "invalid_range"`.
- Recursion validation rejects non-optional self references and cycles in nested dataclasses with `FactoryError.code == "recursion"`; `Optional` self references stop with `None` at `max_depth` (default `5`).
- `build_batch` rejects `n > 10_000` with `FactoryError.code == "batch_too_large"`.
- The implementation does not use `eval`, `exec` or deserialization of untrusted data. Invalid input fails with `FactoryError` codes instead of printing or exiting.

Not defended:

- Factory overrides, `Sequence` callables and `Lazy` callables are supplied by the caller and run with the process's privileges. The library does not inspect, restrict or sandbox them.
- Randomness is `random.Random(seed)` and only its `random()` method is used. It is deterministic and non-cryptographic. UUID values have version 4 bits set, but the stream is not suitable for secrets or security tokens.
- Values are not sanitized for downstream SQL, HTML, shell or other contexts; callers must validate and escape at the sink.
- Resource limits are limited to the `build_batch` cap and `max_depth` for optional self references. Building large or deeply nested structures beyond those limits is the caller's responsibility.

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
