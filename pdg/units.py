"""
Constants and utilities for handling HEP units.
"""

from pdg.errors import PdgApiError
from typing import Optional

HBAR_IN_GEV_S = 6.582E-25

UNIT_CONVERSION_FACTORS = {
    'meV': (1E-3, 'eV'),
    'eV': (1E0, 'eV'),
    'keV': (1E3, 'eV'),
    'MeV': (1E6, 'eV'),
    'GeV': (1E9, 'eV'),
    'TeV': (1E12, 'eV'),
    'PeV': (1E15, 'eV'),
    'u': (931.49410242E6, 'eV'),
    's': (1E0, 's'),
    'yr': (31536000, 's'),
    'year': (31536000, 's'),
    'years': (31536000, 's'),
}


def convert(value: float, old_units: Optional[str]=None, new_units: Optional[str]=None) -> float:
    """Convert a value to a different unit.

    Args:
        value: Value to be converted.
        old_units: Units in which `value` is currently specified. If `None`,
            then `new_units` must be `None` as well.
        new_units: Units into which `value` is to be converted. If `None`, no
            unit conversion will be applied.

    Returns:
        Value after the specified unit conversion (if any) has been applied.

    Raises:
        :exc:`AssertionError`: If `old_units` is `None` but `new_units` is not.
        :exc:`~pdg.errors.PdgApiError`: If the unit conversion is invalid or
            unsupported.
    """
    if new_units is None:
        return value
    else:
        assert old_units is not None
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
