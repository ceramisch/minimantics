#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: sh $0 <raw-triples-file> <threshold-words> <threshold-pairs>"
    exit
fi

INPUT=$1
THRESH1=$2 # typically 50-100
THRESH2=$3 # typically 2-5

echo "Filtering, sorting and uniquing raw triples in ${INPUT}"

awk '{print $1}' $INPUT | LC_ALL=C sort | uniq -c > ${INPUT}.targets
awk '{print $2}' ${INPUT} | LC_ALL=C sort | uniq -c > ${INPUT}.contexts

#echo "No filter"
#wc gigaword.verbs
#wc gigaword.objects

for file in ${INPUT}.targets ${INPUT}.contexts; do
  cat $file |  awk '{ if( $1 > thresh && $2 ~ /^[a-zA-Z-]+$/ && length($2) > 1) print $2; }' thresh=${THRESH1} > $file.filter${THRESH1}
done

#python /storage/raid1/homedirs/alexis.nasr/lexem/src/filter.py ${INPUT}.targets ${THRESH1} > ${INPUT}.targets.filter${THRESH1}
#python /storage/raid1/homedirs/alexis.nasr/lexem/src/filter.py ${INPUT}.contexts ${THRESH1} > ${INPUT}.contexts.filter${THRESH1}

#echo "Filter 100"
#wc gigaword.verbs.filter100
#wc gigaword.objects.filter100

echo "Sorting raw triples..."
LC_ALL=C sort ${INPUT} > ${INPUT}.s


echo "Joining"
# First select only triples containing verbs from the filtered list
LC_ALL=C join -1 1 -2 1 ${INPUT}.s ${INPUT}.targets.filter${THRESH1} | 
# Then sort in object order
LC_ALL=C sort -k 2 | 
# and filter keeping only triples whose objects are in the filtered list
LC_ALL=C join -1 2 -2 1 -o "1.1 1.2" - ${INPUT}.contexts.filter${THRESH1} | 
# and sort again in verb order so that we can uniq afterwards
LC_ALL=C sort |
cat > ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}

echo "Uniquing and counting"
uniq -c ${INPUT}.s.filter.t${THRESH1}.c${THRESH1} |
awk 'BEGIN{ OFS = " "; }{ if( $1 >= thresh ){ print $2, $3, $1 } }' thresh=${THRESH2} |
cat > ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u

echo "The filtered file is in ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u"
echo "In order to build the association profiles for the targets, you may run:"
echo "  ./build_profiles ${INPUT}.s.filter.t${THRESH1}.c${THRESH1}.tc${THRESH2}.u > ${INPUT}.profiles"
