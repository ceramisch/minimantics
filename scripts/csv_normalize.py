#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import argparse
import codecs
import math
import os
import sys
from nltk.corpus import wordnet as wn
from lib import csv

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Output CSV input columns normalized for each target.
        REQUIRES INPUT TO BE GROUPED BY `target` COLUMN.
        """)
parser.add_argument("-c", "--column-names", nargs="*", default=None,
        help="""Normalize given columns (default: all columns).""")


class NormalizingPrinter(csv.CSVHandler):
    def __init__(self, args):
        self.args = args
        self.header_names = None
        self.header_chosen = None
        self.current_target = None
        self.current_group = []


    def handle_header(self, line, header_names):
        self.header_names = header_names
        print(*self.header_names, sep="\t")

        if self.args.column_names is None:
            self.args.column_names = header_names

        chosen = self.args.column_names
        set_header_names = set(header_names)
        assert all(c in set_header_names for c in chosen)

        set_chosen = set(chosen)
        self.header_chosen = [name in chosen for name in self.header_names]


    def handle_data(self, line, data_namedtuple):
        if data_namedtuple.target != self.current_target:
            self.flush_current_group()
            self.current_target = data_namedtuple.target
        self.current_group.append(data_namedtuple)


    def end(self):
        self.flush_current_group()


    def flush_current_group(self):
        r"""Take average of all elements in self.current_group."""
        sum_squares = [0] * len(self.header_names)
        for data_namedtuple in self.current_group:
            for i, elem in enumerate(data_namedtuple):
                try:
                    sum_squares[i] += float(elem)**2
                except ValueError:
                    pass  # Value cannot be converted to float

        denominators = [math.sqrt(s) for s in sum_squares]
        for data_namedtuple in self.current_group:
            print(*[self.divide(i, value, denom) for (i, (value, denom))
                    in enumerate(zip(data_namedtuple, denominators))], sep="\t")

        self.current_group[:] = []


    def divide(self, index, stringvalue, denominator):
        r"""Return float(stringvalue)/denominator."""
        if not self.header_chosen[index]:
            return stringvalue
        try:
            return float(stringvalue) / denominator
        except ValueError:
            return stringvalue


#####################################################

if __name__ == "__main__":
    csv.parse_csv(NormalizingPrinter(parser.parse_args()))
