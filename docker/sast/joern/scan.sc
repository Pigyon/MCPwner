@main def exec(inputPath: String, outFile: String) = {
  importCode(inputPath)
  val findings = cpg.finding.l
  val results = findings.map { f =>
    val evidence = f.evidence.l.map { e =>
      ujson.Obj(
        "label" -> e.label,
        "properties" -> ujson.Obj(
          "code" -> e.propertyOption("CODE").getOrElse("").toString,
          "lineNumber" -> e.propertyOption("LINE_NUMBER").getOrElse("").toString,
          "filename" -> e.propertyOption("FILENAME").getOrElse("").toString
        )
      )
    }
    ujson.Obj(
      "title" -> f.propertyOption("TITLE").getOrElse("").toString,
      "description" -> f.propertyOption("DESCRIPTION").getOrElse("").toString,
      "score" -> f.propertyOption("SCORE").getOrElse("").toString,
      "evidence" -> ujson.Arr(evidence: _*)
    )
  }
  val json = ujson.write(ujson.Arr(results: _*), indent = 2)
  os.write.over(os.Path(outFile), json)
}
