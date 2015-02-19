#ifndef LEXEM_UTIL_H
#define LEXEM_UTIL_H

#include <stdio.h>
#include <glib-2.0/glib.h>

#define MAX_S 50 // Maximum length of a word

#define PRODLOG(a,b) a != 0 ? a * log(b) : 0 // avoids calculating log(0) in LL
#define perr( a ) fprintf( stderr, a ) // print to stderr
#define perra( a, ... ) fprintf( stderr, a, __VA_ARGS__ ) // same + arguments
#define N_SIM_SCORES 9 // Number of calculated similarity/distance scores
// Score types: similarity or distance?
#define T_SIM 0
#define T_DIST 1
#define T_RAND 2 // random is neither
#define UNDEFINED -999999 // an assoc. or sim. score will probably never be 
                          // below this value. This is not 100% safe but will
                          // most probably work.
#define ENTROPY_UNDEFINED -1                          


/**** USEFUL SHARED DATA STRUCTURES ****/

extern char *score_names[ N_SIM_SCORES ];
extern int score_types[ N_SIM_SCORES ];

typedef enum { cosine, wjaccard, lin, l1, l2, jsd, randomic,
               askew1, askew2 } t_scores;

typedef struct _target_contexts {
//  int id_t;
  char *target;
  GHashTable *contexts;
  double sum_square;
  double sum;
} target_contexts;

typedef struct _word_count {
  int id;
  double count;
  GHashTable *links;
  double entropy;
} word_count;

/**** USEFUL SHARED FUNCTIONS ****/

FILE *open_file_read( char *filename );
GHashTable *read_word_list( char *filename );
int should_keep( char *word, GHashTable *filter );
double parse_thresh_option( char *thresh, char opt_n );
int get_index_column_name( FILE *input, char *column_name );
int store_t_c( GHashTable *dict, char *t, int id_t, int id_c, double value );
void destroy_word_count( gpointer wc );
void destroy_target_context( gpointer tc );
void insert_into_index( GHashTable *hash, char *w1, char *w2, double count, 
                        int *id_counter );
void run_multi_threaded( void *function, int nb_threads );  



#endif
