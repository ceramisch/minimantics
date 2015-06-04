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
parser.add_argument("--normalize-before", action='store_true',
        help="""Normalize input vectors before adding them up""")
parser.add_argument("--normalize-after", action='store_true',
        help="""Normalize input vectors after adding them up""")
parser.add_argument("--input-format", choices=("CSV", "word2vec"), default="CSV",
        help="""Choose the file format for input_file (default: CSV).""")
parser.add_argument("target_addition_triples", type=argparse.FileType("r"),
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
    def __init__(self, args, addition_triples):
        self.args = args
        self.addition_triples = addition_triples
        self.data = collections.OrderedDict()  # Dict[TargetVector]
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
        # We only keep in memory the stuff we will use, otherwise we risk
        # running out of memory (true story; has happened before...)
        if any(t == a or t == b  for (a, b, res) in self.addition_triples):
            data_t = self.data.setdefault(t, TargetVector(t))
            data_t.add_entry(c, data_namedtuple)


    def print_merged(self):
        r"""Merge `target_a` and `target_b` and print them."""
        print(*self.list_header_names, sep="\t")
        for triple in self.addition_triples:
            targets = [triple.target_a, triple.target_b]
            for target in targets:
                if target != "@NOTHING" and target not in self.data:
                    print("WARNING: missing target", target,
                            "for", triple.target_result, file=sys.stderr)
            targets = [self.data[t] for t in targets if t in self.data]
            if self.args.normalize_before:
                for t in targets:
                    t.do_normalize(self.list_header_names)
            t_result = TargetVector.sum(triple.target_result, targets)
            if self.args.normalize_after:
                t_result.do_normalize(self.list_header_names)
            t_result.print_csv(self.list_header_names)


class TargetVector(object):
    r"""Represents a sparse vector."""
    def __init__(self, target_name):
        self.target_name = target_name
        self._ctx2vec = collections.OrderedDict()  # Dict[context, data_dict]

    def add_entry(self, context_name, data_namedtuple):
        r"""Add (self, context_name) -> data_namedtuple mapping."""
        if context_name in self._ctx2vec:
            print("WARNING: duplicate target-context pair:",
                    self.target_name, context_name, file=sys.stderr)
        self._add_into(context_name, data_namedtuple._asdict())

    def _add_into(self, context_name, data_dict):
        r"""Increment value for given context_name."""
        vec = self._ctx2vec.setdefault(context_name,
                {"target": self.target_name})
        for col_key, col_value in data_dict.iteritems():
            if col_key == "target": continue
            col_value = self._floatify(col_value)
            if col_key not in vec:
                vec[col_key] = col_value
            else:
                if col_key == "context" or col_key.startswith("id_"):
                    if col_value != vec[col_key]:
                        print("WARNING: incompatible entries", col_key,
                                "for context", context_name, "when adding up",
                                self.target_name, file=sys.stderr)
                else:
                    vec[col_key] += col_value

    @staticmethod
    def sum(new_target_name, iterable):
        r"""Add up instances of TargetVector."""
        ret = TargetVector(new_target_name)
        for tvector in iterable:
            for context, data_dict in tvector._ctx2vec.iteritems():
                ret._add_into(context, data_dict)
        return ret

    def print_csv(self, list_header_names):
        r"""Merge all targets for given context. Yield columns."""
        for data_dict in self._ctx2vec.itervalues():
            print("\t".join(unicode(x) for x in
                self._get_cols(data_dict, list_header_names)))

    def _get_cols(self, data_dict, list_header_names):
        r"""Yield all columns for this line."""
        for header_name in list_header_names:
            yield data_dict.get(header_name, "?")

    def _floatify(self, value):
        r"""Return value as float, if possible."""
        try:
            ret = float(value)
        except (TypeError, ValueError):
            return value
        else:
            if int(ret) == ret:
                return int(ret)
            return ret

    def do_normalize(self, list_header_names):
        r"""Normalize entries is `self`."""
        for header_name in list_header_names:
            sqsumsq = math.sqrt(sum(f**2 for (c, f)
                    in self._header2floats(header_name)))
            if sqsumsq != 0:
                for cvec, f in self._header2floats(header_name):
                    cvec[header_name] = f/sqsumsq

    def _header2floats(self, header_name):
        r"""Given a header name, yields floats for each context."""
        if not header_name.startswith("id_"):
            for c, cvec in self._ctx2vec.iteritems():
                try:
                    yield cvec, float(cvec[header_name])
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
        line = line.strip()
        target, line = line.split(" ", 1)
        for context, value in enumerate(line.split(" ")):
            csv_handler.handle_data(None, W2VNamedTuple(
                target, "c{}".format(context), value))
    return csv_handler

############################################################

def main():
    args = parser.parse_args()
    triples = csv.parse_csv(TriplesCollector(),
            input_file=args.target_addition_triples).triples

    data_parser = csv.parse_csv
    if args.input_format == "word2vec":
        data_parser = word2vec_parser

    collector = data_parser(DataCollector(args, triples),
            input_file=args.input_file)
    collector.print_merged()


#####################################################

if __name__ == "__main__":
    main()
