#!/usr/bin/env python3

from pdg.errors import PdgAmbiguousValueError
from pdg.utils import get_linked_ids, get_row_data

class PdgMeasurement(object):
    """Class for an individual measurement from the PDG Listings."""

    def __init__(self, api, msmt_id):
        self.api = api
        self.id = msmt_id
        self.cache = {}

    def _get_measurement_data(self):
        return self.cache.get(
            'pdgmeasurement',
            get_row_data(self.api, 'pdgmeasurement', self.id))

    def values(self):
        """Returns a iterator of PdgValues for all of the quanities associated
           with this measurement."""
        for value_id in get_linked_ids(
                self.api,
                'pdgmeasurement_values',
                'pdgmeasurement_id',
                self.id):
            yield PdgValue(self.api, value_id)

    def get_value(self):
        """Returns the PdgValue associated with this measurement. Raises
        PdgAmbiguousValueError if there are multiple values (i.e. this is a
        multi-column measurement)."""
        vs = list(self.values())
        if len(vs) != 1:
            err = 'Multiple values associated with this measurement. ' \
                + 'Use the values() method instead.'
            raise PdgAmbiguousValueError(err)
        return vs[0]

    def footnotes(self):
        """Returns an iterator of PdgFootnotes for this measurements."""
        for foot_id in get_linked_ids(
                self.api,
                'pdgmeasurement_footnote',
                'pdgmeasurement_id',
                self.id,
                'pdgfootnote_id'):
            yield PdgFootnote(self.api, foot_id)

    @property
    def reference(self):
        """The PdgReference associated with this measurement."""
        ref_id = self._get_measurement_data()['pdgreference_id']
        return PdgReference(self.api, ref_id)

    @property
    def pdgid(self):
        """The PDG Identifier to which this measurement applies."""
        return self._get_measurement_data()['pdgid']

    @property
    def event_count(self):
        """The number of events in the sample used for this measurement."""
        return self._get_measurement_data()['event_count']

    @property
    def confidence_level(self):
        """The confidence level of this measurement."""
        return self._get_measurement_data()['confidence_level']

    @property
    def technique(self):
        """The technique used in this measurement."""
        return self._get_measurement_data()['technique']

    @property
    def charge(self):
        """Case-specific representation of the charge(s) of the particles
           involved in this measurement."""
        return self._get_measurement_data()['charge']

    @property
    def changebar(self):
        """True if this measurement has been added or updated since the previous
           PDG edition"""
        return self._get_measurement_data()['changebar']

    @property
    def comment(self):
        """Inline comment displayed with this measurement in the PDG Listings."""
        return self._get_measurement_data()['comment']


class PdgValue(object):
    """Class for an individual numerical value associated with a PdgMeasurement."""

    def __init__(self, api, value_id):
        self.api = api
        self.id = value_id
        self.cache = {}

    def _get_value_data(self):
        return self.cache.get(
            'pdgmeasurement_values',
            get_row_data(self.api, 'pdgmeasurement_values', self.id))

    @property
    def measurement(self):
        """The corresponding PdgMeasurement for this value."""
        msmt_id = self._get_value_data()['pdgmeasurement_id']
        return PdgMeasurement(self.api, msmt_id)

    @property
    def column_name(self):
        """The name of the column (in plain text format) in which this value is
           displayed in the PDG Listings."""
        return self._get_value_data()['column_name']

    @property
    def column_name_tex(self):
        """The name of the column (in TeX format) in which this value is
        displayed in the PDG Listings."""
        return self._get_value_data()['column_name_tex']

    @property
    def unit_text(self):
        """The units (in plain text format) in which this value is specified."""
        return self._get_value_data()['unit_text']

    # @property
    # def unit_tex(self):
    #     """The units (in TeX format) in which this value is specified."""
    #     return self._get_value_data()['unit_tex']

    @property
    def value_text(self):
        """Value and uncertainty (in plain text format) in units given by
           property units, including the power of ten, if applicable
           (see display_power_of_ten)"""
        return self._get_value_data()['value_text']

    # @property
    # def value_tex(self):
    #     """Value and uncertainty (in TeX format) in units given by property
    #        units, including the power of ten, if applicable (see
    #        display_power_of_ten)"""
    #     return self._get_value_data()['value_tex']

    @property
    def display_value_text(self):
        """Value and uncertainty in plain text format as displayed in
           Listings tables. Does not include any power of ten or percent sign.
           Must be combined with the display_power_of_ten property in order
           to obtain the numerical value in units given by the property units."""
        return self._get_value_data()['display_value_text']

    @property
    def display_power_of_ten(self):
        """Unit multiplier (as power of ten) as used for display in Listings."""
        return self._get_value_data()['display_power_of_ten']

    @property
    def display_in_percent(self):
        """True if value is rendered in percent for display in Listings.
           Implies that display_power_of_ten is -2."""
        return self._get_value_data()['display_in_percent']

    @property
    def is_limit(self):
        """True if value is a limit."""
        return self._get_value_data()['limit_type'] is not None

    @property
    def is_upper_limit(self):
        """True if value is an upper limit."""
        return self._get_value_data()['limit_type'] == 'U'

    @property
    def is_lower_limit(self):
        """True if value is a lower limit."""
        return self._get_value_data()['limit_type'] == 'L'

    @property
    def used_in_average(self):
        """True if value is used for calculating averages shown in
           Summary Tables."""
        return self._get_value_data()['used_in_average']

    @property
    def used_in_fit(self):
        """True if value is used for calculating best-fits shown in
           Summary Tables."""
        return self._get_value_data()['used_in_fit']

    @property
    def value(self):
        """The numerical value itself."""
        return self._get_value_data()['value']

    @property
    def error_positive(self):
        """The total positive error for this value."""
        return self._get_value_data()['error_positive']

    @property
    def error_negative(self):
        """The total negative error for this value."""
        return self._get_value_data()['error_negative']

    @property
    def stat_error_positive(self):
        """The statistical component of the positive error for this value."""
        return self._get_value_data()['stat_error_positive']

    @property
    def stat_error_negative(self):
        """The statistical component of the negative error for this value."""
        return self._get_value_data()['stat_error_negative']

    @property
    def syst_error_positive(self):
        """The systematic component of the positive error for this value."""
        return self._get_value_data()['syst_error_positive']

    @property
    def syst_error_negative(self):
        """The systematic component of the negative error for this value."""
        return self._get_value_data()['syst_error_negative']

    @property
    def error(self):
        """The total symmetric error for this value. If the positive and
           negative errors differ, accessing this property will give the average
           of the two, unless you are in pedantic mode, in which case a
           PdgAmibguousValueError will be raised."""
        is_asymm = self.error_positive != self.error_negative
        if self.api.pedantic and is_asymm:
            msg = 'In pedantic mode, PdgValue.error is ill-defined when the ' \
                + 'postive and negative errors are unequal.'
            raise PdgAmbiguousValueError(msg)
        if self.error_positive is None or self.error_negative is None:
            return None
        return 0.5*(self.error_positive + self.error_negative)

    @property
    def stat_error(self):
        """The statistical symmetric error for this value. If the positive and
           negative statistical errors differ, accessing this property will give
           the average of the two, unless you are in pedantic mode, in which case a
           PdgAmibguousValueError will be raised."""
        is_asymm = self.stat_error_positive != self.stat_error_negative
        if self.api.pedantic and is_asymm:
            msg = 'In pedantic mode, PdgValue.stat_error is ill-defined when the ' \
                + 'postive and negative statistical errors are unequal.'
            raise PdgAmbiguousValueError(msg)
        if self.stat_error_positive is None or self.stat_error_negative is None:
            return None
        return 0.5*(self.stat_error_positive + self.stat_error_negative)

    @property
    def syst_error(self):
        """The systematic symmetric error for this value. If the positive and
           negative systematic errors differ, accessing this property will give
           the average of the two, unless you are in pedantic mode, in which case a
           PdgAmibguousValueError will be raised."""
        is_asymm = self.syst_error_positive != self.syst_error_negative
        if self.api.pedantic and is_asymm:
            msg = 'In pedantic mode, PdgValue.stat_error is ill-defined when the ' \
                + 'postive and negative systematic errors are unequal.'
            raise PdgAmbiguousValueError(msg)
        if self.syst_error_positive is None or self.syst_error_negative is None:
            return None
        return 0.5*(self.syst_error_positive + self.syst_error_negative)


class PdgReference(object):
    """Class for literature references associated with PdgMeasurements."""

    def __init__(self, api, ref_id):
        self.api = api
        self.id = ref_id
        self.cache = {}

    def _get_reference_data(self):
        return self.cache.get(
            'pdgreference',
            get_row_data(self.api, 'pdgreference', self.id))

    @property
    def publication_name(self):
        """The abbreviated bibliographic name (e.g. journal initials, issue,
           page) of this publication."""
        return self._get_reference_data()['publication_name']

    @property
    def publication_year(self):
        """The year of this publication."""
        return self._get_reference_data()['publication_year']

    @property
    def title(self):
        """The title of this publication."""
        return self._get_reference_data()['title']

    @property
    def doi(self):
        """The DOI of this publication."""
        return self._get_reference_data()['doi']

    @property
    def inspire_id(self):
        """The INSPIRE identifier of this publication."""
        return self._get_reference_data()['inspire_id']

    @property
    def document_id(self):
        """The identifier for this publication in AUTHOR YEAR format."""
        return self._get_reference_data()['document_id']


class PdgFootnote(object):
    """Class for footnotes associated with PdgReferences."""

    def __init__(self, api, foot_id):
        self.api = api
        self.id = foot_id
        self.cache = {}

    def _get_footnote_data(self):
        return self.cache.get(
            'pdgfootnote',
            get_row_data(self.api, 'pdgfootnote', self.id))

    def references(self):
        """Returns an iterator of PdgReferences that refer to this footnote."""
        for ref_id in get_linked_ids(
                self.api,
                'pdgmeasurement_footnote',
                'pdgfootnote_id',
                self.id,
                'pdgmeasurement_id'):
            yield PdgMeasurement(self.api, ref_id)

    @property
    def text(self):
        """The footnote text, in plain text format."""
        return self._get_footnote_data()['text']

    # @property
    # def text_tex(self):
    #     """The footnote text, in plain text format."""
    #     return self._get_footnote_data()['text_tex']
