#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import argparse
import scipy.stats
import itertools
import collections
import sys
from lib import csv

parser = argparse.ArgumentParser(description="""
        Calculates several correlation scores between columns of two CSV files.
        """)
parser.add_argument("-c1", "--file1-corr-columns", nargs="*", default=None, 
        metavar=("<column-name>"), type=unicode,
        help="""Column names of correlatable numeric values in file 1 
        (default: second column).""")
parser.add_argument("-c2", "--file2-corr-columns", nargs="*", default=None,
        metavar=("<column-name>"), type=unicode,
        help="""Column names of correlatable numeric values in file 2 
        (default: second column).""")
parser.add_argument("-i1", "--file1-id-column", default=None, 
        metavar=("<column-name>"), type=unicode,
        help="""Column name of unique item identifier in file 1 
        (default: first column).""")
parser.add_argument("-i2", "--file2-id-column", default=None, 
        metavar=("<column-name>"), type=unicode,
        help="""Column name of unique item identifier in file 2 
        (default: first column).""")
parser.add_argument("file1", type=argparse.FileType('r'), 
        help="""Filename of first CSV file containing correlatable values.
        The first file contains only valid items. 
        A WARNING will be shown if items appear in file1 but not in file2.""")
parser.add_argument("file2",  type=argparse.FileType('r'),
        help="""Filename of second CSV file containing correlatable values.""")

#####################################################

class NumValuesParser(csv.CSVHandler):
    def __init__(self, id_col, corr_cols, result_dict):
        self.id_col = id_col
        self.corr_cols = corr_cols
        self.result_dict = result_dict

    def handle_header(self, line, header_names):
        if self.id_col is None : # by default, first column
            self.id_col = header_names[0]
        if self.corr_cols is None : # by default, second column
            self.corr_cols = [ header_names[1] ]
        for col in self.corr_cols + [ self.id_col ] :
            assert col in header_names, header_names
            self.result_dict[col] = {} #collections.OrderedDict()

    def handle_data(self, line, data_namedtuple):
        key = getattr(data_namedtuple, self.id_col)
        for corr_col in self.corr_cols :
            value = getattr(data_namedtuple, corr_col)
            #assert float(value), value  # Bug if value=0.0
            self.result_dict[corr_col][key] = float(value)

    def end(self):
        pass

#####################################################

warnings = []
def warn_once(message):
    global warnings
    if message not in warnings :
        print(message,file=sys.stderr)
        warnings.append(message)

#####################################################

def calc_correlation( args, columns_f1, columns_f2 ) :
    pairs = itertools.product(args.file1_corr_columns,args.file2_corr_columns)
    for corr_col1, corr_col2 in pairs :
        vec1 = []
        vec2 = []
        for key1 in columns_f1[corr_col1].keys() :
            if key1 not in columns_f2[corr_col2].keys() :
                warn_once("WARNING: {} not found in file 2 ({}). " \
                          "Replaced by 0.".format(key1,args.file1.name))
            else :
                vec1.append(columns_f1[corr_col1][key1])
                vec2.append(columns_f2[corr_col2].get(key1,0))
        print("\n> Correlations btw columns '{}' (file1) and '{}'"\
              " (file2)".format(corr_col1, corr_col2))
        pearson = scipy.stats.pearsonr(vec1, vec2)
        spearman = scipy.stats.spearmanr(vec1, vec2)
        kendalltau = scipy.stats.kendalltau(vec1, vec2)
        print("Pearson = {}\nSpearman = {}\n" \
              "Kendall-tau = {}".format(pearson,spearman,kendalltau))
            

#####################################################

if __name__ == "__main__":
    args = parser.parse_args()
    columns_f1 = {}
    columns_f2 = {}
    csv.parse_csv(NumValuesParser(id_col=args.file1_id_column,
           corr_cols=args.file1_corr_columns, result_dict=columns_f1),
           input_file=args.file1)
    csv.parse_csv(NumValuesParser(id_col=args.file2_id_column,
           corr_cols=args.file2_corr_columns, result_dict=columns_f2),
           input_file=args.file2)
    calc_correlation(args, columns_f1, columns_f2)
