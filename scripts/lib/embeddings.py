#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import math


class EmbeddingSet(object):
    r"""Instances represent a mapping from words to their embeddings."""
    def __init__(self):
        self.word2embedding = {}

    def add_from(self, fileobj):
        for linenum, line in enumerate(fileobj):
            if linenum != 0:  # Ignore first line
                try:
                    data = line.decode('utf8', errors="replace").rstrip().split(" ")
                except Exception as e:
                    raise Exception("Bad line {}: raised {}: {}".format(
                            linenum+1, type(e).__name__, e))
                self.word2embedding[data[0]] = [_to_float(x, linenum, colnum) for
                        (colnum, x) in enumerate(data[1:])]

    def compare(self, word1, word2, type="cosine"):
        r"""Return a cosine comparison of embeddings for the two words."""
        e1 = self.word2embedding[word1]
        e2 = self.word2embedding[word2]

        assert type=="cosine", "only cosine is supported"
        dot_p = sum(a*b for (a,b) in zip(e1,e2))
        e1_norm = math.sqrt(sum(v**2 for v in e1))
        e2_norm = math.sqrt(sum(v**2 for v in e2))
        return dot_p / (e1_norm * e2_norm)


def _to_float(strvalue, linenum, colnum):
    try:
        return float(strvalue)
    except ValueError as e:
        raise Exception("Bad float in line {} (col {}): {!r}" \
                .format(linenum+1, colnum+1, strvalue))
