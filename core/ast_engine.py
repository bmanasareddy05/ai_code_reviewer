import ast
import re
from typing import Dict, Any, List


class PythonASTAnalyzer(ast.NodeVisitor):
    """Deep structural static analysis for Python using standard library AST."""
    def __init__(self):
        self.issues: List[str] = []
        self.complexity: int = 1
        self.max_nesting: int = 0
        self.current_nesting: int = 0
        self.function_count: int = 0
        self.imported_modules: set = set()
        self.used_symbols: set = set()

    def _track_nesting(self, node):
        self.current_nesting += 1
        if self.current_nesting > self.max_nesting:
            self.max_nesting = self.current_nesting
        if self.current_nesting > 3:
            self.issues.append(f"Deeply nested block at line {getattr(node, 'lineno', '?')} (Depth: {self.current_nesting}).")
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_If(self, node):
        self.complexity += 1
        self._track_nesting(node)

    def visit_For(self, node):
        self.complexity += 1
        self._track_nesting(node)

    def visit_While(self, node):
        self.complexity += 1
        self._track_nesting(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imported_modules.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imported_modules.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_symbols.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.function_count += 1
        length = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else len(node.body)
        if length > 25:
            self.issues.append(f"Function '{node.name}' has {length} lines. Refactor for single responsibility.")
        self.generic_visit(node)


class MultiLangStaticScanner:
    """Static checks for compiled languages (C, C++, Java)."""

    DANGEROUS_C_FUNCS = {
        "gets": "Deprecated 'gets()' causes severe buffer overflow vulnerabilities.",
        "strcpy": "Unsafe 'strcpy()' detected. Use 'strncpy()' or safer alternatives.",
        "sprintf": "'sprintf()' lacks boundary checks. Prefer 'snprintf()'."
    }

    @classmethod
    def scan_compiled_code(cls, code: str, language: str) -> Dict[str, Any]:
        issues = []
        lines = code.splitlines()
        metrics = {"lines_of_code": len(lines), "max_nesting_depth": 0}

        # 1. Structural Bracket & Parenthesis Balancing
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        for line_num, line in enumerate(lines, start=1):
            for char in line:
                if char in "({[":
                    stack.append((char, line_num))
                elif char in ")}]":
                    if not stack or stack[-1][0] != mapping[char]:
                        issues.append(f"Mismatched bracket '{char}' around line {line_num}.")
                        break
                    stack.pop()

        if stack:
            unclosed_char, unclosed_line = stack[-1]
            issues.append(f"Unclosed '{unclosed_char}' starting at line {unclosed_line}.")

        # 2. Memory Leak and Safety Diagnostics (C / C++)
        if language in ["C", "C++"]:
            has_malloc = bool(re.search(r'\b(malloc|calloc)\s*\(', code))
            has_free = bool(re.search(r'\bfree\s*\(', code))
            if has_malloc and not has_free:
                issues.append("Potential memory leak: Dynamic memory allocated without matching 'free()'.")

            has_new = bool(re.search(r'\bnew\s+', code))
            has_delete = bool(re.search(r'\bdelete\s+', code))
            if has_new and not has_delete:
                issues.append("Dynamic allocation 'new' detected without matching 'delete'.")

            for func, warning in cls.DANGEROUS_C_FUNCS.items():
                if re.search(rf'\b{func}\s*\(', code):
                    issues.append(warning)

        # 3. Java Specific Smells
        if language == "Java":
            if re.search(r'for\s*\(.*\)\s*\{[^}]*\+=\s*["\']', code):
                issues.append("String concatenation inside loop. Use StringBuilder to optimize memory allocations.")

        # 4. Nesting Depth
        current_depth = 0
        max_depth = 0
        for char in code:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        metrics["max_nesting_depth"] = max_depth

        if max_depth > 3:
            issues.append(f"High nesting level detected ({max_depth} levels). Decompose into helper methods.")

        return {
            "valid_syntax": len(stack) == 0,
            "issues": issues,
            "metrics": metrics
        }


class StaticASTEngine:
    @staticmethod
    def calculate_health_score(ast_issues_count: int, ai_bugs_count: int, complexity: Any) -> int:
        """Calculates a normalized Code Quality Score out of 100."""
        score = 100
        score -= min(ast_issues_count * 10, 30)
        score -= min(ai_bugs_count * 15, 40)
        
        if isinstance(complexity, (int, float)):
            if complexity > 10:
                score -= 20
            elif complexity > 5:
                score -= 10
        return max(score, 10)

    @classmethod
    def run_analysis(cls, code: str, language: str) -> Dict[str, Any]:
        if language.lower() == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return {
                    "valid_syntax": False,
                    "issues": [f"Syntax Error [Line {e.lineno}, Col {e.offset}]: {e.msg}"],
                    "metrics": {"cyclomatic_complexity": "N/A", "max_nesting_depth": "N/A"}
                }

            visitor = PythonASTAnalyzer()
            visitor.visit(tree)

            unused = visitor.imported_modules - visitor.used_symbols
            for imp in unused:
                visitor.issues.append(f"Unused module import: '{imp}'")

            return {
                "valid_syntax": True,
                "issues": visitor.issues,
                "metrics": {
                    "cyclomatic_complexity": visitor.complexity,
                    "max_nesting_depth": visitor.max_nesting,
                    "function_count": visitor.function_count
                }
            }
        else:
            return MultiLangStaticScanner.scan_compiled_code(code, language)