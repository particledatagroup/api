"""
PDG API top-level class.
"""

import logging
import sqlalchemy
from sqlalchemy import func, select, bindparam, distinct, desc
from sqlalchemy.engine.row import RowMapping
import pdg
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError, PdgNoDataError
from pdg.utils import parse_id
from pdg.data import PdgData, PdgProperty, PdgMass, PdgWidth, PdgLifetime, PdgText
from pdg.decay import PdgBranchingFraction, PdgBranchingRatio, PdgItem
from pdg.particle import PdgParticle, PdgParticleList
from typing import Iterator, Optional, cast


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

    def __init__(self, database_url: str, pedantic: bool=False):
        """Initialize PDG API.

        Args:
            database_url: URL of the PDG database to connect to. The default
                database is the SQLite file installed together with package pdg.

            pedantic: Can be set True to enable pedantic mode, where, in cases
                where the choice of "PDG best value" might be ambiguous, no
                assumptions are made and instead a PdgAmbiguousValue exception is
                raised.
        """
        self.database_url = database_url
        self.engine = sqlalchemy.create_engine(self.database_url)
        self.db = sqlalchemy.MetaData()
        self.db.reflect(self.engine)
        for k in self.info_keys():
            setattr(self, k, self.info(k))
        self.pedantic = pedantic

        self.logger = logging.getLogger('PDG')
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())
            self.logger.propagate = False

        self._subdecay_warned = False # see PdgBranchingFraction.subdecays()

    def __str__(self) -> str:
        """Get description of the PDG API.

        Returns:
            String with details including API edition, license, and citation.
        """
        s = ['%s Review of Particle Physics, data release %s, API version %s' % (self.info('edition'),
                                                                                 self.info('data_release_timestamp'),
                                                                                 pdg.__version__),
             '%s' % self.info('citation'),
             '(C) %s, data released under %s' % (self.info('producer'), self.info('license')),
             self.info('about')
             ]
        return '\n'.join(s)

    def info(self, key: str) -> str:
        """Get metadata info specified by key.

        Args:
            key: Metadata key to look up. A list of keys can be obtained using
                :func:`info_keys`.

        Returns:
            Metadata info.
        """
        pdginfo_table = self.db.tables['pdginfo']
        query = select(pdginfo_table.c.value).where(pdginfo_table.c.name == bindparam('key'))
        with self.engine.connect() as conn:
            return cast(str, conn.execute(query, {'key': key}).scalar())

    def info_keys(self) -> list[str]:
        """Get list of all metadata keys.

        Returns:
            List of keys, each of which can be passed to :func:`info`.
        """
        pdginfo_table = self.db.tables['pdginfo']
        query = select(pdginfo_table.c.name)
        with self.engine.connect() as conn:
            return [k[0] for k in conn.execute(query).fetchall()]

    @property
    def editions(self) -> list[str]:
        """List of all editions of the Review for which the database has data."""
        pdgdata_table = self.db.tables['pdgdata']
        query = select(distinct(pdgdata_table.c.edition)).order_by(desc(pdgdata_table.c.edition))
        with self.engine.connect() as conn:
            return [e[0] for e in conn.execute(query).fetchall()]

    @property
    def default_edition(self) -> str:
        """Default edition for this database."""
        return self.info('edition')

    def get(self, pdgid: str, edition: Optional[str]=None) -> PdgData:
        """Get `PdgData` object for given PDG Identifier.

        Args:
            pdgid: PDG Identifier to look up.
            edition: Can be set to a specific edition, from which the data
                should later be retrieved.

        Returns:
            An object of the most appropriate class (based on what the PDG
            Identifier refers to) derived from the :class:`~pdg.data.PdgData`
            base class. For example, for a PDG Identifier describing a particle,
            an object of class :class:`~pdg.particle.PdgParticleList` is
            returned, while for a branching fraction a
            :class:`~pdg.decay.PdgBranchingFraction` object is returned.
        """
        if edition is None:
            baseid, edition = parse_id(pdgid)
        else:
            baseid = pdgid
        pdgid_table = self.db.tables['pdgid']
        try:
            query = select(pdgid_table.c.data_type).where(pdgid_table.c.pdgid == bindparam('pdgid'))
            with self.engine.connect() as conn:
                row = conn.execute(query, {'pdgid': baseid}).fetchone()
                assert row is not None
                data_type = row[0]
        except Exception:
            raise PdgInvalidPdgIdError('PDG Identifier %s not found' % pdgid)
        try:
            cls = DATA_TYPE_MAP[data_type]
        except KeyError:
            cls = PdgProperty
        return cls(self, baseid, edition)

    def get_all(self, data_type_key=None, edition=None) -> Iterator[PdgData]:
        """Get iterator over all PDG Identifiers / quantities.

        Args:
            data_type_key: If set, only quantities of the given type are
                returned. See :func:`~doc_data_type_keys` for the list of
                possible data type codes.
            edition: Can be set to a specific edition, from which data should
                later be retrieved.

        Returns:
            Iterator over objects of class :class:`~pdg.data.PdgProperty` or
            derived classes.
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

    def _get_particles_by_name(self, name: str, case_sensitive: bool=True,
                               edition: Optional[str]=None, unique: bool=True) \
            -> PdgParticle | list[PdgParticle]:
        """Helper function used by `get_particle(s)_by_name`.

        Args:
            name: Name of particle to look up.
            case_sensitive: Whether to perform a case-sensitive search.
            edition: Can be set to a specific edition.
            unique: Whether to require a unique match

        Returns:
            :class:`~pdg.particle.PdgParticle` if `unique` is `True`, otherwise
                a list thereof.

        Raises:
            :exc:`~ValueError`: If no match is found.
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If more than one
                :class:`~pdg.particle.PdgItem` exists with the given `name`, or
                if `unique` is `True` and the :class:`~pdg.particle.PdgItem`
                refers to more than one particle.
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

    def get_particle_by_name(self, name: str, case_sensitive: bool=True,
                             edition: Optional[str]=None) -> PdgParticle:
        """Get particle by its name.

        Args:
            name: Name of particle to look up.
            case_sensitive: Can be set to `False` to indicate that the particle
                name should be considered not case-sensitive.
            edition: Can be set to a specific edition, from which data should be
                retrieved.

        Returns:
            :class:`~pdg.particle.PdgParticle` object.

        Raises:
            :exc:`ValueError`: If no match is found.
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If more than one
                :class:`~pdg.particle.PdgItem` exists with the given `name`, or
                if the :class:`~pdg.particle.PdgItem` refers to more than one
                particle.
        """
        particle =  self._get_particles_by_name(name, case_sensitive=case_sensitive,
                                                edition=edition, unique=True)
        assert isinstance(particle, PdgParticle)
        return particle

    def get_particles_by_name(self, name: str, case_sensitive: bool=True,
                              edition: Optional[str]=None) -> list[PdgParticle]:
        """Get all particles for a (possibly generic) name.

        Args:
            name: Name of particle (or multiplet, etc.) to look up.
            case_sensitive: Can be set to `False` to indicate that the particle
                name should be considered not case-sensitive.
            edition: Can be set to a specific edition, from which data should
                later be retrieved.

        Returns:
            List of :class:`~pdg.particle.PdgParticle` objects.

        Raises:
            :exc:`PdgValueError`: If no match is found.
        """
        particles =  self._get_particles_by_name(name, case_sensitive=case_sensitive,
                                                 edition=edition, unique=False)
        assert not isinstance(particles, PdgParticle)
        return particles

    def get_particle_by_mcid(self, mcid: int, edition: Optional[str]=None) \
            -> PdgParticle:
        """Get particle by its MC ID.

        Args:
            mcid: Monte Carlo ID
            edition: Can be set to a specific edition, from which data should
                later be retrieved.

        Returns:
            :class:`~pdg.particle.PdgParticle` object.
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

    def get_particles(self, edition: Optional[str]=None) -> Iterator[PdgParticleList]:
        """Get iterator over all particles.

        Args:
            edition: Can be set to a specific edition, from which data should
                later be retrieved.

        Returns:
            Iterator over :class:`~pdg.particle.PdgParticleList` objects.
        """
        pdgid_table = self.db.tables['pdgid']
        pdgparticle_table = self.db.tables['pdgparticle']
        query = select(distinct(pdgid_table.c.pdgid)).join(pdgparticle_table)
        query = query.where(pdgid_table.c.data_type == 'PART')
        query = query.order_by(pdgid_table.c.sort)
        with self.engine.connect() as conn:
            for item in conn.execute(query):
                yield PdgParticleList(self, item.pdgid, edition)

    def get_canonical_name(self, name: str) -> str:
        """Get the canonical name of a particle.

        The canonical name can be used, for example, when matching decays that
        may have been encoded using different aliases for the same particle.

        Args:
            name: A particle's name (possibly an alias).

        Returns:
            The particle's canonical name, which will differ from the `name`
            argument when the latter is an alias.

        Raises:
            :exc:`ValueError`: If no match is found.
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If more than one
                :class:`~pdg.particle.PdgItem` exists with the given `name`, or
                if the :class:`~pdg.particle.PdgItem` refers to more than one
                particle.
        """
        return self.get_particle_by_name(name).name

    def doc_key_value(self, table_name: str, column_name: str, key: str) \
            -> RowMapping:
        """Get documentation on the meaning of key values or flags used in the PDG API.

        Args:
            table_name: The name of the SQLite table of interest.
            column_name: The column of interest in the table.
            key: The particle value or flag whose meaning to look up.

        Returns:
            A mapping (with string-valued keys `indicator`, `description`, and
            `comment`) describing the meaning of the value or flag.

        Raises:
            :exc:`~pdg.errors.AttributeError`: If no documentation is found.
        """
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == bindparam('table_name'))
        query = query.where(pdgdoc_table.c.column_name == bindparam('column_name'))
        query = query.where(pdgdoc_table.c.value == bindparam('value'))
        with self.engine.connect() as conn:
            try:
                row = conn.execute(query, {'table_name': table_name, 'column_name': column_name, 'value': key}).\
                    fetchone()
                assert row is not None
                return row._mapping
            except AttributeError:
                raise PdgNoDataError('No documentation for value %s in table %s.%s' % (key, table_name, column_name))

    def _doc_keys(self, table_name: str, column_name: str, as_text: bool) \
            -> str | list[RowMapping]:
        """Helper used by doc_data_type_keys etc.

        Args:
            table_name: The name of the SQLite table of interest.
            column_name: The column of interest in the table.
            as_text: Whether to return a string or a list of mappings.

        Returns:
            If `as_text` is True, a human-readable string description of the
            possible values for the column and table in question. Otherwise,
            a list of mappings, one per possible value.
        """
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == table_name)
        query = query.where(pdgdoc_table.c.column_name == column_name)
        query.order_by(pdgdoc_table.c.indicator, pdgdoc_table.c.value)

        lines: list[str] = []
        mappings: list[RowMapping] = []

        if as_text:
            lines.append('Key value     Description')
            lines.append('-'*60)

        with self.engine.connect() as conn:
            for item in conn.execute(query):
                if as_text:
                    lines.append('  %-8s    %s' % (item.value, item.description))
                else:
                    mappings.append(item._mapping)
        if as_text:
            return '\n'.join(lines)
        else:
            return mappings

    def doc_data_type_keys(self, as_text: bool=True) -> str | list[RowMapping]:
        """Get list of data type keys.

        The PDG API uses a data type key as part of the PDG Identifier metadata
        to denote the kind of information described by a given identifier. These
        data type keys can be used to select desired particle properties in
        methods such as :meth:`PdgParticle.properties
        <pdg.particle.PdgParticle.properties>`.

        Args:
            as_text: If `True`, returns the list as a formatted string suitable
                for printing. Otherwise, a list of mappings is returned, where
                each one (with string-valued keys `value`, `indicator`,
                `description`, etc.) describes a possible key value.

        Returns:
            Documentation of all possible `data_type` values for a PDG
            identifiers.
        """
        return self._doc_keys('PDGID', 'DATA_TYPE', as_text)

    def doc_item_type_keys(self, as_text: bool=True) -> str | list[RowMapping]:
        """Get list of PdgItem item_type keys.

        A :class:`pdg.particle.PdgItem` is used to represent a decay product.
        The item_type distinguishes between concrete particles, aliases for
        concrete particles, generic states (e.g. charge multiplets), unparsed
        text, etc.

        Args:
            as_text: If `True`, returns the list as a formatted string suitable
                for printing. Otherwise, a list of mappings is returned, where
                each one (with string-valued keys `value`, `indicator`,
                `description`, etc.) describes a possible key value.

        Returns:
            Documentation of all possible `item_type` values for a
            :class:`~pdg.particle.PdgItem`.
        """
        return self._doc_keys('PDGITEM', 'ITEM_TYPE', as_text)

    def doc_value_type_keys(self, as_text: bool=True) -> str | list[RowMapping]:
        """Get list of summary value type keys.

        For each summary value, the `value_type` key specifies how this value was
        derived, e.g. whether it is the result of a weighted average, of a fit,
        etc.

        Note:
            The :attr:`PdgSummaryValue.value_type
            <pdg.data.PdgSummaryValue.value_type>` property returns the
            human-readable `indicator`, not the machine-readable `value`.

        Args:
            as_text: If `True`, returns the list as a formatted string suitable
                for printing. Otherwise, a list of mappings is returned, where
                each one (with string-valued keys `value`, `indicator`,
                `description`, etc.) describes a possible key value.

        Returns:
            Documentation of all possible `value_type` values for a summary value.
        """
        pdgdoc_table = self.db.tables['pdgdoc']
        query = select(pdgdoc_table)
        query = query.where(pdgdoc_table.c.table_name == 'PDGDATA')
        query = query.where(pdgdoc_table.c.column_name == 'VALUE_TYPE')
        query.order_by(pdgdoc_table.c.indicator, pdgdoc_table.c.value)

        lines: list[str] = []
        mappings: list[RowMapping] = []

        if as_text:
            lines.append('Key value   Indicator            Description')
            lines.append('-'*60)

        with self.engine.connect() as conn:
            for item in conn.execute(query):
                if as_text:
                    lines.append('  %-8s  %-20s  %s' % (item.value, item.indicator, item.description))
                else:
                    mappings.append(item._mapping)
        if as_text:
            return '\n'.join(lines)
        else:
            return mappings
