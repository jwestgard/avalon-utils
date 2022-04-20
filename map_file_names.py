#!/usr/bin/env python3

import sys
from collections import defaultdict, namedtuple
from csv import DictReader, DictWriter
from os.path import splitext
from pathlib import Path


File = namedtuple('File', ('pid', 'old_name'))


def pid_to_path(pid: str):
    return Path(pid.replace(':', '_'))


try:
    autonumber_base = int(sys.argv[1])
except IndexError:
    autonumber_base = 1

pid_to_autonumber = {}
file_index = defaultdict(list)
reader = DictReader(sys.stdin)
writer = DictWriter(sys.stdout, fieldnames=['umdm', 'umam', 'old_name_base', 'new_name_base'])
writer.writeheader()

for n, row in enumerate(reader):
    old_name_base, _ = splitext(row['streaming_master'])
    umdm = row['umdm']
    umam = row['umam']

    if umdm not in pid_to_autonumber:
        pid_to_autonumber[umdm] = autonumber_base + n

    file_index[umdm].append(umam)
    number = pid_to_autonumber[umdm]
    index = len(file_index[umdm])
    new_name_base = pid_to_path(umdm) / pid_to_path(umam) / f'lms-{number:06d}-{index:04d}'
    writer.writerow({
        'umdm': umdm,
        'umam': umam,
        'old_name_base': old_name_base,
        'new_name_base': new_name_base
    })
