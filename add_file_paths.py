#!/usr/bin/env python3

import csv
import re
import sys
from collections import defaultdict


PATTERN = r'^.+?/(umd_\d+)/(umd_\d+)/(.*)$'
CAMPUSFLAG = "Access is restricted to patrons at the University of Maryland."

results = defaultdict(list)


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
    row[i+1] = pid
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
        match = re.match(PATTERN, path)
        if match:
            umdm = match.group(1).replace("_", ":")
            umam = match.group(2).replace("_", ":")
            filename = match.group(3)
            path = f"{match.group(1)}/{match.group(2)}/{filename}"
            results[umdm].append((filename, umam, path))

    # read the input CSV from STDIN
    reader = csv.reader(sys.stdin)
    header = next(reader)
    header.extend(['Note Type', 'Note'])
    other_identifier_columns = [i for i, h in enumerate(header) if h == 'Other Identifier']

    # write the output CSV to STDOUT
    writer = csv.writer(sys.stdout)
    writer.writerow(header)
    # process each row, enumerating from 2 to account for the header row
    for n, row in enumerate(reader, 2):

        # Set access note field
        if row[header.index('Terms of Use')] == CAMPUSFLAG:
            row.extend(['access', 'campus-only'])
        else:
            row.extend(['access', 'public'])

        # Lookup files using UMDM PID and populate columns
        umdm = find_umdm(other_identifier_columns, row)
        if not umdm:
            sys.exit(f"Could not locate UMDM identifier for row {n}")
        files = results[umdm]
        files.sort()
        start = 0
        for filename, pid, path in files:
            start = insert_next_file(header, row, n, start, pid, path)

        writer.writerow(row)


if __name__ == '__main__':
    add_file_paths()
