Minimalist distributional semantics
by Carlos Ramisch
Sept 11, 2014

Requires NLTK wordnet for evaluation
Requires GNU C compiler with pthreads support (standard in Linux)

We will run on example mini.1, containing verb-noun pairs as extracted from the
corpus, no filtering or counting, no sorting.

Does not support triple-based measures as standard Lin.

Running:

    # compile the programs
    make                        
  
    # Filter out verbs/nouns freq < 10, pairs freq < 2
    ./filterRaw.sh mini.1 10 2   
  
    # Calculate target-context association scores
    ./build_profiles mini.1.s.filter.t10.c10.tc2.u > mini.1.profiles
  
    # Find distributional neighbors (very fast, loads of options). Use -h for doc
    ./calculate_similarity -S 0.2 mini.1.profiles > mini.1.sim-th0.2
  
    # Evaluate based on Wordnet, Moby, Levin, etc.
    cut -d "\t" -f 1,2,3,4,5 mini.1.sim-th0.2 | tail -n +2 >  mini.1.sim-th0.2.cosine ./evalAll-perverb.sh mini.1.sim-th0.2.cosine # -> HAS BUGS
  
    # Generalize contexts of similar targets, get new pairs. Use -h for doc
    ./generalize -S 0.5 mini.1.sim-th0.2 mini.1.profiles -> NOT FINISHED


-----------------------

Minimantics also provides some scripts for evaluation of the output thesaurus:

    # Adding a "wordnet path_similarity" column
    ./minimantics-sort-output.sh mini.1.sim-th0.2 | head -n 100 | ./add_wnpath.py -k10 v >mini.1.wnpath
    
    # Eval and print averages for the 'wnpath' column
    cat mini.1.wnpath | ./csv_statistics.py 'wnpath' -d target --print-global
    
    # Taking a minimantics-style CSV and using the `cosine` field to solve TOEFL
    cat wbst-nanews.v.test | ./solve_toefl.py -a mini.1.sim-th0.2 'cosine'
    
    # Checking how TOEFL is being solved
    head wbst-nanews.v.test | ./solve_toefl.py -as mini.1.sim-th0.2 'cosine'
    
    # Seeing for which lines we have data in wbst-nanews.v.test
    cat wbst-nanews.v.test | ./solve_toefl.py -s mini.1.sim-th0.2 'cosine' | grep $'\t[^?]'
