"""
Classes supporting decays and branching fractions/ratios.
"""

from sqlalchemy import bindparam, select

from pdg.data import PdgProperty
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError, PdgNoDataError
from pdg.particle import PdgItem, PdgParticle


class PdgDecayProduct(object):
    """Class for all information about one product of a decay, including its
    PdgItem (which may resolve to one or more PdgParticles), its multiplier, and
    its subdecay (if any).
    """
    def __init__(self, item, multiplier, subdecay):
        """Instantiate a PdgDecayProduct."""
        assert isinstance(item, PdgItem)
        assert isinstance(multiplier, int)
        assert subdecay is None or isinstance(subdecay, PdgBranchingFraction)

        self.item = item
        self.multiplier = multiplier
        self.subdecay = subdecay


class PdgBranchingFraction(PdgProperty):
    """Class for all information about a decay, including its branching
    fraction, decay products, and subdecays.
    """
    def _get_decay(self):
        """Load decay information from the database."""
        if 'pdgdecay' not in self.cache:
            pdgdecay_table = self.api.db.tables['pdgdecay']
            query = select(pdgdecay_table).where(pdgdecay_table.c.pdgid == bindparam('pdgid'))
            with self.api.engine.connect() as conn:
                try:
                    result = conn.execute(query, {'pdgid': self.baseid}).fetchall()
                    self.cache['pdgdecay'] = [row._mapping for row in result]
                except AttributeError:
                    raise PdgInvalidPdgIdError('No PDGDECAY entry for ' % self.pdgid)
        return self.cache['pdgdecay']

    @property
    def decay_products(self):
        """A list of all PdgDecayProducts for the decay."""
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
    def mode_number(self):
        """Mode number of this decay.

        Note that the decay mode number may change from one edition of the Review of Particle Physics
        to the next one."""
        return self._get_pdgid()['mode_number']

    @property
    def is_subdecay(self):
        """True if this is a subdecay ("indented") decay mode."""
        data_type_code = self.data_type
        if len(data_type_code) < 4:
            return False
        else:
            return data_type_code[0:3] == 'BFX' or data_type_code[0:3] == 'BFI'

    @property
    def subdecay_level(self):
        """Return indentation level of a decay mode."""
        if self.is_subdecay:
            return int(self.data_type[3])
        else:
            return 0
