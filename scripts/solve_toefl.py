#! /usr/bin/env python

# minimantics: minimalist tool for count-based distributional semantic models
#
#    Copyright (C) 2015  Carlos Ramisch, Silvio Ricardo Cordeiro
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. 

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import argparse
import codecs
import os
import sys
from nltk.corpus import wordnet as wn
from lib import csv

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Solve a TOEFL problem file in <stdin> by using a CSV
        `thesaurus_file`, looking at `column_name` to see the
        similarity between `target` and `neighbor` (higher
        numbers mean "more similar").

        The <thesaurus_file> must have many lines with the following
        syntax: "word syn0 syn1 syn2 syn3", where only syn0 is actually
        a valid synonym. This script evaluates the likelihood
        of each proposed synonym.
        """)
parser.add_argument("-a", "--out-all-stats", action="store_true",
        help="""Output statistics regarding the prediction of syn0.""")
parser.add_argument("-s", "--out-similarity", action="store_true",
        help="""Output path_similarity for each synK.""")
parser.add_argument("-d", "--default", default="?",
        help="""Value to be printed when entry is not found.""")
parser.add_argument("thesaurus_file", type=argparse.FileType('r'),
        help="""The file to be loaded as thesaurus.""")
parser.add_argument("column_name", type=unicode,
        help="""Name of the column whose values indicate word distances.""")


class Main(object):
    def __init__(self, args):
        self.args = args
        self.n_lines = 0
        self.n_correct = 0
        self.n_empty = 0

    def run(self):
        self.thesaurus = csv.parse_csv(
                Thesaurus(self.args.column_name),
                self.args.thesaurus_file)
        for line_num, line in enumerate(sys.stdin):
            line = line[:-1]  # Strip off '\n'
            self.treat_line(line, line_num)
        if self.args.out_all_stats:
            print("Accuracy: {:2.2f}%".format(100 * self.n_correct/self.n_lines))
            print("Empty: {:2.2f}%".format(100 * self.n_empty/self.n_lines))

    def treat_line(self, line, line_num):
        r"""Called for each line "word syn0 syn1 syn2 syn3"."""
        data = line.split(" ")
        word, syns = data[0], data[1:]
        similarities = [self.thesaurus[(word, s)] for s in syns]
        if self.args.out_similarity:
            print(self.args.column_name, "(line ", line_num+1, "):\t",
                    "\t".join("{:.4f}".format(s) if s is not None else
                        self.args.default for s in similarities), sep="")

        self.n_lines += 1
        # (We penalize sim0 for being as good as another one)
        if all(similarities[0] > s for s in similarities[1:]):
            self.n_correct += 1  # syn0 was better
        self.n_empty += (similarities[0] is None)


class Thesaurus(csv.CSVHandler):
    def __init__(self, column_name):
        self.column_name = column_name
        self.mapping = {}

    def handle_data(self, line, data_namedtuple):
        self.mapping[(data_namedtuple.target, data_namedtuple.neighbor)] \
                = float(getattr(data_namedtuple, self.column_name))

    def __getitem__(self, target_and_neighbor):
        return self.mapping.get(target_and_neighbor, None)



#####################################################

if __name__ == "__main__":
    Main(parser.parse_args()).run()
