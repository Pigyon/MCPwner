// Multi-language vulnerability heuristics over a Joern CPG.
//
// The CPG is built up-front by main.py via `joern-parse` (which can pass
// frontend-specific flags such as `--delombok-mode no-delombok` for Lombok
// projects like WebGoat, where the default delombok step otherwise yields an
// empty CPG). Here we just load the prebuilt CPG and run language-agnostic
// queries.
//
// Detection strategy (verified empirically against Java, JavaScript/TypeScript,
// Python, PHP, Ruby and Go CPGs):
//   * "Always-dangerous" sinks (command exec, eval, insecure deserialization)
//     are reported wherever they appear — their mere presence is the finding.
//   * "Tainted-input" sinks (SQL, path traversal, open redirect) are reported
//     only when an argument looks dynamically constructed, to avoid flagging
//     safe constant/parameterised usage. A dynamic argument is detected via:
//       - string-building operators: <operator>.addition (Java/JS/Python/Go/
//         Ruby), <operator>.concat (PHP), <operator>.formatString /
//         <operator>.formattedValue (Python/JS f-strings & template literals)
//       - interpolation markers inside a string literal: `#{...}` (Ruby) and
//         `${...}` (JS template literals / Kotlin)
//       - a non-constant argument node (identifier / field access / call),
//         used for redirects and PHP file inclusion.
@main def exec(cpgPath: String, outFile: String) = {
  // Load the CPG raw rather than via importCpg(). importCpg re-applies the
  // frontend post-processing overlays, which can crash on pathological inputs
  // (e.g. jssrc2cpg's ObjectPropertyCallLinker on juice-shop). Our queries are
  // purely syntactic (call names, arguments, literals, AST) and need only the
  // base CPG produced by joern-parse — not the dataflow overlays — so the raw
  // loader is both safe and faster.
  val cpg = io.shiftleft.codepropertygraph.cpgloading.CpgLoader.load(cpgPath)

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

  type Call = io.shiftleft.codepropertygraph.generated.nodes.Call

  // Cross-language string-building operators.
  val DYN_OPS = "<operator>\\.(addition|concat|formatString|formattedValue)"

  // An argument subtree that concatenates / formats strings.
  def hasDynamicArg(c: Call): Boolean =
    c.argument.ast.isCall.name(DYN_OPS).nonEmpty

  // A string literal containing interpolation markers that Joern keeps inline
  // rather than lowering to an operator (Ruby `#{}`, JS/Kotlin `${}`).
  def hasInterpLiteral(c: Call): Boolean =
    c.argument.ast.isLiteral.code("(?s).*(#\\{|\\$\\{).*").nonEmpty

  // A positional argument that is not a constant literal (variable, field
  // access, nested call) — i.e. potentially attacker-influenced.
  def hasNonConstArg(c: Call): Boolean =
    c.argument.l.exists(a => a.argumentIndex > 0 && a.label != "LITERAL")

  def looksTainted(c: Call): Boolean =
    hasDynamicArg(c) || hasInterpLiteral(c)

  // ---- SQL Injection -------------------------------------------------------
  // Sinks across languages: Java (executeQuery/executeUpdate/prepareStatement/
  // createQuery/createNativeQuery), JS (query), Python (execute), PHP
  // (mysqli_query/pg_query/$db->query), Ruby (execute/where/find_by_sql), Go
  // (Query/QueryRow/Exec). Reported when the query string is concatenated or
  // interpolated.
  cpg.call
    .name("(?i).*(execute|query|preparestatement|createquery|nativequery|find_by_sql|mysqli_query|pg_query|sqlquery).*")
    .foreach { c =>
      if (looksTainted(c)) {
        val (f, ln, m) = loc(c)
        mkFinding("Potential SQL Injection",
          s"Dynamically-built query passed to a SQL sink: ${c.code.take(160)}",
          "8.0", f, ln, m)
      }
    }
  // Ruby ActiveRecord string conditions: where/having with interpolation.
  cpg.call.name("(?i)(where|having|find_by_sql|order|group|select)").foreach { c =>
    if (hasInterpLiteral(c) || hasDynamicArg(c)) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential SQL Injection (ActiveRecord)",
        s"Interpolated condition in a query method: ${c.code.take(160)}",
        "8.0", f, ln, m)
    }
  }

  // ---- Command Injection ---------------------------------------------------
  // Always reported. Exact short names (so SQL "execute" is NOT swept in) plus
  // substring matches for language wrappers. Covers JS (exec/execSync/spawn/
  // spawnSync/execFile), Python (os.system/subprocess/Popen), PHP (system/exec/
  // shell_exec/passthru/proc_open), Ruby (system/exec/spawn), Java
  // (ProcessBuilder/Runtime.getRuntime), Go (exec.Command).
  cpg.call
    .name("(?i)(exec|execsync|spawn|spawnsync|execfile|popen|system|shell_exec|passthru|proc_open|command|.*processbuilder.*|.*getruntime.*|.*subprocess.*)")
    .foreach { c =>
      val (f, ln, m) = loc(c)
      mkFinding("Potential Command Injection",
        s"OS command execution sink: ${c.code.take(160)}", "9.0", f, ln, m)
    }

  // ---- Code Injection (eval) -----------------------------------------------
  cpg.call.name("(?i)(eval|create_function|.*\\beval\\b.*)").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Use of eval() / dynamic code execution",
      s"Dynamic code evaluation sink: ${c.code.take(160)}", "7.0", f, ln, m)
  }

  // ---- Insecure Deserialization --------------------------------------------
  // Always-dangerous deserializers across languages.
  cpg.call
    .name("(?i).*(unserialize|readobject|readunshared|readresolve).*")
    .foreach { c =>
      val (f, ln, m) = loc(c)
      mkFinding("Potential Insecure Deserialization",
        s"Deserialization sink: ${c.code.take(160)}", "7.5", f, ln, m)
    }
  // Python (pickle.loads / yaml.load) and Ruby (Marshal.load) — disambiguate
  // the generic load/loads names via the call's code/receiver.
  cpg.call.name("(?i)(load|loads|load_all|full_load)").foreach { c =>
    if (c.code.matches("(?si).*(pickle|yaml|marshal|cpickle|jsonpickle|cloudpickle)\\..*")) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential Insecure Deserialization",
        s"Unsafe object load: ${c.code.take(160)}", "7.5", f, ln, m)
    }
  }

  // ---- Path Traversal ------------------------------------------------------
  // File-access sinks reported when the path is dynamically built.
  cpg.call
    .name("(?i).*(readfile|writefile|readfilesync|writefilesync|createreadstream|createwritestream|fileinputstream|fileoutputstream|filereader|filewriter|file_get_contents|file_put_contents|fopen|sendfile|readlink).*")
    .foreach { c =>
      if (looksTainted(c)) {
        val (f, ln, m) = loc(c)
        mkFinding("Potential Path Traversal",
          s"File access with dynamic path: ${c.code.take(160)}", "6.0", f, ln, m)
      }
    }
  // Generic open() (Python/Ruby) — only when the path is dynamic.
  cpg.call.name("(?i)open").foreach { c =>
    if (looksTainted(c)) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential Path Traversal",
        s"File open with dynamic path: ${c.code.take(160)}", "6.0", f, ln, m)
    }
  }
  // PHP Local/Remote File Inclusion: include/require with non-constant arg.
  cpg.call.name("(?i)(include|include_once|require|require_once)").foreach { c =>
    if (hasNonConstArg(c)) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential File Inclusion (LFI/RFI)",
        s"Dynamic file inclusion: ${c.code.take(160)}", "8.0", f, ln, m)
    }
  }

  // ---- Open Redirect -------------------------------------------------------
  // Redirect sinks pointing at a non-constant (attacker-influenced) target.
  cpg.call.name("(?i)(redirect|sendredirect|redirect_to|.*sendredirect.*)").foreach { c =>
    if (hasNonConstArg(c)) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential Open Redirect",
        s"Redirect to a dynamic target: ${c.code.take(160)}", "5.0", f, ln, m)
    }
  }

  // ---- Server-Side Template Injection / XSS sinks --------------------------
  cpg.call.name("(?i)(render_template_string|render_inline|createtemplate|fromstring)").foreach { c =>
    if (looksTainted(c) || hasNonConstArg(c)) {
      val (f, ln, m) = loc(c)
      mkFinding("Potential Template Injection",
        s"Dynamic template rendering: ${c.code.take(160)}", "7.0", f, ln, m)
    }
  }

  // ---- Weak cryptography ---------------------------------------------------
  cpg.call.name("(?i).*(md5|sha1).*").foreach { c =>
    val (f, ln, m) = loc(c)
    mkFinding("Use of weak hashing algorithm",
      s"Weak hash (MD5/SHA1): ${c.code.take(160)}", "4.0", f, ln, m)
  }

  val json = ujson.write(ujson.Arr(results.toSeq: _*), indent = 2)
  os.write.over(os.Path(outFile), json)
}
