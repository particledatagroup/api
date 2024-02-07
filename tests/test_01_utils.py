"""
Test cases for utility functions.
"""
from __future__ import print_function

from pdg import utils


def test_rounding():
    assert utils.pdg_round(0.827, 0.119) == (0.83, 0.12)
    assert utils.pdg_round(0.827, 0.367) == (0.8, 0.4)
    assert utils.pdg_round(12.3456, .99) == (12.3, 1.0)

def test_parse_id():
    assert utils.parse_id('s043m/2020') == ('S043M', '2020')
    assert utils.parse_id('s043m') == ('S043M', None)

def test_base_id():
    assert utils.base_id('q007/2020') == 'Q007'

def test_make_id():
    assert utils.make_id('q007', None) == 'Q007'
    assert utils.make_id('q007', '2020') == 'Q007/2020'
