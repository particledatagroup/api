#!/usr/bin/env python3

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
        pass

    @property
    def technique(self):
        pass

    @property
    def charge(self):
        pass

    @property
    def changebar(self):
        pass

    @property
    def inline_comment(self):
        pass

    @property
    def when_added(self):
        pass


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
        pass

    @property
    def unit_tex(self):
        pass

    @property
    def display_power_text(self):
        pass

    @property
    def display_power_of_ten(self):
        pass

    @property
    def display_in_percent(self):
        pass

    @property
    def limit_type(self):
        pass

    @property
    def used_in_average(self):
        pass

    @property
    def used_in_fit(self):
        pass

    @property
    def value(self):
        pass

    @property
    def error_positive(self):
        pass

    @property
    def error_negative(self):
        pass

    @property
    def stat_error_negative(self):
        pass

    @property
    def stat_error_positive(self):
        pass

    @property
    def syst_error_positive(self):
        pass

    @property
    def syst_error_negative(self):
        pass


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
        pass

    @property
    def publication_year(self):
        pass

    @property
    def title(self):
        pass

    @property
    def doi(self):
        pass

    @property
    def inspire_id(self):
        pass


class PdgFootnote(object):
    def __init__(self, api, foot_id):
        self.api = api
        self.id = foot_id
        self.cache = {}

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
        pass

    @property
    def text_tex(self):
        pass
