package br.ufrgs.inf

import scala.io.Source
import java.io.{IOException, FileNotFoundException}
import scala.collection.mutable

class BuildProfiles{

  val idT = { var i = 0; () => { i += 1; i}; }
  val idC = { var i = 0; () => { i += 1; i} }

  var targets = mutable.HashMap[String, WordCount]()
  var contexts = mutable.HashMap[String, WordCount]()

  var nPairs: Double = 0.0
  def incNPairs(y: Double) = {
    nPairs += y; nPairs
  }

  def readInputFile(filename: String) = {
    try {
      val src = Source.fromFile(filename)
      for(line <- src.getLines()) {
        val l = line.split(" ")
        val l2 = l(2)
        insertIntoIndexT(l(0), l(1), l2.toDouble)
        insertIntoIndexC(l(1), l(0), l2.toDouble)
        incNPairs(l2.toDouble)
      }
      src.close()
    } catch {
      case ex: FileNotFoundException => println("FileNotFoundException.")
      case ex: IOException => println("IOException.")
    }
  }

  def calculate(){
    contexts = contexts.map{ case(k, v) => (k, v.withEntropy(calculateEntropy(v.count, v.links))) }
    targets = targets.map{ case(k, v) => (k, v.withEntropy(calculateEntropy(v.count, v.links))) }

    for(k <- targets.keys){
      var t = targets(k)
      t.links.map{ case(a, b) =>
        var c: WordCount = contexts(a)
        calculateAndPrintAM(t.word, t.id, c.word, c.id, b, t.count, c.count, t.entropy, c.entropy)
      }
    }
  }

  def expected(cw1: Double, cw2: Double, n: Double): Double = {
    (cw1 * cw2) / n
  }

  def prodLog(a: Double, b: Double): Double = {
    if(a != 0) a * Math.log(b) else 0
  }

  def calculateAndPrintAM(w1: String, idw1:Int,
                           w2: String, idw2: Int,
                           cw1w2: Double, cw1: Double, cw2: Double,
                           tEntropy: Double, cEntropy: Double) = {

    val cw1nw2: Int = cw1.toInt - cw1w2.toInt
    val cnw1w2: Int = cw2.toInt - cw1w2.toInt
    val cnw1nw2: Int = nPairs.toInt - cw1.toInt

    val ew1w2: Double = expected( cw1, cw2, nPairs )
    val ew1nw2: Double = expected( cw1, nPairs - cw2, nPairs )
    val enw1w2: Double  = expected( nPairs - cw1, cw2, nPairs )
    val enw1nw2: Double = expected( nPairs - cw1, nPairs - cw2, nPairs )

    val am_cp: Double = cw1w2 / cw1
    val am_pmi: Double = Math.log( cw1w2 ) - Math.log( ew1w2 )
    val am_npmi:Double = am_pmi / ( Math.log( nPairs) - Math.log( cw1w2) )
    val am_lmi: Double = cw1w2 * am_pmi
    val am_dice: Double = ( 2.0 * cw1w2 ) / ( cw1 + cw2 )
    val am_tscore: Double = (cw1w2 - ew1w2 ) / Math.sqrt( cw1w2 )
    val am_zscore: Double  = (cw1w2 - ew1w2 ) / Math.sqrt( ew1w2 )

    //Check
    val am_chisquare: Double = Math.pow( cw1w2   - ew1w2  , 2 ) / ew1w2   +
      Math.pow( cw1nw2  - ew1nw2 , 2 ) / ew1nw2  +
      Math.pow( cnw1w2  - enw1w2 , 2 ) / enw1w2  +
      Math.pow( cnw1nw2 - enw1nw2, 2 ) / enw1nw2
    val am_loglike: Double = 2.0 * ( prodLog( cw1w2  , cw1w2   / ew1w2   ) +
      prodLog( cw1nw2 , cw1nw2  / ew1nw2  ) +
      prodLog( cnw1w2 , cnw1w2  / enw1w2  ) +
      prodLog( cnw1nw2, cnw1nw2 / enw1nw2 ) )

    println(w1 +"\t"+ idw1 +"\t"+ w2 +"\t"+ idw2 +"\t"+ cw1w2 +"\t"+ cw1 +"\t"+ cw2 +"\t"+ am_cp +"\t"+ am_pmi +"\t"+ am_npmi +"\t"+ am_lmi +"\t"+ am_tscore +"\t"+
      am_zscore +"\t"+ am_dice +"\t"+ am_chisquare +"\t"+ am_loglike +"\t"+ tEntropy +"\t"+ cEntropy);
    //Create tuples
  }

  def calculateEntropy(total: Double, distribution: scala.collection.mutable.HashMap[String, Double]): Double = {
    var p: Double = 0.0
    var entropy: Double = 0.0
    distribution.map(d => {
      p = d._2 / total
      entropy -= p * Math.log(p)
    })
    return entropy
  }

  def insertIntoIndexT(w1: String, w2: String, count: Double) = {
    val link = scala.collection.mutable.HashMap[String, Double]()
    link.put(w2, count)

    val newWC = targets.get(w1).fold {
      WordCount(w1, idT(), count, link, 0.0)
    } {
      oldWC => oldWC.links.put(w2, count)
      oldWC.withCountAndLinks(oldWC.count + count, oldWC.links)
    }
    targets.put(w1, newWC)
  }

  def insertIntoIndexC(w1: String, w2: String, count: Double) = {
    val link = scala.collection.mutable.HashMap[String, Double]()
    link.put(w2, count)

    val newWC = contexts.get(w1).fold {
      WordCount(w1, idC(), count, link, 0.0)
    } {
      oldWC => oldWC.links.put(w2, count)
        oldWC.withCountAndLinks(oldWC.count + count, oldWC.links)
    }
    contexts.put(w1, newWC)
  }
}

object BuildProfiles {

  def main(args: Array[String]){
    println("Running Build Profiles - Scala")
    val bp = new BuildProfiles;
    bp.readInputFile("/home/jkmvsanchez/Dropbox/code/minimantics/src/mini.2.s.filter.t4.c4.tc2.u")
    bp.calculate()
  }
}
