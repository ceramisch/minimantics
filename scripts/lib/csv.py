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

import collections
import sys


def parse_csv(handler, input_file=None, yield_comments=False, yield_header=False):
    r"""Iterate through each line from a CSV input file (or stdin).
    Callbacks are called on `handler`.
    
    Arguments:
    -- yield_comments: If True, yield comments and empty lines as well.
    -- yield_header: If True, yield header as well.
    """
    if input_file is None:
        input_file = sys.stdin

    tupleclass = None
    handler.begin()
    linenum = None
    try:
        for linenum, byteline in enumerate(input_file):
            byteline = byteline[:-1]
            line = byteline.decode('utf8', errors='replace')
            if not byteline or byteline.startswith(b"#"):
                handler.handle_comment(line)
                continue

            bytedata = byteline.split(b"\t")
            data = tuple(d.decode('utf8', errors='replace') for d in bytedata)

            if tupleclass is None:
                tupleclass = collections.namedtuple(
                        "DataTuple", data, rename=True)
                handler.handle_header(line, tupleclass._fields)
            else:
                if len(tupleclass._fields) != len(data):
                    print("BAD input: expected {} entries, " \
                            "but got {!r}".format(
                            len(tupleclass._fields), data), file=sys.stderr)
                    raise Exception("Bad CSV")
                data_tuple = tupleclass(*data)
                handler.handle_data(line, data_tuple)

    except Exception as e:
        print("ERROR when processing line {}" \
                .format(linenum+1), file=sys.stderr)
        raise
    handler.end()
    return handler


class CSVHandler(object):
    r"""Provides callback methods for `parse_csv`.
    You should subclass it and override the desired methods."""

    def handle_comment(self, line):
        r"""Called once per comment/empty line."""
        pass  # Default: just be quiet

    def handle_header(self, line, header_list):
        r"""Called for the header."""
        pass  # Default: just be quiet

    def handle_data(self, line, data_list):
        r"""Called once for each line of data."""
        raise NotImplementedError

    def begin(self):
        r"""Called before parsing."""
        pass  # Default: just begin quietly

    def end(self):
        r"""Called after parsing."""
        pass  # Default: just finish quietly
