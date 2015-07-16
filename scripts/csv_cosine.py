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
        Return the cosine of two `target` vectors in input.

        Given:
        -- A CSV file with columns `target_a` and `target_b`.
        -- A CSV file with AT LEAST the columns `target` and `context`.
        Finds the cosine between columns in the second file and outputs the result.

        Entries are discriminated by the `target` and `context` columns.""")
parser.add_argument("target_pairs", type=argparse.FileType("r"),
        help="""The pairs target_a/target_b.""")
parser.add_argument("input_file", type=argparse.FileType("r"),
        help="""File whose elements should be added.""")
parser.add_argument("column_name", type=unicode,
        help="""The column name from which to take the cosine.""")


############################################################

class TargetPairCollector(csv.CSVHandler):
    r"""Collect (target_a,target_b) namedtuples in self.pairs"""
    def __init__(self):
        self.pairs = []

    def handle_header(self, line, header_names):
        assert set(header_names) == {"target_a", "target_b"}, header_names

    def handle_data(self, line, data_namedtuple):
        self.pairs.append(data_namedtuple)


############################################################

class DataCollector(csv.CSVHandler):
    def __init__(self):
        self.data = collections.OrderedDict()
        self.add_operation = lambda x, y: x+y
        self.list_header_names = []
        self.set_header_names = set()


    def handle_header(self, line, header_names):
        assert "target" in header_names, header_names
        assert "context" in header_names, header_names
        more = (h for h in header_names if h not in self.set_header_names)
        self.list_header_names.extend(more)
        self.set_header_names.update(more)


    def handle_data(self, line, data_namedtuple):
        r"""Add data_namedtuple to `self.data`. Note that multiple namedtuple
        classes may have been produced (with different arity and argument
        name/order). They are all required to have `target` and `context`, though.
        """
        t, c = data_namedtuple.target, data_namedtuple.context
        data_t = self.data.setdefault(t, collections.OrderedDict())
        if c in data_t:
            print("WARNING: duplicate target-context pair:",
                    t, c, file=sys.stderr)
        data_t[c] = data_namedtuple


    def print_merged(self, target_pairs, column_name):
        r"""Merge `target_a` and `target_b` and print them."""
        print(*["target_a", "target_b", "cosine"], sep="\t")
        column_index = self.list_header_names.index(column_name)
        for target_pair in target_pairs:
            self._print_pair(target_pair, column_index)

    def _print_pair(self, target_pair, column_index):
        for target in target_pair:
            if target not in self.data:
                print("WARNING: missing target", target,
                        "for cosine ", target_pair, file=sys.stderr)
                return
        cosine = self._calc_cosine(target_pair, column_index)
        print(*(list(target_pair) + [cosine]), sep="\t")


    def _list_contexts(self, targets):
        seen_ctx = set()
        for target in targets:
            for context in self.data[target]:
                if context not in seen_ctx:
                    yield context
                    seen_ctx.add(context)


    def _calc_cosine(self, target_pair, column_index):
        r"""Return cosine between pair of vectors formed by given contexts."""
        t_a, t_b = target_pair
        contexts = list(self._list_contexts(target_pair))
        vec_a = [self._get_data(t_a, c, column_index) for c in contexts]
        vec_b = [self._get_data(t_b, c, column_index) for c in contexts]
        dotprod = sum(x*y for (x, y) in zip(vec_a, vec_b))
        abs_a = math.sqrt(sum(x*x for x in vec_a))
        abs_b = math.sqrt(sum(x*x for x in vec_b))
        return dotprod/(abs_a*abs_b)


    def _get_data(self, target, context, column):
        try:
            d = self.data[target][context]
        except KeyError:
            return 0.0
        else:
            return float(d[column])


############################################################

def main():
    args = parser.parse_args()
    target_pairs = csv.parse_csv(TargetPairCollector(),
            input_file=args.target_pairs).pairs

    collector = csv.parse_csv(DataCollector(),
            input_file=args.input_file)
    collector.print_merged(target_pairs, args.column_name)


#####################################################

if __name__ == "__main__":
    main()
