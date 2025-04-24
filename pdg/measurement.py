#!/usr/bin/env python3

from pdg.errors import PdgAmbiguousValueError
from pdg.utils import get_linked_ids, get_row_data

class PdgMeasurement(object):
    def __init__(self, api, msmt_id):
        self.api = api
        self.id = msmt_id
        self.cache = {}

    def _get_measurement_data(self):
        return self.cache.get(
            'pdgmeasurement',
            get_row_data(self.api, 'pdgmeasurement', self.id))

    def values(self):
        for value_id in get_linked_ids(
                self.api,
                'pdgmeasurement_values',
                'pdgmeasurement_id',
                self.id):
            yield PdgValue(self.api, value_id)

    @property
    def reference(self):
        ref_id = self._get_measurement_data()['pdgreference_id']
        return PdgReference(self.api, ref_id)

    @property
    def pdgid(self):
        return self._get_measurement_data()['pdgid']

    @property
    def event_count(self):
        return self._get_measurement_data()['event_count']

    @property
    def confidence_level(self):
        return self._get_measurement_data()['confidence_level']

    @property
    def technique(self):
        return self._get_measurement_data()['technique']

    @property
    def charge(self):
        return self._get_measurement_data()['charge']

    @property
    def changebar(self):
        return self._get_measurement_data()['changebar']

    @property
    def inline_comment(self):
        return self._get_measurement_data()['inline_comment']

    @property
    def added_to_rpp(self):
        return self._get_measurement_data()['added_to_rpp']


class PdgValue(object):
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
        msmt_id = self._get_value_data()['pdgmeasurement_id']
        return PdgMeasurement(self.api, msmt_id)

    @property
    def value_name(self):
        return self._get_value_data()['value_name']

    @property
    def unit_text(self):
        return self._get_value_data()['unit_text']

    @property
    def unit_tex(self):
        return self._get_value_data()['unit_tex']

    @property
    def display_value_text(self):
        return self._get_value_data()['display_value_text']

    @property
    def display_power_of_ten(self):
        return self._get_value_data()['display_power_of_ten']

    @property
    def display_in_percent(self):
        return self._get_value_data()['display_in_percent']

    @property
    def limit_type(self):
        return self._get_value_data()['limit_type']

    @property
    def used_in_average(self):
        return self._get_value_data()['used_in_average']

    @property
    def used_in_fit(self):
        return self._get_value_data()['used_in_fit']

    @property
    def value(self):
        return self._get_value_data()['value']

    @property
    def error_positive(self):
        return self._get_value_data()['error_positive']

    @property
    def error_negative(self):
        return self._get_value_data()['error_negative']

    @property
    def stat_error_negative(self):
        return self._get_value_data()['stat_error_negative']

    @property
    def stat_error_positive(self):
        return self._get_value_data()['stat_error_positive']

    @property
    def syst_error_positive(self):
        return self._get_value_data()['syst_error_positive']

    @property
    def syst_error_negative(self):
        return self._get_value_data()['syst_error_negative']

    @property
    def error(self):
        is_asymm = self.error_positive != self.error_negative
        if self.api.pedantic and is_asymm:
            msg = 'Asymmetric error in pedantic mode (FIXME: better msg)'
            raise PdgAmbiguousValueError(msg)
        return 0.5*(self.error_positive + self.error_negative)

    @property
    def stat_error(self):
        is_asymm = self.stat_error_positive != self.stat_error_negative
        if self.api.pedantic and is_asymm:
            msg = 'Asymmetric stat_error in pedantic mode (FIXME: better msg)'
            raise PdgAmbiguousValueError(msg)
        return 0.5*(self.stat_error_positive + self.stat_error_negative)

    @property
    def syst_error(self):
        is_asymm = self.syst_error_positive != self.syst_error_negative
        if self.api.pedantic and is_asymm:
            msg = 'Asymmetric syst_error in pedantic mode (FIXME: better msg)'
            raise PdgAmbiguousValueError(msg)
        return 0.5*(self.syst_error_positive + self.syst_error_negative)

class PdgReference(object):
    def __init__(self, api, ref_id):
        self.api = api
        self.id = ref_id
        self.cache = {}

    def _get_reference_data(self):
        return self.cache.get(
            'pdgreference',
            get_row_data(self.api, 'pdgreference', self.id))

    def footnotes(self):
        for foot_id in get_linked_ids(
                self.api,
                'pdgmeasurement_footnote',
                'pdgmeasurement_id',
                self.id,
                'pdgfootnote_id'):
            yield PdgFootnote(self.api, foot_id)

    @property
    def publication_name(self):
        return self._get_reference_data()['publication_name']

    @property
    def publication_year(self):
        return self._get_reference_data()['publication_year']

    @property
    def title(self):
        return self._get_reference_data()['title']

    @property
    def doi(self):
        return self._get_reference_data()['doi']

    @property
    def inspire_id(self):
        return self._get_reference_data()['inspire_id']


class PdgFootnote(object):
    def __init__(self, api, foot_id):
        self.api = api
        self.id = foot_id
        self.cache = {}

    def _get_footnote_data(self):
        return self.cache.get(
            'pdgfootnote',
            get_row_data(self.api, 'pdgfootnote', self.id))

    def references(self):
        for ref_id in get_linked_ids(
                self.api,
                'pdgmeasurement_footnote',
                'pdgfootnote_id',
                self.id,
                'pdgmeasurement_id'):
            yield PdgMeasurement(self.api, ref_id)

    @property
    def text(self):
        return self._get_footnote_data()['text']

    @property
    def text_tex(self):
        return self._get_footnote_data()['text_tex']
