# Type-driven factory with seeded random() and documented formulas

Status: accepted (generated, pending human review)

## Context

Test data factories often require per-model declarations or produce unstable values across library versions. The specification requires reproducibility across Python versions and only the standard library.

## Decision

Use a single random.Random(seed) per Factory and only its random() method for all draws. Implement exact draw formulas for each supported type as documented in the spec, ensuring overridden fields consume the same draws. Use type hints and dataclass metadata to drive generation, with Sequence/Lazy overrides evaluated after drawing to maintain determinism.

## Consequences

The factory is type-driven and stable across Python versions. Unsupported types raise at construction. Recursion is handled via Optional self-reference with max_depth, non-optional self-reference raises. Overrides and lazy/sequence fields preserve draw order, making tests reproducible even when overriding.
