#! /bin/sh
set -o nounset    # Using "$UNDEF" var raises error
set -o errexit    # Exit on error, do not continue quietly


usage_exit() { {
    echo "Usage: $(basename "$0") <csv-file>"
    echo "Input: a path to a CSV like 'mini.1.sim-th0.2'."
    echo "Output: a CSV sorted in columns 1 and 5, at stdout."
    exit 1
} 1>&2;
}

test "$#" -eq 0  && usage_exit
test "$1" = "-h"  && usage_exit


########################################

input_file="$1"

head -n 1 "$input_file"
tail -n +2 "$input_file" | sort -t " " -k 1,1 -k 5,5nr
