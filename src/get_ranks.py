#!/usr/bin/python
"""
    The input of this script is a csv thesaurus as output by Idiart's program
    calculate_thesaurus_full_cosine_nfeatures, that is, a tab-separated file
    containing the fields
    
    verb1   id_verb1    verb2   id_verb2    similarity_score
    
    There are some extra spaces before the verb IDs but they are removed by my
    script. This script simply sorts the neighbours of a verb by descending
    similarity and adds a rank number. The verb itself is neighbour with rank 
    zero. Ties are shuffled by first randomizing the neighbours and then 
    performing a stable sort.
"""

import sys
import operator
import random
import pdb

def print_out( verb1, idv1, related ) :
    random.shuffle( related ) # This is performed because sort is stable, so
    # tied neighbours are first shuffled and then stable-sorted
    sorted_neighbours = sorted( related, key=operator.itemgetter(2), reverse=True )
    first_neighbour = sorted_neighbours[0][0]
    if first_neighbour == verb1 : # the first neighbour might have been manually removed, so I check if it is the verb itself (first rank = 0) or not (first rank = 1)
        rank = 0
    else :
        rank = 1
    for rel in sorted( related, key=operator.itemgetter(2), reverse=True ) :
        
        print "%(v1)s\t%(idv1)s\t%(v2)s\t%(idv2)s\t%(sim).10f\t%(r)d" % {
                "v1": verb1, "idv1": idv1, "v2": rel[0], "idv2": rel[1], \
                "sim": rel[2], "r": rank }
        rank = rank + 1
if len( sys.argv ) == 1 :
    thesaurus_f = sys.stdin
else :
    thesaurus_f = open( sys.argv[1] )
prevverb1 = None
previdv1 = None
related = []
for line in thesaurus_f.readlines() :    
    (verb1,idv1,verb2,idv2,sim) = line.strip().split("\t")
    if verb1 != prevverb1 and prevverb1 is not None :
        print_out( prevverb1.strip(), previdv1.strip(), related )
        #print >> sys.stderr, "Ranking verb " + prevverb1
        related = [ ( verb2.strip(), idv2.strip(), float(sim) ) ]
    else :
        related.append( ( verb2.strip(), idv2.strip(), float(sim) ) )
    prevverb1 = verb1
    previdv1 = idv1
print_out( prevverb1, previdv1, related )
