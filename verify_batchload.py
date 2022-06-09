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
        self.basename = self.path.name
        if self.path.is_file():
            self.read()
        else:
            self.rows = []

    def read(self):
        with open(self.path) as handle:
            self.title, self.email = handle.readline().strip().split(',')
            fieldnames = handle.readline().strip().split(',')
            reader = csv.reader(handle.readlines())
            self.rows = [list(zip(fieldnames, row)) for row in reader]

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
        

def main():

    av_index = {}
    inputcsv = BatchCsv(sys.argv[1])

    print(f"\n {'*' * 34}")
    print(f" | Avalon Batch Verification Tool |")
    print(f" {'*' * 34}\n")
    print(f"Input CSV: {inputcsv.basename}")
    print(f" Is file?: {inputcsv.is_file()}")
    print(f"    Title: '{inputcsv.title}'")
    print(f"    Email: '{inputcsv.email}'")
    print(f" Num Rows: {len(inputcsv.rows)}")    

    result = requests.get(SOLR_QUERY)
    if result.status_code == 200:
        jsonresponse = result.json()
    else:
        sys.exit(f"Could not get Solr data")

    docs = jsonresponse['response']['docs']
    print(f"Solr recs: {len(docs)}")
    for item in docs:
        obj = AvalonMediaObject(item)
        if obj.pid != "":
            av_index.setdefault(obj.pid, []).append(obj)
        else:
            continue
    print(f" Num PIDs: {len(av_index)}\n")

    print(f"Analyzing CSV Data...")
    for rownum, row in enumerate(inputcsv.rows, 1):
        for colnum, (label, value) in enumerate(row):
            if value == "fedora2":
                pid = row[colnum + 1][1]
        if pid and pid in av_index:
            mediaobjects = av_index[pid]
        else:
            mediaobjects = []
        num_matches = len(mediaobjects)
        urls = ";".join([f"{i.url} ({i.num_parts})" for i in mediaobjects])
        print(f"{rownum:4}. {pid} => {num_matches} {urls}")


if __name__ == "__main__":
    main()
