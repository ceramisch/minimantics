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

import math


class Statistics(object):
    r"""Statistics calculator."""
    def __init__(self):
        self.n = 0
        self.sum = 0
        self.sumsq = 0

    def add(self, data):
        r"""Return the best path_similarity between
        `target` and `neighbor`."""
        self.n += 1
        self.sum += data
        self.sumsq += data**2

    @property
    def avg(self):
        r"""Return the average of all data."""
        return self.sum/self.n

    @property
    def stddev_population(self):
        r"""Return the population StdDev."""
        # (We use a trick to calculate stddev without having to keep everything
        # in memory. We just need N, sum(x) and sumsq=sum(x**2).)
        return math.sqrt(self.sumsq/(self.n) - self.avg**2)

    @property
    def stddev_sample(self):
        r"""Return the sample StdDev."""
        # StdDev here uses Bessel's N-1 correction.
        try:
            return math.sqrt(self.stddev_population**2 * self.n/(self.n-1))
        except ZeroDivisionError:
            return float('inf')
