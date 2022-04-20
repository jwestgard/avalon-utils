#!/usr/bin/env python3

import sys
from csv import DictReader
from os import rename
from pathlib import Path
from typing import Optional, Union

import click
from click import Context, Parameter


class PathExtPair(click.ParamType):
    name = 'path=.extension'

    def convert(self, value: Union[str, tuple], param: Optional[Parameter], ctx: Optional[Context]) -> tuple:
        if isinstance(value, tuple):
            return value
        dir_name, ext = value.split('=', 1)
        return Path(dir_name), ext


@click.command
@click.option('-D', '--directory', 'directories', type=PathExtPair(), multiple=True)
def rename_files(directories):
    reader = DictReader(sys.stdin)

    for row in reader:
        old_name_base = row['old_name_base']
        new_name_base = row['new_name_base']
        if old_name_base and new_name_base:
            for directory, extension in directories:
                old_file = Path(directory) / (old_name_base + extension)
                new_file = Path(directory) / (new_name_base + extension)
                print(old_file, new_file)
                if old_file.is_file():
                    rename(old_file, new_file)
            print()


if __name__ == '__main__':
    rename_files()
