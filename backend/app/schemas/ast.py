from pydantic import BaseModel, Field
from typing import List, Optional

class FunctionContext(BaseModel):
    """
    Pydantic schema representing structural metadata of an impacted function or method.
    """
    name: str = Field(..., description="Name of the function or method.")
    class_name: Optional[str] = Field(None, description="Name of parent class if applicable.")
    start_line: int = Field(..., description="First line of function declaration.")
    end_line: int = Field(..., description="Last line of function body.")
    arguments: List[str] = Field(default_factory=list, description="List of arguments defined in signature.")
    return_annotation: Optional[str] = Field(None, description="Annotated return type, if specified.")
    function_calls: List[str] = Field(default_factory=list, description="Unique names of functions called within the function.")
    variables: List[str] = Field(default_factory=list, description="Unique names of variables loaded or stored within the function.")
    imported_modules: List[str] = Field(default_factory=list, description="Unique names of modules imported inside the scope.")
    inside_try_block: bool = Field(False, description="True if any impacted changes in this function are inside a try block.")
    inside_loop: bool = Field(False, description="True if any impacted changes in this function are inside a loop (for/while).")
    inside_conditional: bool = Field(False, description="True if any impacted changes in this function are inside a conditional (if).")

class ASTExtractionReport(BaseModel):
    """
    Summarizes the AST analysis context for a parsed python source file.
    """
    file: str = Field(..., description="The name of the file.")
    functions: List[FunctionContext] = Field(default_factory=list, description="Impacted function contexts.")
    error: Optional[str] = Field(None, description="Parser syntax or execution error string if failed.")
