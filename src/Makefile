CC = gcc

CCFLAGS  = -O2 -Wall -ggdb #-I../../conll_lib/src
#CCFLAGS = -O6
CCFLAGS	+= $(shell pkg-config --cflags glib-2.0)
#CCFLAGS	+= $(shell pkg-config --cflags conll_lib)

LIBS =  -lm -pthread#../../conll_lib/src/conll_lib.o 
LIBS += $(shell pkg-config --libs glib-2.0)
#LIBS += $(shell pkg-config --libs conll_lib)

OBJ = util.o

EXEC = calculate_similarity build_profiles

all: $(EXEC) 

build_profiles: build_profiles.c $(OBJ)
	$(CC) $(CCFLAGS) -o $@ $^ $(LIBS) 
	
calculate_similarity:  calculate_similarity.c $(OBJ)
	$(CC) $(CCFLAGS) -o $@ $^ $(LIBS) 

generalize:  generalize.c $(OBJ)
	$(CC) $(CCFLAGS) -o $@ $^ $(LIBS)	
	
%.o : %.c %.h
	$(CC) $(CCFLAGS) -c $^ $(LIBS)	

clean:
	- rm -f *.o
	- rm -f $(EXEC)
