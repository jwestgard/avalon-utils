#!/usr/bin/env python3

import csv
import os
import re
import sys
import yaml
from collections import defaultdict


results = defaultdict(list)


config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path) as config_file:
    config = yaml.safe_load(config_file)


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
    print(f" Updating row {n}, col {i}: {row[i]} => {path}", file=sys.stderr)
    row[i] = path
    row[i+1] = os.path.splitext(os.path.basename(path))[0]
    return i + 1


def add_file_paths():
    try:
        with open(sys.argv[1]) as input_file:
            data = [row.strip() for row in input_file.readlines()]
    except IndexError:
        print(
            'Usage: add_file_paths.py <file_list.txt>\n'
            '\n'
            'Reads the input CSV from STDIN and writes the output CSV to STDOUT\n',
            file=sys.stderr
        )
        sys.exit()

    for n, path in enumerate(data, 1):
        path_prefix = config.get('binaries_location', '')
        pattern = r'{}'.format(config.get('path_pattern'))
        match = re.match(pattern, path)
        if match:
            umdm = match.group(1).replace("_", ":")
            umam = match.group(2).replace("_", ":")
            filename = match.group(3)
            path = f'{path_prefix}/{match.group(1)}/{match.group(2)}/{filename}'
            results[umdm].append((filename, umam, path))

    # read the input CSV from STDIN
    reader = csv.reader(sys.stdin)
    header = next(reader)
    header.extend(['Note Type', 'Note', 'Offset'])
    other_identifier_columns = [
        i for i, h in enumerate(header) if h == 'Other Identifier'
        ]
    identifier_patterns = [(i['pattern'], i['label']) for i in config.get('id_mappings')]

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
        print(f"\nProcessing row {n} ({umdm}) ...", file=sys.stderr)
        if not umdm:
            sys.exit(f"Could not locate UMDM identifier for row {n}")
        files = results[umdm]
        files.sort()

        # Update all the "Other Identifiers" using regular expression matching
        for column in other_identifier_columns:
            id = row[column]
            for pattern, label in identifier_patterns:
                #print(pattern, label, id)
                if re.match(pattern, id):
                    row[column - 1] = label
                    # print(f"  Match! '{id}' is a {label} ID", file=sys.stderr)


        start = 0
        for filename, pid, path in files:
            start = insert_next_file(header, row, n, start, pid, path)

        all_filenames = [filename[:-4] for (filename, pid, path) in files]
        print(f" All Files: {all_filenames}", file=sys.stderr)

        writer.writerow(row)


if __name__ == '__main__':
    add_file_paths()
