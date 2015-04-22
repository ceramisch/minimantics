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

from nltk.corpus import wordnet as wn
from lib import csv

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Given two CSV files, add up their columns and output the result.
        Entries are discriminated by the `target` and `context` columns.""")
parser.add_argument("-c", "--column-names", nargs="*", default=None,
        help="""Normalize given columns (default: all columns whose name does
        not start with "id_").""")
parser.add_argument("input_files", nargs="+", type=argparse.FileType("r"),
        help="""Files whose elements should be added""")


class DataCollector(csv.CSVHandler):
    def __init__(self, column_names):
        self.data = collections.OrderedDict()
        self.add_operation = lambda x, y: x+y
        self.list_header_names = []
        self.set_header_names = set()
        self.column_names = column_names


    def handle_header(self, line, header_names):
        assert "target" in header_names, header_names
        assert "context" in header_names, header_names
        more = (h for h in header_names if h not in self.set_header_names)
        self.list_header_names.extend(more)
        self.set_header_names.update(more)


    def handle_data(self, line, data_namedtuple):
        r"""Add data_namedtuple to `self.data`. Note that multiple namedtuple
        classes may have been produced (with different arity and argument
        name/order). All are required to have `target` and `context`, though.
        """
        t, n = data_namedtuple.target, data_namedtuple.context
        self.data.setdefault(t, collections.OrderedDict()) \
                .setdefault(n, list()).append(data_namedtuple)


    def print_merged(self):
        r"""Merge duplicated values (adding them together) and print them."""
        print(*self.list_header_names, sep="\t")

        for target, data_pertarget in self.data.iteritems():
            for context, data_percontext in data_pertarget.iteritems():
                print(*[self.merge(field, data_percontext)
                        for field in self.list_header_names], sep="\t")


    def merge(self, field, data_namedtuples):
        r"""Merge values of `data_namedtuple.FIELDNAME`."""
        sum_value = None
        for data_namedtuple in data_namedtuples:
            value = getattr(data_namedtuple, field, "?")

            if sum_value is None:
                sum_value = value
                # If we have an `id_` field, we don't want to sum it
                if field.startswith("id_"):
                    return sum_value
            else:
                try:
                    sum_value = self.add_operation(float(sum_value), float(value))
                except ValueError:  # Bad conversion
                    pass  # Just keep first value in there

        return sum_value



def main():
    args = parser.parse_args()
    collector = DataCollector(args.column_names)
    for input_file in args.input_files:
        csv.parse_csv(collector, input_file=input_file)
    collector.print_merged()


#####################################################

if __name__ == "__main__":
    main()
