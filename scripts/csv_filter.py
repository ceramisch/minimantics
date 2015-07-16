#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import argparse
import collections
import codecs
import math
import os
import sys

from lib import csv

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Keep only the lines whole column has a valid value.
        A file listing the valid values is required.
        """)
parser.add_argument("--values", type=argparse.FileType("r"),
        help="""File with a list of valid values.""")
parser.add_argument("column_name", type=unicode,
        help="""Name of the column whose values will be filtered.""")
parser.add_argument("input_file", type=argparse.FileType("r"),
        help="""File whose elements should be added.""")


############################################################

class DataCollector(csv.CSVHandler):
    def __init__(self, args, valid_values):
        self.args = args
        self.valid_values = valid_values


    def handle_header(self, line, header_names):
        if not self.args.column_name in header_names:
            print("ERROR: Header does not specify column " \
                    "{}".format(self.args.column_name), file=sys.stderr)
        print(line)


    def handle_data(self, line, data_namedtuple):
        r"""Add data_namedtuple to `self.data`. Note that multiple namedtuple
        classes may have been produced (with different arity and argument
        name/order). They are all required to have `target` and `context`, though.
        """
        value = getattr(data_namedtuple, self.args.column_name)
        if value in self.valid_values:
            print("\t".join(data_namedtuple))


############################################################

def main():
    args = parser.parse_args()
    valid_values = args.values.read().decode('utf8').strip().split("\n")

    data_parser = csv.parse_csv
    collector = data_parser(DataCollector(args, valid_values),
            input_file=args.input_file)


#####################################################

if __name__ == "__main__":
    main()
