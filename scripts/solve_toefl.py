#! /usr/bin/env python

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
        `thesaurus_file`, looking at `column_name`.

        The <thesaurus_file> must have many lines with the following
        syntax: "word syn0 syn1 syn2 syn3", where only syn0 is actually
        a valid synonym. This script evaluates the likelihood
        of each proposed synonym.
        """)
parser.add_argument("-a", "--out-accuracy", action="store_true",
        help="""Output accuracy of predicting syn0.""")
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

    def run(self):
        self.thesaurus = csv.parse_csv(
                Thesaurus(self.args.column_name),
                self.args.thesaurus_file)
        for line_num, line in enumerate(sys.stdin):
            line = line[:-1]  # Strip off '\n'
            self.treat_line(line, line_num)
        if self.args.out_accuracy:
            print("Accuracy: {:2.2f}%".format(100 * self.n_correct/self.n_lines))

    def treat_line(self, line, line_num):
        r"""Called for each line "word syn1 syn2 syn3 syn4"."""
        data = line.split(" ")
        word, syns = data[0], data[1:]
        similarities = [self.thesaurus[(word, s)] for s in syns]
        if self.args.out_similarity:
            print(self.args.column_name, "(line ", line_num+1, "):\t",
                    "\t".join("{:.4f}".format(s) if s is not None else
                        self.args.default for s in similarities), sep="")

        self.n_lines += 1
        # (We reverse it to penalize sim0 for being as good as another one)
        if all(similarities[0] > s for s in similarities[1:]):
            self.n_correct += 1  # got syn0


class Thesaurus(csv.CSVHandler):
    def __init__(self, column_name):
        self.column_name = column_name
        self.mapping = {}

    def handle_data(self, line, data_list, data_dict):
        self.mapping[(data_dict["target"], data_dict["neighbor"])] \
                = float(data_dict[self.column_name])

    def __getitem__(self, target_and_neighbor):
        return self.mapping.get(target_and_neighbor, None)



#####################################################

if __name__ == "__main__":
    Main(parser.parse_args()).run()
