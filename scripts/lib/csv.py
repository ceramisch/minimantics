#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


def parse_csv(handler, input_file=None, yield_comments=False, yield_header=False):
    r"""Iterate through each line from a CSV input file (or stdin).
    Callbacks are called on `handler`.
    
    Arguments:
    -- yield_comments: If True, yield comments and empty lines as well.
    -- yield_header: If True, yield header as well.
    """
    if input_file is None:
        import sys
        input_file = sys.stdin

    header = None
    handler.begin()
    for line in input_file:
        line = line[:-1]
        if not line or line.startswith("#"):
            handler.handle_comment(line)
            continue

        data = line.split()

        if header is None:
            handler.handle_header(line, data)
            header = data
        else:
            handler.handle_data(line, data, dict(zip(header, data)))
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

    def handle_data(self, line, data_list, data_dict):
        r"""Called once for each line of data."""
        raise NotImplementedError

    def begin(self):
        r"""Called before parsing."""
        pass  # Default: just begin quietly

    def end(self):
        r"""Called after parsing."""
        pass  # Default: just finish quietly
