
def test_exception_in_context_manager_plain():
    ordering = []

    class Ctx(object):
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
            return self._iterator.__next__()

        def __exit__(self, *args):
            ordering.append("exit")
            return True

    with Ctx([1, 2, 3]) as c:
        for num in c:
            ordering.append("loop%d" % num)
            if num == 2:
                ordering.append('Exception')
                raise Exception

    assert ordering == ['init', 'enter', 'iter', 'next', 'loop1', 'next', 'loop2', 'Exception', 'exit']
