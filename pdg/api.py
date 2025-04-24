"""
PDG API top-level class.
"""

import sqlalchemy
from sqlalchemy import func, select, bindparam, distinct, desc
import pdg
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError, PdgNoDataError
from pdg.utils import parse_id
from pdg.data import PdgProperty, PdgMass, PdgWidth, PdgLifetime, PdgText
from pdg.decay import PdgBranchingFraction, PdgBranchingRatio, PdgItem
from pdg.particle import PdgParticle, PdgParticleList


# Map PDG data type codes to corresponding classes
DATA_TYPE_MAP = {
    'PART': PdgParticleList,
    'M':    PdgMass,
    'BFX':  PdgBranchingFraction,
    'BFX1': PdgBranchingFraction,
    'BFX2': PdgBranchingFraction,
    'BFX3': PdgBranchingFraction,
    'BFX4': PdgBranchingFraction,
    'BFX5': PdgBranchingFraction,
    'BFI':  PdgBranchingFraction,
    'BFI1': PdgBranchingFraction,
    'BFI2': PdgBranchingFraction,
    'BFI3': PdgBranchingFraction,
    'BFI4': PdgBranchingFraction,
    'BFI5': PdgBranchingFraction,
    'BR': PdgBranchingRatio,
    'G': PdgWidth,
    'T': PdgLifetime,
    'SEC': PdgText,
}


class PdgApi:

    def __init__(self, database_url, pedantic=False):
        """Initialize PDG API.

        database_url is the URL of the PDG database to connect to. The default database is the SQLite file
        installed together with package pdg.

        pedantic can be set True to enable pedantic mode, where, in cases where the choice of "PDG best value" might
        be ambiguous, no assumptions are made and instead a PdgAmbiguousValue exception is raised.
        """
        self.database_url = database_url
        self.engine = sqlalchemy.create_engine(self.database_url)
        self.db = sqlalchemy.MetaData()
        self.db.reflect(self.engine)
        for k in self.info_keys():
            setattr(self, k, self.info(k))
        self.pedantic = pedantic

    def __str__(self):
        s = ['%s Review of Particle Physics, data release %s, API version %s' % (self.info('edition'),
                                                                                 self.info('data_release_timestamp'),
                                                                                 pdg.__version__),
             '%s' % self.info('citation'),
             '(C) %s, data released under %s' % (self.info('producer'), self.info('license')),
             self.info('about')
             ]
        return '\n'.join(s)

    def info(self, key):
        """Return metadata info specified by key."""
        pdginfo_table = self.db.tables['pdginfo']
        query = select(pdginfo_table.c.value).where(pdginfo_table.c.name == bindparam('key'))
        with self.engine.connect() as conn:
            return conn.execute(query, {'key': key}).scalar()

    def info_keys(self):
        """Return list of all metadata keys."""
        pdginfo_table = self.db.tables['pdginfo']
        query = select(pdginfo_table.c.name)
        with self.engine.connect() as conn:
            return [k[0] for k in conn.execute(query).fetchall()]

    @property
    def editions(self):
        """List of all editions of the Review for which the database has data."""
        pdgdata_table = self.db.tables['pdgdata']
        query = select(distinct(pdgdata_table.c.edition)).order_by(desc(pdgdata_table.c.edition))
        with self.engine.connect() as conn:
            return [e[0] for e in conn.execute(query).fetchall()]

    @property
    def default_edition(self):
        """Return the default edition for this database."""
        return self.info('edition')

    def get(self, pdgid, edition=None):
        """Return PdgData object for given PDG Identifier.

        The get method checks what data the PDG Identifier describes and returns an
        object of the most appropriate class derived from the PdgData base class.
        For example, for a PDG Identifier describing a particle, an object of class
        PdgParticleList is returned, while for a branching fraction a PdgBranchingFraction
        object is returned.

        edition can be set to a specific edition, from which the data should later be retrieved.
        """
        if edition is None:
            baseid, edition = parse_id(pdgid)
        else:
            baseid = pdgid
        pdgid_table = self.db.tables['pdgid']
        try:
            query = select(pdgid_table.c.data_type).where(pdgid_table.c.pdgid == bindparam('pdgid'))
            with self.engine.connect() as conn:
                data_type = conn.execute(query, {'pdgid': baseid}).fetchone()[0]
        except Exception:
            raise PdgInvalidPdgIdError('PDG Identifier %s not found' % pdgid)
        try:
            cls = DATA_TYPE_MAP[data_type]
        except KeyError:
            cls = PdgProperty
        return cls(self, baseid, edition)

    def get_all(self, data_type_key=None, edition=None):
        """Return iterator over all PDG Identifiers / quantities. Returns PdgProperties or derived classes.

        If data_type_key is set, only quantities of the given type are returned.
        See doc_data_type_keys() for the list of possible data type codes.

        edition can be set to a specific edition, from which data should later be retrieved.
        """
        pdgid_table = self.db.tables['pdgid']
        query = select(pdgid_table.c.pdgid, pdgid_table.c.data_type)
        if data_type_key is not None:
            query = query.where(pdgid_table.c.data_type == bindparam('data_type_key'))
        query = query.order_by(pdgid_table.c.sort)
        with self.engine.connect() as conn:
            for item in conn.execute(query, {'data_type_key': data_type_key}):
                try:
                    cls = DATA_TYPE_MAP[item.data_type]
                except KeyError:
                    cls = PdgProperty
                yield cls(self, item.pdgid, edition)

    def _get_particles_by_name(self, name, case_sensitive=True, edition=None, unique=True):
        """Helper function used by get_particle(s)_by_name. Returns a
        PdgParticle (list thereof) if unique is True (False). Raises a
        PdgAmbiguousValueError if more than one PdgItem exists with the given
        name, or if unique=True and the PdgItem refers to more than one
        particle.
        """
        pdgitem_table = self.db.tables['pdgitem']
        query = select(pdgitem_table.c.id)
        if case_sensitive:
            query = query.where(pdgitem_table.c.name == bindparam('name'))
        else:
            name = name.lower()
            query = query.where(func.lower(pdgitem_table.c.name) == bindparam('name'))
        with self.engine.connect() as conn:
            matches = conn.execute(query, {'name': name}).fetchall()
        if len(matches) == 0:
            raise ValueError('No particle found with name %s' % name)
        elif len(matches) == 1:
            item = PdgItem(self, matches[0].id, edition=edition)
            return item.particle if unique else item.particles
        else:
            raise PdgAmbiguousValueError('More than one PDGITEM named %s', name)

    def get_particle_by_name(self, name, case_sensitive=True, edition=None):
        """Get particle by its name.

        case_sensitive can be set False to indicate that the particle name should be
        considered not case-sensitive.

        edition can be set to a specific edition, from which data should later be retrieved.
        """
        return self._get_particles_by_name(name, case_sensitive=case_sensitive,
                                           edition=edition, unique=True)

    def get_particles_by_name(self, name, case_sensitive=True, edition=None):
        """Get all particles for a (possibly generic) name.

        case_sensitive can be set False to indicate that the particle name should be
        considered not case-sensitive.

        edition can be set to a specific edition, from which data should later be retrieved.
        """
        return self._get_particles_by_name(name, case_sensitive=case_sensitive,
                                           edition=edition, unique=False)

    def get_particle_by_mcid(self, mcid, edition=None):
        """Get particle by its MC ID.

        edition can be set to a specific edition, from which data should later be retrieved.
        """
        pdgparticle_table = self.db.tables['pdgparticle']
        query = select(distinct(pdgparticle_table.c.pdgid))
        query = query.where(pdgparticle_table.c.mcid == bindparam('mcid'))
        with self.engine.connect() as conn:
            matches = [p.pdgid for p in conn.execute(query, {'mcid': mcid})]
        if len(matches) == 0:
            raise ValueError('No particle found with MC ID %s' % mcid)
        elif len(matches) == 1:
            return PdgParticle(self, matches[0], edition, set_mcid=mcid)
        else:
            raise ValueError('MC number %s matches %i particles with PDG Identifiers %s' % (mcid, len(matches), matches))

    def get_particles(self, edition=None):
        """Return iterator over all particles.

        edition can be set to a specific edition, from which data should later be retrieved.
        """
        pdgid_table = self.db.tables['pdgid']
        pdgparticle_table = self.db.tables['pdgparticle']
        query = select(distinct(pdgid_table.c.pdgid)).join(pdgparticle_table)
        query = query.where(pdgid_table.c.data_type == 'PART')
        query = query.order_by(pdgid_table.c.sort)
        with self.engine.connect() as conn:
            for item in conn.execute(query):
                yield PdgParticleList(self, item.pdgid, edition)

    def get_canonical_name(self, name):
        return self.get_particle_by_name(name).name

    def doc_key_value(self, table_name, column_name, key):
        """Get documentation on the meaning of key values or flags used in the PDG API."""
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == bindparam('table_name'))
        query = query.where(pdgdoc_table.c.column_name == bindparam('column_name'))
        query = query.where(pdgdoc_table.c.value == bindparam('value'))
        with self.engine.connect() as conn:
            try:
                return conn.execute(query, {'table_name': table_name, 'column_name': column_name, 'value': key}).\
                    fetchone()._mapping
            except AttributeError:
                raise PdgNoDataError('No documentation for value %s in table %s.%s' % (key, table_name, column_name))

    def doc_data_type_keys(self, as_text=True):
        """Get list of data type keys.

        The PDG API uses a data type key as part of the PDG Identifier metadata to denote the kind of information
        described by a given identifier. These data type keys can be used to select desired particle properties in
        methods such as PdgParticle.properties().

        doc_data_type_keys() returns a list of all possible data type key values.
        When as_text is True (default), the list is returned as a formatted string suitable for printing.
        Otherwise, a list of dict is returned, where each dict describes a possible key value.
        """
        keys = []
        if as_text:
            keys.append('Key value     Description')
            keys.append('-'*60)
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == 'PDGID')
        query = query.where(pdgdoc_table.c.column_name == 'DATA_TYPE')
        query.order_by(pdgdoc_table.c.indicator, pdgdoc_table.c.value)
        with self.engine.connect() as conn:
            for item in conn.execute(query):
                if as_text:
                    keys.append('  %-8s    %s' % (item.value, item.description))
                else:
                    keys.append(item._mapping)
        if as_text:
            return '\n'.join(keys)
        else:
            return keys

    def doc_value_type_keys(self, as_text=True):
        """Get list of summary value type keys.

        For each summary value, the value type key specifies how this value was derived, e.g. whether it is the
        result of a weighted average, of a fit, etc.

        doc_summary_value_type_keys() returns a list of all possible summary value type key values.
        When as_text is True (default), the list is returned as a formatted string suitable for printing.
        Otherwise, a list of dict is returned, where each dict describes a possible key value.
        """
        keys = []
        if as_text:
            keys.append('Key value   Indicator            Description')
            keys.append('-'*60)
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == 'PDGDATA')
        query = query.where(pdgdoc_table.c.column_name == 'VALUE_TYPE')
        query.order_by(pdgdoc_table.c.indicator, pdgdoc_table.c.value)
        with self.engine.connect() as conn:
            for item in conn.execute(query):
                if as_text:
                    keys.append('  %-8s  %-20s  %s' % (item.value, item.indicator, item.description))
                else:
                    keys.append(item._mapping)
        if as_text:
            return '\n'.join(keys)
        else:
            return keys
