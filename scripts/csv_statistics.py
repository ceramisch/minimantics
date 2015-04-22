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
from lib import statistics, csv

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Output `NLines ArithAvg SampleStdDev` for a given CSV column.""")
parser.add_argument("-d", "--discriminate-by", nargs="*", default=[],
        help="""Separate data by given columns (default: don't discriminate).
        REQUIRES INPUT TO BE SORTED ON THESE COLUMNS.""")
parser.add_argument("-g", "--print-global", action='store_true',
        help="""Print global statistics after the last line.
        These are calculated as averages of each ArithAvg above.""")
parser.add_argument("column_name", type=unicode, default="cosine",
        help="""The column name from which to take the average.""")


class StatsPrinter(csv.CSVHandler):
    def __init__(self, args):
        self.args = args
        self.current_discriminant = None
        self.stats = None
        self.global_stats = statistics.Statistics()
        fields = self.args.discriminate_by \
                + ["NLines", "ArithAvg", "SampleStdDev"]
        print(*fields, sep="\t")

    def handle_header(self, line, header_data):
        columns = set(header_data)
        assert all(d in columns for d in self.args.discriminate_by), \
                (columns, self.args.discriminate_by)
        assert self.args.column_name in columns, \
                (columns, self.args.column_name)

    def handle_data(self, line, data_tuple):
        discriminant = tuple(getattr(data_tuple, col_name)
                for col_name in self.args.discriminate_by)
        if discriminant != self.current_discriminant:
            self.print_stats()
            self.current_discriminant = discriminant
            self.stats = statistics.Statistics()
        self.stats.add(float(getattr(data_tuple, self.args.column_name)))

    def end(self):
        self.print_stats()
        if self.args.print_global:
            print("GLOBAL:", self.global_stats.n, self.global_stats.avg,
                    self.global_stats.stddev_sample)

    def print_stats(self):
        if self.stats is not None:
            fields = self.current_discriminant + (self.stats.n,
                    self.stats.avg, self.stats.stddev_sample)
            self.global_stats.add(self.stats.avg)
            print(*fields, sep="\t")



#####################################################

if __name__ == "__main__":
    csv.parse_csv(StatsPrinter(parser.parse_args()))
