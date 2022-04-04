import csv
import re
import sys

PATTERN = r'^.+?/(umd_\d+)/(umd_\d+)/(.*)$'
CAMPUSFLAG = "Access is restricted to patrons at the University of Maryland."

results = {}

with open(sys.argv[1]) as handle:
    data = [row.strip() for row in handle.readlines()]

for n, path in enumerate(data, 1):
    match = re.match(PATTERN, path)
    #print(n, m, path)
    if match:
        umdm = match.group(1).replace("_", ":")
        umam = match.group(2).replace("_", ":")
        filename = match.group(3)
        path = f"{match.group(1)}/{match.group(2)}/{filename}"
        results.setdefault(umdm, []).append((filename, umam, path))

"""
for k, vals in results.items():
    print(k)
    for n, v in enumerate(sorted(vals), 1):
        print(f"  ({n}) {v}")
"""

with open(sys.argv[2]) as inputhandle, open(sys.argv[3], 'w') as outputhandle:
    reader = csv.reader(inputhandle)
    header = next(reader)
    header.extend(['Note Type', 'Note'])
    # print(len(header))
    writer = csv.writer(outputhandle)
    writer.writerow(header)
    for n, row in enumerate(reader, 1):

        # Set access note field
        if row[header.index('Terms of Use')] == CAMPUSFLAG:
            row.extend(['access', 'campus-only'])
        else:
            row.extend(['access', 'public'])
        
        # Lookup files using UMDM PID and populate columns
        for i, col in enumerate(row):
            if header[i] == "Other Identifier" and row[i].startswith('umd'):
                umdm = row[i]
            else:
                continue
        if not umdm:
            sys.exit(f"Could not locate UMDM identifier for row {n}")
        files = results[umdm]
        start = 0
        while sorted(files):
            i = header.index("File", start)
            (filename, pid, path) = files.pop(0)
            print(f"{row[i]} => {filename}")
            row[i] = path
            row[i+1] = pid
            start = i
            
            
        
        writer.writerow(row)
