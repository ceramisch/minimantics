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
from lib import csv, embeddings

FILE_ENC = "UTF-8"
HERE = os.path.dirname(os.path.realpath(__file__))


parser = argparse.ArgumentParser(description="""
        Read a tab-separated CSV file (as in the output from minimantics)
        from stdin and output the same file with an extra `w2v_cosine` column
        on stdout, based on a word2vec embeddings file.
        """)
parser.add_argument("-k", "--best-k", type=int, default=float('inf'),
        help="""Output only first K entries for each `target`.""")
parser.add_argument("embeddings_file", type=argparse.FileType('r'),
        help="""A file of embeddings: each line has 'word x1 x2 x2 ... xN'""")


class EmbeddingsCmpAdder(csv.CSVHandler):
    def __init__(self, args):
        self.args = args
        self.current_target = None
        self.current_target_count = 0
        self.embedding_set = embeddings.EmbeddingSet()
        self.embedding_set.add_from(args.embeddings_file)

    def handle_comment(self, line):
        print(line.encode('utf8'))

    def handle_header(self, line, header_list):
        print(line.encode('utf8'), "w2v_cosine",  sep="\t")

    def handle_data(self, line, data_namedtuple):
        target = data_namedtuple.target
        neighbor = data_namedtuple.neighbor
        if target != self.current_target:
            self.current_target = target
            self.current_target_count = 0
        self.current_target_count += 1
        if self.current_target_count <= self.args.best_k:
            cosine = "{0:.10f}".format(self.compare(target, neighbor))
            print("\t".join(data_namedtuple).encode('utf8') + "\t" + cosine)

    def compare(self, target, neighbor):
        r"""Return the best path_similarity between
        `target` and `neighbor`."""
        try:
            return self.embedding_set.compare(target, neighbor)
        except KeyError:
            return 0.0


#####################################################

if __name__ == "__main__":
    csv.parse_csv(EmbeddingsCmpAdder(parser.parse_args()))
