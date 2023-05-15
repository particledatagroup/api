"""
Constants and utilities for handling HEP units.
"""

from pdg.errors import PdgApiError

UNIT_CONVERSION_FACTORS = {
    'meV': (1E-3, 'eV'),
    'eV': (1E0, 'eV'),
    'keV': (1E3, 'eV'),
    'MeV': (1E6, 'eV'),
    'GeV': (1E9, 'eV'),
    'TeV': (1E12, 'eV'),
    'PeV': (1E15, 'eV'),
}


def convert(value, old_units=None, new_units=None):
    """Utility to convert value to a different unit."""
    if new_units is None:
        return value
    else:
        try:
            old_factor = UNIT_CONVERSION_FACTORS[old_units]
        except KeyError:
            raise PdgApiError('Cannot convert from %s' % old_units)
        try:
            new_factor = UNIT_CONVERSION_FACTORS[new_units]
        except KeyError:
            raise PdgApiError('Cannot convert to %s' % new_units)
        if old_factor[1] != new_factor[1]:
            raise PdgApiError('Illegal unit conversion from %s to %s', old_factor[1], new_factor[1])
        return value * old_factor[0] / new_factor[0]
