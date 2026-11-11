from __future__ import annotations

import dataclasses
import datetime
import enum
import uuid
from decimal import Decimal
from typing import Literal

import pytest

from test_data_factory import Factory, FactoryError, Lazy, Sequence


# ----------------------------------------------------------------------
# Test dataclasses
# ----------------------------------------------------------------------
@dataclasses.dataclass
class User:
    id: int
    name: str
    active: bool


@dataclasses.dataclass
class LabelUser:
    name: str
    label: str


@dataclasses.dataclass
class Node:
    child: Node | None


@dataclasses.dataclass
class BadNonOptionalNode:
    child: BadNonOptionalNode


@dataclasses.dataclass(frozen=True)
class FrozenUser:
    id: int
    name: str


@dataclasses.dataclass
class InitFalseUser:
    id: int
    name: str = dataclasses.field(init=False, default="fixed")


@dataclasses.dataclass
class KwOnlyUser:
    id: int
    name: str = dataclasses.field(kw_only=True)


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclasses.dataclass
class Nested:
    value: int


@dataclasses.dataclass
class AllTypes:
    enum: Color
    literal: Literal["a", "b"]
    optional: int | None
    lst: list[int]
    date: datetime.date
    dt: datetime.datetime
    dec: Decimal
    uid: uuid.UUID
    nested: Nested


@dataclasses.dataclass
class RangeInt:
    value: int = dataclasses.field(metadata={"factory": {"min": 18, "max": 18}})


@dataclasses.dataclass
class BadRange:
    value: int = dataclasses.field(metadata={"factory": {"min": 5, "max": 1}})


@dataclasses.dataclass
class UseDefault:
    value: int = dataclasses.field(default=42, metadata={"factory": {"use_default": True}})


class NotADataclass:
    pass


class Plain:  # not a dataclass
    pass


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_acceptance_user_first_build():
    factory = Factory(User, seed=42)
    assert factory.build() == User(id=640, name="name-1", active=True)


def test_acceptance_user_second_build():
    factory = Factory(User, seed=42)
    factory.build()
    assert factory.build() == User(id=275, name="name-2", active=True)


def test_acceptance_deterministic_batch():
    f1 = Factory(User, seed=42)
    f2 = Factory(User, seed=42)
    batch1 = f1.build_batch(5)
    batch2 = f2.build_batch(5)
    assert batch1 == batch2
    f3 = Factory(User, seed=43)
    batch3 = f3.build_batch(5)
    assert batch1 != batch3


def test_acceptance_override_consumes_draw():
    factory = Factory(User, seed=42)
    assert factory.build(id=7) == User(id=7, name="name-1", active=True)


def test_acceptance_sequence_and_lazy():
    factory = Factory(
        LabelUser,
        overrides={
            "name": Sequence(lambda n: f"user{n}@example.com"),
            "label": Lazy(lambda f: f["name"].upper()),
        },
    )
    users = factory.build_batch(2)
    assert users[0].name == "user1@example.com"
    assert users[0].label == "USER1@EXAMPLE.COM"
    assert users[1].name == "user2@example.com"
    assert users[1].label == "USER2@EXAMPLE.COM"


def test_acceptance_lazy_uses_generated_name():
    factory = Factory(LabelUser, overrides={"label": Lazy(lambda f: f["name"].upper())})
    obj = factory.build()
    assert obj.name == "name-1"
    assert obj.label == "NAME-1"


def test_acceptance_types():
    factory = Factory(AllTypes, seed=123)
    obj = factory.build()
    assert isinstance(obj.enum, Color)
    assert obj.literal in ("a", "b")
    assert isinstance(obj.optional, int) or obj.optional is None
    assert isinstance(obj.lst, list)
    assert 1 <= len(obj.lst) <= 3
    for item in obj.lst:
        assert isinstance(item, int)
    assert isinstance(obj.date, datetime.date)
    assert obj.date.year == 2026
    assert isinstance(obj.dt, datetime.datetime)
    assert obj.dt.tzinfo == datetime.timezone.utc
    assert obj.dt.year == 2026
    assert isinstance(obj.dec, Decimal)
    assert isinstance(obj.uid, uuid.UUID)
    assert obj.uid.version == 4
    assert isinstance(obj.nested, Nested)
    assert isinstance(obj.nested.value, int)


def test_acceptance_range_same_min_max():
    factory = Factory(RangeInt, seed=0)
    for _ in range(10):
        assert factory.build().value == 18


def test_acceptance_invalid_range():
    with pytest.raises(FactoryError) as exc_info:
        Factory(BadRange)
    assert exc_info.value.code == "invalid_range"


def test_acceptance_unsupported_set():
    @dataclasses.dataclass
    class WithSet:
        values: set[int]

    with pytest.raises(FactoryError) as exc_info:
        Factory(WithSet)
    assert exc_info.value.code == "unsupported_type"
    assert "values" in str(exc_info.value)


def test_acceptance_unknown_field_override():
    factory = Factory(User, seed=0)
    with pytest.raises(FactoryError) as exc_info:
        factory.build(nope=1)
    assert exc_info.value.code == "unknown_field"


def test_acceptance_batch_too_large():
    factory = Factory(User, seed=0)
    with pytest.raises(FactoryError) as exc_info:
        factory.build_batch(10_001)
    assert exc_info.value.code == "batch_too_large"


def test_acceptance_recursion_optional():
    factory = Factory(Node, max_depth=5)
    node = factory.build()
    depth = 0
    current = node
    while current.child is not None:
        depth += 1
        current = current.child
    assert depth == 5
    assert current.child is None


def test_acceptance_recursion_non_optional():
    with pytest.raises(FactoryError) as exc_info:
        Factory(BadNonOptionalNode)
    assert exc_info.value.code == "recursion"


def test_frozen_dataclass():
    factory = Factory(FrozenUser, seed=0)
    obj = factory.build()
    assert isinstance(obj.id, int)
    assert isinstance(obj.name, str)
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.id = 5


def test_init_false_skipped():
    factory = Factory(InitFalseUser, seed=0)
    obj = factory.build()
    assert obj.id is not None
    assert obj.name == "fixed"  # default used, not generated


def test_kw_only_field():
    factory = Factory(KwOnlyUser, seed=0)
    obj = factory.build()
    assert isinstance(obj.id, int)
    assert isinstance(obj.name, str)


def test_list_of_nested_dataclass():
    @dataclasses.dataclass
    class Container:
        items: list[Nested]

    factory = Factory(Container, seed=0)
    obj = factory.build()
    assert isinstance(obj.items, list)
    assert 1 <= len(obj.items) <= 3
    for item in obj.items:
        assert isinstance(item, Nested)


def test_literal_single_value():
    @dataclasses.dataclass
    class Single:
        literal: Literal["only"]

    factory = Factory(Single, seed=0)
    obj = factory.build()
    assert obj.literal == "only"


def test_build_time_sequence_override():
    factory = Factory(LabelUser)
    obj = factory.build(name=Sequence(lambda n: f"user{n}"))
    assert obj.name == "user1"


def test_not_a_dataclass():
    with pytest.raises(FactoryError) as exc_info:
        Factory(NotADataclass)
    assert exc_info.value.code == "not_a_dataclass"


def test_use_default():
    factory = Factory(UseDefault, seed=0)
    obj = factory.build()
    assert obj.value == 42


def test_unsupported_dict():
    @dataclasses.dataclass
    class WithDict:
        value: dict[str, int]

    with pytest.raises(FactoryError) as exc_info:
        Factory(WithDict)
    assert exc_info.value.code == "unsupported_type"


def test_unsupported_union_non_optional():
    @dataclasses.dataclass
    class BadUnion:
        value: int | str

    with pytest.raises(FactoryError) as exc_info:
        Factory(BadUnion)
    assert exc_info.value.code == "unsupported_type"


def test_unsupported_any():
    @dataclasses.dataclass
    class WithAny:
        value: object

    with pytest.raises(FactoryError) as exc_info:
        Factory(WithAny)
    assert exc_info.value.code == "unsupported_type"


def test_unsupported_plain_class():
    @dataclasses.dataclass
    class WithPlain:
        value: Plain

    with pytest.raises(FactoryError) as exc_info:
        Factory(WithPlain)
    assert exc_info.value.code == "unsupported_type"
