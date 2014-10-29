package br.ufrgs.inf;

import java.io.*;
import java.util.HashMap;
import java.util.Map;

/**
 * Created by jkmvsanchez on 10/29/14.
 */
public class JBuildProfiles {

    private int idT = 0;
    private int idC = 0;

    Map<String, JWordCount> targets  = new HashMap<String, JWordCount>();
    Map<String, JWordCount> contexts = new HashMap<String, JWordCount>();
    Double nPairs = 0.0;

    private void readInputFile(String filename){
        try {
            File archivo = new File(filename);
            String linea;
            FileReader fr = new FileReader (archivo);
            BufferedReader br = new BufferedReader(fr);
            int a=0;
            String[] tokens = null;
            while((linea=br.readLine())!=null) {
                tokens = linea.split(" ");
                int count = Integer.parseInt(tokens[2]);
                insertIntoIndexT(tokens[0], tokens[1], count);
                insertIntoIndexC(tokens[1], tokens[0], count);
                nPairs += count;
                a++;
            }

            System.out.println(a+" lineas");
            System.out.println("t: " + targets.size());
            System.out.println("c: " + contexts.size());
            System.out.println("nPairs: " + nPairs);

            fr.close();
        } catch(IOException a){
            System.out.println(a);
        } finally {
        }
    }

    private void calculate(){
        for (Map.Entry<String, JWordCount> c : contexts.entrySet()) {
            if(c.getValue() != null) {
                JWordCount wc = (JWordCount)c.getValue();
                wc.setEntropy(calculateEntropy(wc.getCount(), wc.getLinks()));
            }
        }
        for (Map.Entry<String, JWordCount> t : targets.entrySet()) {
            if(t.getValue() != null) {
                JWordCount wcT = (JWordCount)t.getValue();
                calculateAmsAllSerial(wcT, t.getKey());
            }
        }
    }

    private static double expected(double cw1, double cw2, double n){
        return ( cw1 * cw2) /  n;
    }

    private static double prodlog(double a, double b){
        return a != 0 ? a * Math.log(b) : 0;
    }

    private void calculateAndPrintAM(String w1, int idw1,
                                     String w2, int idw2,
                                     Double cw1w2, Double cw1, Double cw2,
                                     Double tEntropy, Double cEntropy){

        int cw1nw2 = cw1.intValue() - cw1w2.intValue();
        int cnw1w2 = cw2.intValue() - cw1w2.intValue();
        int cnw1nw2 = nPairs.intValue() - cw1.intValue() - cw2.intValue() + cw1w2.intValue();

        double ew1w2   = expected( cw1, cw2, nPairs );
        double ew1nw2  = expected( cw1, nPairs - cw2, nPairs );
        double enw1w2  = expected( nPairs - cw1, cw2, nPairs );
        double enw1nw2 = expected( nPairs - cw1, nPairs - cw2, nPairs );

        double am_cp = cw1w2 / cw1;
        double am_pmi = Math.log( cw1w2 ) - Math.log( ew1w2 );
        double am_npmi = am_pmi / ( Math.log( nPairs) - Math.log( cw1w2) );
        double am_lmi = cw1w2 * am_pmi;
        double am_dice = ( 2.0 * cw1w2 ) / ( cw1 + cw2 );
        double am_tscore = (cw1w2 - ew1w2 ) / Math.sqrt( cw1w2 );
        double am_zscore = (cw1w2 - ew1w2 ) / Math.sqrt( ew1w2 );

        double am_chisquare = Math.pow( cw1w2   - ew1w2  , 2 ) / ew1w2   +
                Math.pow( cw1nw2  - ew1nw2 , 2 ) / ew1nw2  +
                Math.pow( cnw1w2  - enw1w2 , 2 ) / enw1w2  +
                Math.pow( cnw1nw2 - enw1nw2, 2 ) / enw1nw2;
        double am_loglike = 2.0 * ( prodlog( cw1w2  , cw1w2   / ew1w2   ) +
                prodlog( cw1nw2 , cw1nw2  / ew1nw2  ) +
                prodlog( cnw1w2 , cnw1w2  / enw1w2  ) +
                prodlog( cnw1nw2, cnw1nw2 / enw1nw2 ) );

        System.out.println(w1 +"\t"+ idw1 +"\t"+ w2 +"\t"+ idw2 +"\t"+ cw1w2 +"\t"+ cw1 +"\t"+ cw2 +"\t"+ am_cp +"\t"+ am_pmi +"\t"+ am_npmi +"\t"+ am_lmi +"\t"+ am_tscore +"\t"+
                am_zscore +"\t"+ am_dice +"\t"+ am_chisquare +"\t"+ am_loglike +"\t"+ tEntropy +"\t"+ cEntropy);
    }

    private double calculateEntropy(double total, Map<String, Double> distribution){
        double entropy = 0.0;
        double p = 0.0;
        for (Map.Entry<String, Double> t : distribution.entrySet()) {
            p = t.getValue() / total;
            entropy -= p * Math.log(p);
        }
        return entropy;
    }

    private void calculateAmsAllSerial(JWordCount wcT, String keyT){
        double countTC;
        if(wcT != null){
            Map<String, Double> links = wcT.getLinks();
            wcT.setEntropy(calculateEntropy(wcT.getCount(), links));
            for (Map.Entry<String, Double> l : links.entrySet()) {
                countTC = l.getValue();
                JWordCount wcC = (JWordCount)contexts.get(l.getKey());
                calculateAndPrintAM(wcT.getWord(), wcT.getId(), wcC.getWord(), wcC.getId(), countTC, wcT.getCount(), wcC.getCount(), wcT.getEntropy(), wcC.getEntropy());
            }
        }
    }

    public static void main(String[] args){
        System.out.println("Build Profiles - Java");
        JBuildProfiles bp = new JBuildProfiles();
        bp.readInputFile("/home/jkmvsanchez/Dropbox/code/minimantics/src/mini.2.s.filter.t4.c4.tc2.u");
        bp.calculate();
    }

    public int getIdT() {
        return idT;
    }
    public void setIdT(int idT) {
        this.idT = idT;
    }

    public int getIdC() {
        return idC;
    }
    public void setIdC(int idC) {
        this.idC = idC;
    }

    private void insertIntoIndexT(String w1, String w2, double count) {
        JWordCount wordCount = (JWordCount)targets.get(w1);
        if(wordCount == null) {
            wordCount = new JWordCount(w1, idT++);
            targets.put(w1, wordCount);
        }
        wordCount.setCount(wordCount.getCount() + count);
        wordCount.getLinks().put(w2, count);
    }
    private void insertIntoIndexC(String w1, String w2, double count) {
        JWordCount wordCount = (JWordCount)contexts.get(w1);
        if(wordCount == null) {
            wordCount = new JWordCount(w1, idC++);
            contexts.put(w1, wordCount);
        }
        wordCount.setCount(wordCount.getCount() + count);
        wordCount.getLinks().put(w2, count);
    }
}
