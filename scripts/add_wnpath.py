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
        Read a tab-separated CSV file (as in the output from minimantics)
        from stdin and output the same file with an extra `wnpath` column
        on stdout.
        
        The `wnpath` is the highest wordnet path_similarity
        between all synsets of that line's pair of words (that is,
        we disambiguate by picking the closest possible pair).
        
        THIS SCRIPT REQUIRES THE INPUT TO BE SORTED ON `target`.""")
parser.add_argument("-k", "--best-k", type=int, default=float('inf'),
        help="""Output only first K entries for each `target`.""")
parser.add_argument("wordnet_pos_tag", type=unicode,
        help="""The wordnet POS-tag for all `target` and `neighbor` in the input.""")


class WnAdder(csv.CSVHandler):
    def __init__(self, args):
        self.args = args
        self.current_target = None
        self.current_target_count = 0

    def handle_comment(self, line):
        print(line)

    def handle_header(self, line, header_list):
        assert "target" in header_list, header_list
        assert "neighbor" in header_list, header_list
        print(line.decode('utf8'), "wnpath",  sep="\t")

    def handle_data(self, line, data_namedtuple):
        target = data_namedtuple.target
        neighbor = data_namedtuple.neighbor
        if target != self.current_target:
            self.current_target = target
            self.current_target_count = 0
        self.current_target_count += 1
        if self.current_target_count <= self.args.best_k:
            wnpath = "{0:.10f}".format(self.wnpath(target, neighbor))
            print("\t".join(data_namedtuple).encode('utf8'), wnpath, sep="\t")

    def wnpath(self, target, neighbor):
        r"""Return the best path_similarity between
        `target` and `neighbor`."""
        synsetsT = wn.synsets(target, self.args.wordnet_pos_tag)
        synsetsN = wn.synsets(neighbor, self.args.wordnet_pos_tag)
        if not synsetsT:
            return 0  # XXX no synsets for `target`
        if not synsetsN:
            return 0  # XXX no synsets for `neighbor`
        return max(wn.path_similarity(sT, sN)
                for sT in synsetsT for sN in synsetsN) \
                or 0  # When `wn` returns None, we just say sim==0


#####################################################

if __name__ == "__main__":
    csv.parse_csv(WnAdder(parser.parse_args()))
