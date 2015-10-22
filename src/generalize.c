/*
 * minimantics: minimalist tool for count-based distributional semantic models
 *
 *    Copyright (C) 2015  Carlos Ramisch, Silvio Ricardo Cordeiro
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
 
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <getopt.h>
#include <glib-2.0/glib.h>
#include <string.h>
#include <pthread.h>
#include "util.h"

#define DEFAULT_NUMBER_THREADS 1

char score_name[50] = "cosine";
double sim_thresh = UNDEFINED;
double dist_thresh = -UNDEFINED;
int sim_thresh_def = FALSE, dist_thresh_def = FALSE, print_originals = FALSE;
GHashTable *t_filter = NULL, *n_filter = NULL, *c_filter = NULL;
GHashTable *c_dict; // int -> char *
GHashTable *t_dict; // char *target -> struct target_contexts
int idc_c = 0; // identifiers, will be incremented for each new element
pthread_mutex_t iter_mutex = PTHREAD_MUTEX_INITIALIZER;
int nb_threads = DEFAULT_NUMBER_THREADS;
FILE *sim_file;
int sim_index, nb_lines = 0;

/******************************************************************************/

void usage() {
  perr( "Usage:\n\n" );
  perr( "\033[1m./generalize\033[0m [\033[4mOPTIONS\033[0m] \033[4mSIM-FILE\033[0m \033[4mPROFILE-FILE\033[0m\n\n" );
  perr( "Generates new target-context pairs based on similar targets.\n\n" );
  perr( "\033[4mSIM-FILE\033[0m is the output of \"calculate_similarities\", that is, a TAB-separated\n" );
  perr( "list of target pairs and their similarity and distance scores. \033[4mPROFILE-FILE\033[0m is\n" );
  perr( "the output of \"build_profiles\", that is, a TAB-separated list of target-context\n" );
  perr( "pairs and their association scores. The output a list of new target-context\n" );
  perr( "pairs whose counts are estimated from the \033[4mSIM-FILE\033[0m, but which were never\n" );
  perr( "actually observed in \033[4mPROFILE-FILE\033[0m.\n\n" );
  perr( "\033[1mOPTIONS\033[0m :\n\n" );
  perr( "\033[1m-s \033[0m\033[4mSIM-SCORE\033[0m\033[1m, --score=\033[0m\033[4mSIM-SCORE\033[0m\n" );
  perr( "  The option argument \033[4mSIM-SCORE\033[0m specifies the name of the similarity or distance\n" );
  perr( "  score to use, as defined in the header of the \033[4mSIM-FILE\033[0m. Must denote an\n" ); 
  perr( "  existing column name, whose values are real numbers. By default, \"cosine\" is\n  used.\n\n" );
  perr( "\033[1m-t \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --targets=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  perr( "\033[1m-n \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --neighbors=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  perr( "\033[1m-c \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --contexts=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  perr( "  The option argument \033[4mWORDS-FILE\033[0m is the filename of the list of target, neighbor\n" );
  perr( "  or context words which will be taken into consideration to generalize target-\n" );
  perr( "  context pairs. The file should contain the words, one per line, using the same\n" );
  perr( "  encoding and conventions as in \033[4mSIM-FILE\033[0m and \033[4mPROFILE-FILE\033[0m. By default, all\n" );
  perr( "  words in 1st column of \033[4mSIM-FILE\033[0m are considered as targets, all words in 3rd\n" );
  perr( "  column of \033[4mSIM-FILE\033[0m are considered as neighbors, and all words in 3rd column of\n" );
  perr( "  \033[4mPROFILE-FILE\033[0m are considered as contexts.\n\n" );
  perr( "\033[1m-S \033[0m\033[4mTHRESHOLD\033[0m\033[1m, --sim-thresh=\033[0m\033[4mTHRESHOLD\033[0m\n" );
  perr( "\033[1m-D \033[0m\033[4mTHRESHOLD\033[0m\033[1m, --dist-thresh=\033[0m\033[4mTHRESHOLD\033[0m\n" );
  perr( "  Use the specified \033[4mTHRESHOLD\033[0m value: \033[1m-S\033[0m does not generalize if similarity score\n" );
  perr( "  is lower than \033[4mTHRESHOLD\033[0m, or \033[1m-D\033[0m does not generalize if distance score is higher\n" );
  perr( "  than \033[4mTHRESHOLD\033[0m. Default value is -999999 for \033[1m-S\033[0m, +999999 for \033[1m-D\033[0m. ONLY ONE OF\n" );
  perr( "  THESE OPTIONS CAN BE DEFINED, NOT BOTH.\n\n" );
  perr( "\033[1m-T \033[0m\033[4mNB-THREADS\033[0m\033[1m, --threads=\033[0m\033[4mNB-THREADS\033[0m\n" );
  perr( "  Run \033[4mNB-THREADS\033[0m simultaneous threads. Each thread calculates the set of\n" );
  perr( "  similarities with all possible neighbors for a given target. This value is\n" );
  perr( "  usually equal to the number of processors in the machine. The value of\n" );
  perr( "  \033[4mNB-THREADS\033[0m must be a positive integer, that is, at least 1 thread. This option\n" );
  perr( "  can significantly speed up calculations, but also will use the processor\n" );
  perr( "  intensively. The memory overhead for multiple threads is neglectable. Default\n" );
  perr( "  value is 1.\n\n" );   
  perr( "\033[1m-o, --originals\033[0m\n" );
  perr( "  In addition to the new pairs, also output the original ones.\n\n" );
  perr( "\033[1m-h, --help\033[0m\n" );
  perr( "  Display this help message\n\n" );
  exit( -1 );
}

/*****************************************************************************/

void read_profiles_file( char *filename ) {
  FILE *input = open_file_read( filename );
  char *target; 
  char *context;
  double count;  
  int idc, idt, r_read, nb_l = 2, *idc_copy;
  t_dict = g_hash_table_new_full( &g_str_hash, &g_str_equal, free,
           destroy_target_context );
  c_dict = g_hash_table_new_full( &g_str_hash, &g_str_equal, 
           free, free );
  while( !feof( input ) && getc( input ) != '\n' ){ /* read-ignore header */ }
  while( !feof( input ) ) {
    target = malloc( (MAX_S + 1) * sizeof( char ) );
    context = malloc( (MAX_S + 1) * sizeof( char ) );
    r_read = fscanf( input, "%s\t%d\t%s\t%d\t%lf", target, &idt, context, 
                                                   &idc, &count );
    if( r_read == 5 ) {
      if( print_originals ) {     
        printf( "%s\t%s\t%lf\n", target, context, count );
      }      
      if( g_hash_table_lookup( c_dict, &idc ) == NULL ) {
        idc_copy = malloc( sizeof( int ) );
        *idc_copy = idc;
        g_hash_table_insert( c_dict, idc_copy, context );
      }
      
      store_t_c( t_dict, target, idt, idc, count );
    }
    else { // buffers unused, can be freed
      free( target );
      free( context );
      if( r_read != -1 ) { // EOF
        fprintf( stderr, "WARNING: profiles may be corrupted line %d\n", nb_l );
        break; // stop reading the file, there was an error or file ended
      }
    }
    while( getc(input) != '\n' && !feof(input) ){ /*read-ignore rest of line*/ }
    nb_l++;
  }    
  fclose( input );
}

/******************************************************************************/

void generalize( char *t, char *n, int id_t, int id_n, double score ) {
  target_contexts *tc_t, *tc_n;
  GHashTableIter iter_t;
  gpointer idc, value_t1, value_t2;
  double norm;
  char *c;
  tc_t = g_hash_table_lookup( t_dict, &id_t );
  tc_n = g_hash_table_lookup( t_dict, &id_n );
  if( tc_t->sum > tc_n->sum ) { // target is more frequent than neighbor
    norm = tc_n->sum / tc_t->sum;
    g_hash_table_iter_init( &iter_t, tc_t->contexts );
    while( g_hash_table_iter_next( &iter_t, &idc, &value_t1 ) ){
      value_t2 = g_hash_table_lookup( tc_n->contexts, idc );
      if( !value_t2 ) { // The context is not shared by both targets
        c = (char *)g_hash_table_lookup( c_dict, idc );
        if( should_keep( c, c_filter ) ) {
          printf( "%s\t%s\t%lf\n", n, c, norm * *((double *)value_t1) );
        }
      }      
    }
  }
}

/****************************************************************************/

int read_a_pair( char *t, int *id_t, char *n, int *id_n, double *score ) {
  char entry[ MAX_S + 1 ], c;
  int r_read = 0, i = 0, n_tab = 3;
  if( !feof( sim_file ) ) {  
    r_read = fscanf( sim_file, "%s\t%d\t%s\t%d", t, id_t, n, id_n );
    while( !feof(sim_file) && n_tab != sim_index ){ //read-ignore till sim_index
      if( getc(sim_file) == '\t' ) { 
        n_tab++; 
      }
    }
    // read till the end of the field and store string in entry
    while( (c = getc(sim_file)) != '\t' && c != '\n' && !feof(sim_file) ) {      
      entry[ i++ ] = c;
    }
    entry[ i ] = '\0';
    r_read += sscanf( entry, "%lf", score ); // convert to double
    while(getc(sim_file) != '\n' && !feof(sim_file)){/*read-ignore rest line*/}
  }
  nb_lines++;
  if( nb_lines % 1000 == 0 ) {
    fprintf( stderr, "Processing pair: %d\n", nb_lines );
  }
  return r_read == 5;
}
/****************************************************************************/
// Line was correctly read, sim not too low/high, target to be considered,
// neighbor to be considered => generalize it! 
int should_generalize( char *t, char *n, double score ) {
  return should_keep( t, t_filter ) && should_keep( n, n_filter ) &&
         ( ( sim_thresh_def  && score >= sim_thresh ) ||
           ( dist_thresh_def && score <= dist_thresh) );
}    
          
/****************************************************************************/

void *read_sim_and_generalize() {
  int id_t, id_n, stop = FALSE;
  char t[ MAX_S + 1 ], n[ MAX_S + 1 ];
  double score;  
  while( TRUE ) {
      pthread_mutex_lock( &iter_mutex );    
      if( ! read_a_pair( t, &id_t, n, &id_n, &score ) ) { stop = TRUE; }
      pthread_mutex_unlock( &iter_mutex );  
      if( stop ) { break; }  
      else if ( should_generalize( t,n,score) ) {
        generalize( t, n, id_t, id_n, score );
      }
  }
  if( !feof( sim_file ) ){ // Something went wrong and was not EOF
    fprintf( stderr, "ERROR: Format problem at line %d.\n", nb_lines );
  }  
  return NULL;
}

/****************************************************************************/

void read_sim_and_generalize_serial() {
  int id_t, id_n;
  char t[ MAX_S + 1 ], n[ MAX_S + 1 ];
  double score;  
  while( read_a_pair( t, &id_t, n, &id_n, &score ) ) {            
      // Line was correctly read, sim not too low/high, target to be considered,
      // neighbor to be considered => generalize it!    
      if ( should_generalize( t,n,score) ) {
        generalize( t, n, id_t, id_n, score );
      }
  }
  if( !feof( sim_file ) ){ // Something went wrong and was not EOF
    fprintf( stderr, "ERROR: Format problem at line %d.\n", nb_lines );
  }  
}

/****************************************************************************/

int treat_options( int argc, char *argv[] ) {
  char opt;
  int o_ptr;
  struct option longopts[] = {
    {"score", required_argument, 0, 's'},
    {"targets", required_argument, 0, 't'},
    {"neighbors", required_argument, 0, 'n'},
    {"contexts", required_argument, 0, 'c'},
    {"sim-threshold", required_argument, 0, 'S'},
    {"dist-threshold", required_argument, 0, 'D'},
    {"originals", no_argument, 0, 'o'},
    {"threads", required_argument, 0, 'T'},        
    {"help", no_argument, 0, 'h'}
  };
  char *shortopts = "s:t:n:c:S:D:T:oh";
  while ((opt = getopt_long (argc, argv, shortopts, longopts, &o_ptr)) != -1) {
    switch( opt ) {
      case 's' :
        strcpy( score_name, optarg );      
        break;
      case 't' :
        t_filter = read_word_list( optarg );
        break;
      case 'n' :
        n_filter = read_word_list( optarg );
        break;
      case 'c' :
        c_filter = read_word_list( optarg );        
        break;      
      case 'S' :
        sim_thresh = parse_thresh_option( optarg, opt );
        sim_thresh_def = TRUE;
        break;
      case 'D' :
        dist_thresh = parse_thresh_option( optarg, opt );
        dist_thresh_def = TRUE;        
        break;
      case 'T' :
        if( sscanf( optarg, "%d", &nb_threads ) != 1 || nb_threads < 1 ) {
          fprintf( stderr, "Option -T requires positive integer: %s\n", optarg);      
          usage();
        }
        break;          
      case 'o' :
        fprintf( stderr, "Will output original pairs\n" );
        print_originals = TRUE;
        break;
      case 'h' :
        usage();
        break;
      default:
        fprintf( stderr, "Unrecognized option: %c\n", opt );
        usage();
    }
    if( sim_thresh_def && dist_thresh_def ) {
      perr( "ERROR: Only one of -D or -S can be specified!\n" );
      usage();
    }
  }
  return optind;
}
/****************************************************************************/

int main( int argc, char *argv[] ) {  
  int argindex = treat_options( argc, argv );
  if( argindex != argc - 2 ){
    perr( "You must provide two filenames as arguments\n" );
    usage();
  }
  perr( "Reading input profiles into hashmap...\n" );
  read_profiles_file( argv[ argindex + 1 ] );  
  perr( "Generalizing...\n" );
  sim_file = open_file_read( argv[ argindex ] );
  sim_index = get_index_column_name( sim_file, score_name );
  if( sim_index < 4 ) {
    fprintf( stderr, "Column named \"%s\" not found!\nYou must ", score_name );
    perr( "specify a valid -s option. Chose among SIM-FILE column headers.\n");
    perr( "Remember that the 1st 4 fields cannot be used as scores.\n" ); 
    usage();  
  }
  if( nb_threads > 1 ) {
    run_multi_threaded( &read_sim_and_generalize, nb_threads );    
  }
  else {
    perr( "Not using threads\n" );
    read_sim_and_generalize_serial();
  }
  // Clean and free to avoid memory leaks
  perr( "Finished, cleaning up...\n" );
  fclose( sim_file );
  g_hash_table_destroy( c_dict );  
  g_hash_table_destroy( t_dict );
  if( t_filter ) {
    g_hash_table_destroy( t_filter );
  }
  if( n_filter ) {
    g_hash_table_destroy( n_filter );
  }
  if( c_filter ) {
    g_hash_table_destroy( c_filter );
  }
  return 0;
}
