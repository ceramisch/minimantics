package br.ufrgs.inf;

import java.util.HashMap;
import java.util.Map;

/**
 * Created by jkmvsanchez on 10/29/14.
 */
public class JWordCount {

    private String word;
    private int id;
    private double count = 0;
    private Map<String, Double> links = new HashMap<String, Double>();
    private double entropy;

    //@Deprecated
    public JWordCount(String word, int id) {
        this.word = word;
        this.id = id;
    }

    public String getWord() {
        return word;
    }
    public void setWord(String word) {
        this.word = word;
    }

    public int getId() {
        return id;
    }
    public void setId(int id) {
        this.id = id;
    }

    public double getCount() {
        return count;
    }
    public void setCount(double count) {
        this.count = count;
    }

    public Map<String, Double> getLinks() {
        return links;
    }

    public void setLinks(Map<String, Double> links) {
        this.links = links;
    }

    public double getEntropy() {
        return entropy;
    }
    public void setEntropy(double entropy) {
        this.entropy = entropy;
    }
}
