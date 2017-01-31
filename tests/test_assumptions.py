import collections
import pytest


def test_exception_in_context_manager_plain():
    ordering = []

    class Ctx(collections.Iterator):
        def __init__(self, iterable):
            ordering.append("init")
            self._iterator = iter(iterable)

        def __enter__(self):
            ordering.append("enter")
            return self

        def __iter__(self):
            ordering.append("iter")
            return self

        def __next__(self):
            ordering.append("next")
            return next(self._iterator)

        next = __next__

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                ordering.append("Exception")
            ordering.append("exit")
            return

    with pytest.raises(Exception):
        with Ctx([1, 2, 3]) as c:
            for num in c:
                ordering.append("loop%d" % num)
                if num == 2:
                    ordering.append('Exception')
                    raise Exception

    assert 'Exception' in ordering
