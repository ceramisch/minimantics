package br.ufrgs.inf

case class WordCount(word: String,
                     id: Int,
                     var count: Double,
                     var links: scala.collection.mutable.HashMap[String, Double],
                     var entropy: Double) {

  def withCount(v: Double): WordCount = copy(count = v)

  def withCountAndLinks(c: Double, l: scala.collection.mutable.HashMap[String, Double]): WordCount = copy(count = c, links = l)

  def withEntropy(v: Double): WordCount = copy(entropy = v)

  //def withLinks(v: scala.collection.mutable.HashMap[String, Double]) : WordCount = copy(links = Some(v))
}
