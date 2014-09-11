#!/bin/bash
# How to evaluate a thesaurus:

INPUT="$1"  

cat $INPUT | 
python get_ranks.py | 
python get_neighbours.py > $INPUT.neigh
cat $INPUT.neigh |
python eval_measures.py > $INPUT.eval 2> $INPUT.eval-avg

# This will output an eval file which contains per-verb evaluation in 
# thesaurus-eval.csv and outputs to stderr (terminal) the averages of the
# measures for all verbs. Each script is explained in the script itself.
# The input of the first script is a csv thesaurus as output by Idiart's program
# calculate_thesaurus_full_cosine_nfeatures, that is, a tab-separated file
# containing the fields

# verb1   id_verb1    verb2   id_verb2    similarity_score
    
# There are some extra spaces before the verb IDs but they are removed by my
# scripts. Ties are shuffled by first randomizing the neighbours and then 
# performing a stable sort.

################################################################################
# Extra stuff for transforming the reference thesauri. Only useful to developer

# Generate the moby classes file in same format as levin (large but easier to
# process).

#cat mobythes.aur.cr | 
#sed -e 's/ /+/g' -e 's/,,*$//g' |
#awk 'BEGIN{FS=",";OFS="\t"; class=1}{ for( i=1; i<=NF; i++){ print $i, class, class} class++;}' > moby-classes.txt

# Phrasal verbs in verbnet

#sed 's/_/+/g' verbnet-verbclasses.txt > tmp
#mv tmp verbnet-verbclasses.txt
