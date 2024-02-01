"""
Classes supporting decays and branching fractions/ratios.
"""

from sqlalchemy import bindparam, select

from pdg.data import PdgProperty
from pdg.errors import PdgInvalidPdgIdError, PdgNoDataError
from pdg.particle import PdgParticle


class PdgItem:
    def __init__(self, api, pdgitem_id):
        self.api = api
        self.pdgitem_id = pdgitem_id
        self.cache = {}

    def __repr__(self):
        name = self._get_pdgitem()['name']
        return 'PdgItem("%s")' % name

    def _get_pdgitem(self):
        if 'pdgitem' not in self.cache:
            pdgitem_table = self.api.db.tables['pdgitem']
            query = select(pdgitem_table).where(pdgitem_table.c.id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result is None:
                    raise PdgNoDataError('No PDGITEM entry for %s' % self.pdgitem_id)
                self.cache['pdgitem'] = result._mapping
        return self.cache['pdgitem']

    def _get_targets(self):
        pdgitem_map_table = self.api.db.tables['pdgitem_map']
        query = select(pdgitem_map_table).where(pdgitem_map_table.c.pdgitem_id == bindparam('pdgitem_id'))
        with self.api.engine.connect() as conn:
            rows = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchall()
            for row in rows:
                yield PdgItem(self.api, row.target_id)

    @property
    def has_particle(self):
        if 'has_particle' not in self.cache:
            pdgparticle_table = self.api.db.tables['pdgparticle']
            query = select(pdgparticle_table).where(pdgparticle_table.c.pdgitem_id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result:
                    self.cache['pdgparticle'] = result._mapping
                    self.cache['has_particle'] = True
                else:
                    self.cache['has_particle'] = False
        return self.cache['has_particle']

    @property
    def particle(self):
        if not self.has_particle:
            raise PdgNoDataError('No direct PDGPARTICLE for PDGITEM %s' % self.pdgitem_id)
        p = self.cache['pdgparticle']
        return PdgParticle(self.api, p['pdgid'], set_mcid=p['mcid'])

    @property
    def particles(self):
        if self.has_particle:
            yield self.particle
        else:
            for target in self._get_targets():
                for p in target.particles:
                    yield p

    @property
    def name(self):
        return self._get_pdgitem()['name']

    @property
    def name_tex(self):
        return self._get_pdgitem()['name_tex']

    @property
    def item_type(self):
        return self._get_pdgitem()['item_type']


class PdgDecayProduct(object):
    def __init__(self, item, multiplier, subdecay):
        assert isinstance(item, PdgItem)
        assert isinstance(multiplier, int)
        assert subdecay is None or isinstance(subdecay, PdgBranchingFraction)

        self.item = item
        self.multiplier = multiplier
        self.subdecay = subdecay


class PdgBranchingFraction(PdgProperty):
    def _get_decay(self):
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
    def products(self):
        for row in self._get_decay():
            if not row['is_outgoing']:
                continue

            yield PdgDecayProduct(
                item=PdgItem(self.api, row['pdgitem_id']),
                multiplier=row['multiplier'],
                subdecay=(PdgBranchingFraction(self.api, row['subdecay'])
                          if row['subdecay_id'] else None))

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
