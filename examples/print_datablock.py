#!/usr/bin/env python3

from itertools import chain
import sys

import pdg
from pdg.api import PdgApi
from pdg.measurement import PdgReference, PdgValue


def print_value(v: PdgValue):
    print(f'VALUE (10^{v.display_power_of_ten}): {v.value} ± {v.error}')
    print(f'VALUE_TEXT: {v.display_value_text}')
    print(f'EVTS: {v.measurement.event_count}')
    print(f'DOCUMENT ID: {v.measurement.reference.document_id}')
    print(f'TECN: {v.measurement.technique}')
    print(f'COMMENT: {v.measurement.inline_comment}')
    print()


def print_reference(ref: PdgReference):
    print(f'ID: {ref.document_id}')
    print(f'PUBLICATION: {ref.publication_name}')
    print(f'TITLE: {ref.title}')
    print()


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

    vals2 = [v for v in values if v.used_in_average and not v.used_in_fit]

    vals3 = [v for v in values if not (v.used_in_average or v.used_in_fit)]

    print('USED IN FITS AND AVERAGES')
    print('-------------------------')
    for v in vals1:
        print_value(v)

    if vals2:
        print()
        print('USED IN AVERAGES BUT NOT FITS')
        print('-----------------------------')
        for v in vals2:
            print_value(v)

    if vals3:
        print()
        print('NOT USED IN FITS OR AVERAGES')
        print('----------------------------')
        for v in vals3:
            print_value(v)

    print('REFERENCES')
    print('==========')

    refs = [m.reference for m in node.get_measurements()]
    for ref in refs:
        print_reference(ref)


if __name__ == '__main__':
    pdgid = sys.argv[1]
    api = pdg.connect()
    print_datablock(api, pdgid)
