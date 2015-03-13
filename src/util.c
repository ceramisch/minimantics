#include <stdlib.h>
#include <stdio.h>
#include <glib-2.0/glib.h>
#include <string.h>
#include <pthread.h>
#include "util.h"

char *score_names[ N_SIM_SCORES ] = { "cosine", "wjaccard", "lin", "l1", "l2", 
                                      "jsd", "random", "askew", "askew" };
int score_types[ N_SIM_SCORES ] = { T_SIM, T_SIM, T_SIM, T_DIST, T_DIST, T_DIST, 
                                    T_RAND, T_DIST, T_DIST };
                                    
extern void usage();
int idc_symbol = 0;

/******************************************************************************/

FILE *open_file_read( char *filename ) {
  FILE *result = fopen( filename, "r" ); 
  if( !result ) {
    perra( "Error opening file %s\n", filename );
    usage();
  }
  return result;
}

/******************************************************************************/

GHashTable *read_word_list( char *filename ) {
  char *word = NULL, *copy_word;
  int read, len, *dummy = malloc( sizeof(int) );
  FILE *wordlist = open_file_read( filename );
  // fill x_filter hash, and affect in the end if opt is -t, -c or -n
  GHashTable *x_filter = g_hash_table_new_full( &g_str_hash, &g_str_equal, 
                                                free, NULL );
  while ( ( read = getline( &word, (size_t *)&len, wordlist ) ) != -1 ) {
    copy_word = malloc( sizeof( char ) * ( strlen( word ) + 1 ) );
    strcpy( copy_word, word );
    copy_word[ read - 1 ] = '\0'; // remove newline
    // The value in the map should never be used    
    g_hash_table_insert( x_filter, copy_word, dummy ); // dummy value != NULL  
  }
  free( word );
  free( dummy ); // freed here, value in hashmap never accessed
  return x_filter;
}

/******************************************************************************/

int should_keep( char *word, GHashTable *filter ) {
  return filter == NULL || g_hash_table_lookup( filter, word ) != NULL;
}

/******************************************************************************/

double parse_thresh_option( char *thresh, char opt_n ) {
  double result;
  if( !sscanf( thresh, "%lf", &result ) ) {
    perra( "Option -%c ignored. Must be a real value\n", opt_n );
  }
  else {
    perra( "Using threshold -%c = %lf.\n", opt_n, result );
  }
  return result;
}

/******************************************************************************/
/**
 * Very ugly character-level string manipulation. Allows to process files with
 * variable number of columns, as long as the assoc_name column is in place and
 * well formatted.
 * Check all headers, find the index of the selected assoc_name 
 */

int get_index_column_name( FILE *input, char *column_name ) {
  char header_name[ MAX_S + 1 ], c;
  int h_counter = 0, i = 0, column_index = -1;
  while( ( c = getc( input )) != '\n' ) {
    if( c == '\t' ) {
      header_name[ i ] = '\0';
      if( strcmp( header_name, column_name ) == 0 ){ 
        column_index = h_counter; 
        perra( "Using column named: %s\n", header_name );        
      }
      h_counter++;       
      i = 0;
    }
    else { header_name[ i++ ] = c; }
  }  
  header_name[ i ] = '\0'; // verifie le dernier
  if( strcmp( header_name, column_name ) == 0 ){ 
    column_index = h_counter; 
    perra( "Using column named: %s\n", header_name );        
  }
  return column_index;
}

/******************************************************************************/

int store_t_c( GHashTable *dict, char *t, int id_t, int id_c, double value ) {
  target_contexts *value_in_hash = g_hash_table_lookup( dict, &id_t );
  int *key;
  int new_added = 0;
  double *copy_value;
  if( ! value_in_hash ) {
    key = malloc( sizeof( int ) );
    *key = id_t;
    value_in_hash = malloc( sizeof( target_contexts ) ) ;
    value_in_hash->sum = 0.0;         // used to calculate lin & wjaccard    
    value_in_hash->sum_square = 0.0;  // used to calculate cosine    
    value_in_hash->target = malloc( ( strlen( t ) + 1 ) * sizeof( char ) );    
    strcpy( value_in_hash->target, t );
    value_in_hash->contexts = g_hash_table_new_full( &g_int_hash, &g_int_equal, 
                                                     free, free );
    g_hash_table_insert( dict, key, value_in_hash );
    new_added = 1;
  }
  key = malloc( sizeof( int ) );
  *key = id_c; 
  copy_value = malloc( sizeof( double ) );     
  *copy_value = value;
  value_in_hash->sum += value;    
  value_in_hash->sum_square += value * value;
  g_hash_table_insert( value_in_hash->contexts, key, copy_value );
  return new_added;
}


/******************************************************************************/

void destroy_word_count( gpointer wc ) {
  g_hash_table_destroy( ( ( word_count * )wc )->links );
  free( ( word_count * )wc );
}

/******************************************************************************/

void destroy_target_context( gpointer tc ) {
  g_hash_table_destroy( ( ( target_contexts * )tc )->contexts );
  free( ( ( target_contexts * )tc )->target );
  free( ( target_contexts * )tc );  
}

/******************************************************************************/

word_count *create_word_count( int id ) {
  word_count *result = malloc( sizeof( word_count ) );
  result->id = id;
  result->count = 0;
  result->entropy = ENTROPY_UNDEFINED;
  result->links = g_hash_table_new_full(&g_int_hash, &g_int_equal, NULL, free);
  return result;
}

/******************************************************************************/

int *get_id( GHashTable *symbols_dict, GHashTable *inv_symbols_dict, 
             char *entry_buff, int entry_len ){
  int *id = g_hash_table_lookup( symbols_dict, entry_buff );
  if( !id ) {
    char *entry = malloc( sizeof( char ) * ( entry_len + 1 ) );
    strcpy( entry, entry_buff );
    id = malloc( sizeof( int ) );
    *id = idc_symbol++;
    g_hash_table_insert( symbols_dict, entry, id );
    g_hash_table_insert( inv_symbols_dict, id, entry );    
  }
  return id;
} 

/******************************************************************************/

void insert_into_index( GHashTable *hash, GHashTable *symbols, 
                        GHashTable *inv_symbols, char *w1, char *w2, int lenw1,
                        int lenw2, double count, int *id_counter ) {
  int *idw1 = get_id( symbols, inv_symbols, w1, lenw1 );
  int *idw2 = get_id( symbols, inv_symbols, w2, lenw2 );  
  word_count *value_in_hash = g_hash_table_lookup( hash, idw1 );
  double *link_count = malloc( sizeof( double ) );
  if( ! value_in_hash ) {
    value_in_hash = create_word_count( (*id_counter)++ );
    g_hash_table_insert( hash, idw1, value_in_hash );
  }
  value_in_hash->count += count;
  *link_count = count;
  if( g_hash_table_lookup( value_in_hash->links, idw2 ) ) {
    perra( "Repeated entry! %s-%s\n", w1, w2 );    
  }
  g_hash_table_insert(value_in_hash->links, idw2, link_count);  
}

/******************************************************************************/

void run_multi_threaded( void *function, int nb_threads ) {
  int i;
  pthread_t *threadpool;
  perr( "Multi-threaded version\n" );
  threadpool = malloc( sizeof( pthread_t ) * nb_threads );
  for( i = 0; i < nb_threads; i++ ) {
    //fprintf( stderr, "Creating thread %d\n", i );  
    pthread_create( &threadpool[i], NULL, function, NULL );
  }
  for( i = 0; i < nb_threads; i++ ) {
    pthread_join( threadpool[i], NULL );
    //fprintf( stderr, "Finished thread %d\n", i );
  }
  free( threadpool );
}

/******************************************************************************/


