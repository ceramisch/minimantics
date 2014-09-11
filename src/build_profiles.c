#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <glib-2.0/glib.h>
#include <string.h>
#include "util.h"

#define DEFAULT_NUMBER_THREADS 1

GHashTable *t_dict;
GHashTable *c_dict;
double n_pairs = 0.0; // sums of all values in the hashmaps
int idc_t = 0; // identifiers, will be incremented for each new element
int idc_c = 0;
GHashTableIter iter_t;
pthread_mutex_t iter_mutex = PTHREAD_MUTEX_INITIALIZER;
int nb_threads = DEFAULT_NUMBER_THREADS, pair_counter = 0;
int finish = FALSE; 

/******************************************************************************/

void usage() {
  fprintf( stderr, "Usage: ./build_profiles <triples-file>\n" );  
  fprintf( stderr, "Please, provide a file containing the tripes\n" );
  fprintf( stderr, "One triple per line, \"target   context   count\"\n" );
  fprintf( stderr, "With TAB between the elements\n" ); 
  exit( -1 );
}

/******************************************************************************
 * Reads the input file and inserts all values in appropriate hashmaps
 * @param filename String containing the name of the file. The file must contain
 * triples in the form "target context count", space-separated.
 ******************************************************************************/

void read_input_file( char *filename ) {
  FILE *input = open_file_read( filename );
  char *target, *context;
  int r;
  double count;  
  t_dict = g_hash_table_new_full( &g_str_hash, &g_str_equal, 
           NULL, destroy_word_count );
  c_dict = g_hash_table_new_full( &g_str_hash, &g_str_equal, 
           NULL, destroy_word_count );
  while( !feof( input ) ) {
    target = malloc( (MAX_S + 1) * sizeof( char ) );
    context = malloc( (MAX_S + 1) * sizeof( char ) );
    r = fscanf( input, "%s\t%s\t%lf", target, context, &count );
    if( r == 3 && !feof( input ) ) {       
      insert_into_index( t_dict, target, context, count, &idc_t );
      insert_into_index( c_dict, context, target, count, &idc_c );
      n_pairs += count; // was being calculated twice. Bug?      
    }
    else { // buffers unused, can be freed
      free( target );
      free( context );
    }
  } 
  fclose( input );
}

/******************************************************************************/

double expected( double cw1, double cw2, double n ) {
  return ( cw1 * cw2 ) / n;
}

/******************************************************************************
 * Calculate and print many association measures for a pair w1=target w2=context
 ******************************************************************************/

void calculate_and_print_am( char *w1, int idw1, char *w2, int idw2, 
                             double cw1w2, double cw1, double cw2, 
                             double t_entropy, double c_entropy ) {
  int cw1nw2 = cw1 - cw1w2,
      cnw1w2 = cw2 - cw1w2,
      cnw1nw2 = n_pairs - cw1 - cw2 + cw1w2;                             
  double ew1w2   = expected( cw1, cw2, n_pairs ),
         ew1nw2  = expected( cw1, n_pairs - cw2, n_pairs ),
         enw1w2  = expected( n_pairs - cw1, cw2, n_pairs ),
         enw1nw2 = expected( n_pairs - cw1, n_pairs - cw2, n_pairs );
  double am_cp = cw1w2 / (double)cw1,
         am_pmi = log( cw1w2 ) - log( ew1w2 ),
         am_npmi = am_pmi / ( log( n_pairs) - log( cw1w2) ),
         am_lmi = cw1w2 * am_pmi,
         am_dice = ( 2.0 * cw1w2 ) / ( cw1 + cw2 ),
         am_tscore = (cw1w2 - ew1w2 ) / sqrt( cw1w2 ),
         am_zscore = (cw1w2 - ew1w2 ) / sqrt( ew1w2 ),
         am_chisquare = pow( cw1w2   - ew1w2  , 2 ) / ew1w2   +
                        pow( cw1nw2  - ew1nw2 , 2 ) / ew1nw2  +
                        pow( cnw1w2  - enw1w2 , 2 ) / enw1w2  +
                        pow( cnw1nw2 - enw1nw2, 2 ) / enw1nw2 ,
         am_loglike = 2.0 * ( PRODLOG( cw1w2  , cw1w2   / ew1w2   ) +
                              PRODLOG( cw1nw2 , cw1nw2  / ew1nw2  ) +
                              PRODLOG( cnw1w2 , cnw1w2  / enw1w2  ) +
                              PRODLOG( cnw1nw2, cnw1nw2 / enw1nw2 ) );
  printf( "%s\t%d\t%s\t%d\t%.2lf\t%.2lf\t%.2lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\t%lf\n", 
          w1, idw1, w2, idw2, cw1w2, cw1, cw2, am_cp, am_pmi, am_npmi, am_lmi, am_tscore, 
          am_zscore, am_dice , am_chisquare, am_loglike, t_entropy, c_entropy );
}

/******************************************************************************/

double calculate_entropy( double total, GHashTable *distribution ) {
  double entropy = 0.0;
  GHashTableIter iter_d;
  gpointer value_d;
  double p;
  g_hash_table_iter_init( &iter_d, distribution );
  while( g_hash_table_iter_next( &iter_d, NULL, &value_d ) ){
    p = *((double *)value_d) / total;
    entropy -= p * log( p );
  }
  return entropy;
}

/******************************************************************************/

void update_count() {
  int p;
  if( pair_counter % 100 == 0 ) {
    p = (int)( (100.0 * pair_counter) / n_pairs );
    fprintf( stderr, "Processing target: %d (%d%%)\n", pair_counter, p );
  }
  pair_counter++;
}

/******************************************************************************/

void calculate_ams_all_serial( word_count *casted_t, gpointer key_t ) {
  double count_t_c;
  gpointer key_c, value_t_c;    
  word_count *casted_c;  
  GHashTableIter iter_c;  
  g_hash_table_iter_init( &iter_c, casted_t->links );
  casted_t->entropy = calculate_entropy(casted_t->count, casted_t->links);
  while( g_hash_table_iter_next( &iter_c, &key_c, &value_t_c ) ){
    casted_c = g_hash_table_lookup( c_dict, key_c );
    count_t_c = *((double *)value_t_c);             
    calculate_and_print_am( (char *)key_t, casted_t->id, (char *)key_c, 
                      casted_c->id, count_t_c, casted_t->count, casted_c->count, 
                      casted_t->entropy, casted_c->entropy );
  }
}
/******************************************************************************/

void *calculate_ams_all() {
  int stop = FALSE;
  gpointer value_t, key_t;
  while( TRUE ) {
    pthread_mutex_lock( &iter_mutex );  
    if( !finish && g_hash_table_iter_next( &iter_t, &key_t, &value_t ) ){
      update_count();
    }
    else {  stop = TRUE; finish=TRUE; }
    pthread_mutex_unlock( &iter_mutex );  
    if( stop ) { break; }
    calculate_ams_all_serial( (word_count *)value_t, key_t );
  }
  return NULL;
}

/******************************************************************************/

int main( int argc, char *argv[] ) {
  word_count *casted_c;
  GHashTableIter iter_c;    
  gpointer key_c, value_t_c, value_t, key_t;  
  if( argc != 2 ) { usage(); }
  fprintf( stderr, "Reading input file into hashmap...\n" );
  read_input_file( argv[1] );  
  // File header
  perr( "Calculating association scores...\n" );
  printf( "target\tid_target\tcontext\tid_context\tf_tc\tf_t\tf_c\t" );
  printf( "cond_prob\tpmi\tnpmi\tlmi\ttscore\tzscore\tdice\tchisquare\t" );
  printf( "loglike\tentropy_target\tentropy_context\n" );
  // First calculate all entropies for 
  g_hash_table_iter_init( &iter_c, c_dict );
  while( g_hash_table_iter_next( &iter_c, &key_c, &value_t_c ) ){
    casted_c = g_hash_table_lookup( c_dict, key_c );
    casted_c->entropy = calculate_entropy(casted_c->count, casted_c->links);      
  }
  g_hash_table_iter_init( &iter_t, t_dict );
  if( nb_threads > 1 ) {
    run_multi_threaded( &calculate_ams_all, nb_threads );
  }
  else {
    while( g_hash_table_iter_next( &iter_t, &key_t, &value_t ) ){
      calculate_ams_all_serial( (word_count *)value_t, key_t );
      update_count();
    }
  }
  // Clean and free to avoid memory leaks
  perr( "Finished, cleaning up...\n" );
  g_hash_table_destroy( c_dict );
  g_hash_table_destroy( t_dict );
  fprintf( stderr, "Number of targets: %d\n", idc_t );
  fprintf( stderr, "Number of contexts: %d\n", idc_c );
  //fprintf( stderr, "You can now calculate similarities with command below\n");
  //fprintf( stderr, "  ./calculate_similarity [OPTIONS] <out-file>\n\n" );
  return 0;
}

/******************************************************************************/
