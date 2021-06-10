# coding: utf8

import json

from tankobon.jsonclasses import *


def test_dumps_and_loads():
    @dataclass
    class Test:
        foo: int
        bar: str = "baz"

    instance = Test(0)

    dumped = json.dumps(instance, indent=4)
    print(dumped)

    loaded = json.loads(dumped)
    print(loaded)

    assert isinstance(loaded, Test)
