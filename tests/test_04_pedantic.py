"""
Test cases for PdgParticle.
"""
from __future__ import print_function

from pytest import raises

from pdg.errors import PdgAmbiguousValueError


def test_properties(api):
    api.pedantic = True
    with raises(PdgAmbiguousValueError):
        getattr(api.get('Q007'), 'mass')

def test_summary(api):
    api.pedantic = True
    with raises(PdgAmbiguousValueError):
        api.get('S013D').best_summary()
