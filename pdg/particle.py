"""
Definition of top-level particle container class.
"""

from sqlalchemy import select, bindparam, distinct
from sqlalchemy import and_, or_
from pdg.errors import PdgApiError, PdgNoDataError, PdgAmbiguousValue
from pdg.utils import make_id
from pdg.data import PdgData


class PdgParticle(PdgData):
    """Container class for all information about a given particle.

    In addition to access to basic particle properties such as mass, charge, quantum numbers and
    PDG MC ID, this class provides methods to iterate over the data on all particle properties listed
    in Particle Listings and Summary Tables, including branching fractions, masses, life-times, etc.
    """

    def __init__(self, api, pdgid, edition=None, set_mcid=None):
        """Constructor for a PdgParticle given its PDG Identifier and possibly its MC ID."""
        super(PdgParticle, self).__init__(api, pdgid, edition)
        self.set_mcid = set_mcid
        self.cc_type_flag = 'P'
        if set_mcid is not None and set_mcid < 0:
            self.cc_type_flag = 'A'

    def _get_particle_data(self):
        """Get particle data."""
        if 'pdgparticle' not in self.cache:
            # FIXME: if we keep PDGPARTICLE.PDGID, don't need to join with PDGID table
            pdgid_table = self.api.db.tables['pdgid']
            pdgparticle_table = self.api.db.tables['pdgparticle']
            query = select(pdgparticle_table).join(pdgid_table)
            query = query.where(pdgid_table.c.pdgid == bindparam('pdgid'))
            if self.set_mcid is not None:
                query = query.where(pdgparticle_table.c.mcid == bindparam('mcid'))
            query = query.where(pdgparticle_table.c.entry_type == 'P')
            query = query.where(or_(and_(pdgparticle_table.c.charge_type == 'S', pdgparticle_table.c.cc_type == bindparam('cc_type')),
                                    and_(pdgparticle_table.c.charge_type == 'S', pdgparticle_table.c.cc_type == 'S'),
                                    and_(pdgparticle_table.c.charge_type == 'E', pdgparticle_table.c.cc_type.is_(None))))
            with self.api.engine.connect() as conn:
                params = {'pdgid': self.baseid, 'cc_type': self.cc_type_flag, 'mcid': self.set_mcid}
                matches = conn.execute(query, params).fetchall()
                if len(matches) == 1:
                    self.cache['pdgparticle'] = matches[0]._mapping
                elif len(matches) == 0:
                    mcid_string = ', MC ID = %s' % self.set_mcid if self.set_mcid else ''
                    raise PdgNoDataError('Particle data for %s%s not found' % (self.pdgid, mcid_string))
                else:
                    raise PdgAmbiguousValue('Multiple particles for %s - please set MC ID' % self.pdgid)
        return self.cache['pdgparticle']

    def properties(self, data_type_key=None, require_summary_data=False):
        """Return iterator over specified particle property data.

        By default, all properties excluding branching fractions and branching fraction ratios
        are returned (these should be retrieved via the specific branching fraction methods).

        By setting data_type_key, only the properties of the corresponding type are returned.
        For example, using data_type_key='M' will return particle masses. Use PdgApi.doc_data_type_keys()
        to get a list of possible data_type_key values.

        require_summary_data can be set True to request only properties where the current edition has
        summary value(s) in the Particle Listings or Summary Table.
        """
        pdgid_table = self.api.db.tables['pdgid']
        query = select(distinct(pdgid_table.c.pdgid))
        if require_summary_data:
            pdgdata_table = self.api.db.tables['pdgdata']
            query = query.join(pdgdata_table)
            query = query.where(pdgdata_table.c.edition == bindparam('edition'))
        query = query.where(pdgid_table.c.parent_pdgid == bindparam('parent_id'))
        if data_type_key is None:
            # NOTE: like/notlike SQL operators never match null values
            query = query.where((pdgid_table.c.data_type.notlike('BF%')) | (pdgid_table.c.data_type.is_(None)))
            query = query.where((pdgid_table.c.data_type.notlike('BR%')) | (pdgid_table.c.data_type.is_(None)))
        else:
            query = query.where(pdgid_table.c.data_type == bindparam('data_type_key'))
        query = query.order_by(pdgid_table.c.sort)
        with self.api.engine.connect() as conn:
            for entry in conn.execute(query, {'parent_id': self.baseid,
                                              'edition': self.edition,
                                              'data_type_key': data_type_key}):
                yield self.api.get(make_id(entry.pdgid, self.edition))

    def masses(self, require_summary_data=False):
        """Return iterator over mass data.

        For most particles, there is only a single mass property, and so the particle's
        PDG best mass value in GeV can be obtained e.g. from

        list(some_particle.masses())[0].best_value_in_GeV()

        For other particles (e.g. for the top quark) there are different ways to determine the mass and the user
        needs to decide which mass value is the most appropriate for their use case.
        """
        return self.properties('M', require_summary_data)

    def mass(self):
        """Return PDG "best" mass in GeV.

        mass() returns the PDG "best" mass value in cases where the choice of value is unambiguous.
        If the choice of value is ambiguous, Exception PdgAmbiguousValue is raised.
        If no mass value is available, None is returned.
        """
        masses = list(self.masses())
        if len(masses) == 0:
            return None
        if len(masses) == 1:
            return masses[0].best_value_in_GeV()     # May also raise PdgAmbiguousValue
        else:
            raise PdgAmbiguousValue('%s (%s) has multiple mass properties' % (self.pdgid, self.description()))

    def lifetimes(self, require_summary_data=False):
        """Return iterator over lifetime data."""
        return self.properties('T', require_summary_data)

    def branching_fractions(self, data_type_key='BF%', require_summary_data=False):
        """Return iterator over given type(s) of branching fraction data.

        With data_type_key='BF%' (default), all branching fractions, including subdecay modes, are returned.

        require_summary_data can be set True to request only branching fractions where the current edition has
        summary value(s) in the Particle Listings or Summary Table.
        """
        if data_type_key[0:2] != 'BF':
            raise PdgApiError('illegal branching fraction data type key %s' % data_type_key)
        pdgid_table = self.api.db.tables['pdgid']
        query = select(distinct(pdgid_table.c.pdgid))
        if require_summary_data:
            pdgdata_table = self.api.db.tables['pdgdata']
            query = query.join(pdgdata_table)
            query = query.where(pdgdata_table.c.edition == bindparam('edition'))
        query = query.where(pdgid_table.c.parent_pdgid.like(bindparam('parent_id')))
        query = query.where(pdgid_table.c.data_type.like(bindparam('data_type_key')))
        query = query.order_by(pdgid_table.c.sort)
        with self.api.engine.connect() as conn:
            for entry in conn.execute(query, {'parent_id': self.baseid+'%',
                                              'data_type_key': data_type_key,
                                              'edition': self.edition}):
                yield self.api.get(make_id(entry.pdgid, self.edition))

    def exclusive_branching_fractions(self, include_subdecays=False, require_summary_data=False):
        """Return iterator over exclusive branching fraction data.

        Set include_subdecays to True (default is False) to also include
        subdecay modes (i.e. modes shown indented in the Summary Tables).

        require_summary_data can be set True to request only branching fractions where the current edition has
        summary value(s) in the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFX%', require_summary_data)
        else:
            return self.branching_fractions('BFX', require_summary_data)

    def inclusive_branching_fractions(self, include_subdecays=False, require_summary_data=False):
        """Return iterator over inclusive branching fraction data.

        Set include_subdecays to True (default is False) to also include
        subdecay modes (i.e. modes shown indented in the Summary Tables).

        require_summary_data can be set True to request only branching fractions where the current edition has
        summary value(s) in the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFI%', require_summary_data)
        else:
            return self.branching_fractions('BFI', require_summary_data)

    def name(self):
        """Get particle name."""
        return self._get_particle_data()['name']

    def mcid(self):
        """Get the particle's MC ID."""
        return self._get_particle_data()['mcid']

    def charge(self):
        """Get the particle's charge."""
        return self._get_particle_data()['charge']

    def quantum_I(self):
        """Get the particle's quantum number I"""
        return self._get_particle_data()['quantum_i']

    def quantum_G(self):
        """Get the particle's quantum number G"""
        return self._get_particle_data()['quantum_g']

    def quantum_J(self):
        """Get the particle's quantum number J"""
        return self._get_particle_data()['quantum_j']

    def quantum_P(self):
        """Get the particle's quantum number P"""
        return self._get_particle_data()['quantum_p']

    def quantum_C(self):
        """Get the particle's quantum number C"""
        return self._get_particle_data()['quantum_c']

    def is_boson(self):
        """Return True if particle is a gauge boson."""
        return 'G' in self.data_flags()

    def is_quark(self):
        """Return True if particle is a quark."""
        return 'Q' in self.data_flags()

    def is_lepton(self):
        """Return True if particle is a lepton."""
        return 'L' in self.data_flags()

    def is_meson(self):
        """Return True if particle is a meson."""
        return 'M' in self.data_flags()

    def is_baryon(self):
        """Return True if particle is a baryon."""
        return 'B' in self.data_flags()
