import ast
from typing import List, Optional, Set, Dict, Any
from backend.app.schemas.ast import FunctionContext, ASTExtractionReport

class ASTContextExtractor(ast.NodeVisitor):
    """
    AST Visitor to traverse nodes and extract definitions, class associations,
    variables, calls, and import metadata at function/method scope levels.
    """
    
    def __init__(self):
        self.functions = []
        self.current_class = None
        self.current_function = None

    def visit_ClassDef(self, node):
        # Track class name for method context
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        # Extract function arguments names
        arguments = [arg.arg for arg in node.args.args]
        
        # Extract return type annotation
        return_annotation = None
        if node.returns:
            try:
                return_annotation = ast.unparse(node.returns).strip()
            except Exception:
                pass

        # Build context dictionary
        func_ctx = {
            "name": node.name,
            "class_name": self.current_class,
            "start_line": node.lineno,
            "end_line": node.end_lineno or node.lineno,
            "arguments": arguments,
            "return_annotation": return_annotation,
            "function_calls": set(),
            "variables": set(),
            "imported_modules": set(),
            "node": node
        }

        # Visit internal node statements
        old_func = self.current_function
        self.current_function = func_ctx
        
        self.generic_visit(node)
        
        # Convert tracked sets to sorted lists
        func_ctx["function_calls"] = sorted(list(func_ctx["function_calls"]))
        func_ctx["variables"] = sorted(list(func_ctx["variables"]))
        func_ctx["imported_modules"] = sorted(list(func_ctx["imported_modules"]))
        
        self.functions.append(func_ctx)
        self.current_function = old_func

    def visit_Call(self, node):
        if self.current_function:
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                try:
                    func_name = ast.unparse(node.func)
                except Exception:
                    pass
            if func_name:
                self.current_function["function_calls"].add(func_name)
        self.generic_visit(node)

    def visit_Name(self, node):
        if self.current_function:
            # Gather names referenced in load/store contexts (ignores keywords and definitions)
            if isinstance(node.ctx, (ast.Load, ast.Store)):
                self.current_function["variables"].add(node.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        if self.current_function:
            for alias in node.names:
                self.current_function["imported_modules"].add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.current_function and node.module:
            self.current_function["imported_modules"].add(node.module)
        self.generic_visit(node)


class ASTParser:
    """
    Parser wrapper utilizing Python's built-in `ast` module.
    Responsible for generating trees, tracking errors, and matching diffs.
    """
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tree = None
        self.error = None

    def parse(self) -> bool:
        """
        Parses source code into an AST. Returns True on success, False on SyntaxError.
        """
        if not self.source_code or not self.source_code.strip():
            self.tree = ast.Module(body=[], type_ignores=[])
            return True
            
        try:
            self.tree = ast.parse(self.source_code)
            return True
        except SyntaxError as e:
            self.error = f"SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}"
            return False
        except Exception as e:
            self.error = f"AST Generation Failure: {str(e)}"
            return False

    def extract_impacted_contexts(self, changed_lines: List[int]) -> ASTExtractionReport:
        """
        Extracts structural contexts of functions and class methods containing changes.
        """
        if self.error:
            return ASTExtractionReport(file="", functions=[], error=self.error)

        if not self.tree:
            self.parse()
            if self.error:
                return ASTExtractionReport(file="", functions=[], error=self.error)

        extractor = ASTContextExtractor()
        extractor.visit(self.tree)

        impacted_functions = []
        for f in extractor.functions:
            start = f["start_line"]
            end = f["end_line"]
            
            # Find subset of changed lines located within this function boundary
            overlapping_lines = [line for line in changed_lines if start <= line <= end]
            if not overlapping_lines:
                continue

            # Determine control structure nesting container states
            func_node = f["node"]
            inside_try = False
            inside_loop = False
            inside_conditional = False

            for sub_node in ast.walk(func_node):
                if isinstance(sub_node, ast.Try):
                    t_start = sub_node.lineno
                    t_end = sub_node.end_lineno or t_start
                    if any(t_start <= line <= t_end for line in overlapping_lines):
                        inside_try = True
                elif isinstance(sub_node, (ast.For, ast.While)):
                    l_start = sub_node.lineno
                    l_end = sub_node.end_lineno or l_start
                    if any(l_start <= line <= l_end for line in overlapping_lines):
                        inside_loop = True
                elif isinstance(sub_node, ast.If):
                    c_start = sub_node.lineno
                    c_end = sub_node.end_lineno or c_start
                    if any(c_start <= line <= c_end for line in overlapping_lines):
                        inside_conditional = True

            ctx = FunctionContext(
                name=f["name"],
                class_name=f["class_name"],
                start_line=start,
                end_line=end,
                arguments=f["arguments"],
                return_annotation=f["return_annotation"],
                function_calls=f["function_calls"],
                variables=f["variables"],
                imported_modules=f["imported_modules"],
                inside_try_block=inside_try,
                inside_loop=inside_loop,
                inside_conditional=inside_conditional
            )
            impacted_functions.append(ctx)

        return ASTExtractionReport(file="", functions=impacted_functions)
