#!/usr/bin/env python3

import csv
import json
from pathlib import Path
import requests
import sys


SOLR_QUERY = """http://localhost:8983/solr/avalon/select?fl=id,mods_tesim&fq=has_model_ssim:%22MediaObject%22&indent=on&q=*:*&rows=100000&wt=json"""


class AvalonCsvFile:
    """Class representing an Avalon-style batch CSV with extra header row"""
    def __init__(self, filepath):
        self.path = Path(filepath)
        if self.path.is_file():
            print(f"{self.path} is a file!", file=sys.stderr)
            self.read()
        else:
            print(f"{self.path} is NOT a file!", file=sys.stderr)

    def read(self):
        with open(self.path) as handle:
            self.title, self.email = handle.readline().strip().split(',')
            reader = csv.DictReader(handle.readlines())
            self.rows = [row for row in reader]


class SolrDictionary:
    """A dictionary constructed from the Solr index of the Avalon server,
    where keys are Fedora 2 PID and values are the (Avalon) id and handle"""
    def __init__(self, data):
        self.lookup = {}
        for mediaobject in data:
            id = mediaobject['id']
            for value in mediaobject['mods_tesim']:
                if value.startswith('umd:'):
                    self.lookup.get(value, []).append(id)
                     

def main():
    csvfile = AvalonCsvFile(sys.argv[1])
    print(csvfile.title)
    print(csvfile.email)
    print(len(csvfile.rows))
    
    result = requests.get(SOLR_QUERY)
    if result.status_code == 200:
        jsonresponse = result.json()
        print(len(jsonresponse['response']['docs']))


if __name__ == "__main__":
    main()
