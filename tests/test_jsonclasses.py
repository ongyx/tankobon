# coding: utf8

import json

from tankobon.jsonclasses import dataclass  # type: ignore


@dataclass
class Case:
    foo: int
    bar: str = "baz"


@dataclass
class NestedCase:
    foo: Case


def test_dumps_and_loads():

    instance = Case(0)

    dumped = json.dumps(instance, indent=4)
    print(dumped)

    loaded = json.loads(dumped)
    print(loaded)

    assert isinstance(loaded, Case)


def test_nested():
    instance = NestedCase(Case(0))

    dumped = json.dumps(instance)
    print(dumped)
