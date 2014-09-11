#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <getopt.h>
#include <glib-2.0/glib.h>
#include <string.h>
#include <pthread.h>
#include "util.h"
                        
#define ALPHA 0.99        // Smoothing factors for a-skewness measure
#define NALPHA 0.01
#define DEFAULT_NUMBER_THREADS 8

// ABORTED: normalization is not possible as max must be calculated and only on
// a second pass distances can be inverted and normalized
//double max_l1 = UNDEFINED, max_l2 = UNDEFINED, max_askew1 = UNDEFINED,
//       max_askew2 = UNDEFINED, max_jsd = UNDEFINED; // normalization factors
GHashTable *t_dict = NULL; // (char *, id_contexts( int, GHashTable *))
int n_targets = 0;
int warned_rel_entropy = FALSE;
int calculate_distances = TRUE;
//int inverse_distances = FALSE;
char assoc_name[30] = "cond_prob"; // by default use cond_prob association score
double sim_thresh = UNDEFINED;     // by default does not remove anything
double assoc_thresh = UNDEFINED;   // by default does not remove anything
double dist_thresh = -UNDEFINED;   // by default does not remove anything
t_scores sim_scores[ N_SIM_SCORES ];
GHashTable *t_filter = NULL, *n_filter = NULL, *c_filter = NULL;
GList *iter_t1;
GList *target_ids = NULL;
pthread_mutex_t iter_mutex = PTHREAD_MUTEX_INITIALIZER;
int nb_threads = DEFAULT_NUMBER_THREADS;
int target_counter = 0;

/******************************************************************************/

void usage() {
  fprintf( stderr, "Usage:\n\n" );
  fprintf( stderr, "\033[1m./calculate_similarity\033[0m [\033[4mOPTIONS\033[0m] \033[4mIN-FILE\033[0m\n\n" );
  fprintf( stderr, "Calculates several similarity and distance measures based on distributional\nprofiles of context words. " );
  fprintf( stderr, "The input file \033[4mIN-FILE\033[0m is the output of the \n\"build_profiles\" program. The output is a list of context-neighbor pairs and\nthe corresponding similarity and distance scores. The output is not sorted.\n\n" );
  fprintf( stderr, "\033[1mOPTIONS\033[0m :\n\n" );
  fprintf( stderr, "\033[1m-a \033[0m\033[4mASSOC-SCORE\033[0m\033[1m, --association=\033[0m\033[4mASSOC-SCORE\033[0m\n" );
  fprintf( stderr, "  The option argument \033[4mASSOC-SCORE\033[0m specifies the name of the association scores\n" );
  fprintf( stderr, "  to use, as defined in the header of the \033[4mIN-FILE\033[0m. Must denote an existing\n" ); 
  fprintf( stderr, "  column name, whose values are real numbers. By default, \"cond_prob\" is used.\n\n" );  
  fprintf( stderr, "\033[1m-s \033[0m\033[4mSCORE-LIST\033[0m\033[1m, --scores=\033[0m\033[4mSCORE-LIST\033[0m\n" );
  fprintf( stderr, "  The option argument \33[4mSCORE-LIST\033[0m specifies a list of similarity and distance\n" );
  fprintf( stderr, "  score names that should be calculated. It is possible to specify multiple\n" );
  fprintf( stderr, "  similarity and distance scores at the same time by using a colon-separated\n" );
  fprintf( stderr, "  list, for instance:\"--similarity lin:cosine:jsd\" will calculate Lin's, cosine\n" );
  fprintf( stderr, "  and Jensen-Shannon scores. Available score names are: \n" );
  fprintf( stderr, "   * \033[1mcosine\033[0m: Cosine, similarity ∈ [-1..1]\n" );
  fprintf( stderr, "   * \033[1mwjaccard\033[0m: weighted Jaccard index, similarity ∈ [-1..1]\n" );
  fprintf( stderr, "   * \033[1mlin\033[0m: Lin's 1998 measure, similarity ∈ [-1..1]\n" );
  fprintf( stderr, "   * \033[1ml1\033[0m: L1 norm or Manhattan, distance ∈ [0..+∞]\n" );
  fprintf( stderr, "   * \033[1ml2\033[0m: L2 norm or Euclidean, distance ∈ [0..+∞]\n" );
  fprintf( stderr, "   * \033[1maskew\033[0m: α-skewness or smoothed Kullback-Leibler, asym. distance ∈ [0..+∞]\n" );
  fprintf( stderr, "   * \033[1mjsd\033[0m: Jensen-Shannon divergence, distance ∈ [0..1]\n" );
  fprintf( stderr, "   * \033[1mrandom\033[0m: random number ∈ [0..1]\n" );
  fprintf( stderr, "  Please remember that cosine, wjaccard and lin are similarity scores while l1,\n" );
  fprintf( stderr, "  l2, jsd and askew are distance scores. By default, all scores are calculated.\n\n" );
  // It is recommended to use option \033[1m-d\033[0m, to\n" );
//  fprintf( stderr, "  reverse distance scores in order to obtain equivalent similarity scores." );
  fprintf( stderr, "\033[1m-t \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --targets=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  fprintf( stderr, "\033[1m-n \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --neighbors=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  fprintf( stderr, "\033[1m-c \033[0m\033[4mWORDS-FILE\033[0m\033[1m, --contexts=\033[0m\033[4mWORDS-FILE\033[0m\n" );
  fprintf( stderr, "  The option argument \033[4mWORDS-FILE\033[0m is the filename of the list of target, neighbor\n" );
  fprintf( stderr, "  or context words which will be taken into consideration to calculate\n" );
  fprintf( stderr, "  similarities and distances. The file should contain the words, one per line,\n" );
  fprintf( stderr, "  using the same encoding and conventions as in the \033[4mIN-FILE\033[0m. By default, all\n" );
  fprintf( stderr, "  words in 1st column of \033[4mIN-FILE\033[0m are considered as targets and neighbors,\n" );
  fprintf( stderr, "  and all words in 3rd column of \033[4mIN-FILE\033[0m are considered as contexts.\n\n" );
  fprintf( stderr, "\033[1m-A \033[0m\033[4mTHRESHOLD\033[0m\033[1m, --assoc-thresh=\033[0m\033[4mTHRESHOLD\033[0m\n" );
  fprintf( stderr, "\033[1m-S \033[0m\033[4mTHRESHOLD\033[0m\033[1m, --sim-thresh=\033[0m\033[4mTHRESHOLD\033[0m\n" );
  fprintf( stderr, "\033[1m-D \033[0m\033[4mTHRESHOLD\033[0m\033[1m, --dist-thresh=\033[0m\033[4mTHRESHOLD\033[0m\n" );
  fprintf( stderr, "  Use the specified \033[4mTHRESHOLD\033[0m value: \033[1m-A\033[0m to filter out contexts whose association\n" );
  fprintf( stderr, "  score with the target is lower than \033[4mTHRESHOLD\033[0m, or \033[1m-S\033[0m to filter out neighbors\n" );
  fprintf( stderr, "  whose similarity score with the target is lower than \033[4mTHRESHOLD\033[0m, or \033[1m-D\033[0m to\n" );
  fprintf( stderr, "  filter out neighbors whose distance score with the score is higher than\n" );
  fprintf( stderr, "  \033[4mTHRESHOLD\033[0m. When calculating multiple similarity and distance scores, a target-\n" );
  fprintf( stderr, "  neighbor pair is filtered out if one of the scores is below (similarity) or\n" );
  fprintf( stderr, "  above (distance) the thresholds. If all scores are above (resp. below) the\n" );
  fprintf( stderr, "  threshold, the pair is printed out.  Default value is -999999 for \033[1m-A\033[0m and \033[1m-S\033[0m,\n" );
  fprintf( stderr, "  +999999 for \033[1m-D\033[0m.\n\n" );
  fprintf( stderr, "\033[1m-T \033[0m\033[4mNB-THREADS\033[0m\033[1m, --threads=\033[0m\033[4mNB-THREADS\033[0m\n" );
  fprintf( stderr, "  Run \033[4mNB-THREADS\033[0m simultaneous threads. Each thread calculates the set of\n" );
  fprintf( stderr, "  similarities with all possible neighbors for a given target. This value is\n" );
  fprintf( stderr, "  usually equal to the number of processors in the machine. The value of\n" );
  fprintf( stderr, "  \033[4mNB-THREADS\033[0m must be a positive integer, that is, at least 1 thread. This option\n" );
  fprintf( stderr, "  can significantly speed up calculations, but also will use the processor\n" );
  fprintf( stderr, "  intensively. The memory overhead for multiple threads is neglectable. Default\n" );
  fprintf( stderr, "  value is 8.\n\n" ); 
//  fprintf( stderr, "\033[1m-d, --distance\033[0m\n" );
//  fprintf( stderr, "  Convert all distance scores into similarities. That is, instead of l1, l2,\n" ); 
//  fprintf( stderr, "  askew and jsd, print the inverse of the scores. If m is the maximum value of\n" );
//  fprintf( stderr, "  of distance d, the resulting similarity s ∈ [0..1] is obtained by calculating \n" );
//  fprintf( stderr, "  s = (m - d)/m. Default false.\n\n" );
  fprintf( stderr, "\033[1m-h, --help\033[0m\n" );
  fprintf( stderr, "  Display this help message\n\n" );
  exit( -1 );
}

/******************************************************************************/

void read_and_store_profile_line( FILE *input, int assoc_index ) {
  int id_target, id_context, r_read,
      n_tab = 3, i = 0;
  char target[ MAX_S + 1 ], context[ MAX_S + 1 ], entry[ MAX_S + 1 ], c;
  static int nb_lines = 1;
  double score;
  nb_lines++;      
  r_read = fscanf( input, "%s\t%d\t%s\t%d", target, &id_target, 
                                            context, &id_context );
  while( !feof(input) && n_tab != assoc_index ) { //read-ignore till assoc_index
    if( getc(input) == '\t' ) { 
      n_tab++; 
    }
  }
  // read till the end of the field and store string in entry
  while( (c = getc(input)) != '\t' && c != '\n' && !feof(input) ) {      
    entry[ i++ ] = c;
  }
  entry[ i ] = '\0';      
  r_read += sscanf( entry, "%lf", &score ); // convert to double
  while( getc(input) != '\n' && !feof(input) ){ /*read-ignore rest of line*/ }
  // Line was correctly read, score not too low, context not to be filtered out
  // target to be kept as target or as neighbor => store it!
  if( r_read == 5 ) {
    if( score >= assoc_thresh && should_keep( context, c_filter ) && 
      ( should_keep( target, t_filter ) || should_keep( target, n_filter ) ) ) {
      n_targets += store_t_c( t_dict, target, id_target, id_context, score );        
    }
  }
  else if( r_read != -2 ){ // Something went wrong and was not EOF (-1 + -1)
    fprintf( stderr, "Format problem at line %d\n", nb_lines );
  }
}

/******************************************************************************/

void read_input_file( char *filename ) {
  FILE *input = open_file_read( filename ); 
  int assoc_index = -1;
  t_dict = g_hash_table_new_full( &g_str_hash, &g_str_equal, free,
           destroy_target_context );
  // check all headers, find the index of the selected assoc_name
  assoc_index = get_index_column_name( input, assoc_name );
  // test if the assoc_name is a valid column header
  if( assoc_index < 4 ) {
    fprintf( stderr, "Column named \"%s\" not found!\n", assoc_name );
    fprintf( stderr, "You must specify a valid -a option. Chose among " );
    fprintf( stderr, "IN-FILE column headers.\nRemember that the first " ); 
    fprintf( stderr, "four fields cannot be used as association scores.\n" );
    exit(-1);
  }
  // Read the input file.
  while( !feof( input ) ) {
    read_and_store_profile_line( input, assoc_index );
  }
  fclose( input );
}

/******************************************************************************/

double rel_entropy_smooth( double p1, double p2 ) {
  if( p1 != 0.0 ) {
    if( p1 > 1.0 || p2 > 1.0 ) {
      if( !warned_rel_entropy ) {
        fprintf( stderr, "Warning: Relative entropy requires probabilities\n" );
        warned_rel_entropy = TRUE;
      }
    }
    return p1 * log( p1 / (ALPHA * p2 + NALPHA * p1 ) );
  }
  return 0.0; // If p1=0, then product is 0. If p2=0, then smoothed  
}

/******************************************************************************/

void calc_sim( GHashTable *c_t1, double sum1, double sum_square1,
               GHashTable *c_t2, double sum2, double sum_square2,
               double *r ) {
  GHashTableIter iter;
  gpointer key, value_t1, value_t2;
  double v1, v2, absdiff, avg, sumsum = 0.0;
  r[ jsd ] = 0.0;     r[ cosine ] = 0.0;  
  r[ l2 ] = 0.0;      r[ l1 ] = 0.0;
  r[ askew2 ] = 0.0;  r[ askew1 ] = 0.0;
  //double r[ N_SIM_SCORES];
  g_hash_table_iter_init( &iter, c_t1 );
  while( g_hash_table_iter_next( &iter, &key, &value_t1 ) ){    
    v1 = *((double *)value_t1);
    value_t2 = g_hash_table_lookup( c_t2, key );
    if( value_t2 ) { // The context is shared by both targets
      v2 = *((double *)value_t2);      
      sumsum += v1 + v2;
      r[ cosine ] += v1 * v2;
      if( calculate_distances ) {
        absdiff = fabs(v1 - v2);
        r[ l1 ] += absdiff;
        r[ l2 ] += absdiff * absdiff;        
        r[ askew1 ] += rel_entropy_smooth( v1, v2 );        
        r[ askew2 ] += rel_entropy_smooth( v2, v1 );
        avg = (v1+v2)/2.0;
        r[ jsd ] += rel_entropy_smooth( v1, avg ) + 
                    rel_entropy_smooth( v2, avg );
      }
    }
    else if (calculate_distances){
      r[ askew1 ] += rel_entropy_smooth( v1, 0 );     
      r[ jsd ] += rel_entropy_smooth( v1, v1/2.0 );
      r[ l1 ] += v1;
      r[ l2 ] += v1 * v1;
    }
  } 
  // Distance measures use the union of contexts and require this part
  if( calculate_distances ) {
    g_hash_table_iter_init( &iter, c_t2 ); 
    while( g_hash_table_iter_next( &iter, &key, &value_t2 ) ){    
      v2 = *((double *)value_t2);
      value_t1 = g_hash_table_lookup( c_t1, key );
      if( !value_t1 ) { // The context is not shared by both targets     
        r[ askew2 ] += rel_entropy_smooth( v2, 0 );
        r[ jsd ] += rel_entropy_smooth( v2, v2/2.0 );
        r[ l1 ] += v2;      
        r[ l2 ] += v2 * v2;      
      }
    }  
    r[ l2 ] = sqrt( r[ l2 ] );
  }
  r[ cosine ] = r[ cosine ] / (sqrt(sum_square1) * sqrt(sum_square2));
  r[ lin ] = sumsum / (sum1 + sum2);
  /* Different version of jaccard: you are supposed to use it with 
     assoc_measures f_c or entropy_context. In this case, the sumsum value is 
     2 * context_weights, and dividing by 2 is the same as averaging between 2 
     equal values. However, when used with different assoc_scores, this can give
     interesting results. To be tested. Should give similar results to Lin */
  r[ wjaccard ] = (sumsum/2.0) / ( sum1 + sum2 - (sumsum/2.0) );
  r[ randomic ] = rand() / (double)RAND_MAX;
}

/******************************************************************************/

gint compare_ints( gconstpointer a, gconstpointer b ) {
  return *((int *)a) - *((int *)b);
}

/******************************************************************************/

int process_sim_scores( int askewdirection, double *result, char *scores ) {
  int i, filtered_out = FALSE;
  double score;
  char score_string[ 50 ];
  for( i = 0; i < N_SIM_SCORES - 1; i++ ) {
    // the score is calculated and: (a) is below defined similarity threshold, 
    // if this is a similarity score or (b) is above defined distance threshold,
    // if this is a distance score => FILTER THE ENTRY OUT
    if( sim_scores[ i ] && ( 
        ( sim_thresh != UNDEFINED && score_types[ i ] == T_SIM && 
          result[ ( i == askew1 ) ? i + askewdirection : i ] < sim_thresh ) || 
        ( dist_thresh != UNDEFINED && score_types[ i ] == T_DIST && 
          result[ ( i == askew1 ) ? i + askewdirection : i ] > dist_thresh ) ) ) {
      filtered_out = TRUE;    
    }
  } 
  if( ! filtered_out ) {
    scores[0] = '\0'; // start result as empty string  
    for( i = 0; i < N_SIM_SCORES - 1; i++ ) {
      if( sim_scores[ i ] ) {
        score = result[ ( i == askew1 ) ? i + askewdirection : i ];
        // is similar enough to be printed or close enough to be printed      
        sprintf( score_string, "\t%.10lf", score );
        strcat( scores, score_string );   
      }
    }
  }
  return !filtered_out;
}

/******************************************************************************/

void output_sim( char *t1, int id_t1, char *t2, int id_t2, double *result ){
  char scores[ 500 ];
  if( should_keep( t1, t_filter ) && should_keep( t2, n_filter ) ) {
    if( process_sim_scores( 0, result, scores ) ) {
      printf( "%s\t%d\t%s\t%d%s\n", t1, id_t1, t2, id_t2, scores );
    }
  }
  // And print the symmetric as well (requires sort of output afterwards)
  if( should_keep( t2, t_filter ) && should_keep( t1, n_filter ) ) {
    if( process_sim_scores( 1, result, scores ) ) {
      printf( "%s\t%d\t%s\t%d%s\n", t2, id_t2, t1, id_t1, scores );
    }
  }
}

/******************************************************************************/

void parse_sim_scores_option( char *optarg ) {
  char *score_name = NULL;
  int i, this_score, one_score = FALSE;
  for( i = 0; i < N_SIM_SCORES; i++ ) {
    sim_scores[ i ] = FALSE;
  }
  calculate_distances = FALSE;
  score_name = strtok ( optarg, ":" );
  while ( score_name != NULL ) {
    fprintf ( stderr, "Will calculate score: %s\n", score_name );
    this_score = FALSE;
    for( i = 0; i < N_SIM_SCORES ; i++ ){ 
      if( !strcmp( score_name, score_names[i] ) ) {
        sim_scores[ i ] = TRUE;
        this_score = TRUE;
        if ( score_types[ i ] == T_DIST ) {
          calculate_distances = TRUE;
        }
      }
    }
    if( !this_score ) {
      fprintf( stderr, "Invalid similarity score: %s. Ignored!\n", score_name );
    }      
    one_score |= this_score;
    score_name = strtok (NULL, ":");
  }
  if( !one_score ) {
    perr( "No valid score name was provided to option -s!" );
    usage();
  }
}

/******************************************************************************/

int treat_options( int argc, char *argv[] ) {
  char opt;
  int o_ptr, i;
  struct option longopts[] = {
    {"association", required_argument, 0, 'a'},
    {"scores", required_argument, 0, 's'},
    {"targets", required_argument, 0, 't'},
    {"neighbors", required_argument, 0, 'n'},
    {"contexts", required_argument, 0, 'c'},
    {"assoc-threshold", required_argument, 0, 'A'},
    {"sim-threshold", required_argument, 0, 'S'},
    {"dist-threshold", required_argument, 0, 'D'},
    {"threads", required_argument, 0, 'T'},    
    {"help", no_argument, 0, 'h'}
  };
  char *shortopts = "a:s:t:n:c:A:S:D:T:h";  
  // By default, calculate all similarity scores
  for( i = 0; i < N_SIM_SCORES; i++ ) {
    sim_scores[ i ] = TRUE;
  }
  while ((opt = getopt_long (argc, argv, shortopts, longopts, &o_ptr)) != -1) {
    switch( opt ) {
      case 'a' :
        strcpy( assoc_name, optarg );
        break;
      case 's' :
        parse_sim_scores_option( optarg );
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
      case 'A' :
        assoc_thresh = parse_thresh_option( optarg, opt );
        break;
      case 'S' :
        sim_thresh = parse_thresh_option( optarg, opt );
        break;
      case 'D' :
        dist_thresh = parse_thresh_option( optarg, opt );
        break;
      case 'T' :
        if( sscanf( optarg, "%d", &nb_threads ) != 1 || nb_threads < 1 ) {
          fprintf( stderr, "Option -T requires positive integer: %s\n", optarg);      
          usage();
        }
        break;        
      case 'h' :
        usage();
        break;
      default:
        fprintf( stderr, "Unrecognized option: %c\n", opt );      
        usage();
    }
  }
  return optind;
}

/******************************************************************************/

void print_header() {
  int i;
  printf( "target\tid_target\tneighbor\tid_neighbor" );
  for( i = 0; i < N_SIM_SCORES - 1; i++ ) {
    if( sim_scores[i] ) {
      printf( "\t%s", score_names[i] );
    }
  }
  printf( "\n" );  
}

/******************************************************************************/

void update_count() {
  int p;
  if( target_counter % 100 == 0 ) {
    p = (int)( (100.0 * target_counter) / n_targets );
    fprintf( stderr, "Processing target: %d (%d%%)\n", target_counter, p );
  }
  target_counter++;
}

/******************************************************************************/

void similarity_worker_serial(int *id_t1 ) {
  double result_sim[ N_SIM_SCORES ];
  GList *iter_t2;
  int *id_t2;
  target_contexts *tc_t1, *tc_t2; 
  tc_t1 = g_hash_table_lookup( t_dict, id_t1 );
  iter_t2 = g_list_first( target_ids );        
  while( iter_t2 ) {
    id_t2 = (int *)iter_t2->data;
    tc_t2 = g_hash_table_lookup( t_dict, id_t2 );
    if( *id_t1 > *id_t2 ) {
      calc_sim( tc_t1->contexts, tc_t1->sum, tc_t1->sum_square, 
                tc_t2->contexts, tc_t2->sum, tc_t2->sum_square, result_sim );
      output_sim( tc_t1->target, *id_t1, tc_t2->target, *id_t2, result_sim );
    }
    iter_t2 = iter_t2->next;
  }
  free( iter_t2 );
}

/******************************************************************************/

void *similarity_worker() { // executed multi-threaded
  int *id_t1, stop = FALSE;
  while( TRUE ) {
    pthread_mutex_lock( &iter_mutex );  
    if( ! iter_t1 ) { stop = TRUE; } // end of the list, can suicide
    else { // get data and move to next list item
      id_t1 = (int *)iter_t1->data;
      iter_t1 = iter_t1->next;
      update_count();
    }
    pthread_mutex_unlock( &iter_mutex );  
    if( stop ) { break; } // break here, otherwise mutex wouldn't be unlocked 
    similarity_worker_serial( id_t1 );
  }
  return NULL;
}

/******************************************************************************/

int main( int argc, char *argv[] ) { 
  int argindex = treat_options( argc, argv );
  if( argindex != argc - 1 ){
    fprintf( stderr, "You must provide a single filename as argument\n" );
    usage();
  }
  fprintf( stderr, "Reading input file into lists...\n" );
  read_input_file( argv[argindex] );  
  fprintf( stderr, "Calculating similarities...\n" );
  print_header();  
  target_ids = g_hash_table_get_keys( t_dict );
  iter_t1 = g_list_first( target_ids ); 
  if( nb_threads > 1 ) { 
    run_multi_threaded( &similarity_worker, nb_threads );
  }
  else {
    perr( "Not using threads\n" );
    while( iter_t1 ) {
      similarity_worker_serial( (int *)iter_t1->data );
      iter_t1 = iter_t1->next;
      update_count();    
    }
  }
  // Clean and free to avoid memory leaks
  perr( "Finished, cleaning up...\n" );
  g_list_free( target_ids );
  g_list_free( iter_t1 );
  g_hash_table_destroy( t_dict );
  if( t_filter ) {  g_hash_table_destroy( t_filter );  }
  if( n_filter ) {  g_hash_table_destroy( n_filter );  }
  if( c_filter ) {  g_hash_table_destroy( c_filter );  }
  return 0;
}
