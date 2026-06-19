import pytest
from backend.app.parsers.ast_parser import ASTParser

# Sample Python source code code text for unit testing AST parsing
SAMPLE_PY_SOURCE = (
    "import os\n"
    "import math\n\n"
    "class CalculatorService:\n"
    "    def calculate(self, x: float, y: float) -> float:\n"
    "        total = x + y\n"
    "        print('debugging calculate call')\n"
    "        return total\n\n"
    "def orchestrate_data(data_list: list) -> None:\n"
    "    try:\n"
    "        for data in data_list:\n"
    "            if data > 0:\n"
    "                os.getenv('RUN_MODE')\n"
    "                print(data)\n"
    "    except Exception as e:\n"
    "        pass\n"
)

def test_ast_parser_valid_extraction():
    """
    Verifies that the ASTParser parses standard python functions and class methods,
    correctly identifying arguments, returns, variables, imports, calls, and control blocks.
    """
    parser = ASTParser(SAMPLE_PY_SOURCE)
    success = parser.parse()
    assert success is True
    assert parser.error is None
    
    # 1. Test CalculatorService.calculate method context (Changed line 6)
    # Line 6 is: "total = x + y" (inside class method)
    report = parser.extract_impacted_contexts([6])
    assert len(report.functions) == 1
    func = report.functions[0]
    
    assert func.name == "calculate"
    assert func.class_name == "CalculatorService"
    assert func.start_line == 5
    assert func.end_line == 8
    assert func.arguments == ["self", "x", "y"]
    assert func.return_annotation == "float"
    assert "print" in func.function_calls
    assert "total" in func.variables
    assert "x" in func.variables
    
    # Check that line 6 is not in try, loop, or conditional blocks
    assert func.inside_try_block is False
    assert func.inside_loop is False
    assert func.inside_conditional is False

    # 2. Test orchestrate_data function context (Changed line 14)
    # Line 14 is: "os.getenv('RUN_MODE')" (inside try, loop, conditional)
    report_nested = parser.extract_impacted_contexts([14])
    assert len(report_nested.functions) == 1
    func_nest = report_nested.functions[0]
    
    assert func_nest.name == "orchestrate_data"
    assert func_nest.class_name is None
    assert func_nest.arguments == ["data_list"]
    assert func_nest.return_annotation == "None"
    assert "os.getenv" in func_nest.function_calls or "os" in func_nest.imported_modules
    assert "data" in func_nest.variables
    assert "data_list" in func_nest.variables
    
    # Check control flow nesting matching line 14
    assert func_nest.inside_try_block is True
    assert func_nest.inside_loop is True
    assert func_nest.inside_conditional is True


def test_ast_parser_syntax_error_resilience():
    """
    Verifies that ASTParser gracefully handles syntax errors, returning the syntax traceback error.
    """
    invalid_source = "def broken_syntax(:\n    pass"
    parser = ASTParser(invalid_source)
    success = parser.parse()
    
    assert success is False
    assert parser.error is not None
    assert "SyntaxError" in parser.error
    
    report = parser.extract_impacted_contexts([1])
    assert report.error is not None
    assert len(report.functions) == 0

def test_ast_parser_empty_file():
    """
    Verifies that parsing empty files executes without crashing.
    """
    parser = ASTParser("")
    success = parser.parse()
    assert success is True
    assert parser.error is None
    
    report = parser.extract_impacted_contexts([1])
    assert len(report.functions) == 0
