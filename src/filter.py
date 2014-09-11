#!/usr/python

import sys
import pdb
import re

THRESHOLD=100

def isalpha( token ) :
    for c in token :
        if not re.match(r'[a-zA-Z\+-]',c) :
            return False
    return not token.startswith("-") and not token.endswith("-")

if len(sys.argv) == 3 :
    input = open(sys.argv[1])
    thresh = int( sys.argv[2] )
else :
    input = sys.stdin
    thresh = THRESHOLD

for line in input.readlines() :
    (freq, token) = line.strip().split( )
    if isalpha(token) and len(token) > 1 and int(freq) > thresh :
        print token
