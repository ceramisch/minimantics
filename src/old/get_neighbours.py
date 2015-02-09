#!/usr/bin/python

import sys
import pdb
from nltk.corpus import wordnet
from operator import itemgetter

dictionaries = {}

def open_dict( dname ):
    try :
        dictionary = {}
        dictionary_f = open( dname )
        for line in dictionary_f.readlines() :
            (verb, classid, classname) = line.strip().split("\t")
            v_classes = dictionary.get( verb, set([]) )
            v_classes.add( classid )
            dictionary[ verb ] = v_classes
        return dictionary
    except Exception :
        pdb.set_trace()

def check_inclusion( synsets, lemma_target ) :
    count = 0
    for syn in synsets :
        for lemma in syn.lemmas :
            if( lemma.name == lemma_target ) :
                count = count + 1
    return count

def get_neigh_wordnet( verb1, verb2 ) :
    intersect = {}
    antonyms = 0
    synsv1 = wordnet.synsets( verb1, pos=wordnet.VERB )
    intersect[ "wn_syn" ] =  check_inclusion( synsv1, verb2 )
    # OOOH This was a huge bug! 
    # Only the last syset was considered in previous version
    intersect[ "wn_hyper" ] = 0 
    intersect[ "wn_hypo" ] = 0
    intersect[ "wn_mero" ] = 0
    intersect[ "wn_sibling" ] = 0
    for syn in synsv1 :
        hypernyms = syn.hypernyms()
        # corrected from assign to increment - ceramisch 2013.jan.02
        intersect[ "wn_hyper" ] += check_inclusion( syn.hypernyms(), verb2 ) 
        intersect[ "wn_hypo" ] += check_inclusion( syn.hyponyms(), verb2 )
        intersect[ "wn_mero" ] += check_inclusion( syn.member_holonyms(), verb2 )
        # siblings are the hyponyms (sons) of my fathers (hypernyms)
        for hyper in hypernyms :
            intersect[ "wn_sibling" ] += check_inclusion(hyper.hyponyms(), verb2)
        for lemma in syn.lemmas :
            antos = lemma.antonyms()
            for a in antos :
                if( a.name == verb2 ) :
                    antonyms = antonyms + 1
    intersect[ "wn_anto" ] = antonyms
    intersect[ "wn_1" ] = sum( intersect.values() )
    # Too much information! Only output wn_1 cumulated values
    new_intersect = {}
    new_intersect[ "wn_1" ] = intersect[ "wn_1" ]
    #pdb.set_trace()
    return new_intersect

def get_neigh_thesaurus( verb1, verb2 ) :
    global dictionaries
    intersect = {}
    for dict_id in dictionaries.keys() :
        dictio = dictionaries[ dict_id ]            
        neighs_v1 = dictio.get( verb1, set([]) )        
        neighs_v2 = dictio.get( verb2, set([]) )
        #if len(neighs_v1) != 0 :
            #pdb.set_trace()
        intersect[ dict_id ] = len( neighs_v1 & neighs_v2 )
    return intersect         

#dictionaries["levin"] = open_dict( "levin-verbclasses.txt" )
# Verbnet is more complete than levin
dictionaries["verbnet"] = open_dict( "verbnet-verbclasses.txt" )
dictionaries["moby"] = open_dict( "moby-classes.txt" )

if len( sys.argv ) == 1 :
    thesaurus_f = sys.stdin
else :
    thesaurus_f = open( sys.argv[1] )
    
firstLine = True
for line in thesaurus_f.readlines() :
    (verb1,idv1,verb2,idv2,sim,rank) = line.strip().split("\t")
    i_wn = get_neigh_wordnet( verb1, verb2 )
    i_thes = get_neigh_thesaurus( verb1, verb2 )
    if firstLine :
        print "\t".join( [ "verb1", "idverb1", "verb2", "idverb2", \
            "similarity", "rank" ] ) + "\t" + \
            "\t".join( map( str, sorted( i_wn.keys() ) ) ) + "\t" + \
            "\t".join( map( str, sorted( i_thes.keys() ) ) ) + "\tany"            
        firstLine = False
    val_wn = map(lambda(a,b):str(b),sorted(i_wn.items(),key=itemgetter(0)))
    val_thes = map(lambda(a,b):str(b),sorted(i_thes.items(),key=itemgetter(0)))
    print line.strip() + "\t" + \
        "\t".join( val_wn ) + "\t" + "\t".join( val_thes ) + "\t" + \
        str( sum( i_wn.values() + i_thes.values() ) )
