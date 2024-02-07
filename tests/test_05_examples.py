"""
Test cases for some use examples.
"""
from __future__ import print_function

def test_dm(api):
    p = api.get_particle_by_name('p')
    n = api.get_particle_by_name('n')
    dm = n.mass - p.mass
    assert round(dm, 5) == 0.00129
