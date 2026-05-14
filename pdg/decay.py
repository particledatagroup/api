"""
Classes supporting decays and branching fractions/ratios.
"""

from sqlalchemy import bindparam, select

from pdg.data import PdgProperty
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError, PdgNoDataError
from pdg.particle import PdgItem, PdgParticle
from sqlalchemy.engine.row import RowMapping
from typing import Iterator, Optional, cast


class PdgDecayProduct(object):
    """Class for all information about one product of a decay.

    This information includes the decay product's :class:`~pdg.particle.PdgItem`
    (which may resolve to one or more :class:`pdg.particle.PdgParticle`
    objects), its multiplier, and its subdecay (if any).
    """
    def __init__(self, item: PdgItem, multiplier: int,
                 subdecay: Optional['PdgBranchingFraction']=None):
        """
        Note:
            The constructor is intended for internal API use.

        Args:
            item: Corresponding :class:`~pdg.particle.PdgItem`.
            multiplier: Multiplicity of this product in the decay.
            subdecay: Optional description of this product's further decay.
        """
        self.item = item
        self.multiplier = multiplier
        self.subdecay = subdecay

    def __repr__(self) -> str:
        """Get a concise representation of the decay product."""
        fmt = "PdgDecayProduct(item='%s', multiplier=%d, subdecay=%r)"
        return fmt % (self.item.name, self.multiplier, self.subdecay)


class PdgBranchingFraction(PdgProperty):
    """Class for all information about a decay.

    This information includes the decay's branching fraction, decay products,
    and subdecays.
    """
    def _get_decay(self) -> list[RowMapping]:
        """Get decay information from the database."""
        if 'pdgdecay' not in self.cache:
            pdgdecay_table = self.api.db.tables['pdgdecay']
            query = select(pdgdecay_table).where(pdgdecay_table.c.pdgid == bindparam('pdgid'))
            with self.api.engine.connect() as conn:
                try:
                    result = conn.execute(query, {'pdgid': self.baseid}).fetchall()
                    self.cache['pdgdecay'] = [row._mapping for row in result]
                except AttributeError:
                    raise PdgInvalidPdgIdError('No PDGDECAY entry for %s' % self.pdgid)
        return cast(list[RowMapping], self.cache['pdgdecay'])

    def _repr_extra(self) -> str:
        "Extra details for `__repr`"
        return '"%s"' % self.description

    @property
    def decay_products(self) -> list[PdgDecayProduct]:
        "A list of all `PdgDecayProduct` objects for the decay."
        products = []
        for row in self._get_decay():
            if not row['is_outgoing']:
                continue

            product = PdgDecayProduct(
                item=PdgItem(self.api, row['pdgitem_id']),
                multiplier=row['multiplier'],
                subdecay=(PdgBranchingFraction(self.api, row['subdecay'])
                          if row['subdecay_id'] else None))
            products.append(product)
        return products

    @property
    def mode_number(self) -> int:
        """Mode number of this decay.

        Note:
            The decay mode number may change from one edition of the Review of
            Particle Physics to the next one.
        """
        return self._get_pdgid()['mode_number']

    @property
    def is_subdecay(self) -> bool:
        """`True` if this is a subdecay ("indented") decay mode."""
        data_type_code = self.data_type
        if len(data_type_code) < 4:
            return False
        else:
            return data_type_code[0:3] == 'BFX' or data_type_code[0:3] == 'BFI'

    @property
    def subdecay_level(self) -> int:
        "Indentation level of a decay mode."
        if self.is_subdecay:
            return int(self.data_type[3])
        else:
            return 0

    def subdecays(self) -> Iterator['PdgBranchingFraction']:
        """Get iterator over all subdecays of this decay.

        Note:
            Subdecay data is returned as-is from the Particle Listings. Its
            interpretation will depend on the conventions used by the specific
            section of the Listings.
        """
        if not hasattr(self.api, '_subdecay_warned'):
            warning = ('Warning: Subdecay data is returned as-is from the ' +
                       'Particle Listings. Its interpretation will depend on the ' +
                       'conventions used by the specific section of the Listings.')
            self.api.logger.warning(warning)
            self.api._subdecay_warned = True
        child_dtype = self.data_type[:3] + str(self.subdecay_level + 1)
        pdgid = self.api.db.tables['pdgid']
        query = select(pdgid.c.pdgid)
        query = query.where(pdgid.c.parent_pdgid == bindparam('parent_pdgid'))
        query = query.where(pdgid.c.data_type == bindparam('data_type'))
        with self.api.engine.connect() as conn:
            matches = conn.execute(query, {'parent_pdgid': self.baseid,
                                           'data_type': child_dtype}).fetchall()
        for row in matches:
            yield PdgBranchingFraction(self.api, row.pdgid, self.edition)

    def branching_ratios(self) -> Iterator['PdgBranchingRatio']:
        """Get iterator over all branching ratios associated with this
        branching fraction."""
        pdgid_map = self.api.db.tables['pdgid_map']
        query = select(pdgid_map.c.target) \
            .where(pdgid_map.c.source == bindparam('source'))
        with self.api.engine.connect() as conn:
            matches = conn.execute(query, {'source': self.baseid}).fetchall()
        for row in matches:
            yield PdgBranchingRatio(self.api, row.target, self.edition)


class PdgBranchingRatio(PdgProperty):
    "Class for all information about a branching ratio."
    def branching_fractions(self) -> Iterator[PdgBranchingFraction]:
        """Get iterator over all branching fractions associated with this
        branching ratio."""
        pdgid_map = self.api.db.tables['pdgid_map']
        query = select(pdgid_map.c.source) \
            .where(pdgid_map.c.target == bindparam('target'))
        with self.api.engine.connect() as conn:
            matches = conn.execute(query, {'target': self.baseid}).fetchall()
        for row in matches:
            yield PdgBranchingFraction(self.api, row.source, self.edition)

    def _repr_extra(self) -> str:
        "Extra details for `__repr`"
        return '"%s"' % self.description
