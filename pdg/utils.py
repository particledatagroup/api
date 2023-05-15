"""
Utilities for PDG API.
"""

from pdg.errors import PdgNoDataError, PdgAmbiguousValueError


def parse_id(pdgid):
    """Parse PDG Identifier and return (normalized base identifier, edition)."""
    try:
        baseid, edition = pdgid.split('/')
    except ValueError:
        baseid = pdgid
        edition = None
    return baseid.upper(), edition


def base_id(pdgid):
    """Return normalized base part of PDG Identifier."""
    return parse_id(pdgid)[0]


def make_id(baseid, edition=None):
    """Return normalized full PDG Identifier, possibly including edition."""
    if baseid is None:
        return None
    if edition is None:
        return baseid.upper()
    else:
        return ('%s/%s' % (baseid, edition)).upper()


def best(properties, pedantic=False, quantity=None):
    """Return the "best" property from an iterable of properties, or raise an exception.

    best does (pedantic=False) or does not (pedantic=True) make assumptions about what the best property might
    be in cases where the choice may be ambiguous. In the latter case, a PdgAmbiguous exception is raised while in the
    former case the best property is determined based on data flags and position in the Summary Tables.
    PdgNoDataError will be raised if there is no property that qualifies as best one.

    quantity is an optional string that in case of an exception will describe the property being sought.
    """
    for_what = ' for %s' % quantity if quantity else ''
    props_without_alternates = [p for p in properties if p.data_flags is None or 'A' not in p.data_flags]
    if len(props_without_alternates) == 0:
        raise PdgNoDataError('No best property found%s' % for_what)
    elif len(props_without_alternates) == 1:
        return props_without_alternates[0]
    else:
        if pedantic:
            raise PdgAmbiguousValueError('Ambiguous best property%s' % for_what)
        else:
            props_best = [p for p in props_without_alternates if p.data_flags is not None and 'D' in p.data_flags]
            if len(props_best) >= 1:
                return props_best[0]
            else:
                return props_without_alternates[0]
