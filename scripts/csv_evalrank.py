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
import collections
import itertools
import math
import os
import scipy.stats
import sys
import textwrap

from lib import csv


parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        Calculates several scores between columns of two CSV files.
        The first file is the Gold Standard (G); the second is a set of
        Predictions (P).

        These measures are always calculated:
        * PearsonR: linear correlation between values  [-1..+1]
        * SpearmanRho: rank correlation; penalizes sum(dist**2)  [-1..+1]
        * KendallTau: rank correlation; penalizes sum(2*dist)  [-1..+1]

        These measures require --gold-threshold:
        * BestF1: max(F1 of top N values for all N)  [0..+1]
        * AvgPrec: avg(prec of top k values if isrelevant(k'th))  [0..+1]
        * Prec@X: precision using top X values  [0..+1]
        * NDCG: normalized(sum(isrelevant(k'th) / log(k)))  [0..+1]
        """))
parser.add_argument("--gold-id-column", default=None, 
        metavar=("<colname>"), type=unicode,
        help="""Column name of unique item identifier in gold_file
        (default: first column).""")
parser.add_argument("--pred-id-column", default=None, 
        metavar=("<colname>"), type=unicode,
        help="""Column name of unique item identifier in pred_file
        (default: first column).""")
parser.add_argument("--gold-value-columns", nargs="*", default=None, 
        metavar=("<colname>"), type=unicode,
        help="""Column names of numeric values in gold_file
        (default: second column).""")
parser.add_argument("--pred-value-columns", nargs="*", default=None,
        metavar=("<colname>"), type=unicode,
        help="""Column names of numeric values in pred_file
        (default: second column).""")

parser.add_argument("--gold-threshold", metavar="T", type=float,
        help="""Threshold above which (>=) the value should be interpreted as
        true/positive label. Values below this are considered
        false/negative.""")
parser.add_argument("--inverted-scales", action="store_true",
        help="""Indicates that gold-standard and prediction measures
        use inverted scales (e.g. one measures "compositionality"
        and the other measures "non-compositionality".""")
parser.add_argument("--precision-at", metavar="N", type=int, default=10,
        help="""Calculate precision at top N pred_file elements with
        highest value (default: 10 elements).""")

parser.add_argument("--debug", action="store_true",
        help="""Print extra debug info.""")

parser.add_argument("gold_file", type=argparse.FileType('r'), 
        help="""Filename of first CSV file (gold-standard values).
        This file must contain only valid items.""")
parser.add_argument("pred_file",  type=argparse.FileType('r'),
        help="""Filename of second CSV file (predicted values).""")


#####################################################

class NumValuesParser(csv.CSVHandler):
    def __init__(self, id_col, colnames, inverted_scales=False):
        self.id_col = id_col
        self.colnames = colnames
        self.inverted_scales = inverted_scales
        self.result_columns = {}

    def handle_header(self, line, header_names):
        if self.id_col is None : # by default, first column
            self.id_col = header_names[0]
        if self.colnames is None : # by default, second column
            self.colnames = [ header_names[1] ]
        for col in self.colnames + [ self.id_col ] :
            assert col in header_names, (col, header_names)
            self.result_columns[col] = {} #collections.OrderedDict()

    def handle_data(self, line, data_namedtuple):
        key = getattr(data_namedtuple, self.id_col)
        for colname in self.colnames :
            value = float(getattr(data_namedtuple, colname))
            if self.inverted_scales: value = -value
            self.result_columns[colname][key] = value

    def end(self):
        pass


#####################################################

warnings = set()
def warn_once(message, **kwargs):
    global warnings
    if message not in warnings :
        print("WARNING ONCE:", message.format(**kwargs), file=sys.stderr)
        warnings.add(message)


#####################################################

class Main(object):
    def __init__(self, args, parser_gold, parser_pred):
        self.args = args
        self.parser_gold = parser_gold
        self.parser_pred = parser_pred
        self.columns_gold = parser_gold.result_columns
        self.columns_pred = parser_pred.result_columns

    def run(self):
        sample_col_gold = self.parser_gold.colnames[0]
        sample_col_pred = self.parser_pred.colnames[0]
        for key_gold in self.columns_gold[sample_col_gold].iterkeys():
            if key_gold not in self.columns_pred[sample_col_pred]:
                warn_once("gold key `{key}` not found in prediction file " \
                        "`{filename}`; will use avg(predictions)", key=key_gold,
                            filename=os.path.basename(self.args.pred_file.name))
        for key_pred in self.columns_pred[sample_col_pred].iterkeys():
            if key_pred not in self.columns_gold[sample_col_gold]:
                warn_once("pred key `{key}` not found in gold-standard file " \
                        "`{filename}`; will use 0.0", key=key_pred,
                            filename=os.path.basename(self.args.gold_file.name))

        for col_gold, col_pred in itertools.product(
                self.parser_gold.colnames, self.parser_pred.colnames):
            print("\n==> Scores between columns `{}` (gold) and `{}`"\
                  " (pred)".format(col_gold, col_pred))

            avg_pred = sum(self.columns_pred[col_pred].itervalues()) \
                    / len(self.columns_pred[col_pred])

            vec_gold, vec_pred = [], []  # aligned based on `gold`; unsorted
            for key_gold in self.columns_gold[col_gold].keys():
                vec_gold.append(self.columns_gold[col_gold][key_gold])
                vec_pred.append(self.columns_pred[col_pred] \
                        .get(key_gold, avg_pred))

            self.print_correl("PearsonR", scipy.stats.pearsonr(vec_gold, vec_pred))
            self.print_correl("SpearmanRho", scipy.stats.spearmanr(vec_gold, vec_pred))
            self.print_correl("KendallTau", scipy.stats.kendalltau(vec_gold, vec_pred))

            ############################################################

            vec_gold, vec_pred = [], []  # aligned & sorted based on `pred` ranking
            ordered_gold_items = sorted(self.columns_pred[col_pred].iteritems(),
                    key=lambda item: item[1], reverse=True)  # descending order
            for key_pred, value_pred in ordered_gold_items:
                vec_pred.append(value_pred)
                vec_gold.append(self.columns_gold[col_gold].get(key_pred, 0.0))
            self.calc_print_precision(vec_gold, vec_pred)


    def print_correl(self, name, correl_pair):
        correl_score, correl_stddev = correl_pair
        print("{name}: {score:.5f}  (deviation={stddev:.5f})".format(
            name=name, score=correl_score, stddev=correl_stddev))


    def calc_print_precision(self, vec_gold, vec_pred):
        r"""Calculate and print threshold-based measures
        (Both vectors must be aligned, with vec_pred
        sorted by descending order).
        """
        if self.args.gold_threshold is None:
            warn_once("--gold-threshold not specified; skipping some measures")
            return  # Skip these measures

        total_positives = sum(1 for value in vec_gold \
                if value >= self.args.gold_threshold)

        self.precs, self.f1s = [float('-inf')], [float('-inf')]
        n_true_positives = 0
        # (All predictions are assumed to be positive)
        for n_pred_positives, (value_gold, value_pred) \
                in enumerate(zip(vec_gold, vec_pred), 1):
            if value_gold >= self.args.gold_threshold:
                n_true_positives += 1
            precision = n_true_positives / n_pred_positives
            recall = n_true_positives / total_positives
            self.precs.append(precision)
            if precision == 0 or recall == 0:
                self.f1s.append(float("-inf"))
            else:
                self.f1s.append(2 / ((1/precision) + (1/recall)))

        if self.args.debug:
            print("DEBUG:PredList:", " ".join(
                    "{:.2f}".format(p) for p in vec_pred))
            print("DEBUG:GoldList:", " ".join(
                    "{:.2f}".format(p) for p in vec_gold))
            print("DEBUG:PrecisList:", " ".join(
                    "{:.2f}".format(p) for p in self.precs[1:]))
            print("DEBUG:F1List:", " ".join(
                    "{:.2f}".format(p) for p in self.f1s[1:]))

        # Output: max(F1 for all possible top subvectors of length N)
        n_best_f1 = max(xrange(len(self.f1s)), key=lambda N: self.f1s[N])
        print("BestF1: {score:.5f}  (@{N}, where prec={prec})".format(
            score=self.f1s[n_best_f1], N=n_best_f1, prec=self.precs[n_best_f1]))

        # Output: average precision among all possible top subvectors
        avg_prec = sum(self.precs[k] for (k, value_gold) in enumerate(vec_gold, 1) \
                if value_gold >= self.args.gold_threshold) / total_positives
        print("AvgPrec: {score:.5f}".format(score=avg_prec))

        try:
            # Output: Precision using top subvector of length X
            print("Prec@{X}: {score:.5f}".format(X=self.args.precision_at,
                score=self.precs[self.args.precision_at]))
        except IndexError:
            warn_once("Prec@{X} unavailable; pred vector has {len} entries",
                    X=self.args.precision_at, len=len(self.precs))

        # Output: Normalized DCG
        dcg = self.calc_dcg([int(value >= self.args.gold_threshold) \
                for value in vec_gold])  # relevance in {0, 1}
        idcg = self.calc_dcg([1]*total_positives)
        print("NDCG: {ndcg:.5f}  (DCG={dcg:.5f})".format(
                dcg=dcg, ndcg=dcg/idcg))


    def calc_dcg(self, relevances):
        r"""Calculate the DCG as:
        => rel_0 + \sum_{i=1}^{len(rel)-1} rel_i / log2(i+1)
        """
        indexes = xrange(1, len(relevances))
        return (relevances[0] if relevances else 0) \
                + sum(relevances[i] / math.log(i+1, 2) for i in indexes)


#####################################################

if __name__ == "__main__":
    args = parser.parse_args()
    parser_gold = NumValuesParser(id_col=args.gold_id_column,
           colnames=args.gold_value_columns)
    parser_pred = NumValuesParser(id_col=args.pred_id_column,
           colnames=args.pred_value_columns,
           inverted_scales=args.inverted_scales)
    csv.parse_csv(parser_gold, input_file=args.gold_file)
    csv.parse_csv(parser_pred, input_file=args.pred_file)
    Main(args, parser_gold, parser_pred).run()
