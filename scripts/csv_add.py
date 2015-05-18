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
        Return the sum of two `target` vectors in input.

        Given:
        -- A CSV file with columns `target_a`, `target_b` and `target_result`.
        The special target name @NOTHING can also be used.
        -- A CSV file with AT LEAST the columns `target` and `context`.
        Adds up the columns in the second file and output the result.

        Entries are discriminated by the `target` and `context` columns.""")
parser.add_argument("--input-format", choices=("CSV", "word2vec"), default="CSV",
        help="""Choose the file format for input_file (default: CSV).""")
parser.add_argument("target_triples", type=argparse.FileType("r"),
        help="""The pairs target_a/target_b/target_result.""")
parser.add_argument("input_file", type=argparse.FileType("r"),
        help="""File whose elements should be added.""")


############################################################

class TriplesCollector(csv.CSVHandler):
    r"""Collect (target_a,target_b,target_result) namedtuples in self.triples"""
    def __init__(self):
        self.triples = []

    def handle_header(self, line, header_names):
        assert set(header_names) == {"target_a", "target_b", "target_result"}, header_names

    def handle_data(self, line, data_namedtuple):
        self.triples.append(data_namedtuple)


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


    def print_merged(self, triples):
        r"""Merge `target_a` and `target_b` and print them."""
        print(*self.list_header_names, sep="\t")
        for triple in triples:
            targets = [triple.target_a, triple.target_b]
            for target in targets:
                if target != "@NOTHING" and target not in self.data:
                    print("WARNING: missing target", target,
                            "for", triple.target_result, file=sys.stderr)
            targets = [t for t in targets if t in self.data]
            for context in self._list_contexts(targets):
                print(*self._merged_columns(targets, triple.target_result, context), sep="\t")


    def _list_contexts(self, targets):
        seen_ctx = set()
        for target in targets:
            for context in self.data[target]:
                if context not in seen_ctx:
                    yield context
                    seen_ctx.add(context)


    def _merged_columns(self, targets, target_result, context):
        r"""Merge all targets for given context and yield columns."""
        for header_name in self.list_header_names:
            if header_name == "target":
                yield target_result
                continue
            cell_vectors = [self.data[target][context] for target
                    in targets if (context in self.data[target])]
            cell_values = [getattr(cv, header_name) for cv in cell_vectors]
            assert cell_values, (targets, target_result, context)

            if len(cell_values) == 1:
                yield cell_values[0]
            elif header_name == "context" or header_name.startswith("id_"):
                if len(set(cell_values)) != 1:
                    print("WARNING: bad entry", header_name, "when adding:",
                            target_result, file=sys.stderr)
                yield cell_values[0]
            else:
                yield sum(self._floatify(cell_values))


    def _floatify(self, values):
        r"""Return values as floats, skipping bad values."""
        for v in values:
            try:
                yield float(v)
            except (TypeError, ValueError):
                pass


############################################################

W2VNamedTuple = collections.namedtuple('W2VNamedTuple', 'target context value')

def word2vec_parser(csv_handler, input_file):
    r"""(Similar to a CSVParser, but reads word2vec output format)"""
    next(input_file)  # Skip first line

    header = ("target", "context", "value")
    csv_handler.handle_header(None, header)

    for line in input_file:
        line = line[:-1]
        target, line = line.split(" ", 1)
        for context, value in enumerate(line.split(" ")):
            csv_handler.handle_data(None, W2VNamedTuple(
                target, "c{}".format(context), value))
    return csv_handler

############################################################

def main():
    args = parser.parse_args()
    triples = csv.parse_csv(TriplesCollector(),
            input_file=args.target_triples).triples

    data_parser = csv.parse_csv
    if args.input_format == "word2vec":
        data_parser = word2vec_parser

    collector = data_parser(DataCollector(),
            input_file=args.input_file)
    collector.print_merged(triples)


#####################################################

if __name__ == "__main__":
    main()
