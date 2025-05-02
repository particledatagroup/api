#!/usr/bin/env python3

from itertools import chain
import sys

from tabulate import tabulate

import pdg
from pdg.api import PdgApi
from pdg.measurement import PdgReference, PdgValue


def dictify_value(v: PdgValue):
    return {
        'PWR_OF_TEN': f'10^{v.display_power_of_ten}',
        'VALUE': f'{v.value} ± {v.error}',
        'VALUE_TEXT': v.display_value_text,
        'EVTS': v.measurement.event_count,
        'DOCUMENT ID': v.measurement.reference.document_id,
        'TECN': v.measurement.technique,
        'COMMENT': v.measurement.inline_comment,
    }


def dictify_reference(ref: PdgReference):
    return {
        'ID': ref.document_id,
        'PUBLICATION': ref.publication_name,
        'TITLE': ref.title,
    }


def print_datablock(api: PdgApi, pdgid: str):
    node = api.get(pdgid)

    print(node.description)
    print()

    for sv in node.summary_values():
        print(f'{sv.value_type}: {sv.value} ± {sv.error}')
        print(f'{sv.display_value_text}')
        print()
    print()

    values = chain.from_iterable(m.values() for m in node.get_measurements())
    values = list(values)

    vals1 = [v for v in values if v.used_in_fit]
    assert all(v.used_in_average for v in vals1)
    vals1 = [dictify_value(v) for v in vals1]

    vals2 = [v for v in values if v.used_in_average and not v.used_in_fit]
    vals2 = [dictify_value(v) for v in vals2]

    vals3 = [v for v in values if not (v.used_in_average or v.used_in_fit)]
    vals3 = [dictify_value(v) for v in vals3]

    print('USED IN FITS AND AVERAGES')
    print('-------------------------')
    print(tabulate(vals1, headers='keys'))

    if vals2:
        print()
        print('USED IN AVERAGES BUT NOT FITS')
        print('-----------------------------')
        print(tabulate(vals2, headers='keys'))

    if vals3:
        print()
        print('NOT USED IN FITS OR AVERAGES')
        print('----------------------------')
        print(tabulate(vals3, headers='keys'))

    print()
    print('REFERENCES')
    print('==========')

    refs = [m.reference for m in node.get_measurements()]
    refs = [dictify_reference(r) for r in refs]
    print(tabulate(refs, headers='keys'))


if __name__ == '__main__':
    pdgid = sys.argv[1]
    api = pdg.connect()
    print_datablock(api, pdgid)
