@main def exec(inputPath: String, outFile: String) = {
  importCode(inputPath)

  val results = scala.collection.mutable.ArrayBuffer[ujson.Value]()

  def mkFinding(title: String, desc: String, score: String,
                filename: String, line: String, method: String): Unit = {
    results += ujson.Obj(
      "title"       -> title,
      "description" -> desc,
      "score"       -> score,
      "filepath"    -> filename,
      "line"        -> line,
      "function"    -> method
    )
  }

  def loc(c: io.shiftleft.codepropertygraph.generated.nodes.CfgNode) = {
    val l = c.location
    (l.filename, l.lineNumber.map(_.toString).getOrElse(""), l.methodFullName)
  }

  // SQL Injection — look for query/execute calls with SQL-like string args
  cpg.call.name("query|execute").foreach { c =>
    val hasSQL = c.argument.isLiteral
      .code("(?i).*(SELECT|INSERT|UPDATE|DELETE|DROP).*").nonEmpty
    val hasConcat = c.argument.isCall.name("<operator>.addition").nonEmpty
    if (hasSQL || hasConcat) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential SQL Injection",
        s"SQL operation: ${c.code.take(120)}", "8.0", f, ln, m)
    }
  }

  // Command Injection
  cpg.call.name("exec|execSync|spawn|spawnSync|execFile").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Potential Command Injection",
      s"OS command execution: ${c.code.take(120)}", "9.0", f, ln, m)
  }

  // eval() usage
  cpg.call.name("eval").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Use of eval()",
      s"eval() may allow code injection: ${c.code.take(120)}", "7.0", f, ln, m)
  }

  // Path traversal — file system access
  cpg.call.name("readFile|readFileSync|createReadStream|writeFile|writeFileSync")
    .foreach { c =>
      val (f, ln, m) = loc(c)
      mkFinding("Potential Path Traversal",
        s"File system access: ${c.code.take(120)}", "6.0", f, ln, m)
    }

  // Insecure deserialization
  cpg.call.name("unserialize|deserialize|serialize").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Potential Insecure Deserialization",
      s"Deserialization call: ${c.code.take(120)}", "7.0", f, ln, m)
  }

  // Dangerous redirects
  cpg.call.name("redirect").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Potential Open Redirect",
      s"Redirect call: ${c.code.take(120)}", "5.0", f, ln, m)
  }

  val json = ujson.write(ujson.Arr(results.toSeq: _*), indent = 2)
  os.write.over(os.Path(outFile), json)
}
