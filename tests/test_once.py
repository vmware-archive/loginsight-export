import pytest
import warnings
import logging

from loginsightexport.paramhelper import once


def test_once():
    """Verify warnings are emitted when a @once'd function is invoked"""
    @once
    def a(x):
        return x

    @once
    def b(x):
        return x

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")

        assert 1 == a(1)
        assert 2 == a(2)
        assert 1 == a(1)

        assert 2 == b(2)

        assert len(w) == 1
        assert 'called multiple times' in str(w[-1].message)

    assert len(a._seen_history) == 2
    assert len(b._seen_history) == 1
