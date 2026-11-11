from __future__ import annotations

import dataclasses
import enum
import logging
import math
import random
import uuid
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import UnionType
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = ["Factory", "FactoryError", "Lazy", "Sequence"]

T = TypeVar("T")
_MISSING = object()


class FactoryError(Exception):
    """Base error for the test data factory."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message)
        self.code = code


class Sequence:
    """Wrapper for a callable that receives the 1-based build counter."""

    def __init__(self, fn: Callable[[int], object]) -> None:
        self.fn = fn


class Lazy:
    """Wrapper for a callable that receives field values computed so far."""

    def __init__(self, fn: Callable[[dict[str, object]], object]) -> None:
        self.fn = fn


class Factory(Generic[T]):
    """Typed test data factory for dataclasses."""

    def __init__(
        self,
        model: type[T],
        *,
        seed: int = 0,
        overrides: Mapping[str, object] | None = None,
        max_depth: int = 5,
    ) -> None:
        if not dataclasses.is_dataclass(model):
            raise FactoryError("not_a_dataclass", f"{model.__name__} is not a dataclass")
        self._model = model
        self._rng = random.Random(seed)  # noqa: S311 - deterministic, non-crypto stream
        self._counter = 0
        self._overrides = dict(overrides) if overrides is not None else {}
        self._max_depth = max_depth

        # Resolve forward references for the top-level model.
        self._type_hints = self._get_type_hints(model)
        self._fields = self._get_fields(model)
        self._field_names = {f.name for f in self._fields}

        # Validate metadata and field types at construction.
        for field in self._fields:
            meta = field.metadata.get("factory", {})
            min_val = meta.get("min")
            max_val = meta.get("max")
            type_hint = self._type_hints[field.name]
            if (
                self._is_range_type(type_hint)
                and min_val is not None
                and max_val is not None
                and min_val > max_val
            ):
                raise FactoryError(
                    "invalid_range", f"min {min_val} > max {max_val} for field {field.name}"
                )
            self._validate_field_type(type_hint, field.name, {cast(type[Any], model)})

    def build(self, **overrides: object) -> T:
        """Build one instance, applying per-build overrides."""
        for key in overrides:
            if key not in self._field_names:
                raise FactoryError("unknown_field", f"Unknown field '{key}'")
        self._counter += 1
        effective_overrides = {**self._overrides, **overrides}
        return cast(T, self._build_instance_common(self._model, 0, effective_overrides))

    def build_batch(self, n: int, **overrides: object) -> list[T]:
        """Build n instances (n <= 10_000)."""
        if n > 10_000:
            raise FactoryError("batch_too_large", f"n must be at most 10000, got {n}")
        return [self.build(**overrides) for _ in range(n)]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_fields(self, dataclass_type: type[Any]) -> tuple[dataclasses.Field[Any], ...]:
        """Return init=True fields in declaration order."""
        return tuple(f for f in dataclasses.fields(dataclass_type) if f.init)

    def _get_type_hints(self, dataclass_type: type[Any]) -> dict[str, Any]:
        """Resolve type hints for a dataclass, using typing.get_type_hints."""
        return get_type_hints(dataclass_type)

    @staticmethod
    def _is_range_type(type_: Any) -> bool:
        """Check if a type supports min/max range metadata."""
        return type_ in (int, float, Decimal)

    def _validate_field_type(self, type_: Any, field_name: str, seen: set[type[Any]]) -> None:
        """Reject unsupported field types and non-optional self references."""
        if type_ in (bool, int, float, str, Decimal, date, datetime, uuid.UUID):
            return
        if isinstance(type_, type) and issubclass(type_, enum.Enum):
            return

        origin = get_origin(type_)
        args = get_args(type_)

        if origin is Literal:
            return

        if origin is Union or origin is UnionType:
            # Optional only; any other Union is unsupported.
            if type(None) in args and len(args) == 2:
                inner = next(a for a in args if a is not type(None))
                if inner is self._model:
                    return
                self._validate_field_type(inner, field_name, seen)
                return
            raise FactoryError("unsupported_type", f"Unsupported union type for field {field_name}")

        if origin is list:
            if not args:
                raise FactoryError(
                    "unsupported_type", f"Unsupported list type for field {field_name}"
                )
            self._validate_field_type(args[0], field_name, seen)
            return

        if dataclasses.is_dataclass(type_):
            nested_type = cast(type[Any], type_)
            if nested_type is self._model or nested_type in seen:
                raise FactoryError("recursion", f"Recursive field {field_name}")
            nested_seen = set(seen)
            nested_seen.add(nested_type)
            hints = self._get_type_hints(nested_type)
            for nested_field in self._get_fields(nested_type):
                self._validate_field_type(hints[nested_field.name], nested_field.name, nested_seen)
            return

        # set, dict, tuple, plain classes, object/Any, etc.
        raise FactoryError("unsupported_type", f"Unsupported type {type_} for field {field_name}")

    def _build_instance_common(
        self, dataclass_type: type[Any], depth: int, overrides_dict: Mapping[str, object]
    ) -> Any:
        """Build an instance of dataclass_type with given overrides and current depth."""
        fields = self._get_fields(dataclass_type)
        type_hints = self._get_type_hints(dataclass_type)
        values: dict[str, Any] = {}
        lazy_pending: list[tuple[str, Lazy]] = []

        for field in fields:
            name = field.name
            type_hint = type_hints[name]
            override = overrides_dict.get(name, _MISSING)
            metadata = field.metadata.get("factory", {})
            use_default = metadata.get("use_default", False)
            min_val = metadata.get("min")
            max_val = metadata.get("max")

            # Determine lo/hi for range types from metadata (defaults applied in _generate).
            lo = min_val if self._is_range_type(type_hint) else None
            hi = max_val if self._is_range_type(type_hint) else None

            # Validate range if both bounds are provided for a range type.
            if (
                self._is_range_type(type_hint)
                and min_val is not None
                and max_val is not None
                and min_val > max_val
            ):
                raise FactoryError(
                    "invalid_range", f"min {min_val} > max {max_val} for field {name}"
                )

            if override is not _MISSING:
                # Consume draws for this field's type, then apply override.
                _ = self._generate(type_hint, depth, name, lo=lo, hi=hi)
                if isinstance(override, Sequence):
                    values[name] = override.fn(self._counter)
                elif isinstance(override, Lazy):
                    lazy_pending.append((name, override))
                else:
                    values[name] = override
            elif use_default:
                if field.default_factory is not dataclasses.MISSING:
                    values[name] = field.default_factory()
                else:
                    default = field.default
                    if default is dataclasses.MISSING:
                        # use_default without any default is not a usable configuration.
                        raise FactoryError(
                            "invalid_range", f"use_default set but no default for field {name}"
                        )
                    values[name] = default
            else:
                values[name] = self._generate(type_hint, depth, name, lo=lo, hi=hi)

        # Evaluate lazy fields after all non-lazy fields, in declaration order.
        for name, lazy in lazy_pending:
            values[name] = lazy.fn(dict(values))

        return dataclass_type(**values)

    def _generate(
        self,
        type_: Any,
        depth: int,
        field_name: str,
        *,
        lo: float | None = None,
        hi: float | None = None,
    ) -> Any:
        """Generate a value, consuming the rng.random() draws its type requires."""
        rng = self._rng
        n = self._counter
        max_depth = self._max_depth
        model = self._model

        origin = get_origin(type_)
        args = get_args(type_)

        # bool before int (bool is subclass)
        if type_ is bool:
            return rng.random() < 0.5
        if type_ is int:
            low = int(lo) if lo is not None else 0
            high = int(hi) if hi is not None else 1000
            return low + math.floor(rng.random() * (high - low + 1))
        if type_ is float:
            low_f = float(lo) if lo is not None else 0.0
            high_f = float(hi) if hi is not None else 1000.0
            return low_f + rng.random() * (high_f - low_f)
        if type_ is str:
            return f"{field_name}-{n}"
        if type_ is Decimal:
            low_d = lo if lo is not None else 0
            high_d = hi if hi is not None else 1000
            scaled_low = int(low_d * 100)
            scaled_range = int((high_d - low_d) * 100)
            val = scaled_low + math.floor(rng.random() * (scaled_range + 1))
            return Decimal(val) / Decimal(100)
        if type_ is date:
            start = date(2026, 1, 1)
            days = math.floor(rng.random() * 365)
            return start + timedelta(days=days)
        if type_ is datetime:
            start_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
            seconds = math.floor(rng.random() * 31_536_000)
            return start_dt + timedelta(seconds=seconds)
        if type_ is uuid.UUID:
            words = [math.floor(rng.random() * 2**32) for _ in range(4)]
            # Combine into a 128-bit int, then set version 4 and RFC 4122 variant bits.
            w0, w1, w2, w3 = words
            # Version nibble lives in bits 76-79, i.e. bits 12-15 of the second word.
            w1 = (w1 & ~0xF000) | 0x4000
            # Variant top bits '10' live in bits 62-63, i.e. bits 30-31 of the third word.
            w2 = (w2 & ~0xC0000000) | 0x80000000
            int_val = (w0 << 96) | (w1 << 64) | (w2 << 32) | w3
            return uuid.UUID(int=int_val)

        if isinstance(type_, type) and issubclass(type_, enum.Enum):
            members = list(type_.__members__.values())
            idx = math.floor(rng.random() * len(members))
            return members[idx]

        if origin is Literal:
            values = [a for a in args if a is not type(None)]
            if not values:
                return None
            idx = math.floor(rng.random() * len(values))
            return values[idx]

        if origin is Union or origin is UnionType:
            # Optional only; any other Union is unsupported.
            if type(None) in args and len(args) == 2:
                inner = next(a for a in args if a is not type(None))
                if inner is model:
                    if depth >= max_depth:
                        return None
                    return self._build_instance_common(model, depth + 1, {})
                return self._generate(inner, depth, field_name, lo=lo, hi=hi)
            raise FactoryError("unsupported_type", f"Unsupported union type for field {field_name}")

        if origin is list:
            if not args:
                raise FactoryError(
                    "unsupported_type", f"Unsupported list type for field {field_name}"
                )
            item_type = args[0]
            length = 1 + math.floor(rng.random() * 3)
            return [
                self._generate(item_type, depth, field_name, lo=lo, hi=hi) for _ in range(length)
            ]

        if dataclasses.is_dataclass(type_):
            nested_type = cast(type[Any], type_)
            if nested_type is model:
                raise FactoryError("recursion", f"Recursive field {field_name}")
            return self._build_instance_common(nested_type, depth + 1, {})

        # set, dict, tuple, plain classes, object/Any, etc.
        raise FactoryError("unsupported_type", f"Unsupported type {type_} for field {field_name}")
