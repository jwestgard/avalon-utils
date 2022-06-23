#!/usr/bin/env python3

import csv
import json
from pathlib import Path
import requests
import sys


SOLR_QUERY = """http://localhost:8983/solr/avalon/select?fl=*&fq=has_model_ssim:%22MediaObject%22&indent=on&q=*:*&rows=100000&wt=json"""


class BatchCsv:
    """Class representing an Avalon-style batch CSV with extra header row"""
    def __init__(self, filepath):
        self.path = Path(filepath)
        self.filename = self.path.name
        self.basename = self.path.stem
        self.ext = self.path.suffix
        if self.path.is_file():
            self.read()
        else:
            self.rows = []

    def read(self):
        with open(self.path) as handle:
            self.title, self.email = handle.readline().strip().split(',')
            self.fieldnames = handle.readline().strip().split(',')
            reader = csv.reader(handle.readlines())
            self.rows = [list(zip(self.fieldnames, row)) for row in reader]

    def is_file(self):
        return self.path.is_file()


class AvalonMediaObject:
    """A python object with attributes corresponding to the fields in the Solr
    document representing an Avalon media object"""
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
            #print(key, value)

        pidlist = [i for i in self.mods_tesim if i.startswith('umd:')]
        if len(pidlist) == 0:
            self.pid = ""
        elif len(pidlist) == 1:
            self.pid = pidlist[0]
        else:
            sys.exit(f"ERROR: Unexpected multi-pid object!: {pidlist}")

        handlelist = [i for i in self.mods_tesim if i.startswith('hdl:')]
        if len(handlelist) == 0:
            self.handle = ""
        elif len(handlelist) == 1:
            self.handle = handlelist[0]
        else:
            sys.exit(f"ERROR: Unexpected multi-handle object!: {handlelist}")

        self.url = "https://av.lib.umd.edu/media_objects/" + self.id
        if hasattr(self, 'section_id_ssim'):
            self.num_parts = len(self.section_id_ssim)
        else:
            self.num_parts = 0

    def is_private(self):
        return "Access condition: campus-only." in self.mods_tesim 


def main():

    print(f"\n {'*' * 34}")
    print(f" | Avalon Batch Verification Tool |")
    print(f" {'*' * 34}\n")
    
    """ Query Solr and create index of Media Objects that can be looked up by PID """
    av_index = {}

    print("   Querying Solr index and creating Media Object lookup dictionary...")
    result = requests.get(SOLR_QUERY)

    if result.status_code == 200:
        jsonresponse = result.json()
    else:
        sys.exit(f" => Could not get Solr data!")

    docs = jsonresponse['response']['docs']
    print(f"\n  Solr records: {len(docs)}")
    for item in docs:
        obj = AvalonMediaObject(item)
        if obj.pid != "":
            av_index.setdefault(obj.pid, []).append(obj)
        else:
            continue

    print(f"   Unique PIDs: {len(av_index)}")
    print(f"\n   {'=' * 80}\n")

    """ Process each input CSV, writing results to cleanup CSV files """
    outputdir = sys.argv[1]
    missingmedia_file = Path(outputdir) / "missingmedia.csv"
    duplicates_file = Path(outputdir) / "duplicates.csv"
    if missingmedia_file.exists():
        missingmedia = open(missingmedia_file, 'a')
    else:
        missingmedia = open(missingmedia_file, 'w')

    if duplicates_file.exists():
        duplicates = open(duplicates_file, 'a')
    else:
        duplicates = open(duplicates_file, 'w')

    total_objects_count = 0
    public_objects_count = 0
    campus_objects_count = 0
    expected_files_count = 0
    loaded_files_count = 0

    for n, inputfile in enumerate(sys.argv[2:], 1):
        inputcsv = BatchCsv(inputfile)
        print(f"   File #{n}: {inputcsv.filename}\n")
        print(f"    Input filename: {inputcsv.filename}")
        print(f"    Input basename: {inputcsv.basename}")
        print(f"   Input extension: {inputcsv.ext}")
        print(f"          Is file?: {inputcsv.is_file()}")
        print(f"             Title: '{inputcsv.title}'")
        print(f"             Email: '{inputcsv.email}'")
        print(f"          Num Rows: {len(inputcsv.rows)}\n")

        reloads = []

        for rownum, row in enumerate(inputcsv.rows, 1):
            #print(row)
            total_objects_count += 1
            for colnum, (label, value) in enumerate(row):
                if label == "File" and value != "":
                    expected_files_count += 1
                if value == "fedora2":
                    pid = row[colnum + 1][1]
                if value == "access":
                    if row[colnum + 1][1] == "Access condition: campus-only.":
                        access_rule = "campus"
                        campus_objects_count += 1
                    elif row[colnum + 1][1] == "Access condition: public.":
                        access_rule = "public"
                        public_objects_count += 1
                    else:
                        access_rule = None


            if pid and pid in av_index:
                mediaobjects = av_index[pid]
            else:
                mediaobjects = []

            num_matches = len(mediaobjects)
            urls = ";".join([f"{i.url} ({i.num_parts})" for i in mediaobjects])
            print(f"{rownum:6}. {pid} ({access_rule}) => {num_matches} {urls}")

            # add the number of files on the first matching media object, ignoring dupes
            if num_matches > 0:
                loaded_files_count += mediaobjects[0].num_parts

            # add records to the duplicates and missing media containers
            if num_matches > 1:
                duplicates.write(f"{pid},{','.join([i.url for i in mediaobjects])}\n")
            elif num_matches == 1 and mediaobjects[0].num_parts == 0:
                missingmedia.write(f"{pid},{','.join([i.url for i in mediaobjects])}\n")
            elif num_matches == 0:
                reloads.append([value for (column, value) in row])

        if reloads:
            reloadcsv = Path(outputdir) / f"{inputcsv.basename}.reload.csv"
            reloadwriter = csv.writer(open(reloadcsv, 'w'))
            reloadwriter.writerow([inputcsv.title + ' RELOAD', inputcsv.email])
            reloadwriter.writerow(inputcsv.fieldnames)
            for row in reloads:
                reloadwriter.writerow(row)

        print(f"\n   {'=' * 80}\n")

    print(f"    Batch Summary")
    print(f"    -------------")
    print(f"         Public count: {public_objects_count:4}")
    print(f"    Campus-only count: {campus_objects_count:4}")
    print(f"        Objects count: {total_objects_count:4}")
    print(f" Expected Files count: {expected_files_count:4}")
    print(f"   Loaded Files count: {loaded_files_count:4}\n")

if __name__ == "__main__":
    main()
