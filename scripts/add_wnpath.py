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
