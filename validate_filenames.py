#!/usr/bin/env python3

import os
import re
import sys

'''
Scans paths on STDIN and compares the filenames to standard naming conventions.
Sends paths to files with invalid filenames to STDOUT.
Optionally, echos "OK: <path>" for valid names to STDERR.
'''

PATTERN = r"(bcast|histmss|labor|litmss|lms" + \
          r"|ntl|prange|scpa|univarch)" + \
          r"-(\d{6})-(\d{4})\.[a-z0-9]{3}"


def is_valid(filename):
    match = re.match(PATTERN, filename)
    if match:
        return True
    else:
        return False


if __name__ == "__main__":
    for line in sys.stdin:
        path = line.rstrip('\n')
        filename = os.path.basename(path)
        if not is_valid(filename):
            print(path, file=sys.stdout)
        else:
            # print(f"OK: {path}", file=sys.stderr)
            pass
