package br.ufrgs.inf

import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import java.io.FileWriter

sealed trait Scores {def name: String; def typo: String}
object Scores {
  case object cosine extends Scores   { val name = "cosine";   val typo = "T_SIM"; }
  case object wjaccard extends Scores { val name = "wjaccard"; val typo = "T_SIM"; }
  case object lin extends Scores      { val name = "lin";      val typo = "T_SIM"; }
  case object l1 extends Scores       { val name = "l1";       val typo = "T_DIST"; }
  case object l2 extends Scores       { val name = "l2";       val typo = "T_DIST"; }
  case object jsd extends Scores      { val name = "jsd";      val typo = "T_DIST"; }
  case object random extends Scores   { val name = "random";   val typo = "T_RAND"; }
  case object askew1 extends Scores   { val name = "askew";    val typo = "T_DIST"; }
  case object askew2 extends Scores   { val name = "askew";    val typo = "T_DIST"; }
}

sealed trait Profiles {def name: String; def id: Int}
object Profiles {
  case object f_tc extends Profiles       { val name = "f_tc";      val id = 0; }
  case object f_t extends Profiles        { val name = "f_t";       val id = 1; }
  case object f_c extends Profiles        { val name = "f_c";       val id = 2; }
  case object cond_prob extends Profiles  { val name = "cond_prob"; val id = 3; }
  case object pmi extends Profiles        { val name = "pmi";       val id = 4; }
  case object npmi extends Profiles       { val name = "npmi";      val id = 5; }
  case object lmi extends Profiles        { val name = "lmi";       val id = 6; }
  case object tscore extends Profiles     { val name = "tscore";    val id = 7; }
  case object zscore extends Profiles     { val name = "zscore";    val id = 8; }
  case object dice extends Profiles       { val name = "dice";      val id = 9; }
  case object chisquare extends Profiles  { val name = "chisquare"; val id = 10; }
  case object loglike extends Profiles    { val name = "loglike";   val id = 11; }
  case object entropy_target extends Profiles   { val name = "entropy_target";  val id = 12; }
  case object entropy_context extends Profiles  { val name = "entropy_context"; val id = 13; }
}

object Minimantics {

  val Alpha:Double  = 0.99
  val Nalpha:Double = 0.01
  val RandMax = 32767 //32768
  val NumSimScores:Int = 9
  val NumSimScores2: Int = 6
  val Undefined: Double = 99999.0
  val T_SIM = "T_SIM"
  val T_DIST = "T_DIST"
  val T_RAND = "T_RAND"

  var AssocName: String = Profiles.cond_prob.name
  var AssocThresh: Option[Double] = None
  var SimThresh: Option[Double] = None
  var DistThresh: Option[Double] = None
  var calculateDistances:Boolean = true

  def getScoresType(id: Int): Scores = {
    id match {
      case 0 => Scores.cosine
      case 1 => Scores.wjaccard
      case 2 => Scores.lin
      case 3 => Scores.l1
      case 4 => Scores.l2
      case 5 => Scores.jsd
      case 6 => Scores.random
      case 7 => Scores.askew1
      case 8 => Scores.askew2
    }
  }

  def getProfilesType(name: String): Profiles = {
    name match {
      case "f_tc"       => Profiles.f_tc
      case "f_t"        => Profiles.f_t
      case "f_c"        => Profiles.f_c
      case "cond_prob"  => Profiles.cond_prob
      case "pmi"        => Profiles.pmi
      case "npmi"       => Profiles.npmi
      case "lmi"        => Profiles.lmi
      case "tscore"     => Profiles.tscore
      case "zscore"     => Profiles.zscore
      case "dice"       => Profiles.dice
      case "chisquare"  => Profiles.chisquare
      case "loglike"    => Profiles.loglike
      case "entropy_target"   => Profiles.entropy_target
      case "entropy_context"  => Profiles.entropy_context
    }
  }

  def usage() = {
    println("Usage: ")
  }

  def treatOptions(opt: String, value: String) = {
    opt match {
      case "a" => println("a"); AssocName = value
      case "s" => println("s")
      case "t" => println("t")
      case "n" => println("n")
      case "c" => println("c")
      case "A" => println("A"); AssocThresh = Some(value.toDouble)
      case "S" => println("S"); SimThresh = Some(value.toDouble)
      case "D" => println("D"); DistThresh = Some(value.toDouble)
      case _ => usage()
    }
  }

  def calculateEntropy(total: Double, distribution: scala.collection.immutable.Map[String, Int]): Double = {
    var p: Double = 0.0
    var entropy: Double = 0.0
    distribution.map(d => {
      p = d._2 / total
      entropy -= p * math.log(p)
    })
    entropy
  }

  def expected(cw1: Double, cw2: Double, n: Double): Double = { (cw1 * cw2) / n }

  def prodLog(a: Double, b: Double): Double = { if(a != 0) a * math.log(b) else 0 }

  def calculate(w1: String,
                w2: String,
                cw1w2: Double, cw1: Double, cw2: Double,
                tEntropy: Double, cEntropy: Double, nPairs: Double) = {

    val cw1nw2: Int = cw1.toInt - cw1w2.toInt
    val cnw1w2: Int = cw2.toInt - cw1w2.toInt
    val cnw1nw2: Int = nPairs.toInt - cw1.toInt

    val ew1w2: Double = expected( cw1, cw2, nPairs )
    val ew1nw2: Double = expected( cw1, nPairs - cw2, nPairs )
    val enw1w2: Double  = expected( nPairs - cw1, cw2, nPairs )
    val enw1nw2: Double = expected( nPairs - cw1, nPairs - cw2, nPairs )

    val am_cp: Double = cw1w2 / cw1
    val am_pmi: Double = math.log( cw1w2 ) - math.log( ew1w2 )
    val am_npmi:Double = am_pmi / ( math.log( nPairs) - math.log( cw1w2) )
    val am_lmi: Double = cw1w2 * am_pmi
    val am_dice: Double = ( 2.0 * cw1w2 ) / ( cw1 + cw2 )
    val am_tscore: Double = (cw1w2 - ew1w2 ) / math.sqrt( cw1w2 )
    val am_zscore: Double  = (cw1w2 - ew1w2 ) / math.sqrt( ew1w2 )

    //Check
    val am_chisquare: Double = math.pow( cw1w2   - ew1w2  , 2 ) / ew1w2   +
      math.pow( cw1nw2  - ew1nw2 , 2 ) / ew1nw2  +
      math.pow( cnw1w2  - enw1w2 , 2 ) / enw1w2  +
      math.pow( cnw1nw2 - enw1nw2, 2 ) / enw1nw2
    val am_loglike: Double = 2.0 * ( prodLog( cw1w2  , cw1w2   / ew1w2   ) +
      prodLog( cw1nw2 , cw1nw2  / ew1nw2  ) +
      prodLog( cnw1w2 , cnw1w2  / enw1w2  ) +
      prodLog( cnw1nw2, cnw1nw2 / enw1nw2 ) )

    Tuple3(w1, w2, List(cw1w2, cw1, cw2, am_cp, am_pmi, am_npmi, am_lmi, am_tscore, am_zscore, am_dice, am_chisquare, am_loglike, tEntropy, cEntropy))
  }

  def calculateSumAndSumSquare (key: String, mapa: scala.collection.immutable.Map[String,Double]) = {
    var sum: Double = 0.0
    var sumSquare: Double = 0.0
    mapa.map(d => {
      sum += d._2
      sumSquare += d._2 * d._2
    })
    Tuple4(key, sum, sumSquare, mapa)
  }

  def calcSim(key1: String, map1: scala.collection.immutable.Map[String,Double],
              key2: String, map2: scala.collection.immutable.Map[String,Double],
              sum1: Double, sum2: Double, sumSquare1: Double, sumSquare2: Double) = {

    var sumSum: Double = 0.0

    var cosine: Double = 0.0
    var l1: Double = 0.0
    var l2: Double = 0.0
    var askew1: Double = 0.0
    var askew2: Double = 0.0
    var jsd: Double = 0.0
    var lin: Double = 0.0
    var wjaccard: Double = 0.0
    var randomic: Double = 0.0

    map1.map {
      case (k1, v1) => {
        map2.get(k1) match {
          case Some(v2) => {
            sumSum += v1 + v2
            cosine += v1 * v2
            if (calculateDistances) {
              val absDiff: Double = math.abs(v1 - v2)
              val avg: Double = (v1 + v2) / 2.0

              l1 += absDiff
              l2 += absDiff * absDiff
              askew1 += relEntropySmooth(v1, v2)
              askew2 += relEntropySmooth(v2, v1)
              jsd += relEntropySmooth(v1, avg) + relEntropySmooth(v2, avg)
            }
          }

          case None => {
            if (calculateDistances) {
              l1 += v1
              l2 += v1 * v1
              askew1 += relEntropySmooth(v1, 0)

              jsd += relEntropySmooth(v1, v1 / 2.0)
            }
          }
        }
      }
    }

    //
    if (calculateDistances) {
      map2.map {
        case (k2, v2) => {
          map1.get(k2) match {
            case Some(v1) => { /* Nothing */ }
            case None => {
              askew2 += relEntropySmooth(v2, 0)
              jsd += relEntropySmooth(v2, v2/2.0)
              l1 += v2
              l2 += v2 * v2
            }
          }
        }
      }
      l2 = math.sqrt(l2)
    }

    cosine = cosine / math.sqrt(sumSquare1) * math.sqrt(sumSquare2)
    lin = sumSum / (sum1 + sum2)

    wjaccard = (sumSum / 2.0) / (sum1 + sum2 - (sumSum / 2.0))
    randomic = math.random / RandMax

    Tuple9(cosine, wjaccard, lin, l1, l2, jsd, randomic, askew1, askew2)
  }

  def relEntropySmooth(p1: Double, p2: Double): Double = {
    if(p1 != 0.0){
      if(p1 > 1.0 || p2 > 1.0) {
        println("Warning: Relative entropy requires probabilities")
        return  0.0
      } else {
        return p1 * math.log( p1 / (Alpha * p2 + Nalpha * p1 ) )
      }
    }
    return 0.0
  }

  def processSimScores(value: Int, scores: List[Double], key1: String, key2: String): Boolean = {
    var FilteredOut: Boolean = false

    for(i <- 0 to 6) {
      if( (T_SIM.equals(getScoresType(i).typo) && scores(i) < SimThresh.getOrElse(Undefined)) ||
        (T_DIST.equals(getScoresType(i).typo) && scores(i) > DistThresh.getOrElse(Undefined)) ){
        FilteredOut = true
      }
    }
    //
    if(value.equals(0)){
      if( (T_SIM.equals(getScoresType(7).typo) && scores(7) < SimThresh.getOrElse(Undefined)) ||
        (T_DIST.equals(getScoresType(7).typo) && scores(7) > DistThresh.getOrElse(Undefined)) ){
        FilteredOut = true
      }
    } else {
      if( (T_SIM.equals(getScoresType(8).typo) && scores(8) < SimThresh.getOrElse(Undefined)) ||
        (T_DIST.equals(getScoresType(8).typo) && scores(8) > DistThresh.getOrElse(Undefined)) ){
        FilteredOut = true
      }
    }
    return FilteredOut
  }

  def outputSim (key1: String, key2: String,
                 scores: List[Double]) = {

    val filteredOut0 = processSimScores(0, scores, key1, key2)
    val filteredOut1 = processSimScores(1, scores, key1, key2)

    if(!filteredOut0 && !filteredOut1){
      Tuple2(
        Tuple10(key1, key2, scores(0), scores(1), scores(2), scores(3), scores(4), scores(5), scores(6), scores(7)),
        Tuple10(key2, key1, scores(0), scores(1), scores(2), scores(3), scores(4), scores(5), scores(6), scores(8))
      )
    } else {
      None
    }
  }

  def process (master: String) = {
    val sc = new SparkContext(master, "Minimantics", System.getenv("SPARK_HOME"))  

    val input = sc.textFile("hdfs://ufrgsjvsmaster:9000/user/hduser/bnc.txt")

    //Build Profiles
    val words = input.map(line => line.split("\t"))
    val target = words.map(line => (line(0), (line(2).toInt, Map(line(1) -> line(2).toInt) ))).reduceByKey((x,y) => (x._1 + y._1, ((x._2)++y._2)))
    val nPairs = target.map(m => m._2._1).sum
    val resT = target.map(m => (m._1, (m._2._1, m._2._2, calculateEntropy(m._2._1, m._2._2))))
    val context = words.map(line => (line(1), (line(2).toInt, Map((line(0), line(2).toInt)) ))).reduceByKey((x,y) => (x._1 + y._1, ((x._2)++y._2)))
    val resC = context.map(m => (m._1, (m._2._1, m._2._2, calculateEntropy(m._2._1, m._2._2))))

    val newT: org.apache.spark.rdd.RDD[(String, (String, Int, Int, Double))] = resT.flatMap {case (t, (i, map, e)) => map.toList.map { case (k, v) => (k, (t, i, v, e)) } }
    val profiles = newT.join(resC).map(res => calculate(res._2._1._1, res._1, res._2._1._3, res._2._1._2, res._2._2._1, res._2._1._4, res._2._2._3, nPairs))
    
    //Calculate Similarity
    val cs1 = profiles.map{ case (word1, word2, profiles) => (word1, Map(word2 -> profiles(getProfilesType(AssocName).id)))}.reduceByKey(_ ++ _)
    val withSumAndSumSquare = cs1.map(m => calculateSumAndSumSquare(m._1, m._2))
    val cs3 = withSumAndSumSquare.cartesian(withSumAndSumSquare).filter{ m => m._1._1 > m._2._1 }
    val cs4 = cs3.map(m => ((m._1._1, m._2._1), calcSim(m._1._1, m._1._4, m._2._1, m._2._4, m._1._2, m._2._2, m._1._3, m._2._3)))
    val cs5 = cs4.map{case((k1, k2), (cosine, wjaccard, lin, l1, l2, jsd, randomic, askew1, askew2)) => outputSim(k1, k2, List(cosine, wjaccard, lin, l1, l2, jsd, randomic, askew1, askew2))}
    val filtro = cs5.filter{m => m != None}
    val last = filtro.flatMap{m => m.productIterator.toList.map{ m => m }}

    profiles.saveAsTextFile("/tmp")

    sc.stop()
  }

  def main(args: Array[String]) {
    if(args.length > 0){
      for(i <- args){
        val x = i.split(":")
        treatOptions(x(0), x(1))
      }
      println(s"args: $SimThresh - $AssocName")
    } else{
      treatOptions("S", "0.2")
      treatOptions("a", Profiles.cond_prob.name)
      println(s"$SimThresh - $AssocName")
    }
    process("local")
  }
}
