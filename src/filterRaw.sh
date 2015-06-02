#!/bin/bash

alias sort="LC_ALL=C sort"
alias join="LC_ALL=C join"
NBPROC=`cat /proc/cpuinfo | grep "processor" | wc -l`
SORTCMD="sort -T . --parallel ${NBPROC}"
JOINCMD="join"


if [ "$#" -ne 3 ]; then
    echo "Usage: sh $0 <raw-triples-file> <threshold-words> <threshold-pairs>"
    exit
fi

INPUT=$1
THRESH1=$2 # typically 50-100
THRESH2=$3 # typically 2-5


echo "Filtering, sorting and uniquing raw triples in ${INPUT}"

awk '{print $1}' ${INPUT} | ${SORTCMD} | uniq -c > ${INPUT}.targets
awk '{print $2}' ${INPUT} | ${SORTCMD} | uniq -c > ${INPUT}.contexts

# Keep only words that occur more than threshold, and are longer than 1 char
# Previous versions removed any special character too, but this is risky - c.f.
# compound words include _, different languages have different conventions
# Please, before running filter.sh, remove lines containing spurious words
# Modified by CR on Feb 25 2015
for file in ${INPUT}.targets ${INPUT}.contexts; do
  cat $file |  awk '{ if( $1 > thresh && length($2) > 1) print $2; }' thresh=${THRESH1} > $file.filter${THRESH1}
done

echo "Sorting raw triples..."
${SORTCMD} ${INPUT} > ${INPUT}.s

echo "Joining"
# First select only triples containing verbs from the filtered list
${JOINCMD} -1 1 -2 1 ${INPUT}.s ${INPUT}.targets.filter${THRESH1} | 
# Then sort in object order
${SORTCMD} -k 2 | 
# and filter keeping only triples whose objects are in the filtered list
${JOINCMD} -1 2 -2 1 -o "1.1 1.2" - ${INPUT}.contexts.filter${THRESH1} | 
# and sort again in verb order so that we can uniq afterwards
${SORTCMD} |
cat > ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}

echo "Uniquing and counting"
uniq -c ${INPUT}.s.filter.t${THRESH1}.c${THRESH1} |
awk 'BEGIN{ OFS = " "; }{ if( $1 >= thresh ){ print $2, $3, $1 } }' thresh=${THRESH2} |
cat > ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u

echo "The filtered file is in ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u"
echo "In order to build the association profiles for the targets, you may run:"
echo "  ./build_profiles ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u > ${INPUT}.profiles"
