#!/usr/bin/python

import sys
import pdb
from operator import itemgetter
import math

measures = [ "refs", "energy@100", "U@100", "Rprec", "P@10", "P@100" , "MAP" ]

################################################################################

def mean_avg_prec( ranks ) :
    prec_sum = 0.0
    for nb_tp in range(len(ranks)) :
        prec_sum = prec_sum + ( (nb_tp + 1) / ranks[ nb_tp ] )
    if len(ranks) != 0 :
        return prec_sum / len(ranks)        
    else :  
        return 0.0

################################################################################

def precision_at( ranks, at ) :
    correct = 0.0
    for r in ranks :
        if r > at :
            break
        else :
            correct = correct + 1.0
    if at != 0 :
        return correct / at
    else :
        return float( 'nan' )
            
################################################################################    

def create_header_map( line ) :
    fields = line.strip().split( "\t" )
    header_map = {}
    for f in range(len(fields)) :
        header_map[ fields[f] ] = f
    return header_map

################################################################################

def has_nonzero( fields, header_map, resources_map ) :
    if fields[ header_map[ "rank" ] ] != "0" :
        for res_field, res_order in resources_map.items() :
            if fields[ res_order ] != "0" :
                return True
                
################################################################################                

def add_or_create_list( hashmap, key, item ) :
    entry = hashmap.get( key, [] )
    entry.append( item )
    hashmap[ key ] = entry

################################################################################                

def update_verbs_ranks( verbs_ranks, fields, header_map, resources_map ) :
    verb = fields[ header_map[ "verb1" ] ]       
    rank = fields[ header_map[ "rank" ] ]        
    one_verb_entry = verbs_ranks.get( verb, {} )
    for res_field, res_order in resources_map.items() :

        try :
            if fields[ res_order ] != "0" :
                add_or_create_list( one_verb_entry, res_field, int(rank) )
        except Exception :
            pdb.set_trace()
    verbs_ranks[ verb ] = one_verb_entry

################################################################################

def create_resources_map( header_map ) :
    no_ref = [ "verb1", "idverb1", "verb2", "idverb2", "similarity", "rank" ]
    resources_map = {}
    for fieldname in header_map.keys() :
        if fieldname not in no_ref :
            resources_map[ fieldname ] = header_map[ fieldname ]
    return resources_map

################################################################################

def get_energy( ranks, threshold ) :
    """
        This function calculates 3 measures: energy, smooth energy and useless 
        proportion. All consider a given rank threshold. Typical threshold 
        values are 100 or 500 since after these ranks the neighbours can be 
        safely ignored and any difference in their ranks is irrelevant. If 
        threshold is very large (say 99999) it corresponds to traditional 
        energy using all neighbours. The output of this function is a tuple of
        3 floats (energy@threshold, smoothENergy@threshold, U@threshold).
        Smooth energy is computed by applying a hyperbolic tangent on the
        ranks, so that at rank threshold we have 0.95 energy and all ranks
        below threshold will have energies between 0.95 and 1. The intuition
        behind it is that a difference of 500->1000 is much less relevant
        for energy than a difference 15->150, because 500 was already bad
        anyway whereas 15->150 means a good neighbour now is too far.
        Energy : 1 (good) to unbounded (bad)
        Smooth Energy: 0 (good) to 1 (bad)
        Useless proportion : 0 (good) to 1 (bad)
    """
    sum_ranks = 0.0
    useless = 0.0
    norm_fact = math.atanh(0.95)/threshold
    smoothing_func = lambda x : math.tanh(x * norm_fact)
    e3 = 0.0
    e3min = 0.0
    n_j = len(ranks)
    for i in range(len(ranks)) :
        r = ranks[i]
        # rank is below threshold. It interests us
        if r <= threshold :
            sum_ranks = sum_ranks + r
        # after the threshold, all neighbours have the same rank. We count it as
        # useless and U@threshold is incremented
        else :
            sum_ranks = sum_ranks + threshold + 1
            useless = useless + 1
        e3 = e3 + smoothing_func( r )
        e3min = e3min + smoothing_func( i )
    energy_at_t = 2.0 * sum_ranks / ( ( n_j ) * ( n_j + 1 ) )
    u_at_t = useless / len(ranks)
    s_energy_at_t = (e3 - e3min) / (n_j - e3min)
    return (energy_at_t, s_energy_at_t, u_at_t)

################################################################################

def calculate_measures( ranks, measures ) :
    measures_vals = []
    for m in measures :
        if m == "refs" :
            measures_vals.append( len( ranks ) )
        elif m.startswith( "energy@" ) :
            at = int( m.split("@")[1] )
            if len( ranks ) != 0 :
                #energy = 2.0 * sum( ranks ) / ( len( ranks ) * ( len( ranks )+1 ) )
                (o_energy,energy,u) = get_energy( ranks, at)
            else :
                (o_energy,energy,u) = (float('nan'),float('nan'),float('nan'))
            measures_vals.append(energy)
            measures_vals.append(u)
        elif m.startswith( "U@" ):
            pass # ignore. This measure always follows energy and is calculated
            # at the same time.
        elif m == "Rprec" : 
            measures_vals.append( precision_at( ranks, len(ranks) ) )
        elif m.startswith( "P@" ) :
            at = int( m.split("@")[1] )
            measures_vals.append( precision_at( ranks, at ) )
        elif m == "MAP" :
            measures_vals.append( mean_avg_prec( ranks ) )
        else :
            print >> sys.stderr, "Measure not implemented: " + m
    return measures_vals
    
################################################################################    
    
def update_averages( averages, r_name, measures, verb_res_measures ) :
    for m_i in range(len(measures)) :
        m = r_name + "-" + measures[ m_i ]        
        (s,n) = averages.get( m, (0.0, 0.0) )
        # test if it is NaN
        if verb_res_measures[ m_i ] == verb_res_measures[ m_i ] :
            s = s + verb_res_measures[ m_i ]
            n = n + 1
            averages[ m ] = (s,n)
            
################################################################################
# MAIN
################################################################################

if len( sys.argv ) == 1 :
    thesaurus_f = sys.stdin
else :
    thesaurus_f = open( sys.argv[1] )

header_map = create_header_map( thesaurus_f.readline() )
resources_map = create_resources_map( header_map )

verbs_ranks = {}
for line in thesaurus_f.readlines() :
    fields = line.strip().split( "\t" )    
    if has_nonzero( fields, header_map, resources_map ) :
        update_verbs_ranks( verbs_ranks, fields, header_map, resources_map )
        #print >> sys.stderr, "Evaluating verb " + fields[header_map["verb1"]]

# Create cartersian product of resources x measures 
# Resources are sorted by order in the input file (second field of items tuple)
# MEasures are sorted as in the measures list
measures_resources = map( lambda (x, y) : x + "-" + y, \
      [(a,b) for (a,c) in sorted( resources_map.items(), key=itemgetter(1) ) \
      for b in measures ] )
      
# print header      
print "verb\t" + "\t".join( measures_resources )

averages = {}
for verb in sorted( verbs_ranks.keys() ) :
    output = verb 
    for (r_name, r_order) in sorted(resources_map.items(), key=itemgetter(1)) :
        ranks = verbs_ranks[ verb ].get( r_name, [] )
        verb_res_measures = calculate_measures(ranks, measures )
        #pdb.set_trace() 
        update_averages( averages, r_name, measures, verb_res_measures )
        output = output + "\t" + "\t".join( map( str, verb_res_measures ) )
    print output
    
for mr in measures_resources :
    (s,n) = averages.get( mr, ( float('nan'), float('nan') ) )
    print >> sys.stderr, "Average " + mr + ": " + str( s/n )

