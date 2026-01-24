"""Language adapters for extracting code elements via CodeQL."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LanguageAdapter(ABC):
    """Base class for language-specific CodeQL adapters."""

    @abstractmethod
    def get_functions_query(self) -> str:
        """
        Get CodeQL query string for extracting functions.

        Returns:
            CodeQL query string
        """
        pass

    @abstractmethod
    def get_call_graph_query(self) -> str:
        """
        Get CodeQL query string for extracting call relationships.

        Returns:
            CodeQL query string
        """
        pass

    def parse_function_result(self, row: List[str]) -> Dict[str, Any]:
        """
        Parse CSV row from CodeQL function query into standard dict.

        Args:
            row: CSV row as list of strings

        Returns:
            Dictionary with keys: name, qualified_name, file, start_line, end_line, code
        """
        # Default implementation - can be overridden by subclasses
        return {
            "name": row[0] if len(row) > 0 else "",
            "qualified_name": row[1] if len(row) > 1 else "",
            "file": row[2] if len(row) > 2 else "",
            "start_line": int(row[3]) if len(row) > 3 and row[3] else 0,
            "end_line": int(row[4]) if len(row) > 4 and row[4] else 0,
            "code": row[5] if len(row) > 5 else "",
        }

    def parse_call_graph_result(self, row: List[str]) -> Dict[str, Any]:
        """
        Parse CSV row from CodeQL call graph query into standard dict.

        Args:
            row: CSV row as list of strings

        Returns:
            Dictionary with keys: caller_name, caller_file, callee_name, callee_file, call_line
        """
        return {
            "caller_name": row[0] if len(row) > 0 else "",
            "caller_file": row[1] if len(row) > 1 else "",
            "callee_name": row[2] if len(row) > 2 else "",
            "callee_file": row[3] if len(row) > 3 else "",
            "call_line": int(row[4]) if len(row) > 4 and row[4] else None,
        }


class PythonAdapter(LanguageAdapter):
    """Adapter for Python language."""

    def get_functions_query(self) -> str:
        return """
import python

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import python

from Call c, Function caller, Function callee
where 
    c.getScope() = caller and
    c.getFunc().(Name).getId() = callee.getName()
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    c.getLocation().getStartLine() as call_line
"""


class CppAdapter(LanguageAdapter):
    """Adapter for C/C++ language."""

    def get_functions_query(self) -> str:
        return """
import cpp

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import cpp

from FunctionCall fc, Function caller, Function callee
where 
    fc.getEnclosingFunction() = caller and
    fc.getTarget() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    fc.getLocation().getStartLine() as call_line
"""


class JavaAdapter(LanguageAdapter):
    """Adapter for Java language."""

    def get_functions_query(self) -> str:
        return """
import java

from Method m
select 
    m.getName() as name,
    m.getQualifiedName() as qualified_name,
    m.getLocation().getFile().getRelativePath() as file,
    m.getLocation().getStartLine() as start_line,
    m.getLocation().getEndLine() as end_line,
    m.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import java

from MethodAccess ma, Method caller, Method callee
where 
    ma.getEnclosingCallable() = caller and
    ma.getMethod() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    ma.getLocation().getStartLine() as call_line
"""


class JavaScriptAdapter(LanguageAdapter):
    """Adapter for JavaScript/TypeScript language."""

    def get_functions_query(self) -> str:
        return """
import javascript

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import javascript

from CallExpr call, Function caller, Function callee
where 
    call.getEnclosingFunction() = caller and
    call.getCallee() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    call.getLocation().getStartLine() as call_line
"""


class GoAdapter(LanguageAdapter):
    """Adapter for Go language."""

    def get_functions_query(self) -> str:
        return """
import go

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import go

from CallExpr call, Function caller, Function callee
where 
    call.getEnclosingFunction() = caller and
    call.getTarget() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    call.getLocation().getStartLine() as call_line
"""


class CSharpAdapter(LanguageAdapter):
    """Adapter for C# language."""

    def get_functions_query(self) -> str:
        return """
import csharp

from Method m
select 
    m.getName() as name,
    m.getQualifiedName() as qualified_name,
    m.getLocation().getFile().getRelativePath() as file,
    m.getLocation().getStartLine() as start_line,
    m.getLocation().getEndLine() as end_line,
    m.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import csharp

from MethodCall mc, Method caller, Method callee
where 
    mc.getEnclosingCallable() = caller and
    mc.getTarget() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    mc.getLocation().getStartLine() as call_line
"""


class KotlinAdapter(LanguageAdapter):
    """Adapter for Kotlin language."""

    def get_functions_query(self) -> str:
        # Kotlin uses Java adapter since it compiles to JVM bytecode
        return """
import java

from Method m
where m.getLocation().getFile().getExtension() = "kt"
select 
    m.getName() as name,
    m.getQualifiedName() as qualified_name,
    m.getLocation().getFile().getRelativePath() as file,
    m.getLocation().getStartLine() as start_line,
    m.getLocation().getEndLine() as end_line,
    m.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import java

from MethodAccess ma, Method caller, Method callee
where 
    ma.getEnclosingCallable() = caller and
    ma.getMethod() = callee and
    caller.getLocation().getFile().getExtension() = "kt"
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    ma.getLocation().getStartLine() as call_line
"""


class RubyAdapter(LanguageAdapter):
    """Adapter for Ruby language."""

    def get_functions_query(self) -> str:
        return """
import ruby

from Method m
select 
    m.getName() as name,
    m.getQualifiedName() as qualified_name,
    m.getLocation().getFile().getRelativePath() as file,
    m.getLocation().getStartLine() as start_line,
    m.getLocation().getEndLine() as end_line,
    m.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import ruby

from MethodCall mc, Method caller, Method callee
where 
    mc.getEnclosingMethod() = caller and
    mc.getTarget() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    mc.getLocation().getStartLine() as call_line
"""


class RustAdapter(LanguageAdapter):
    """Adapter for Rust language."""

    def get_functions_query(self) -> str:
        return """
import rust

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import rust

from CallExpr call, Function caller, Function callee
where 
    call.getEnclosingCallable() = caller and
    call.getFunction() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    call.getLocation().getStartLine() as call_line
"""


class SwiftAdapter(LanguageAdapter):
    """Adapter for Swift language."""

    def get_functions_query(self) -> str:
        return """
import swift

from Function f
select 
    f.getName() as name,
    f.getQualifiedName() as qualified_name,
    f.getLocation().getFile().getRelativePath() as file,
    f.getLocation().getStartLine() as start_line,
    f.getLocation().getEndLine() as end_line,
    f.toString() as code
"""

    def get_call_graph_query(self) -> str:
        return """
import swift

from ApplyExpr call, Function caller, Function callee
where 
    call.getEnclosingDecl() = caller and
    call.getStaticTarget() = callee
select 
    caller.getName() as caller_name,
    caller.getLocation().getFile().getRelativePath() as caller_file,
    callee.getName() as callee_name,
    callee.getLocation().getFile().getRelativePath() as callee_file,
    call.getLocation().getStartLine() as call_line
"""


# Registry mapping language names to adapter instances
LANGUAGE_ADAPTERS: Dict[str, LanguageAdapter] = {
    "python": PythonAdapter(),
    "cpp": CppAdapter(),
    "c": CppAdapter(),  # C uses same adapter as C++
    "csharp": CSharpAdapter(),
    "java": JavaAdapter(),
    "kotlin": KotlinAdapter(),
    "javascript": JavaScriptAdapter(),
    "typescript": JavaScriptAdapter(),  # TypeScript uses same adapter
    "go": GoAdapter(),
    "ruby": RubyAdapter(),
    "rust": RustAdapter(),
    "swift": SwiftAdapter(),
}


def get_adapter(language: str) -> LanguageAdapter:
    """
    Get language adapter for a given language.

    Args:
        language: Programming language name

    Returns:
        LanguageAdapter instance

    Raises:
        ValueError: If language is not supported
    """
    adapter = LANGUAGE_ADAPTERS.get(language.lower())
    if not adapter:
        raise ValueError(f"Unsupported language: {language}")
    return adapter
