#!/usr/bin/env python3

import csv
import os
import re
import sys
import yaml
from collections import defaultdict


results = defaultdict(list)


with open('config.yaml') as handle:
    config = yaml.safe_load(handle)


def find_umdm(other_identifier_columns, row):
    for i in other_identifier_columns:
        if row[i].startswith('umd'):
            return row[i]


def insert_next_file(header, row, n, start, pid, path):
    """
    Find the next column with a "File" header that occurs after the column
    numbered start. Add the path and pid to the appropriate columns of the row,
    and return the column number of the "File" column just updated.
    """
    i = header.index("File", start)
    print(f"Updating row {n}, col {i}: {row[i]} => {path}", file=sys.stderr)
    row[i] = path
    row[i+1] = os.path.basename(path)
    return i + 1


def add_file_paths():
    try:
        with open(sys.argv[1]) as handle:
            data = [row.strip() for row in handle.readlines()]
    except IndexError:
        print(
            'Usage: add_file_paths.py <file_list.txt>\n'
            '\n'
            'Reads the input CSV from STDIN and writes the output CSV to STDOUT\n',
            file=sys.stderr
        )
        sys.exit()

    for n, path in enumerate(data, 1):
        pattern = r'{}'.format(config.get('path_pattern'))
        match = re.match(pattern, path)
        if match:
            umdm = match.group(1).replace("_", ":")
            umam = match.group(2).replace("_", ":")
            filename = match.group(3)
            path = f'{match.group(1)}/{match.group(2)}/{filename}'
            results[umdm].append((filename, umam, path))

    # read the input CSV from STDIN
    reader = csv.reader(sys.stdin)
    header = next(reader)
    header.extend(['Note Type', 'Note', 'Offset'])
    other_identifier_columns = [
        i for i, h in enumerate(header) if h == 'Other Identifier'
        ]

    # write the output CSV to STDOUT
    writer = csv.writer(sys.stdout)
    writer.writerow(header)
    # process each row, enumerating from 2 to account for the header row
    for n, row in enumerate(reader, 2):

        # Set access note field
        if row[header.index('Terms of Use')] == config.get('campus_flag'):
            row.extend(['access', config.get('access_campus')])
        else:
            row.extend(['access', config.get('access_public')])

        # If offset found in config, set it, otherwise leave blank
        if 'offset' in config:
            row.append(config.get('offset'))
        else:
            row.append('')

        # Lookup files using UMDM PID and populate columns
        umdm = find_umdm(other_identifier_columns, row)
        if not umdm:
            sys.exit(f"Could not locate UMDM identifier for row {n}")
        files = results[umdm]
        files.sort()

        # Update PID identifier type
        row[2] = 'fedora'

        # Update filename identifier
        if row[6] == 'local':
            row[6] = 'filename'
        elif row[6] == '' and len(files) > 0:
            row[6] = 'filename'
            row[7] = os.path.splitext(files[0][0])[0]

        start = 0
        for filename, pid, path in files:
            start = insert_next_file(header, row, n, start, pid, path)

        writer.writerow(row)


if __name__ == '__main__':
    add_file_paths()
